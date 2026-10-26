"""End-to-end run flow with a real subprocess (no mocks of the runner)."""
import sys
import textwrap

import pytest

from app.execution import command_registry
from app.execution.command_registry import CommandSpec
from app.extensions import db
from app.models import TestRun, TestSuite


@pytest.fixture()
def sync_app(app):
    app.config["RUN_DISPATCH"] = "sync"
    return app


def _register(app, key, args, **kw):
    with app.app_context():
        db.session.add(TestSuite(suite_key=key, name=key, description="t", suite_type="UNIT"))
        db.session.commit()
    command_registry.COMMAND_REGISTRY[key] = CommandSpec(
        args=tuple(args), result_format="junit", result_file="junit.xml", **kw)


@pytest.fixture(autouse=True)
def _cleanup_registry():
    before = set(command_registry.COMMAND_REGISTRY)
    yield
    for k in set(command_registry.COMMAND_REGISTRY) - before:
        del command_registry.COMMAND_REGISTRY[k]


def _pytest_args(path):
    return ("{python}", "-m", "pytest", str(path), "-p", "no:cacheprovider",
            "--junitxml={run_dir}/junit.xml", "-q", "--rootdir", str(path.parent))


def test_passing_suite_end_to_end(sync_app, tmp_path):
    t = tmp_path / "test_ok.py"
    t.write_text("def test_a():\n    assert 1+1==2\n\ndef test_b():\n    assert True\n")
    _register(sync_app, "e2e_pass", _pytest_args(t))
    with sync_app.test_client() as c:
        r = c.post("/api/runs", json={"suite_key": "e2e_pass"})
        assert r.status_code == 202
        run_id = r.json["run_id"]
        body = c.get(f"/api/runs/{run_id}").json
    assert body["status"] == "PASSED"
    assert body["counts"] == {"passed": 2, "failed": 0, "error": 0, "skipped": 0}
    assert body["return_code"] == 0 and body["duration_seconds"] >= 0
    assert "console.log" in str(body["artifacts"]) and body["started_at"] and body["finished_at"]


def test_failing_suite_is_failed_not_error_and_keeps_logs(sync_app, tmp_path):
    t = tmp_path / "test_bad.py"
    t.write_text("def test_ok():\n    assert True\n\ndef test_bad():\n    assert 1 == 2\n")
    _register(sync_app, "e2e_fail", _pytest_args(t))
    with sync_app.test_client() as c:
        run_id = c.post("/api/runs", json={"suite_key": "e2e_fail"}).json["run_id"]
        body = c.get(f"/api/runs/{run_id}").json
        assert body["status"] == "FAILED" and body["counts"]["failed"] == 1
        page = c.get(f"/runs/{run_id}")
        assert page.status_code == 200 and b"assert 1 == 2" in page.data
        assert c.get(f"/runs/{run_id}/artifacts/console.log").status_code == 200


def test_timeout_is_error_and_app_survives(sync_app):
    sync_app.config["RUN_TIMEOUT_SECONDS"] = 1
    _register(sync_app, "e2e_sleep", ("{python}", "-c", "import time; time.sleep(30)"))
    with sync_app.test_client() as c:
        run_id = c.post("/api/runs", json={"suite_key": "e2e_sleep"}).json["run_id"]
        body = c.get(f"/api/runs/{run_id}").json
        assert (body["status"], body["error_kind"]) == ("ERROR", "TIMEOUT")
        assert c.get("/api/health").status_code == 200


def test_missing_junit_is_parse_error_not_fake_counts(sync_app):
    _register(sync_app, "e2e_noxml", ("{python}", "-c", "print('hello')"))
    with sync_app.test_client() as c:
        run_id = c.post("/api/runs", json={"suite_key": "e2e_noxml"}).json["run_id"]
        body = c.get(f"/api/runs/{run_id}").json
    assert (body["status"], body["error_kind"]) == ("ERROR", "PARSE_ERROR")
    assert body["counts"]["passed"] is None  # no misleading numbers (PRD 12)


def test_unstartable_command_is_spawn_error(sync_app):
    _register(sync_app, "e2e_nobin", ("/definitely/not/a/binary",))
    with sync_app.test_client() as c:
        run_id = c.post("/api/runs", json={"suite_key": "e2e_nobin"}).json["run_id"]
        assert c.get(f"/api/runs/{run_id}").json["error_kind"] == "SPAWN_ERROR"


def test_unauthorised_target_blocks_run(sync_app):
    sync_app.config["DEMO_BASE_URL"] = "http://example.com"
    with sync_app.app_context():
        s = TestSuite.query.filter_by(suite_key="api_smoke").one()
        assert s.enabled
    with sync_app.test_client() as c:
        run_id = c.post("/api/runs", json={"suite_key": "api_smoke"}).json["run_id"]
        body = c.get(f"/api/runs/{run_id}").json
    assert (body["status"], body["error_kind"]) == ("ERROR", "TARGET_NOT_AUTHORIZED")


def test_background_thread_dispatch_does_not_block_request(app, tmp_path):
    """RUN_DISPATCH=thread returns 202 while the run is still QUEUED/RUNNING (FR-03, US-02)."""
    import time

    app.config["RUN_DISPATCH"] = "thread"
    _register(app, "e2e_bg", ("{python}", "-c", "import time; time.sleep(2)"))
    with app.test_client() as c:
        t0 = time.monotonic()
        r = c.post("/api/runs", json={"suite_key": "e2e_bg"})
        assert r.status_code == 202 and time.monotonic() - t0 < 1.5
        run_id = r.json["run_id"]
        assert c.get(f"/api/runs/{run_id}").json["status"] in ("QUEUED", "RUNNING")
        for _ in range(60):
            if c.get(f"/api/runs/{run_id}").json["status"] not in ("QUEUED", "RUNNING"):
                break
            time.sleep(0.25)
        assert c.get(f"/api/runs/{run_id}").json["status"] == "ERROR"  # no junit.xml -> parse error
    with app.app_context():
        assert db.session.get(TestRun, run_id).finished_at is not None
    assert sys.version_info >= (3, 11) and textwrap  # keep imports used
