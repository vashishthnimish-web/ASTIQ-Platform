# ASTQ — User Manual

## 1. Install and start
1. Install Python 3.11+ (3.12 recommended).
2. `python -m venv .venv` and activate it.
3. `pip install -r requirements.txt -r requirements-dev.txt`
4. Optional: `cp .env.example .env` and adjust values.
5. `python run.py` → open **http://127.0.0.1:5000**.

## 2. Pages
| Page | Use |
|---|---|
| **Dashboard** | totals, pass rate, quick **Run** buttons per enabled suite, 8 most recent runs |
| **Test Suites** | name, key, type, description, enabled state, **Run** (disabled suites cannot be run) |
| **Run History** | table of runs; filter by suite and status; paginated |
| **Run Detail** | status badge, timestamps, duration, return code, counts, summary, links to `console.log`, `error.log`, `junit.xml`, `report.html`; log excerpts below |

## 3. Running a suite
1. Open *Test Suites* (or the dashboard) and press **Run**. You are taken to the run page.
2. The status moves QUEUED → RUNNING → PASSED/FAILED/ERROR; the page refreshes automatically.
3. Read the counts and, for failures, the console log; open `report.html` for the full Pytest report.

## 4. Reading statuses
| Status | Meaning | What to do |
|---|---|---|
| PASSED | tests ran and passed | – |
| FAILED | one or more tests failed | read the console log / report |
| ERROR | the run could not be trusted | check *error kind* in the summary: TIMEOUT (raise `RUN_TIMEOUT_SECONDS`), PARSE_ERROR (open console log), NO_TESTS_EXECUTED (e.g. no browser driver), TARGET_NOT_AUTHORIZED (remote target) |
| QUEUED/RUNNING | in progress (only `MAX_CONCURRENT_RUNS` run at once) | wait |

## 4a. Enabling the performance suite
Install Java and JMeter, then `python scripts/set_suite_enabled.py performance_baseline on` (see `performance/README.md`).

## 5. API use
See `docs/api-specification.md`. Example: `curl -X POST localhost:5000/api/runs -H 'Content-Type: application/json' -d '{"suite_key":"unit_regression"}'`.

## 6. Housekeeping & troubleshooting
| Problem | Fix |
|---|---|
| Port 5000 busy | `PORT=5050 python run.py` |
| UI suite → ERROR (NO_TESTS_EXECUTED) | install Chrome and a matching chromedriver, or set `CHROME_BIN` / `CHROMEDRIVER_PATH` |
| `api_smoke` fails to connect | port in `DEMO_BASE_URL` in use; change it |
| Reset everything | stop the app, delete `instance/astq.db` and `artifacts/runs/*` |
| Old artifacts piling up | delete folders under `artifacts/runs/` (no automatic retention in v1.0) |
