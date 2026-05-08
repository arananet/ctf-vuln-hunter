"""Tests for src/report_parser.py."""
import pytest

from src.report_parser import NO_VULN_SENTINEL, VulnReport, parse

_SAMPLE_REPORT = """\
---
VULNERABILITY REPORT
====================

## Vulnerability
Stack-based Buffer Overflow (CWE-121)

## Location
foo.c, function main(), line 12

## Description
The call to gets() reads unbounded user input into a fixed-size stack buffer,
allowing an attacker to overwrite the return address.

## How to Replicate
Run: python3 -c "print('A'*300)" | ./foo
Observe segmentation fault / arbitrary code execution.

## Proposed Fix
Replace gets(buf) with fgets(buf, sizeof(buf), stdin).

## Severity
CRITICAL — arbitrary code execution with no authentication required.
---
"""


def test_parse_all_sections():
    report = parse(_SAMPLE_REPORT)
    assert "Buffer Overflow" in report.vulnerability
    assert "CWE-121" in report.vulnerability
    assert "foo.c" in report.location
    assert "gets()" in report.description
    assert "python3" in report.how_to_replicate
    assert "fgets" in report.proposed_fix
    assert "CRITICAL" in report.severity


def test_parse_no_vulnerability_sentinel():
    report = parse(f"Scanned 1234 lines.\n{NO_VULN_SENTINEL}\n")
    assert report.no_vulnerability is True
    assert report.vulnerability == ""


def test_parse_preserves_raw():
    text = "some raw text"
    report = parse(text)
    assert report.raw == text


def test_parse_empty_string():
    report = parse("")
    assert report.no_vulnerability is False
    assert report.vulnerability == ""


def test_parse_partial_report():
    partial = "## Vulnerability\nFormat String (CWE-134)\n\n## Severity\nHIGH\n"
    report = parse(partial)
    assert "CWE-134" in report.vulnerability
    assert "HIGH" in report.severity
    assert report.location == ""
