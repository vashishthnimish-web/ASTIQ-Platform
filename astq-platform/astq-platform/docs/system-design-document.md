# System Design Document — ASTQ

**Project:** Advanced Software Testing and Quality Assurance Platform  
**Version:** 1.0  
**Audience:** Third-year B.Tech CSE project team

## 1. Document Overview

**Purpose:** This System Design Document (SDD) describes the architecture, components, interfaces, data model, execution workflow, security controls, and implementation plan for the Advanced Software Testing and Quality Assurance Platform (ASTQ). It is intended as a practical blueprint for a third-year B.Tech Computer Science project.

**Scope:** ASTQ is a web-based dashboard for registering test suites, launching controlled automated tests, collecting results, reviewing execution history, and generating reports. The initial version supports UI automation with Selenium and Pytest, API checks with Requests/Pytest, and performance-test integration with Apache JMeter.

**Assumptions:** The first release runs in a local development environment. A controlled demo e-commerce application is used as the target under test. Tests run only against applications the project team owns or has permission to test. SQLite is the initial database; the design can later migrate to PostgreSQL.

## 2. Goals and Non-Goals

**Goals:** Provide a simple interface to select and execute registered test suites; persist run metadata and results; show pass/fail/error/skipped counts and duration; retain logs and report artifacts; expose a REST API for core operations; support CI execution through GitHub Actions; and keep test execution separate from the web request process.

**Non-goals for MVP:** The first version is not a cloud-scale test orchestration service, a full commercial test-management system, a multi-tenant SaaS product, or an unrestricted public load-testing service. It does not execute arbitrary user-uploaded code.

## 3. Functional Requirements

**FR-01 Suite catalogue:** An authorized user can view registered test suites and their descriptions, type, command, and enabled status.

**FR-02 Start a run:** A user can launch an enabled suite. The application creates a run record and executes the configured command in a subprocess.

**FR-03 Run status:** The system exposes queued/running/completed/failed status and records start time, end time, and duration.

**FR-04 Results:** The system stores summary counts (passed, failed, errors, skipped), return code, and a link/path to the generated report.

**FR-05 History:** Users can browse recent runs, filter by suite/status, and open a run detail page.

**FR-06 Reports:** Users can view a run summary and access generated HTML/XML/JSON or JMeter artifacts where available.

**FR-07 API:** The system provides REST endpoints to list suites, start runs, and retrieve run status/results.

**FR-08 Audit and errors:** Execution failures and application errors are logged with enough context for troubleshooting, without exposing secrets.

## 4. Non-Functional Requirements

**Security:** Use allow-listed suite identifiers rather than accepting arbitrary shell commands; validate inputs; keep secrets in environment variables; apply authentication if exposed beyond localhost; and restrict test targets to authorized systems.

**Reliability:** A failed test run should not crash the Flask web process. Store run state before execution and record final state even if parsing fails.

**Performance:** Dashboard pages should respond quickly for normal student-project datasets. Long-running test execution must happen asynchronously outside the HTTP request lifecycle.

**Maintainability:** Use a modular monolith, service-layer business logic, configuration by environment, automated tests, and documented setup.

**Portability:** Support Python virtual environments on common desktop operating systems. CI should use a reproducible dependency file.

## 5. Architecture

**Architectural style:** Use a modular monolith: one Flask application with distinct routes, services, data models, execution adapters, parsers, and reporting components. This keeps the project achievable while preserving clear boundaries.

**Presentation layer:** Flask templates and static assets render the dashboard, suite list, run history, run detail, and report views.

**Application layer:** Services validate requests, create run records, dispatch execution, update status, parse results, and build report metadata.

**Execution layer:** A subprocess runner invokes allow-listed Pytest or JMeter commands. The web worker does not run test suites synchronously.

**Persistence layer:** SQLAlchemy models store suites and runs in SQLite. Files such as logs, screenshots, XML output, HTML reports, and JMeter results are stored in an artifacts directory; database rows reference them.

**External tools:** Selenium WebDriver automates browser flows; Pytest runs test collections; Requests supports API checks; Apache JMeter runs performance scenarios; GitHub Actions executes tests on pushes and pull requests.

## 6. Component Design

