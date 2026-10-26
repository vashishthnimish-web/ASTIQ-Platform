"""Server-side allow-list mapping suite keys to approved commands.

The browser only ever sends a suite_key. Commands are argument lists (never shell
strings) and are resolved here (PRD FR-04, SDD 11).

Placeholders substituted at run time (never from user input):
  {python}     current interpreter
  {run_dir}    artifacts/runs/<run_id>
  {jmeter}     JMETER_PATH
  {demo_host} / {demo_port}   parsed from DEMO_BASE_URL
"""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True)
class CommandSpec:
    args: tuple[str, ...]
    result_format: str  # "junit" or "jtl"
    result_file: str  # file inside the run dir that the parser reads
    report_file: str | None = None  # optional human-readable report inside run dir
    needs_demo_app: bool = False
    meta: dict = field(default_factory=dict)


def _pytest(*targets: str) -> tuple[str, ...]:
    return (
        "{python}", "-m", "pytest", *targets,
        "-p", "no:cacheprovider",
        "--junitxml={run_dir}/junit.xml",
        "--html={run_dir}/report.html", "--self-contained-html",
        "-q",
    )


SUITE_DEFINITIONS = [
    {
        "suite_key": "unit_regression",
        "name": "Unit & Integration Regression",
        "description": "Pytest regression suite for ASTQ itself: parsers, run service, "
        "state transitions, path safety, and the end-to-end run flow.",
        "suite_type": "UNIT",
        "enabled": True,
    },
    {
        "suite_key": "api_smoke",
        "name": "Demo Shop API Smoke",
        "description": "Requests-based API checks against the bundled demo e-commerce app "
        "(health, catalogue, cart, checkout, error cases).",
        "suite_type": "API",
        "enabled": True,
    },
    {
        "suite_key": "ui_smoke",
        "name": "Dashboard UI Smoke (Selenium)",
        "description": "Selenium page-object tests of the ASTQ dashboard. Tests are skipped "
        "automatically when no Chrome/Chromium browser is available.",
        "suite_type": "UI",
        "enabled": True,
    },
    {
        "suite_key": "sample_mixed",
        "name": "Sample Mixed Results (intentional failure)",
        "description": "Demonstration suite containing passing, skipped and one intentionally "
        "failing test so evaluators can see failure evidence, logs and reports.",
        "suite_type": "UNIT",
        "enabled": True,
    },
    {
        "suite_key": "performance_baseline",
        "name": "JMeter Performance Baseline",
        "description": "Small opt-in JMeter baseline (5 threads, 10 loops) against the demo "
        "app only. Disabled by default; requires Java and Apache JMeter.",
        "suite_type": "PERFORMANCE",
        "enabled": False,
    },
]

COMMAND_REGISTRY: dict[str, CommandSpec] = {
    "unit_regression": CommandSpec(
        args=_pytest("tests/unit", "tests/integration"),
        result_format="junit", result_file="junit.xml", report_file="report.html",
    ),
    "api_smoke": CommandSpec(
        args=_pytest("tests/api/test_demo_api.py"),
        result_format="junit", result_file="junit.xml", report_file="report.html",
        needs_demo_app=True,
    ),
    "ui_smoke": CommandSpec(
        args=_pytest("tests/ui"),
        result_format="junit", result_file="junit.xml", report_file="report.html",
    ),
    "sample_mixed": CommandSpec(
        args=_pytest("tests/samples/sample_mixed_results.py"),
        result_format="junit", result_file="junit.xml", report_file="report.html",
    ),
    "performance_baseline": CommandSpec(
        args=(
            "{jmeter}", "-n", "-t", "performance/baseline.jmx",
            "-l", "{run_dir}/results.jtl",
            "-Jhost={demo_host}", "-Jport={demo_port}",
        ),
        result_format="jtl", result_file="results.jtl",
        needs_demo_app=True,
    ),
}


def get_spec(suite_key: str) -> CommandSpec | None:
    return COMMAND_REGISTRY.get(suite_key)


def build_args(spec: CommandSpec, *, python: str, run_dir: str, jmeter: str, demo_base_url: str):
    parsed = urlparse(demo_base_url)
    values = {
        "python": python,
        "run_dir": run_dir,
        "jmeter": jmeter,
        "demo_host": parsed.hostname or "127.0.0.1",
        "demo_port": str(parsed.port or 80),
    }
    return [a.format(**values) for a in spec.args]
