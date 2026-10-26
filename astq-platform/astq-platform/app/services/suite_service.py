from app.execution.command_registry import SUITE_DEFINITIONS
from app.extensions import db
from app.models import TestSuite


def list_suites(include_disabled: bool = True):
    q = TestSuite.query.order_by(TestSuite.id)
    if not include_disabled:
        q = q.filter_by(enabled=True)
    return q.all()


def get_suite(suite_key: str) -> TestSuite | None:
    return TestSuite.query.filter_by(suite_key=suite_key).first()


def seed_suites() -> int:
    """Insert any missing suites; refresh text of existing ones but keep their enabled flag."""
    created = 0
    for d in SUITE_DEFINITIONS:
        suite = get_suite(d["suite_key"])
        if suite is None:
            db.session.add(TestSuite(**d))
            created += 1
        else:
            suite.name, suite.description, suite.suite_type = d["name"], d["description"], d["suite_type"]
    db.session.commit()
    return created
