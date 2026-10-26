from app.extensions import db
from app.models.test_suite import utcnow

STATUSES = ("QUEUED", "RUNNING", "PASSED", "FAILED", "ERROR", "CANCELLED")
TERMINAL_STATUSES = ("PASSED", "FAILED", "ERROR", "CANCELLED")


class TestRun(db.Model):
    __test__ = False
    __tablename__ = "test_runs"

    id = db.Column(db.Integer, primary_key=True)
    suite_id = db.Column(db.Integer, db.ForeignKey("test_suites.id"), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default="QUEUED", index=True)
    requested_by = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)
    return_code = db.Column(db.Integer, nullable=True)
    passed_count = db.Column(db.Integer, nullable=True)
    failed_count = db.Column(db.Integer, nullable=True)
    error_count = db.Column(db.Integer, nullable=True)
    skipped_count = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    # TIMEOUT / PARSE_ERROR / SPAWN_ERROR / NONZERO_EXIT / NO_TESTS_EXECUTED / INTERRUPTED (FR-11)
    error_kind = db.Column(db.String(32), nullable=True)
    log_path = db.Column(db.String(255), nullable=True)  # relative to ARTIFACTS_DIR
    report_path = db.Column(db.String(255), nullable=True)  # relative to ARTIFACTS_DIR

    suite = db.relationship("TestSuite", back_populates="runs")

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def artifact_links(self) -> dict:
        """Safe, URL-based references (never raw filesystem paths)."""
        from app.services.report_service import artifact_urls_for_run

        return artifact_urls_for_run(self)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "suite_key": self.suite.suite_key,
            "suite_name": self.suite.name,
            "status": self.status,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "duration_seconds": self.duration_seconds,
            "return_code": self.return_code,
            "counts": {
                "passed": self.passed_count,
                "failed": self.failed_count,
                "error": self.error_count,
                "skipped": self.skipped_count,
            },
            "summary": self.summary,
            "error_kind": self.error_kind,
            "artifacts": self.artifact_links(),
        }


def _iso(dt):
    return dt.isoformat() + "Z" if dt else None
