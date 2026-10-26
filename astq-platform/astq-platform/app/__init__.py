"""ASTQ application factory (SDD 5)."""
from __future__ import annotations

import logging
import secrets
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, session

from app.config import Config
from app.extensions import db, init_executor, migrate


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["ARTIFACTS_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    init_executor(app.config["MAX_CONCURRENT_RUNS"])

    from app import models  # noqa: F401  (register tables)
    from app.routes import api, dashboard, runs, suites

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(suites.bp)
    app.register_blueprint(runs.bp)
    app.register_blueprint(api.bp)

    _register_csrf(app)
    _register_error_handlers(app)
    _register_helpers(app)

    with app.app_context():
        db.create_all()
        from app.services import run_service, suite_service

        suite_service.seed_suites()
        run_service.recover_interrupted_runs()
    return app


# ---------------------------------------------------------------- CSRF (browser forms only)
def _register_csrf(app: Flask) -> None:
    def token() -> str:
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_urlsafe(32)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = token

    @app.before_request
    def _check_csrf():
        if not app.config.get("CSRF_ENABLED", True):
            return
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and not request.path.startswith("/api/"):
            sent = request.form.get("_csrf", "")
            expected = session.get("_csrf", "")
            if not expected or not secrets.compare_digest(sent, expected):
                abort(400, description="Missing or invalid CSRF token")
        return


# ---------------------------------------------------------------- errors
def _wants_json() -> bool:
    return request.path.startswith("/api/")


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _register_error_handlers(app: Flask) -> None:
    from app.services.run_service import RunServiceError

    @app.errorhandler(RunServiceError)
    def _run_error(exc: RunServiceError):
        if _wants_json():
            return jsonify(error_body(exc.code, str(exc))), exc.http_status
        return render_template("error.html", status=exc.http_status, message=str(exc)), exc.http_status

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    def _client_error(exc):
        codes = {400: "BAD_REQUEST", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        if _wants_json():
            return jsonify(error_body(codes[exc.code], exc.description)), exc.code
        return render_template("error.html", status=exc.code, message=exc.description), exc.code

    @app.errorhandler(500)
    def _server_error(exc):
        if _wants_json():
            return jsonify(error_body("INTERNAL_ERROR", "Unexpected server error")), 500
        return render_template("error.html", status=500, message="Unexpected server error"), 500


def _register_helpers(app: Flask) -> None:
    @app.template_filter("dt")
    def _dt(value):
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else "—"

    @app.template_filter("dur")
    def _dur(value):
        if value is None:
            return "—"
        return f"{value:.1f}s" if value < 120 else f"{value / 60:.1f}m"
