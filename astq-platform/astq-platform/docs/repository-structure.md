# GitHub Repository Structure — ASTQ

## Repository Tree

```text
astq-platform/
├── .github/
│   └── workflows/
│       └── tests.yml
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_suite.py
│   │   └── test_run.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── suites.py
│   │   ├── runs.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── suite_service.py
│   │   ├── run_service.py
│   │   └── report_service.py
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── command_registry.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── junit_parser.py
│   │   └── jmeter_parser.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── summary_builder.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── suites.html
│   │   ├── run_history.html
│   │   └── run_detail.html
│   └── static/
│       ├── css/
│       │   └── app.css
│       └── js/
│           └── app.js
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_run_service.py
│   │   └── test_junit_parser.py
│   ├── integration/
│   │   └── test_run_flow.py
│   ├── api/
│   │   └── test_api_endpoints.py
│   └── ui/
│       ├── conftest.py
│       ├── pages/
│       │   ├── base_page.py
│       │   └── dashboard_page.py
│       └── test_dashboard.py
├── pages/
│   └── README.md
├── performance/
│   ├── baseline.jmx
│   └── README.md
├── demo_app/
│   ├── app.py
│   ├── templates/
│   └── README.md
├── scripts/
│   ├── init_db.py
│   └── seed_suites.py
├── docs/
│   ├── system-design-document.md
│   ├── repository-structure.md
│   └── api-specification.md
├── artifacts/
│   └── .gitkeep
├── instance/
│   └── .gitkeep
├── migrations/
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── run.py
└── README.md
```

## 1. Repository Purpose

This structure separates the ASTQ web application, automated tests for ASTQ itself, the controlled demo application under test, performance scenarios, scripts, documentation, and generated artifacts. It is intentionally modular without requiring a microservices deployment.

## 2. Main Directories

app/ contains the Flask product code. models/ defines SQLAlchemy entities. routes/ contains page and API endpoints. services/ implements business logic. execution/ safely launches allow-listed test commands. parsers/ normalizes structured output. reporting/ creates summary data. templates/ and static/ provide the dashboard UI.

## 3. Test Directories

tests/unit/ tests isolated functions and services. tests/integration/ tests multi-component workflows with a temporary database or mocked runner. tests/api/ validates HTTP endpoints. tests/ui/ contains Selenium tests and page objects for the ASTQ dashboard. demo_app/ is the controlled target application and should have its own smoke tests as the project grows.

## 4. Key Files

run.py is the local entry point. app/__init__.py creates the Flask application and registers blueprints. app/config.py loads environment-based settings. app/extensions.py initializes SQLAlchemy and other extensions. execution/command_registry.py maps stable suite keys to approved commands. scripts/init_db.py initializes local data; scripts/seed_suites.py inserts initial suite definitions.

## 5. Recommended Dependencies

Runtime: Flask, Flask-SQLAlchemy, Flask-Migrate, python-dotenv, pytest, pytest-html, pytest-cov, requests, selenium. Development: ruff or flake8, black (optional), and pytest tooling. JMeter is installed separately as a Java-based tool; document its supported version and executable path.

## 6. Suite Registry Example

Register stable identifiers such as unit_regression, api_smoke, ui_smoke, and performance_baseline. Each identifier should resolve to a server-defined argument list and working directory. The browser must never submit an arbitrary shell command. Keep the initial performance suite disabled by default or explicitly opt-in.

## 7. Environment Example

SECRET_KEY=replace-for-local-development\nDATABASE_URL=sqlite:///astq.db\nARTIFACTS_DIR=artifacts/runs\nDEMO_BASE_URL=http://127.0.0.1:5001\nRUN_TIMEOUT_SECONDS=300\nMAX_CONCURRENT_RUNS=1

## 8. .gitignore Guidance

Ignore .env, virtual environments, __pycache__, .pytest_cache, coverage output, local SQLite databases, instance configuration, generated run artifacts, browser downloads, and OS/editor files. Commit artifacts/.gitkeep and instance/.gitkeep only if you want the directories to exist in a fresh checkout.

## 9. CI Workflow

On pushes and pull requests, install the supported Python version, install requirements, run unit and API/integration tests, generate JUnit XML and coverage output, and upload reports as CI artifacts. Run Selenium UI tests only after browser setup is reliable. Do not run performance load tests on every commit by default.

## 10. Suggested Build Order

1) App factory and health route; 2) database models and seeded suite registry; 3) dashboard and suite listing; 4) safe runner for a single Pytest suite; 5) JUnit parser and run details; 6) API endpoints; 7) Selenium UI checks; 8) JMeter baseline; 9) CI, documentation, and security hardening.

## 11. Initial README Sections

Project overview; problem statement; features; architecture diagram; tech stack; prerequisites; local setup; environment configuration; database initialization; running the app; running tests; supported suite keys; API examples; report/artifact locations; CI workflow; limitations; future enhancements; screenshots; and contributors.

## 12. First Milestone

The first milestone is complete when a fresh checkout can start Flask, initialize SQLite, show at least one registered suite, launch a small Pytest run in a separate process, persist its state and counts, and display the run detail page with a link to its output.

## Example GitHub Actions Workflow

```yaml
name: ASTQ Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install --upgrade pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/unit tests/api --junitxml=artifacts/junit-ci.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-reports
          path: artifacts/
```

## Example .gitignore

```gitignore
.env
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
instance/*.db
*.sqlite
*.sqlite3
artifacts/runs/*
!artifacts/.gitkeep
.DS_Store
Thumbs.db
```
