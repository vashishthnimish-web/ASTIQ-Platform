"""Normalise Pytest JUnit XML into a ResultSummary (SDD 6, FR-06)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


class ParseError(Exception):
    """Raised when a result file is missing, empty or malformed.

    Kept separate from test failures so the UI never shows misleading counts (PRD 12).
    """


@dataclass
class ResultSummary:
    passed: int
    failed: int
    errors: int
    skipped: int
    note: str = ""

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.errors + self.skipped

    def as_text(self) -> str:
        base = (
            f"{self.total} tests: {self.passed} passed, {self.failed} failed, "
            f"{self.errors} errors, {self.skipped} skipped"
        )
        return f"{base}. {self.note}".strip() if self.note else base


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ParseError(f"Non-numeric count in JUnit XML: {value!r}") from exc


def parse_junit_xml(path: str | Path) -> ResultSummary:
    p = Path(path)
    if not p.is_file():
        raise ParseError(f"JUnit XML not found: {p.name}")
    if p.stat().st_size == 0:
        raise ParseError("JUnit XML is empty")
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError as exc:
        raise ParseError(f"Malformed JUnit XML: {exc}") from exc

    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = list(root.iter("testsuite"))
        # nested suites would double count; keep only outermost level
        nested = {id(s) for outer in suites for s in outer.iter("testsuite") if s is not outer}
        suites = [s for s in suites if id(s) not in nested]
    else:
        raise ParseError(f"Unexpected root element <{root.tag}>")
    if not suites:
        raise ParseError("No <testsuite> element found")

    tests = failures = errors = skipped = 0
    for s in suites:
        tests += _int(s.get("tests"))
        failures += _int(s.get("failures"))
        errors += _int(s.get("errors"))
        skipped += _int(s.get("skipped"))
    passed = tests - failures - errors - skipped
    if passed < 0:
        raise ParseError("Inconsistent counts in JUnit XML")
    return ResultSummary(passed=passed, failed=failures, errors=errors, skipped=skipped)
