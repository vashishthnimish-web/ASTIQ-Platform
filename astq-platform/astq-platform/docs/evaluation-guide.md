# ASTQ — Evaluation Guide (demo script, checklist, viva Q&A)

## 1. 10-minute demo script
| Min | Action | What the evaluator sees |
|---|---|---|
| 0–1 | `pip install -r requirements.txt -r requirements-dev.txt` → `python run.py` → open http://127.0.0.1:5000 | app starts from a clean checkout, DB auto-created |
| 1–2 | **Dashboard** | totals, pass-rate, quick-run buttons, recent runs |
| 2–3 | **Test Suites** | 5 suites, types, enabled state; performance suite disabled |
| 3–4 | Run **Unit & Integration Regression** | status QUEUED → RUNNING → PASSED (page auto-refreshes), ≈45 tests |
| 4–5 | Run **Demo Shop API Smoke** | demo app auto-starts; 7/7 pass |
| 5–7 | Run **Sample Mixed Results** | FAILED: 2 pass / 1 fail / 1 skip; open console log (assertion text) and `report.html` (use case B) |
| 7–8 | **Run History** with filters (status=FAILED, suite) | persisted history (use case C) |
| 8–9 | Terminal: `curl -X POST localhost:5000/api/runs -H 'Content-Type: application/json' -d '{"suite_key":"api_smoke"}'` then `curl localhost:5000/api/runs/<id>` | 202 + JSON; error cases 400/404/409 |
| 9–10 | `pytest tests/unit tests/integration tests/api --cov=app -q` | 79 passed, 93 % |

Security talking points to show live: send `{"suite_key":"x; rm -rf /"}` → 400; browse
`/runs/1/artifacts/..%2F..%2Fapp%2Fconfig.py` → 404; POST a form without CSRF → 400.

## 2. Requirement → evidence checklist
| Req. | Where to look |
|---|---|
| FR-01 – FR-03 | dashboard, suites page, Run button |
| FR-04 | `app/execution/command_registry.py` (tuples, no shell) |
| FR-05 – FR-06 | run detail page; `run_service.py` |
| FR-07 – FR-08 | `/runs` filters, `/runs/<id>` |
| FR-09 | `artifacts/runs/<id>/` |
| FR-10 | `docs/api-specification.md`; `tests/api` |
| FR-11 | status table in project report §3.3; try `RUN_TIMEOUT_SECONDS=1` |
| FR-12 | `tests/`; `docs/evidence/report-core.html` |
| FR-13 | `.github/workflows/tests.yml` |
| FR-14 | `README.md`, `docs/` |
| MVP DoD (PRD §18) | project report Appendix A |
| Success metrics 1–6 (PRD §15) | M1 README steps · M2 ≥2 suites persisted · M3 accurate counts · M4 failed run keeps logs, app survives · M5 CI workflow · M6 this script |

## 3. Honest status (say this before being asked)
Verified here: all core tests (79/79), live runs, screenshots. **Not verified here:** Selenium (no
chromedriver), JMeter (not installed), GitHub Actions (not pushed). Procedures are in the test report §6.

## 4. Likely viva questions
1. **Why a subprocess rather than calling pytest in-process?** Isolation: a crashing/hanging suite cannot take down Flask; timeouts can kill the process group; stdout/stderr are captured per run.
2. **How do you prevent command injection?** Browser sends only a validated key; commands live server-side as argument tuples; `shell=False`; tests assert it.
3. **What happens if the app restarts mid-run?** Rows left QUEUED/RUNNING are closed as ERROR/INTERRUPTED at start-up.
4. **FAILED vs ERROR?** FAILED = tests ran and some failed. ERROR = the run could not be trusted (timeout, parse failure, spawn failure, nothing executed).
5. **Why SQLite and threads?** Local MVP scope; `dispatch()` and SQLAlchemy URL isolate the move to a queue (RQ/Celery) and PostgreSQL.
6. **How do you stop testing other people’s sites?** Loopback-only targets unless `ALLOW_REMOTE_TARGETS=true`; performance suite disabled by default.
7. **How are reports protected?** Fixed artifact allow-list, resolved path must stay under the root, HTML reports sandboxed with CSP.
8. **What would you add next?** Authentication, scheduling, run comparison, Docker Compose, durable queue.
9. **How do you know the tests are good?** 93 % coverage plus negative/edge tests (timeouts, malformed XML, traversal, CSRF) and a defect log (D-1…D-3) from real findings.
