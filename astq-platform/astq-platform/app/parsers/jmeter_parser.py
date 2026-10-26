"""Parse a JMeter CSV results file (.jtl) into a ResultSummary (SDD 6)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from app.parsers.junit_parser import ParseError, ResultSummary


def parse_jmeter_jtl(path: str | Path) -> ResultSummary:
    p = Path(path)
    if not p.is_file():
        raise ParseError(f"JMeter results not found: {p.name}")
    elapsed: list[int] = []
    ok = bad = 0
    try:
        with p.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or "success" not in reader.fieldnames:
                raise ParseError("JTL file has no 'success' column (CSV output expected)")
            for row in reader:
                if str(row.get("success", "")).strip().lower() == "true":
                    ok += 1
                else:
                    bad += 1
                if row.get("elapsed"):
                    elapsed.append(int(row["elapsed"]))
    except (csv.Error, ValueError, UnicodeDecodeError) as exc:
        raise ParseError(f"Malformed JTL file: {exc}") from exc
    if ok + bad == 0:
        raise ParseError("JTL file contains no samples")
    avg = sum(elapsed) / len(elapsed) if elapsed else 0.0
    ordered = sorted(elapsed)
    p95 = ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)] if ordered else 0
    note = f"Avg response {avg:.0f} ms, p95 {p95} ms."
    return ResultSummary(passed=ok, failed=bad, errors=0, skipped=0, note=note)
