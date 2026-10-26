# Demo Shop (system under test)

A tiny in-memory e-commerce API used as the **only default target** for ASTQ's API and
performance suites. Start it with `python demo_app/app.py --port 5001`.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | liveness |
| GET | `/api/products`, `/api/products/<id>` | catalogue (404 for unknown id) |
| POST | `/api/cart` | `{"product_id":1,"quantity":2}` → 201; 400 invalid; 404 unknown; 409 out of stock |
| GET | `/api/cart` | cart lines and total |
| POST | `/api/checkout` | 201 order; 409 when cart empty |

ASTQ starts this app automatically for suites that need it when it is not already running.
