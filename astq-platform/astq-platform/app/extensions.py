from concurrent.futures import ThreadPoolExecutor

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

# Worker pool used to execute runs outside the HTTP request thread.
# Its size enforces MAX_CONCURRENT_RUNS; extra runs wait as QUEUED.
_executor: ThreadPoolExecutor | None = None


def init_executor(max_workers: int) -> ThreadPoolExecutor:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False, cancel_futures=False)
    _executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix="astq-run")
    return _executor


def get_executor() -> ThreadPoolExecutor:
    if _executor is None:
        raise RuntimeError("Executor not initialised")
    return _executor
