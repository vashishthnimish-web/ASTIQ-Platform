"""Starts the bundled demo app for suites that need a target, if it is not already up."""
from __future__ import annotations

import contextlib
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def target_is_authorized(base_url: str, allow_remote: bool) -> bool:
    host = urlparse(base_url).hostname or ""
    return allow_remote or host in LOOPBACK_HOSTS


def is_up(base_url: str, timeout: float = 1.0) -> bool:
    try:
        return requests.get(f"{base_url}/api/health", timeout=timeout).status_code == 200
    except requests.RequestException:
        return False


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def demo_app_running(base_url: str, project_root: str, wait_seconds: float = 15.0):
    """Yield once the demo app answers on base_url; stop it afterwards if we started it."""
    if is_up(base_url):
        yield None
        return
    parsed = urlparse(base_url)
    port = parsed.port or 5001
    proc = subprocess.Popen(
        [sys.executable, str(Path(project_root) / "demo_app" / "app.py"), "--port", str(port)],
        cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if is_up(base_url):
                break
            time.sleep(0.25)
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            proc.kill()
