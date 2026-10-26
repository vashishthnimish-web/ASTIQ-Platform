from datetime import UTC, datetime

from app.extensions import db

SUITE_TYPES = ("UI", "API", "PERFORMANCE", "UNIT")


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TestSuite(db.Model):
    __test__ = False  # stop pytest treating this model as a test class
    __tablename__ = "test_suites"

    id = db.Column(db.Integer, primary_key=True)
    suite_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    suite_type = db.Column(db.String(16), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    runs = db.relationship("TestRun", back_populates="suite", lazy="dynamic")

    def to_dict(self) -> dict:
        # Never expose the server-side command (SDD 8 / PRD 13).
        return {
            "suite_key": self.suite_key,
            "name": self.name,
            "description": self.description,
            "type": self.suite_type,
            "enabled": self.enabled,
        }
