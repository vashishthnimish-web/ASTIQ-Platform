"""Safe artifact resolution (FR-09, SDD 6/11): no path traversal, allow-listed names only."""
from __future__ import annotations

from pathlib import Path

from flask import current_app

ARTIFACT_NAMES = {
    "console.log": "text/plain; charset=utf-8",
    "error.log": "text/plain; charset=utf-8",
    "junit.xml": "application/xml",
    "report.html": "text/html; charset=utf-8",
    "results.jtl": "text/csv; charset=utf-8",
}


def artifacts_root() -> Path:
    return Path(current_app.config["ARTIFACTS_DIR"]).resolve()


def run_dir(run_id: int) -> Path:
    return artifacts_root() / str(int(run_id))


def resolve_artifact(run_id: int, name: str) -> Path | None:
    """Return a real file path beneath the artifact root, or None if not allowed/existing."""
    if name not in ARTIFACT_NAMES:
        return None
    candidate = (run_dir(run_id) / name).resolve()
    root = artifacts_root()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def safe_join_under(root: Path, relative: str) -> Path | None:
    """Generic traversal guard (unit-tested)."""
    root = root.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def artifact_urls_for_run(run) -> dict:
    urls = {}
    for name in ARTIFACT_NAMES:
        if resolve_artifact(run.id, name):
            urls[name.split(".")[0] if name != "results.jtl" else "jmeter_results"] = (
                f"/runs/{run.id}/artifacts/{name}"
            )
    return urls


def read_log_excerpt(run_id: int, name: str, limit: int) -> str | None:
    path = resolve_artifact(run_id, name)
    if path is None:
        return None
    data = path.read_bytes()
    text = data[-limit:].decode("utf-8", errors="replace")
    if len(data) > limit:
        text = f"... (showing last {limit} bytes of {len(data)})\n" + text
    return text
