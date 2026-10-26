from flask import Blueprint, render_template

from app.reporting.summary_builder import build_dashboard
from app.services import suite_service

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    return render_template(
        "dashboard.html", data=build_dashboard(), suites=suite_service.list_suites()
    )
