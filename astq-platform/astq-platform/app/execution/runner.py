"""Safe subprocess runner (SDD 6, 9, 11).

* argument list, never shell=True
* stdout/stderr go to files in the run's artifact folder
* hard timeout; process tree is killed on expiry
* never raises into the web process: every outcome becomes a RunOutcome
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("astq.runner")


@dataclass
class RunOutcome:
    return_code: int | None
    timed_out: bool
    spawn_error: str | None
    duration_seconds: float


def run_command(args: list[str], *, cwd: str, run_dir: Path, timeout: int, env_extra: dict | None = None,
                run_id: int | None = None) -> RunOutcome:
    run_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **(env_extra or {})}
    started = time.monotonic()
    with (run_dir / "console.log").open("wb") as out, (run_dir / "error.log").open("wb") as err:
        try:
            proc = subprocess.Popen(
                args, cwd=cwd, env=env, stdout=out, stderr=err, shell=False,
                start_new_session=True,
            )
        except (OSError, ValueError) as exc:
            log.error("run_id=%s component=runner spawn failed: %s", run_id, exc)
            err.write(f"Failed to start process: {exc}\n".encode())
            return RunOutcome(None, False, str(exc), time.monotonic() - started)
        try:
            rc = proc.wait(timeout=timeout)
            return RunOutcome(rc, False, None, time.monotonic() - started)
        except subprocess.TimeoutExpired:
            log.warning("run_id=%s component=runner timeout after %ss", run_id, timeout)
            _kill_tree(proc)
            err.write(f"\nASTQ: run exceeded timeout of {timeout}s and was terminated.\n".encode())
            return RunOutcome(None, True, None, time.monotonic() - started)


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, AttributeError, OSError):
        proc.kill()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:  # pragma: no cover
        pass
