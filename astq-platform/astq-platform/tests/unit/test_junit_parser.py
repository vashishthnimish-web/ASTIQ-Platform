from pathlib import Path

import pytest

from app.parsers import ParseError, parse_jmeter_jtl, parse_junit_xml

FIX = Path(__file__).parent.parent / "fixtures"


def test_parses_counts_from_testsuites_root():
    r = parse_junit_xml(FIX / "junit_ok.xml")
    assert (r.passed, r.failed, r.errors, r.skipped) == (4, 2, 1, 3)
    assert r.total == 10


def test_parses_single_testsuite_root():
    r = parse_junit_xml(FIX / "junit_single_suite.xml")
    assert (r.passed, r.failed, r.errors, r.skipped) == (4, 0, 0, 0)


def test_missing_file_raises_parse_error(tmp_path):
    with pytest.raises(ParseError):
        parse_junit_xml(tmp_path / "nope.xml")


def test_empty_file_raises_parse_error(tmp_path):
    p = tmp_path / "e.xml"
    p.write_text("")
    with pytest.raises(ParseError):
        parse_junit_xml(p)


def test_malformed_xml_raises_parse_error(tmp_path):
    p = tmp_path / "bad.xml"
    p.write_text("<testsuite tests='1'")
    with pytest.raises(ParseError):
        parse_junit_xml(p)


def test_inconsistent_counts_raise(tmp_path):
    p = tmp_path / "x.xml"
    p.write_text('<testsuite tests="1" failures="5" errors="0" skipped="0"/>')
    with pytest.raises(ParseError):
        parse_junit_xml(p)


def test_wrong_root_raises(tmp_path):
    p = tmp_path / "x.xml"
    p.write_text("<html/>")
    with pytest.raises(ParseError):
        parse_junit_xml(p)


def test_summary_text_mentions_all_counts():
    text = parse_junit_xml(FIX / "junit_ok.xml").as_text()
    assert "10 tests" in text and "4 passed" in text and "2 failed" in text


def test_jmeter_parser_counts_and_latency():
    r = parse_jmeter_jtl(FIX / "results.jtl")
    assert (r.passed, r.failed) == (3, 1)
    assert "Avg response 250 ms" in r.note


def test_jmeter_parser_rejects_non_csv(tmp_path):
    p = tmp_path / "r.jtl"
    p.write_text("<xml/>")
    with pytest.raises(ParseError):
        parse_jmeter_jtl(p)
