# ASTQ — Advanced Software Testing and Quality Assurance Platform

A web dashboard that lets student developers **register approved test suites, launch them safely,
store the results, and review logs/reports in one place**. Built with Flask, SQLite, Pytest,
Requests, Selenium and Apache JMeter integration, with GitHub Actions CI.

> Third-year B.Tech CSE project · Version 1.0 · Implements the PRD, System Design and Repository
> Structure documents in `docs/`.

![Dashboard](docs/screenshots/dashboard.png)

## Features
- **Suite catalogue** – server-side registry (`unit_regression`, `api_smoke`, `ui_smoke`, `sample_mixed`, `performance_baseline`).
- **Safe execution** – browser sends only a *suite key*; commands are allow-listed argument lists (no `shell=True`), with timeout, process-group kill, and a loopback-only target policy.
- **Asynchronous runs** – worker pool outside the request thread; `QUEUED → RUNNING → PASSED/FAILED/ERROR`; concurrency limit (`MAX_CONCURRENT_RUNS`).
- **Normalised results** – JUnit XML / JMeter JTL parsed to pass/fail/error/skipped counts. Parse problems are reported as `ERROR`, never as fake numbers.
- **History & detail** – filter by suite/status, paginated; logs, JUnit XML and HTML report served from a path-safe artifact route.
- **REST API** – health, suites, start run (202), history, run detail; uniform JSON errors.
- **Security** – CSRF on forms, input validation, path-traversal guard, no secrets in git, sandboxed report pages.
- **Demo target** – bundled in-memory shop app (`demo_app/`) so no external system is ever tested.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                                    # optional; safe defaults exist
python scripts/init_db.py                               # creates SQLite DB + seeds suites (also automatic on start)
python run.py                                           # http://127.0.0.1:5000
```
Open the dashboard, press **Run** on *Unit & Integration Regression*, then on *Sample Mixed Results*
to see a failing run with evidence. The demo shop starts automatically when a suite needs it
(or manually: `python demo_app/app.py --port 5001`).

## Running the tests
```bash
pytest                                  # unit + integration + api (+ ui, skipped if no browser driver)
pytest tests/unit tests/integration tests/api --cov=app
ruff check .
```
Selenium tests need Chrome + a matching chromedriver (`CHROME_BIN` / `CHROMEDRIVER_PATH` optional).
Without them they are **skipped, and ASTQ reports such a run as `ERROR (NO_TESTS_EXECUTED)`** rather than a misleading pass.

## Suite keys
| Key | Type | Enabled | What it runs |
|---|---|---|---|
| `unit_regression` | UNIT | yes | `tests/unit` + `tests/integration` |
| `api_smoke` | API | yes | `tests/api/test_demo_api.py` against the demo shop |
| `ui_smoke` | UI | yes | Selenium page-object tests of the dashboard |
| `sample_mixed` | UNIT | yes | 2 pass, 1 skip, **1 intentional failure** (for demos) |
| `performance_baseline` | PERFORMANCE | **no** | JMeter 5 threads × 10 loops (see `performance/README.md`) |

## API examples
```bash
curl localhost:5000/api/health
curl localhost:5000/api/suites
curl -X POST localhost:5000/api/runs -H 'Content-Type: application/json' -d '{"suite_key":"api_smoke"}'   # 202
curl "localhost:5000/api/runs?suite_key=api_smoke&status=PASSED&page=1&per_page=10"
curl localhost:5000/api/runs/1
```
Full reference: [`docs/api-specification.md`](docs/api-specification.md).

## Configuration (`.env`)
`SECRET_KEY`, `DATABASE_URL`, `ARTIFACTS_DIR`, `DEMO_BASE_URL`, `RUN_TIMEOUT_SECONDS`, `MAX_CONCURRENT_RUNS`, `JMETER_PATH`, `ALLOW_REMOTE_TARGETS` (keep `false`).

## Architecture
Modular monolith: `routes → services → execution/parsers/reporting → models`.
```
Browser ─► Flask routes (thin) ─► run_service ─► SQLite (TestSuite, TestRun)
                                      │ submit
                                      ▼
                         ThreadPool worker ─► runner (subprocess, timeout) ─► artifacts/runs/<id>/
                                      │                                         console.log error.log
                                      └─► parsers (JUnit/JTL) ─► final status    junit.xml report.html
```
Details: [`docs/system-design-document.md`](docs/system-design-document.md) and the as-built
notes in [`docs/project-report.md`](docs/project-report.md).

## Artifacts
`artifacts/runs/<run_id>/` – `console.log`, `error.log`, `junit.xml`, `report.html`, `results.jtl`.
Generated artifacts and the local DB are git-ignored; clean old runs by deleting folders.

## CI
`.github/workflows/tests.yml` runs ruff + unit/integration/API tests with coverage on every push and
pull request and uploads JUnit, HTML and coverage reports as artifacts.

## Known limitations
Single-user local tool (no login); SQLite; in-process worker pool (queued runs are closed as
`ERROR/INTERRUPTED` after a restart); Selenium needs a locally installed browser driver; JMeter must
be installed separately and was not executable in the build environment (see test report).

## Documentation index
`docs/project-report.md` · `docs/test-plan-and-report.md` · `docs/evaluation-guide.md` ·
`docs/user-manual.md` · `docs/api-specification.md` · `docs/product-requirements-document.md` ·
`docs/system-design-document.md` · `docs/repository-structure.md` · `docs/evidence/` (real test output).

## Contributors
Add team names / roll numbers here.
