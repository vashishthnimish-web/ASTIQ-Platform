"""ASTQ's own REST API (PRD 13). Uses Flask's test client with a temp DB."""
import pytest

from app.extensions import db
from app.models import TestRun, TestSuite
from app.models.test_suite import utcnow


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_list_suites_exposes_safe_metadata_only(client):
    r = client.get("/api/suites")
    assert r.status_code == 200
    suites = r.json["suites"]
    assert {"unit_regression", "api_smoke", "ui_smoke", "performance_baseline"} <= {s["suite_key"] for s in suites}
    for s in suites:
        assert set(s) == {"suite_key", "name", "description", "type", "enabled"}  # no command leak


def test_performance_suite_disabled_by_default(client):
    assert client.get("/api/suites/performance_baseline").json["enabled"] is False


def test_get_suite_and_404(client):
    assert client.get("/api/suites/api_smoke").json["type"] == "API"
    r = client.get("/api/suites/nope")
    assert r.status_code == 404 and r.json["error"]["code"] == "SUITE_NOT_FOUND"


def test_post_run_returns_202_with_run_id(client):
    r = client.post("/api/runs", json={"suite_key": "api_smoke"})
    assert r.status_code == 202
    assert r.json["status"] == "QUEUED" and isinstance(r.json["run_id"], int)


@pytest.mark.parametrize("payload", [None, {}, {"other": 1}, [1, 2]])
def test_post_run_bad_body_400(client, payload):
    r = client.post("/api/runs", json=payload) if payload is not None else client.post("/api/runs", data="not json")
    assert r.status_code == 400 and r.json["error"]["code"] == "INVALID_REQUEST"


def test_post_run_invalid_key_400(client):
    r = client.post("/api/runs", json={"suite_key": "bad key; rm -rf /"})
    assert r.status_code == 400 and r.json["error"]["code"] == "INVALID_SUITE_KEY"


def test_post_run_unknown_suite_404(client):
    r = client.post("/api/runs", json={"suite_key": "ghost"})
    assert r.status_code == 404 and r.json["error"]["code"] == "SUITE_NOT_FOUND"


def test_post_run_disabled_suite_409(client):
    r = client.post("/api/runs", json={"suite_key": "performance_baseline"})
    assert r.status_code == 409 and r.json["error"]["code"] == "SUITE_DISABLED"


def test_get_run_detail_and_404(client):
    rid = client.post("/api/runs", json={"suite_key": "unit_regression"}).json["run_id"]
    body = client.get(f"/api/runs/{rid}").json
    assert body["id"] == rid and body["suite_key"] == "unit_regression" and body["status"] == "QUEUED"
    assert set(body["counts"]) == {"passed", "failed", "error", "skipped"}
    r = client.get("/api/runs/99999")
    assert r.status_code == 404 and r.json["error"]["code"] == "RUN_NOT_FOUND"


def _make_runs(app):
    with app.app_context():
        u = TestSuite.query.filter_by(suite_key="unit_regression").one()
        a = TestSuite.query.filter_by(suite_key="api_smoke").one()
        for suite, status in [(u, "PASSED"), (u, "FAILED"), (a, "PASSED"), (a, "ERROR")]:
            db.session.add(TestRun(suite_id=suite.id, status=status, started_at=utcnow(),
                                   finished_at=utcnow(), duration_seconds=1.0))
        db.session.commit()


def test_run_history_filters_and_pagination(app, client):
    _make_runs(app)
    assert client.get("/api/runs").json["total"] == 4
    assert client.get("/api/runs?suite_key=api_smoke").json["total"] == 2
    assert client.get("/api/runs?status=passed").json["total"] == 2
    assert client.get("/api/runs?suite_key=api_smoke&status=ERROR").json["total"] == 1
    page = client.get("/api/runs?per_page=3&page=2").json
    assert len(page["runs"]) == 1 and page["pages"] == 2


def test_run_history_invalid_status_400(client):
    assert client.get("/api/runs?status=bogus").status_code == 400


def test_run_history_newest_first(app, client):
    _make_runs(app)
    ids = [r["id"] for r in client.get("/api/runs").json["runs"]]
    assert ids == sorted(ids, reverse=True)


def test_unknown_api_route_returns_json_404(client):
    r = client.get("/api/nothing")
    assert r.status_code == 404 and r.json["error"]["code"] == "NOT_FOUND"


def test_wrong_method_returns_json_405(client):
    r = client.delete("/api/health")
    assert r.status_code == 405 and r.json["error"]["code"] == "METHOD_NOT_ALLOWED"


# ------------------------------------------------------------------ browser pages & CSRF
@pytest.mark.parametrize("path", ["/", "/suites", "/runs"])
def test_pages_render(client, path):
    assert client.get(path).status_code == 200


def test_form_post_without_csrf_rejected(client):
    r = client.post("/suites/api_smoke/run")
    assert r.status_code == 400


def test_form_post_with_csrf_creates_run_and_redirects(client, app):
    html = client.get("/suites").data.decode()
    token = html.split('name="_csrf" value="')[1].split('"')[0]
    r = client.post("/suites/api_smoke/run", data={"_csrf": token})
    assert r.status_code == 302 and "/runs/" in r.headers["Location"]
    detail = client.get(r.headers["Location"])
    assert detail.status_code == 200 and b"QUEUED" in detail.data


def test_disabled_suite_run_button_is_disabled(client):
    html = client.get("/suites").data.decode()
    row = html.split('data-suite="performance_baseline"')[1].split("</tr>")[0]
    assert "disabled" in row


def test_run_detail_404_page(client):
    assert client.get("/runs/424242").status_code == 404


def test_history_page_filters(client):
    assert client.get("/runs?status=PASSED&suite=api_smoke").status_code == 200
    assert client.get("/runs?status=nonsense").status_code == 400


def test_artifact_route_blocks_traversal_and_unknown(client):
    assert client.get("/runs/1/artifacts/..%2F..%2Fconfig.py").status_code == 404
    assert client.get("/runs/1/artifacts/passwd").status_code == 404
    assert client.get("/runs/1/artifacts/console.log").status_code == 404  # not created yet
