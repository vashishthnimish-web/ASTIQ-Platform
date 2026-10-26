import pytest

from app.execution import command_registry
from app.execution.demo_launcher import target_is_authorized
from app.execution.runner import RunOutcome
from app.extensions import db
from app.models import TestRun
from app.parsers import ResultSummary
from app.services import report_service, run_service


def outcome(rc=0, timed_out=False, spawn=None):
    return RunOutcome(rc, timed_out, spawn, 1.0)


# ---- status rules (SDD 12) -------------------------------------------------------------
def test_status_passed():
    s = ResultSummary(5, 0, 0, 1)
    assert run_service.determine_status(outcome(0), s, None)[0] == "PASSED"


def test_status_failed_when_tests_fail():
    s = ResultSummary(3, 1, 0, 0)
    status, kind, _ = run_service.determine_status(outcome(1), s, None)
    assert (status, kind) == ("FAILED", None)


def test_status_failed_when_tests_error():
    assert run_service.determine_status(outcome(1), ResultSummary(1, 0, 2, 0), None)[0] == "FAILED"


def test_status_error_on_timeout():
    status, kind, text = run_service.determine_status(outcome(None, timed_out=True), None, None, 30)
    assert (status, kind) == ("ERROR", "TIMEOUT") and "30s" in text


def test_status_error_on_spawn_failure():
    assert run_service.determine_status(outcome(None, spawn="boom"), None, None)[1] == "SPAWN_ERROR"


def test_status_error_on_parse_failure_never_shows_counts():
    status, kind, text = run_service.determine_status(outcome(0), None, "Malformed JUnit XML")
    assert (status, kind) == ("ERROR", "PARSE_ERROR") and "unsuccessful" in text


def test_status_error_when_every_test_was_skipped():
    status, kind, text = run_service.determine_status(outcome(0), ResultSummary(0, 0, 0, 3), None)
    assert (status, kind) == ("ERROR", "NO_TESTS_EXECUTED") and "nothing was verified" in text


def test_status_error_on_nonzero_exit_without_failures():
    status, kind, _ = run_service.determine_status(outcome(5), ResultSummary(0, 0, 0, 0), None)
    assert (status, kind) == ("ERROR", "NONZERO_EXIT")


# ---- creation / validation -------------------------------------------------------------
def test_create_run_unknown_suite(app):
    with app.app_context(), pytest.raises(run_service.SuiteNotFound):
        run_service.create_run("does_not_exist")


@pytest.mark.parametrize("bad", ["", "a b", "../etc/passwd", "x;rm -rf /", "UPPER", None, 5, "a" * 65])
def test_create_run_rejects_invalid_keys(app, bad):
    with app.app_context(), pytest.raises(run_service.InvalidSuiteKey):
        run_service.create_run(bad)


def test_create_run_disabled_suite_conflict(app):
    with app.app_context(), pytest.raises(run_service.SuiteDisabled):
        run_service.create_run("performance_baseline")


def test_create_run_persists_queued_record(app):
    with app.app_context():
        run = run_service.start_run("unit_regression", requested_by="test")
        assert run.status == "QUEUED" and run.id is not None
        assert db.session.get(TestRun, run.id).requested_by == "test"


def test_recover_interrupted_runs_marks_error(app):
    with app.app_context():
        run = run_service.create_run("unit_regression")
        assert run_service.recover_interrupted_runs() == 1
        run = db.session.get(TestRun, run.id)
        assert (run.status, run.error_kind) == ("ERROR", "INTERRUPTED") and run.finished_at


# ---- command registry safety (FR-04) ---------------------------------------------------
def test_every_seeded_suite_has_a_registered_command():
    for d in command_registry.SUITE_DEFINITIONS:
        assert command_registry.get_spec(d["suite_key"]) is not None


def test_registry_commands_are_argument_tuples_not_shell_strings():
    for spec in command_registry.COMMAND_REGISTRY.values():
        assert isinstance(spec.args, tuple) and all(isinstance(a, str) for a in spec.args)


def test_build_args_substitutes_placeholders():
    spec = command_registry.get_spec("api_smoke")
    args = command_registry.build_args(spec, python="py", run_dir="/r/1", jmeter="jm",
                                       demo_base_url="http://127.0.0.1:5001")
    assert args[0] == "py" and "--junitxml=/r/1/junit.xml" in args
    assert not any("{" in a for a in args)


def test_jmeter_args_use_host_and_port():
    spec = command_registry.get_spec("performance_baseline")
    args = command_registry.build_args(spec, python="py", run_dir="/r/2", jmeter="jmeter",
                                       demo_base_url="http://localhost:5055")
    assert "-Jhost=localhost" in args and "-Jport=5055" in args


# ---- target authorisation & path safety -----------------------------------------------
def test_loopback_targets_authorised_remote_not():
    assert target_is_authorized("http://127.0.0.1:5001", False)
    assert target_is_authorized("http://localhost:5001", False)
    assert not target_is_authorized("http://example.com", False)
    assert target_is_authorized("http://example.com", True)


def test_safe_join_blocks_traversal(tmp_path):
    assert report_service.safe_join_under(tmp_path, "1/console.log") is not None
    assert report_service.safe_join_under(tmp_path, "../secret") is None
    assert report_service.safe_join_under(tmp_path, "/etc/passwd") is None


def test_resolve_artifact_only_allow_listed_names(app):
    with app.app_context():
        assert report_service.resolve_artifact(1, "../../config.py") is None
        assert report_service.resolve_artifact(1, "secrets.txt") is None


def test_resolve_artifact_rejects_symlink_escape(app, tmp_path):
    with app.app_context():
        rd = report_service.run_dir(7)
        rd.mkdir(parents=True)
        outside = tmp_path / "outside.txt"
        outside.write_text("secret")
        (rd / "console.log").symlink_to(outside)
        assert report_service.resolve_artifact(7, "console.log") is None
