# Product Requirements Document (PRD) — ASTQ

**Project:** Advanced Software Testing and Quality Assurance Platform  
**Version:** 1.0  
**Audience:** Third-year B.Tech CSE project team / evaluator

## 1. Executive Summary

**Product:** Advanced Software Testing and Quality Assurance Platform (ASTQ).

**Summary:** ASTQ is a web-based dashboard that helps student developers register approved test suites, launch automated tests, inspect execution results, and access reports in one place. It combines a Flask web application with Pytest, Selenium, Requests-based API tests, Apache JMeter integration, and a SQLite database.

**Problem:** Students often run different testing tools independently and review results in separate terminals or report files. This makes it harder to track runs, compare outcomes, demonstrate testing coverage, and present a coherent QA workflow.

**Solution:** ASTQ provides a central interface for approved suites, execution history, normalized pass/fail summaries, logs, and reports, while keeping test execution isolated from web requests.

## 2. Product Vision and Objectives

**Vision:** Make automated software testing easier to run, understand, and demonstrate through one accessible quality-assurance dashboard.

**Objective 1:** Provide one place to discover and launch registered test suites.

**Objective 2:** Persist test-run history and make outcomes easy to inspect.

**Objective 3:** Integrate UI, API, unit/regression, and basic performance testing tools.

**Objective 4:** Demonstrate software-engineering practices such as modular design, REST APIs, automated tests, version control, and CI.

**Objective 5:** Keep the initial product small enough for a third-year B.Tech CSE project and expand it in clearly scoped phases.

## 3. Target Users and Personas

**Primary user — Student developer:** Wants to run tests for a project, inspect failures, and demonstrate the test process to a faculty evaluator.

**Secondary user — Project teammate:** Wants consistent test commands, shared run history, and a repeatable workflow.

**Evaluator / mentor:** Wants to understand supported test types, inspect evidence of execution, and review project quality.

**MVP assumption:** The first release is intended for local use by a small student team. Multi-user roles and public hosting are optional later enhancements.

## 4. User Problems and Use Cases

**Pain point 1:** Tests are launched through different commands and tools, so the overall status is difficult to see quickly.

**Pain point 2:** Past results may be lost in terminal output or scattered files.

**Pain point 3:** A demonstration may show test execution but not a persistent, understandable record.

**Use case A:** A student opens the dashboard, selects the API smoke suite, launches it, and reviews the result summary.

**Use case B:** A student opens a failed run, reviews logs and the generated report, and uses the failure evidence to debug.

**Use case C:** A teammate checks run history to confirm that a regression suite passed after a code change.

**Use case D:** A CI workflow runs unit/API checks on a pull request and stores the test report as an artifact.

## 5. Scope

**In scope — MVP:** Flask web dashboard; SQLite persistence; registered suite catalogue; controlled subprocess-based execution; Pytest results; JUnit XML parsing; run status/history/detail pages; log and report links; basic REST endpoints; unit and API tests for ASTQ; GitHub Actions CI.

**In scope — planned extensions:** Selenium UI suite and page objects; Requests-based API suite; optional Apache JMeter baseline against a controlled demo app; screenshots on UI failures; richer filtering and summary metrics.

**Out of scope for MVP:** Public multi-tenant SaaS; distributed execution grid; arbitrary user-supplied test code; unrestricted testing of external targets; enterprise role hierarchy; advanced analytics; automated production deployments; full commercial test-management functionality.

## 6. Functional Requirements

**FR-01 — Dashboard:** The system shall show summary information about recent runs, their status, and quick access to test suites.

**FR-02 — Suite catalogue:** The system shall list registered suites with name, description, type, and enabled/disabled state.

**FR-03 — Start a run:** The system shall let a user start an enabled suite using its stable suite identifier.

**FR-04 — Safe execution:** The system shall map suite identifiers to server-side allow-listed commands and shall not accept arbitrary shell commands from the browser.

**FR-05 — Run lifecycle:** The system shall record queued/running/terminal status, start and finish timestamps, duration, and process return code.

**FR-06 — Result summary:** The system shall store pass, fail, error, and skipped counts where the test tool provides them.

**FR-07 — Run history:** The system shall list past runs and support basic filtering by suite and status.

**FR-08 — Run detail:** The system shall display a run's suite, status, duration, summary counts, and safe links to logs/reports.

**FR-09 — Artifact storage:** The system shall save run-specific logs and structured reports under a controlled artifact directory.

**FR-10 — REST API:** The system shall expose endpoints to check health, list suites, start runs, list run history, and retrieve run details.

**FR-11 — Error handling:** The system shall distinguish test failures from execution errors, timeouts, and result-parsing errors where feasible.

