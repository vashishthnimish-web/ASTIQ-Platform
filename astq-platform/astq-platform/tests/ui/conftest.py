"""Selenium fixtures. If no Chrome/Chromium + driver can be started, UI tests are SKIPPED
(never silently passed) so the report shows exactly what ran."""
import socket
import threading

import pytest
from werkzeug.serving import make_server

selenium = pytest.importorskip("selenium")


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    from app import create_app

    tmp = tmp_path_factory.mktemp("ui")
    app = create_app({
        "TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp / 'ui.db'}",
        "ARTIFACTS_DIR": str(tmp / "art"), "RUN_DISPATCH": "none",
    })
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = make_server("127.0.0.1", port, app, threaded=True)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="session")
def driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,900"):
        opts.add_argument(a)
    import os

    if os.getenv("CHROME_BIN"):
        opts.binary_location = os.environ["CHROME_BIN"]
    service = None
    if os.getenv("CHROMEDRIVER_PATH"):
        from selenium.webdriver.chrome.service import Service

        service = Service(os.environ["CHROMEDRIVER_PATH"])
    try:
        d = webdriver.Chrome(options=opts, service=service) if service else webdriver.Chrome(options=opts)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Chrome/Chromium WebDriver unavailable: {str(exc).splitlines()[0][:120]}")
    yield d
    d.quit()


@pytest.fixture()
def screenshot_on_failure(request, driver, tmp_path_factory):
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        import os
        run_dir = os.getenv("ASTQ_RUN_DIR")
        from pathlib import Path

        out = Path(run_dir) / "screenshots" if run_dir else tmp_path_factory.getbasetemp()
        out.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(out / f"{request.node.name}.png"))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    setattr(item, "rep_" + call.when, outcome.get_result())
