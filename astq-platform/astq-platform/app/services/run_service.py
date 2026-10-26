"""Run lifecycle: create -> QUEUED -> RUNNING -> PASSED/FAILED/ERROR (FR-03/05/06/11)."""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

from flask import current_app

from app.execution import command_registry
from app.execution.demo_launcher import demo_app_running, target_is_authorized
from app.execution.runner import RunOutcome, run_command
from app.extensions import db, get_executor
from app.models import TERMINAL_STATUSES, TestRun, TestSuite
from app.models.test_suite import utcnow
from app.parsers import ParseError, ResultSummary, parse_jmeter_jtl, parse_junit_xml
from app.services import suite_service
from app.services.report_service import ARTIFACT_NAMES, run_dir

log = logging.getLogger("astq.run_service")
SUITE_KEY_RE = re.compile(r"^[a-z0-9_]{1,64}$")


class RunServiceError(Exception):
    code = "RUN_ERROR"
    http_status = 400


class InvalidSuiteKey(RunServiceError):
    code, http_status = "INVALID_SUITE_KEY", 400


class SuiteNotFound(RunServiceError):
    code, http_status = "SUITE_NOT_FOUND", 404


class SuiteDisabled(RunServiceError):
    code, http_status = "SUITE_DISABLED", 409


# --------------------------------------------------------------------------- creation
def create_run(suite_key, requested_by: str | None = None) -> TestRun:
    if not isinstance(suite_key, str) or not SUITE_KEY_RE.match(suite_key):
        raise InvalidSuiteKey("suite_key must be 1-64 characters of a-z, 0-9 or underscore")
    suite = suite_service.get_suite(suite_key)
    if suite is None or command_registry.get_spec(suite_key) is None:
        raise SuiteNotFound(f"No registered suite with key '{suite_key}'")
    if not suite.enabled:
        raise SuiteDisabled(f"Suite '{suite_key}' is disabled")
    run = TestRun(suite_id=suite.id, status="QUEUED", requested_by=requested_by)
    db.session.add(run)
    db.session.commit()  # state is stored before execution (SDD 4)
    log.info("run_id=%s suite_key=%s component=run_service queued", run.id, suite_key)
    return run


def start_run(suite_key, requested_by: str | None = None) -> TestRun:
    run = create_run(suite_key, requested_by)
    dispatch(run.id)
    return run


def dispatch(run_id: int) -> None:
    mode = current_app.config.get("RUN_DISPATCH", "thread")
    if mode == "none":
        return
    app = current_app._get_current_object()
    if mode == "sync":
        execute_run(app, run_id)
    else:
        get_executor().submit(execute_run, app, run_id)  # outside the request thread


# --------------------------------------------------------------------------- status rules
def determine_status(outcome: RunOutcome, summary: ResultSummary | None, parse_error: str | None,
                     timeout: int | None = None):
    """Return (status, error_kind, summary_text). Documented rule (SDD 12):

    * runner problems (spawn failure, timeout, unreadable results) -> ERROR
    * parsed results with any failed/errored test                 -> FAILED
    * non-zero exit code with no failing test (e.g. nothing collected) -> ERROR
    * every test skipped (nothing actually verified, e.g. no browser) -> ERROR / NO_TESTS_EXECUTED
    * otherwise                                                    -> PASSED
    """
    if outcome.spawn_error:
        return "ERROR", "SPAWN_ERROR", f"Could not start the test process: {outcome.spawn_error}"
    if outcome.timed_out:
        return "ERROR", "TIMEOUT", f"Run exceeded the {timeout}s timeout and was terminated."
    if parse_error:
        return (
            "ERROR", "PARSE_ERROR",
            f"Result parsing unsuccessful ({parse_error}). Counts unavailable; see console log.",
        )
    assert summary is not None
    if summary.failed or summary.errors:
        return "FAILED", None, summary.as_text()
    if outcome.return_code not in (0, None):
        return (
            "ERROR", "NONZERO_EXIT",
            f"{summary.as_text()} Process exited with code {outcome.return_code}.",
        )
    if summary.total > 0 and summary.passed == 0:
        return (
            "ERROR", "NO_TESTS_EXECUTED",
            f"{summary.as_text()} No test actually executed, so nothing was verified.",
        )
    return "PASSED", None, summary.as_text()


# --------------------------------------------------------------------------- execution
def execute_run(app, run_id: int) -> None:
    """Runs in a worker thread (or inline in tests). Always attempts to persist a terminal state."""
    with app.app_context():
        run = db.session.get(TestRun, run_id)
        if run is None or run.status != "QUEUED":
            return
        run.status, run.started_at = "RUNNING", utcnow()
        db.session.commit()
        try:
            _execute(app, run)
        except Exception as exc:
            log.exception("run_id=%s component=run_service unexpected failure", run_id)
            db.session.rollback()
            run = db.session.get(TestRun, run_id)
            _finish(run, "ERROR", "INTERNAL_ERROR", f"Unexpected runner failure: {exc}", None, None)