**FR-12 — Automated tests:** The repository shall include unit and API/integration tests for critical ASTQ behavior.

**FR-13 — Continuous integration:** GitHub Actions shall run a core automated test set on pushes and pull requests.

**FR-14 — Documentation:** The project shall include setup instructions, architecture notes, API examples, known limitations, and guidance for running tests.

## 7. Non-Functional Requirements

**Usability:** A first-time evaluator should be able to find a suite and understand a completed run without reading source code.

**Performance:** Normal dashboard requests should be responsive for a small student-project dataset; long-running tests must not block the web request thread.

**Reliability:** A runner failure should not crash the Flask application, and the system should retain diagnostic logs for failed runs.

**Security:** Validate inputs, avoid shell injection, keep secrets out of source control, restrict test targets to authorized systems, and use CSRF protection for browser forms.

**Maintainability:** Use a modular Flask structure, service-layer logic, clear naming, automated tests, and environment-based configuration.

**Portability:** Document supported Python and browser-driver versions and provide reproducible dependency installation steps.

**Accessibility:** Use clear status labels, readable contrast, semantic HTML, and keyboard-accessible primary controls.

## 8. User Stories and Acceptance Criteria

**US-01 Browse suites:** As a student, I want to view available suites so that I can choose the correct test. Acceptance: the suite page shows name, type, description, and enabled state.

**US-02 Start test run:** As a student, I want to launch an approved suite so that I can run checks from the dashboard. Acceptance: the system creates a run record and returns/redirects with a run identifier; execution occurs outside the request thread.

**US-03 Track status:** As a student, I want to see run status so that I know whether it is running or finished. Acceptance: status and timestamps persist and the detail page reflects the final state.

**US-04 Review results:** As a student, I want a pass/fail summary and report link so that I can understand the outcome. Acceptance: available structured results are parsed and shown accurately; raw logs remain available if parsing fails.

**US-05 Browse history:** As a teammate, I want to see past runs so that I can compare outcomes. Acceptance: recent runs display suite, status, time, duration, and basic filters.

**US-06 Use API:** As a developer, I want REST endpoints so that the platform can be tested or integrated programmatically. Acceptance: documented endpoints return consistent JSON and appropriate status codes.

**US-07 CI validation:** As a project maintainer, I want CI to run core tests so that regressions are detected. Acceptance: a push or pull request triggers the workflow and exposes test output/artifacts.

## 9. User Journey

**Step 1:** User opens the dashboard and reviews recent runs.

**Step 2:** User opens the suite catalogue and selects an enabled suite.

**Step 3:** User clicks Run; the backend validates the suite key and creates a queued run record.

**Step 4:** The execution service starts the approved command as a separate process.

**Step 5:** The dashboard displays running status and later refreshes to show the final result.

**Step 6:** User opens run details, inspects counts and logs, and opens the generated report if available.

## 10. Information Architecture and Main Screens

**Dashboard:** Recent runs, high-level status counts, and shortcuts to suites.

**Test Suites:** List of registered suites, suite type, description, enabled state, and Run action.

**Run History:** Table of runs with identifier, suite, status, start time, duration, and filters.

**Run Details:** Run status, timestamps, result counts, return code, log links, report links, and error details.

**API documentation:** A concise docs page or README section describing endpoints and example requests.

**Visual direction:** Use a clean, simple dashboard with clear status badges, consistent spacing, responsive layout, and no unnecessary visual complexity.

## 11. Technical Requirements and Dependencies

**Backend:** Python 3.11+ or a project-selected supported version; Flask; Flask-SQLAlchemy; Flask-Migrate; python-dotenv.

**Testing:** Pytest and pytest-html/pytest-cov as needed; Selenium for browser UI tests; Requests for API checks.

**Performance testing:** Apache JMeter installed separately with a supported Java runtime. Keep performance scenarios small and limited to the controlled demo application.

**Database:** SQLite for MVP; consider PostgreSQL only if multi-user deployment or higher concurrency becomes necessary.

**CI and version control:** Git and GitHub Actions.

**Storage:** Local run-specific artifact folders in development; define a controlled artifact retention policy if the project is later hosted.

## 12. Data and Reporting Requirements

**Suite metadata:** Each suite should have a stable key, display name, description, type, enabled flag, and server-controlled command configuration.

**Run metadata:** Each run should record suite reference, status, created/start/finish timestamps, duration, return code, pass/fail/error/skipped counts, summary, and log/report paths.

**Artifacts:** Use artifacts/runs/<run_id>/ for console logs, error logs, JUnit XML, HTML reports, screenshots, and JMeter output as applicable.

