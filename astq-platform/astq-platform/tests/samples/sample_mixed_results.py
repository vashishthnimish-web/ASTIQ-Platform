"""Demonstration suite for evaluators (suite key: sample_mixed).

Deliberately contains passing, skipped and ONE intentionally failing test so the dashboard can
show failure evidence. This file is NOT collected by default (see pyproject testpaths) and is
only executed when ASTQ launches the `sample_mixed` suite.
"""
import pytest


def test_addition_works():
    assert 2 + 2 == 4


def test_string_upper():
    assert "astq".upper() == "ASTQ"


@pytest.mark.skip(reason="demonstrates a skipped test in the report")
def test_skipped_example():
    raise AssertionError("never runs")


def test_intentional_failure_for_demo():
    expected_total = 100
    actual_total = sum([10, 20, 30])
    assert actual_total == expected_total, "Intentional failure: totals differ"
