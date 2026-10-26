"""Dashboard summary metrics (FR-01)."""
from sqlalchemy import func

from app.extensions import db
from app.models import STATUSES, TestRun, TestSuite


def status_counts() -> dict:
    rows = db.session.query(TestRun.status, func.count(TestRun.id)).group_by(TestRun.status).all()
    counts = {s: 0 for s in STATUSES}
    counts.update({status: n for status, n in rows})
    return counts


def pass_rate(counts: dict) -> float | None:
    finished = counts["PASSED"] + counts["FAILED"] + counts["ERROR"]
    return round(100.0 * counts["PASSED"] / finished, 1) if finished else None


def last_run_by_suite() -> dict:
    result = {}
    for suite in TestSuite.query.all():
        result[suite.suite_key] = suite.runs.order_by(TestRun.id.desc()).first()
    return result


def build_dashboard() -> dict:
    counts = status_counts()
    recent = TestRun.query.order_by(TestRun.id.desc()).limit(8).all()
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "pass_rate": pass_rate(counts),
        "recent": recent,
        "last_by_suite": last_run_by_suite(),
    }