**Retention:** For a student MVP, retain recent local runs and document that artifacts may be manually cleaned. Automated retention can be added later.

**Report integrity:** If structured parsing fails, preserve raw logs and show that result parsing was unsuccessful rather than silently displaying misleading counts.

## 13. API Requirements

**GET /api/health:** Returns application health, such as {"status":"ok"}.

**GET /api/suites:** Returns registered suites and safe public metadata.

**GET /api/suites/<suite_key>:** Returns one suite or 404 if it does not exist.

**POST /api/runs:** Accepts {"suite_key":"api_smoke"}; validates the suite, creates a run, and returns HTTP 202 with run ID/status.

**GET /api/runs:** Returns run history with optional suite/status filters and pagination.

**GET /api/runs/<run_id>:** Returns status, timestamps, counts, and safe artifact references.

**Error response:** Use a consistent JSON format with a machine-readable error code and a human-readable message. Use 400 for invalid input, 404 for missing resources, 409 for state conflicts, and 500 for unexpected failures.

## 14. Security, Privacy, and Safety

**Command safety:** Do not allow users to submit raw commands or Python code. Use a server-side suite registry and subprocess argument arrays; avoid shell=True.

**Target restrictions:** Run tests only against the bundled demo application or hosts the team has permission to test. Performance testing must be opt-in and controlled.

**Secrets:** Use environment variables and a committed .env.example containing placeholders only. Never commit credentials, tokens, or personal data.

**Web protection:** If the app is exposed beyond localhost, add authentication, secure sessions, CSRF protection, and appropriate access controls before deployment.

**Artifact access:** Resolve artifact paths safely beneath the configured artifact root. Logs and screenshots may contain sensitive information and should not be publicly exposed by default.

## 15. Success Metrics

**Metric 1:** A fresh checkout can be configured and started by following the README without undocumented manual steps.

**Metric 2:** At least two registered suites can be launched and their run records persisted.

**Metric 3:** A completed run displays accurate counts when supported by its result format.

**Metric 4:** Failed runs retain diagnostic output and do not crash the web application.

**Metric 5:** Core unit/API tests pass in GitHub Actions on pushes and pull requests.

**Metric 6:** A faculty evaluator can demonstrate the core flow in a short live demo.

## 16. Milestones and Delivery Plan

**Milestone 1 — Foundation:** Flask app factory, configuration, database setup, health endpoint, and initial models.

**Milestone 2 — Suite catalogue:** Seeded suite registry, dashboard, and suite list.

**Milestone 3 — Execution engine:** Safe subprocess runner, run status lifecycle, timeout, and log capture.

**Milestone 4 — Result reporting:** JUnit XML parsing, run history, run details, and report links.

**Milestone 5 — Tool integrations:** API checks and Selenium UI checks; page objects where appropriate.

**Milestone 6 — Performance and CI:** Small JMeter baseline, GitHub Actions, uploaded reports, and documentation.

**Milestone 7 — Final polish:** Error cases, security review, demo data, screenshots, README, and project presentation.

## 17. Risks and Mitigations

**Scope creep:** Deliver the end-to-end MVP before adding advanced scheduling, accounts, or distributed workers.

**Flaky UI tests:** Use stable selectors, explicit waits, controlled test data, and screenshots on failure.

**Tool setup differences:** Document Python, browser, driver, Java, and JMeter versions and provide troubleshooting notes.

**Long-running tests:** Run tests asynchronously, set timeouts, and limit concurrent jobs.

**Unsafe execution:** Use allow-listed suite keys, approved targets, no arbitrary commands, and restricted performance tests.

**Misleading reports:** Retain raw output and clearly separate test failures from runner/parser errors.

## 18. MVP Definition of Done

**Completion checklist:** A clean checkout can start the app; SQLite initializes; at least two suites appear; the user can start a suite; execution occurs outside the web request thread; run status and results persist; logs/reports are accessible; unit/API tests run in CI; and README explains setup, architecture, endpoints, limitations, and demo steps.

## 19. Future Enhancements

**Potential additions:** User authentication and roles; richer filtering; scheduled runs; comparison of repeated runs; coverage visualization; notifications; PostgreSQL support; a durable task queue such as RQ/Celery; Docker Compose; additional test adapters; and report export.

## 20. Glossary

**ASTQ:** Advanced Software Testing and Quality Assurance Platform.

**Suite:** A named, registered collection of tests or performance scenarios.

**Run:** One execution attempt of a registered suite.

**JUnit XML:** A structured XML format used to exchange automated test results.

**CI:** Continuous Integration: automatically running checks when code changes.

**MVP:** Minimum Viable Product: the smallest version that demonstrates the core value.

