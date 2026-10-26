from flask import Blueprint, flash, redirect, render_template, url_for

from app.services import run_service, suite_service

bp = Blueprint("suites", __name__)


@bp.get("/suites")
def list_suites():
    return render_template("suites.html", suites=suite_service.list_suites())


@bp.post("/suites/<suite_key>/run")
def start(suite_key: str):
    try:
        run = run_service.start_run(suite_key, requested_by="dashboard")
    except run_service.RunServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("suites.list_suites"))
    flash(f"Run #{run.id} queued for '{suite_key}'.", "info")
    return redirect(url_for("runs.detail", run_id=run.id))
