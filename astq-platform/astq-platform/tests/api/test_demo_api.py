"""API smoke suite (suite key: api_smoke) - Requests-based checks of the demo shop.

If DEMO_BASE_URL already answers, it is used; otherwise the demo app is started on a free port
for the duration of the session so the suite also runs standalone and in CI.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]


def _up(url):
    try:
        return requests.get(f"{url}/api/health", timeout=1).status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def base_url():
    configured = os.getenv("DEMO_BASE_URL")
    if configured and _up(configured):
        yield configured
        return
    from app.execution.demo_launcher import free_port

    port = free_port()
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen([sys.executable, str(ROOT / "demo_app" / "app.py"), "--port", str(port)],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            if _up(url):
                break
            time.sleep(0.25)
        else:
            pytest.fail("demo app did not start")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture()
def http(base_url):
    s = requests.Session()
    s.base = base_url
    return s


def test_health(http):
    r = http.get(f"{http.base}/api/health", timeout=5)
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_product_catalogue(http):
    r = http.get(f"{http.base}/api/products", timeout=5)
    items = r.json()["products"]
    assert r.status_code == 200 and len(items) >= 3
    assert all({"id", "name", "price", "stock"} <= set(p) for p in items)


def test_single_product_and_404(http):
    assert http.get(f"{http.base}/api/products/1", timeout=5).json()["id"] == 1
    r = http.get(f"{http.base}/api/products/9999", timeout=5)
    assert r.status_code == 404 and r.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_add_to_cart_validation(http):
    assert http.post(f"{http.base}/api/cart", data="x", timeout=5).status_code == 400
    assert http.post(f"{http.base}/api/cart", json={"product_id": "a"}, timeout=5).status_code == 400
    assert http.post(f"{http.base}/api/cart", json={"product_id": 1, "quantity": 0}, timeout=5).status_code == 400
    assert http.post(f"{http.base}/api/cart", json={"product_id": 999}, timeout=5).status_code == 404


def test_out_of_stock_conflict(http):
    r = http.post(f"{http.base}/api/cart", json={"product_id": 3, "quantity": 1}, timeout=5)
    assert r.status_code == 409 and r.json()["error"]["code"] == "OUT_OF_STOCK"


def test_cart_and_checkout_flow(http):
    assert http.post(f"{http.base}/api/checkout", timeout=5).status_code in (201, 409)
    assert http.post(f"{http.base}/api/cart", json={"product_id": 2, "quantity": 2}, timeout=5).status_code == 201
    cart = http.get(f"{http.base}/api/cart", timeout=5).json()
    assert cart["total"] == 2598.0
    order = http.post(f"{http.base}/api/checkout", timeout=5)
    assert order.status_code == 201 and order.json()["total"] == 2598.0
    assert http.post(f"{http.base}/api/checkout", timeout=5).status_code == 409  # cart now empty


def test_home_page_html(http):
    r = http.get(f"{http.base}/", timeout=5)
    assert r.status_code == 200 and "Demo Shop" in r.text