**Web routes:** Render pages and expose API endpoints. Routes should remain thin and call service functions instead of containing execution logic.

**Suite registry:** Stores approved suite metadata: stable identifier, display name, suite type, command configuration, description, enabled flag, and optional target environment.

**Run service:** Creates a run, checks that the requested suite is registered and enabled, launches the runner, and updates state.

**Process runner:** Uses subprocess with an argument list rather than shell=True, enforces a timeout, captures stdout/stderr to files, and records the process return code.

**Result parsers:** Parse Pytest JUnit XML and supported JMeter output into a normalized result summary. Parsing errors are recorded separately from test failures.

**Report service:** Builds dashboard summaries and exposes safe links to artifacts. The service should prevent path traversal when resolving artifact paths.

**Logging:** Use Python logging with timestamps and run identifiers. Do not log passwords, tokens, or full secret-bearing environment values.

## 7. Data Model

**TestSuite:** id (primary key); suite_key (unique stable identifier); name; description; suite_type (UI/API/PERFORMANCE/UNIT); command_config (JSON or structured fields); enabled; created_at; updated_at.

**TestRun:** id; suite_id (foreign key); status (QUEUED/RUNNING/PASSED/FAILED/ERROR/CANCELLED); requested_by (optional); started_at; finished_at; duration_seconds; return_code; passed_count; failed_count; error_count; skipped_count; summary; log_path; report_path; created_at.

**Optional future entities:** User (for authentication and roles), Environment (approved base URL and configuration), and AuditEvent (who launched or changed a run and when).

**Relationships:** One TestSuite can have many TestRun records. A TestRun references one suite. Store artifact paths as relative paths beneath a controlled artifacts root.

## 8. API Design

**GET /api/health:** Returns service health, for example: {"status": "ok"}.

**GET /api/suites:** Returns registered suites with safe display metadata; do not expose internal secrets or raw arbitrary commands.

**GET /api/suites/<suite_key>:** Returns details for one registered suite.

**POST /api/runs:** Accepts a JSON body such as {"suite_key":"api_smoke"}. Validates the suite, creates a run, and returns HTTP 202 with the run identifier and status.

**GET /api/runs:** Returns paginated run history, with optional suite_key and status filters.

**GET /api/runs/<run_id>:** Returns status, timestamps, summary counts, and safe report/log references.

**Error conventions:** Use 400 for malformed input, 404 for unknown suite/run, 409 for conflicting state, and 500 for unexpected server failures. Return consistent JSON error objects.

## 9. Execution Workflow

**Step 1:** User selects a registered suite and requests execution.

**Step 2:** The route validates the request and calls the run service.

**Step 3:** The service creates a QUEUED TestRun record and commits it.

**Step 4:** A background worker or lightweight process manager marks the run RUNNING and starts the configured command.

**Step 5:** The runner writes stdout/stderr and test output to a run-specific artifact folder and enforces a timeout.

**Step 6:** The parser reads the structured output, normalizes test counts, and stores the summary and artifact references.

**Step 7:** The run becomes PASSED, FAILED, or ERROR, with finish time and duration.

**Step 8:** The dashboard refreshes run details and lets the user inspect the report.

## 10. Repository and Artifact Conventions

**Artifact layout:** artifacts/runs/<run_id>/ should contain console.log, error.log, junit.xml, report.html where applicable, screenshots/, and performance output. Do not commit generated artifacts or local databases unless a small sample fixture is intentionally included.

**Configuration:** Use .env for local values and commit only .env.example. Set FLASK_ENV or an equivalent application configuration deliberately; never place credentials in source control.

**Test separation:** Keep tests for the ASTQ application in tests/unit, tests/integration, tests/ui, and tests/api. Keep demo target application code separate under demo_app/.

**Naming:** Use stable suite keys such as ui_smoke, api_smoke, unit_regression, and performance_baseline.

## 11. Security and Safety

**Command execution:** Never accept a command string from the browser. Resolve suite_key to server-side configuration and pass subprocess arguments as a list. Avoid shell=True.

**Target authorization:** Allow tests only against the bundled demo application or explicitly approved hosts. Require a deliberate configuration change before running tests against a remote target.

