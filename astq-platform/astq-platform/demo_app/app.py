"""Demo e-commerce app: the controlled system under test (SDD 1, 10).

Run:  python demo_app/app.py --port 5001
Pure in-memory; resets on restart.
"""
import argparse
import threading

from flask import Flask, jsonify, render_template, request

PRODUCTS = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 3499.00, "stock": 25},
    {"id": 2, "name": "Wireless Mouse", "price": 1299.00, "stock": 60},
    {"id": 3, "name": "USB-C Hub", "price": 1899.00, "stock": 0},
    {"id": 4, "name": "27-inch Monitor", "price": 15999.00, "stock": 8},
]


def create_demo_app() -> Flask:
    app = Flask(__name__)
    state = {"cart": {}, "orders": []}
    lock = threading.Lock()

    def err(code, message, status):
        return jsonify({"error": {"code": code, "message": message}}), status

    def find(pid):
        return next((p for p in PRODUCTS if p["id"] == pid), None)

    @app.get("/")
    def home():
        return render_template("shop.html", products=PRODUCTS)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "demo-shop"})

    @app.get("/api/products")
    def products():
        return jsonify({"products": PRODUCTS})

    @app.get("/api/products/<int:pid>")
    def product(pid):
        p = find(pid)
        return jsonify(p) if p else err("PRODUCT_NOT_FOUND", f"No product {pid}", 404)

    @app.post("/api/cart")
    def add_to_cart():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return err("INVALID_REQUEST", "JSON body required", 400)
        pid, qty = body.get("product_id"), body.get("quantity", 1)
        if not isinstance(pid, int) or not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            return err("INVALID_REQUEST", "product_id and positive integer quantity required", 400)
        p = find(pid)
        if p is None:
            return err("PRODUCT_NOT_FOUND", f"No product {pid}", 404)
        with lock:
            wanted = state["cart"].get(pid, 0) + qty
            if wanted > p["stock"]:
                return err("OUT_OF_STOCK", f"Only {p['stock']} of '{p['name']}' in stock", 409)
            state["cart"][pid] = wanted
        return jsonify({"cart": {str(k): v for k, v in state["cart"].items()}}), 201

    @app.get("/api/cart")
    def get_cart():
        with lock:
            items = [{"product_id": k, "quantity": v, "line_total": round(find(k)["price"] * v, 2)}
                     for k, v in state["cart"].items()]
        return jsonify({"items": items, "total": round(sum(i["line_total"] for i in items), 2)})

    @app.post("/api/checkout")
    def checkout():
        with lock:
            if not state["cart"]:
                return err("EMPTY_CART", "Cart is empty", 409)
            total = 0.0
            for pid, qty in state["cart"].items():
                p = find(pid)
                p["stock"] -= qty
                total += p["price"] * qty
            order = {"order_id": len(state["orders"]) + 1, "total": round(total, 2)}
            state["orders"].append(order)
            state["cart"].clear()
        return jsonify(order), 201

    return app


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    create_demo_app().run(host=a.host, port=a.port, threaded=True)