def _execute(app, run: TestRun) -> None:
    cfg = app.config
    suite: TestSuite = run.suite
    spec = command_registry.get_spec(suite.suite_key)
    rdir: Path = run_dir(run.id)
    rdir.mkdir(parents=True, exist_ok=True)
    base_url = cfg["DEMO_BASE_URL"]

    if spec.needs_demo_app and not target_is_authorized(base_url, cfg["ALLOW_REMOTE_TARGETS"]):
        (rdir / "error.log").write_text(
            f"Target {base_url} is not authorised. Only loopback hosts may be tested unless "
            "ALLOW_REMOTE_TARGETS=true is set deliberately.\n"
        )
        run.log_path = f"{run.id}/error.log"
        _finish(run, "ERROR", "TARGET_NOT_AUTHORIZED",
                "Target host is not authorised for testing (see error log).", None, None)
        return

    args = command_registry.build_args(
        spec, python=sys.executable, run_dir=str(rdir), jmeter=cfg["JMETER_PATH"],
        demo_base_url=base_url,
    )
    env = {"DEMO_BASE_URL": base_url, "ASTQ_RUN_ID": str(run.id), "ASTQ_RUN_DIR": str(rdir),
           "PYTHONUNBUFFERED": "1"}
    timeout = cfg["RUN_TIMEOUT_SECONDS"]

    if spec.needs_demo_app:
        with demo_app_running(base_url, cfg["PROJECT_ROOT"]):
            outcome = run_command(args, cwd=cfg["PROJECT_ROOT"], run_dir=rdir, timeout=timeout,
                                  env_extra=env, run_id=run.id)
    else:
        outcome = run_command(args, cwd=cfg["PROJECT_ROOT"], run_dir=rdir, timeout=timeout,
                              env_extra=env, run_id=run.id)

    summary, parse_error = None, None
    if not outcome.spawn_error and not outcome.timed_out:
        parser = parse_junit_xml if spec.result_format == "junit" else parse_jmeter_jtl
        try:
            summary = parser(rdir / spec.result_file)
        except ParseError as exc:
            parse_error = str(exc)

    status, kind, text = determine_status(outcome, summary, parse_error, timeout)
    run.log_path = f"{run.id}/console.log"
    if spec.report_file and (rdir / spec.report_file).is_file():
        run.report_path = f"{run.id}/{spec.report_file}"
    run.return_code = outcome.return_code
    _finish(run, status, kind, text, summary, outcome.duration_seconds)


def _finish(run: TestRun, status: str, kind, text, summary: ResultSummary | None, duration) -> None:
    run.status, run.error_kind, run.summary = status, kind, text
    run.finished_at = utcnow()
    if duration is None and run.started_at:
        duration = (run.finished_at - run.started_at).total_seconds()
    run.duration_seconds = round(duration, 2) if duration is not None else None
    if summary is not None:
        run.passed_count, run.failed_count = summary.passed, summary.failed
        run.error_count, run.skipped_count = summary.errors, summary.skipped
    db.session.commit()
    log.info("run_id=%s suite_key=%s component=run_service finished status=%s",
             run.id, run.suite.suite_key, status)


# --------------------------------------------------------------------------- queries
def get_run(run_id: int) -> TestRun | None:
    return db.session.get(TestRun, run_id)


def list_runs(suite_key: str | None = None, status: str | None = None, page: int = 1,
              per_page: int = 20):
    q = TestRun.query.join(TestSuite)
    if suite_key:
        q = q.filter(TestSuite.suite_key == suite_key)
    if status:
        q = q.filter(TestRun.status == status.upper())
    return q.order_by(TestRun.id.desc()).paginate(page=page, per_page=per_page, error_out=False)


def recover_interrupted_runs() -> int:
    """After a restart no worker owns QUEUED/RUNNING rows; close them so history stays truthful."""
    stale = TestRun.query.filter(TestRun.status.notin_(TERMINAL_STATUSES)).all()
    for run in stale:
        run.status, run.error_kind = "ERROR", "INTERRUPTED"
        run.summary = "Run was interrupted because the application restarted."
        run.finished_at = utcnow()
    db.session.commit()
    return len(stale)


__all__ = [
    "ARTIFACT_NAMES",
    "InvalidSuiteKey",
    "RunServiceError",
    "SuiteDisabled",
    "SuiteNotFound",
    "create_run",
    "determine_status",
    "execute_run",
    "get_run",
    "list_runs",
    "recover_interrupted_runs",
    "start_run",
]