**Web security:** Use CSRF protection for browser forms, secure session settings, input validation, safe template rendering, and authentication before exposing the dashboard to a network.

**Resource controls:** Set execution timeouts, cap output size where practical, limit concurrent runs, and prevent untrusted users from starting performance tests.

**Artifacts:** Treat logs, screenshots, and reports as potentially sensitive. Use controlled paths and avoid serving arbitrary filesystem paths.

## 12. Error Handling and Observability

**Failure categories:** Distinguish test assertion failures from runner errors, timeouts, missing dependencies, malformed result files, and application-level failures.

**Run state:** Always attempt to persist a terminal state. If parsing fails after the command exits, mark the run ERROR or FAILED according to the documented rule and retain the raw log.

**Logging:** Include run_id, suite_key, timestamp, severity, and component in structured log messages.

**Health checks:** Expose /api/health for application availability. A future enhancement may add checks for browser-driver availability and JMeter installation.

## 13. Deployment and Configuration

**Local development:** Create a Python virtual environment, install requirements, configure environment variables, initialize the database, start Flask, and run the demo app separately if needed.

**CI:** GitHub Actions should install dependencies, run lint/unit/API tests, and upload test reports as artifacts. UI tests should use a configured browser/driver strategy supported by the runner.

**Suggested environment values:** SECRET_KEY, DATABASE_URL, ARTIFACTS_DIR, DEMO_BASE_URL, RUN_TIMEOUT_SECONDS, MAX_CONCURRENT_RUNS. Use safe local defaults and do not commit secrets.

**Database migrations:** Use Flask-Migrate/Alembic once schema changes begin. For an early prototype, create_all may be acceptable, but migrations are preferable for a maintained project.

## 14. Testing Strategy

**Unit tests:** Test validation, suite lookup, state transitions, result normalization, path safety, and duration calculations.

**Integration tests:** Test route/service/database interactions with a temporary database and mocked process runner.

**API tests:** Use Flask's test client or Requests against a running local server to validate status codes, schemas, and error cases.

**UI tests:** Use Selenium to validate core user journeys: view suites, start a run, open run details, and view report links.

**Performance tests:** Use a small, authorized JMeter baseline against the demo application. Document thread count, ramp-up, duration, and target URL.

**Acceptance criteria:** A user can launch an approved suite, see a persisted run record, review accurate summary counts, and open generated artifacts. Tests and CI pass on a clean checkout.

## 15. Implementation Plan

**Phase 1 — Foundation:** Create repository, Flask app factory, configuration, SQLAlchemy setup, health route, and database models.

**Phase 2 — Suite catalogue:** Add seeded suite registry, dashboard pages, suite detail, and validation.

**Phase 3 — Runner:** Implement subprocess runner with timeouts, output capture, run state transitions, and one small Pytest suite.

**Phase 4 — Results:** Generate JUnit XML, parse counts, store summaries, and render run history/detail pages.

**Phase 5 — UI and API testing:** Add Selenium page objects and API checks with Requests/Pytest.

**Phase 6 — JMeter and CI:** Add an opt-in small performance baseline and GitHub Actions workflow with report artifacts.

**Phase 7 — Hardening:** Add CSRF/authentication if needed, path validation, concurrency limits, error handling, documentation, and demo screenshots.

## 16. Definition of Done

**MVP checklist:** Application starts from documented instructions; database initializes; at least two suites are registered; a user can launch a suite; execution occurs outside the request thread; status and results persist; logs/reports are accessible; automated tests run in CI; and README includes setup, architecture, API examples, limitations, and screenshots.

## 17. Risks and Mitigations

**Platform differences:** Browser drivers and JMeter installation vary by operating system. Document supported versions and isolate tool-specific configuration.

**Long-running jobs:** Subprocess execution can outlive the web process. For the MVP, use a local worker/process manager; later move to Celery/RQ or another durable queue.

**Flaky UI tests:** Use stable selectors, explicit waits, controlled test data, and screenshots on failure.

**Unsafe target execution:** Use server-side allow-listed suites and authorized target hosts; never expose arbitrary command execution.

**Scope growth:** Prioritize one end-to-end flow before adding advanced scheduling, user roles, or distributed execution.

