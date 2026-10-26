"""REST API (PRD 13 / SDD 8). JSON in, JSON out, consistent error format."""
from flask import Blueprint, jsonify, request

from app import error_body
from app.services import run_service, suite_service

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "astq"})


@bp.get("/suites")
def list_suites():
    return jsonify({"suites": [s.to_dict() for s in suite_service.list_suites()]})


@bp.get("/suites/<suite_key>")
def get_suite(suite_key: str):
    suite = suite_service.get_suite(suite_key)
    if suite is None:
        return jsonify(error_body("SUITE_NOT_FOUND", f"No suite with key '{suite_key}'")), 404
    return jsonify(suite.to_dict())


@bp.post("/runs")
def create_run():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or "suite_key" not in body:
        return jsonify(error_body("INVALID_REQUEST", "JSON body with 'suite_key' is required")), 400
    run = run_service.start_run(body["suite_key"], requested_by="api")
    return jsonify({"run_id": run.id, "status": run.status, "suite_key": run.suite.suite_key,
                    "links": {"self": f"/api/runs/{run.id}"}}), 202


@bp.get("/runs")
def list_runs():
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    status = request.args.get("status")
    from app.models import STATUSES

    if status and status.upper() not in STATUSES:
        return jsonify(error_body("INVALID_REQUEST", f"status must be one of {', '.join(STATUSES)}")), 400
    p = run_service.list_runs(request.args.get("suite_key"), status, page=max(page, 1),
                              per_page=per_page)
    return jsonify({"runs": [r.to_dict() for r in p.items], "page": p.page, "per_page": per_page,
                    "total": p.total, "pages": p.pages})


@bp.get("/runs/<int:run_id>")
def get_run(run_id: int):
    run = run_service.get_run(run_id)
    if run is None:
        return jsonify(error_body("RUN_NOT_FOUND", f"No run with id {run_id}")), 404
    return jsonify(run.to_dict())
