# ASTQ — Test Plan and Test Report

**Version:** 1.0 · **Executed:** 19 Oct 2026 · **Environment:** Linux, Python 3.12.3, Flask 3.1, pytest 9.1, SQLite

## 1. Test strategy (SDD §14)
| Level | Purpose | Location | Tooling |
|---|---|---|---|
| Unit | validation, status rules, parsers, path safety, registry safety | `tests/unit` | pytest |
| Integration | route → service → runner → parser → DB with **real subprocesses** and a temp DB | `tests/integration` | pytest, Flask test client |
| API | ASTQ endpoints, error format, CSRF, pages; plus demo-shop smoke with Requests | `tests/api` | Flask client, Requests |
| UI | dashboard journeys via page objects | `tests/ui` | Selenium 4 (headless Chrome) |
| Performance | small authorised baseline | `performance/baseline.jmx` | JMeter |

**Entry:** clean checkout, dependencies installed. **Exit:** all core tests pass; no open High defects.
**Isolation:** every test uses a temp SQLite file and temp artifact dir; ports are chosen dynamically.

## 2. Results — core suite (evidence: `docs/evidence/`)
| Level | File | Tests | Passed | Failed |
|---|---|---|---|---|
| Unit | `test_junit_parser.py` | 10 | 10 | 0 |
| Unit | `test_run_service.py` | 28 | 28 | 0 |
| Integration | `test_run_flow.py` | 7 | 7 | 0 |
| API | `test_api_endpoints.py` | 27 | 27 | 0 |
| API (demo shop) | `test_demo_api.py` | 7 | 7 | 0 |
| **Total** | | **79** | **79** | **0** |

Duration ≈ 7 s. Lint: `ruff check .` → *All checks passed*.

### Coverage (pytest-cov, `app/`)
**93 % overall (679 statements, 50 missed).** 100 %: config, registry, models, summary builder,
API/dashboard routes. Lowest: `demo_launcher.py` 50 % (auto-start branches, exercised only in live runs), `suites.py` 80 %, `jmeter_parser.py` / `suite_service.py` 90 %.

## 3. Test case catalogue (selected)
| ID | Case | Expected | Result |
|---|---|---|---|
| TC-01 | GET /api/health | 200 `{"status":"ok"}` | Pass |
| TC-02 | List suites | only safe metadata, no command | Pass |
| TC-03 | POST /api/runs valid key | 202 + run id, status QUEUED | Pass |
| TC-04 | POST /api/runs with `bad key; rm -rf /` | 400 `INVALID_SUITE_KEY` | Pass |
| TC-05 | POST unknown suite / disabled suite | 404 / 409 | Pass |
| TC-06 | Run passing pytest suite end-to-end | PASSED, counts 2/0/0/0, rc 0, artifacts | Pass |
| TC-07 | Run failing suite | FAILED (not ERROR), logs show `assert 1 == 2` | Pass |
| TC-08 | Command exceeds timeout | ERROR/TIMEOUT, process killed, app still healthy | Pass |
| TC-09 | Tool produced no JUnit XML | ERROR/PARSE_ERROR, counts `null` | Pass |
| TC-10 | Command binary missing | ERROR/SPAWN_ERROR | Pass |
| TC-11 | Remote `DEMO_BASE_URL` | ERROR/TARGET_NOT_AUTHORIZED | Pass |
| TC-12 | POST returns while run still active | < 1.5 s, status QUEUED/RUNNING then terminal | Pass |
| TC-13 | All tests skipped | ERROR/NO_TESTS_EXECUTED | Pass |
| TC-14 | Artifact route with `..%2F..%2Fconfig.py`, unknown name, symlink escape | 404 / None | Pass |
| TC-15 | Form POST without CSRF token | 400 | Pass |
| TC-16 | History filters + pagination + invalid status | correct totals; 400 | Pass |
| TC-17 | Restart with QUEUED run | ERROR/INTERRUPTED | Pass |
| TC-18 | JUnit/JTL parsers: valid, empty, malformed, inconsistent | counts / `ParseError` | Pass |

## 4. Live system test (through the real server, `python run.py`)
Runs were started via the REST API and inspected via API and browser.

| Run | Suite | Status | Counts (pass/fail/err/skip) | Notes |
|---|---|---|---|---|
| 1 | unit_regression | PASSED | 45 / 0 / 0 / 0 | ~5 s |
| 2 | api_smoke | PASSED | 7 / 0 / 0 / 0 | demo app auto-started and stopped |
| 3 | sample_mixed | FAILED | 2 / 1 / 0 / 1 | expected: intentional failure, assertion visible in log + HTML report |
| 4 | ui_smoke | ERROR (NO_TESTS_EXECUTED) | 0 / 0 / 0 / 3 | expected: no chromedriver here |
| – | performance_baseline | rejected 409 SUITE_DISABLED | – | expected: opt-in |

Screenshots: `docs/screenshots/` (dashboard, suites, history, passed and failed run detail).

## 5. Defects found and fixed during testing
| # | Finding | Fix |
|---|---|---|
| D-1 | Selenium suite showed **PASSED** with 0 passed / 3 skipped (misleading green) | new rule `NO_TESTS_EXECUTED → ERROR`, test TC-13 |
| D-2 | Skip count glyph did not render in the results column | replaced symbols with text labels (`pass/fail/err/skip`) |
| D-3 | Stale RUNNING rows after restart would stay forever | `recover_interrupted_runs()` + test TC-17 |

## 6. Not executed in the build environment (must be verified before evaluation)
| Item | Why | How to verify |
|---|---|---|
| Selenium UI tests (3) | Chromium present but no chromedriver; tests skip cleanly | install Chrome + matching driver, or set `CHROME_BIN` / `CHROMEDRIVER_PATH`, then `pytest tests/ui -v` or press Run on *ui_smoke* — expect 3 passed |
| JMeter baseline | JMeter not installed | install JMeter 5.6.x, `python scripts/set_suite_enabled.py performance_baseline on`, run from dashboard — expect 100 samples, 0 failed |
| GitHub Actions | repository not pushed | push; workflow runs automatically |

## 7. Conclusion
The core platform meets its acceptance criteria: 79/79 automated tests pass at 93 % coverage and a
live end-to-end run demonstrates launch → persisted status → counts → logs/report for passing,
failing and errored suites.
