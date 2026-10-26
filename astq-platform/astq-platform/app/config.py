"""Environment-based configuration (SDD section 13)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _abs(path_str: str) -> str:
    p = Path(path_str)
    return str(p if p.is_absolute() else BASE_DIR / p)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///astq.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ARTIFACTS_DIR = _abs(os.getenv("ARTIFACTS_DIR", "artifacts/runs"))
    DEMO_BASE_URL = os.getenv("DEMO_BASE_URL", "http://127.0.0.1:5001")
    RUN_TIMEOUT_SECONDS = int(os.getenv("RUN_TIMEOUT_SECONDS", "300"))
    MAX_CONCURRENT_RUNS = int(os.getenv("MAX_CONCURRENT_RUNS", "1"))
    JMETER_PATH = os.getenv("JMETER_PATH", "jmeter")
    # Tests may only target loopback hosts unless this is deliberately switched on (SDD 11).
    ALLOW_REMOTE_TARGETS = os.getenv("ALLOW_REMOTE_TARGETS", "false").lower() == "true"
    PROJECT_ROOT = str(BASE_DIR)
    # "thread" = background worker pool (default), "sync" = run inline (tests),
    # "none" = leave the run QUEUED (API tests).
    RUN_DISPATCH = "thread"
    CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_LOG_VIEW_BYTES = 200_000
