from flask import Blueprint, abort, current_app, render_template, request, send_file

from app.models import STATUSES
from app.services import report_service, run_service, suite_service

bp = Blueprint("runs", __name__)


@bp.get("/runs")
def history():
    suite_key = request.args.get("suite") or None
    status = request.args.get("status") or None
    if status and status.upper() not in STATUSES:
        abort(400, description="Unknown status filter")
    page = request.args.get("page", 1, type=int)
    pagination = run_service.list_runs(suite_key, status, page=max(page, 1), per_page=15)
    return render_template(
        "run_history.html", pagination=pagination, suites=suite_service.list_suites(),
        statuses=STATUSES, f_suite=suite_key, f_status=(status or "").upper(),
    )


@bp.get("/runs/<int:run_id>")
def detail(run_id: int):
    run = run_service.get_run(run_id)
    if run is None:
        abort(404, description=f"Run {run_id} not found")
    limit = current_app.config["MAX_LOG_VIEW_BYTES"]
    return render_template(
        "run_detail.html", run=run,
        console=report_service.read_log_excerpt(run.id, "console.log", limit),
        errlog=report_service.read_log_excerpt(run.id, "error.log", limit),
    )


@bp.get("/runs/<int:run_id>/artifacts/<name>")
def artifact(run_id: int, name: str):
    path = report_service.resolve_artifact(run_id, name)
    if path is None:
        abort(404, description="Artifact not found")
    resp = send_file(path, mimetype=report_service.ARTIFACT_NAMES[name].split(";")[0])
    resp.headers["X-Content-Type-Options"] = "nosniff"
    if name == "report.html":  # keep generated reports isolated from the dashboard origin
        resp.headers["Content-Security-Policy"] = "sandbox allow-scripts"
    return resp
