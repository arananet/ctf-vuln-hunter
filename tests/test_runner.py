"""Tests for src/runner.py — subprocess interactions are fully mocked."""
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.runner import (
    DEFAULT_LOG,
    DEFAULT_OUTPUT,
    InstallationError,
    NonZeroExitError,
    build_prompt,
    run_scan,
)


def test_build_prompt_contains_paths():
    prompt = build_prompt("/src/foo.c", "/tmp/out.txt")
    assert "/src/foo.c" in prompt
    assert "/tmp/out.txt" in prompt


def test_build_prompt_contains_required_sections():
    prompt = build_prompt("/src/foo.c", "/tmp/out.txt")
    for section in ["Vulnerability", "Location", "Description", "How to Replicate", "Proposed Fix", "Severity"]:
        assert section in prompt


def _make_completed(returncode: int = 0) -> MagicMock:
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.returncode = returncode
    return m


@patch("src.runner.subprocess.run")
@patch("builtins.open", mock_open())
def test_run_scan_returns_report_on_success(mock_run, tmp_path):
    mock_run.return_value = _make_completed(0)
    report_content = "VULNERABILITY REPORT\n## Vulnerability\nBuffer Overflow"
    report_file = tmp_path / "report.txt"
    report_file.write_text(report_content)

    result = run_scan("/src/foo.c", str(report_file), str(tmp_path / "log.txt"))
    assert result == report_content


@patch("src.runner.subprocess.run", side_effect=FileNotFoundError)
def test_run_scan_raises_installation_error_when_claude_missing(mock_run, tmp_path):
    with pytest.raises(InstallationError) as exc_info:
        run_scan("/src/foo.c", str(tmp_path / "out.txt"), str(tmp_path / "log.txt"))
    assert "npm install" in str(exc_info.value)


@patch("src.runner.subprocess.run")
def test_run_scan_raises_non_zero_exit_error(mock_run, tmp_path):
    log_content = "error: something went wrong\nline2\n"

    def side_effect(cmd, stdout, stderr):
        stdout.write(log_content)
        return _make_completed(1)

    mock_run.side_effect = side_effect
    log_file = tmp_path / "log.txt"

    with pytest.raises(NonZeroExitError) as exc_info:
        run_scan("/src/foo.c", str(tmp_path / "out.txt"), str(log_file))
    assert "exited with code 1" in str(exc_info.value)
    assert "error: something went wrong" in str(exc_info.value)


@patch("src.runner.subprocess.run")
def test_run_scan_returns_log_tail_when_report_empty(mock_run, tmp_path):
    log_content = "scan ran but nothing found\n"

    def side_effect(cmd, stdout, stderr):
        stdout.write(log_content)
        return _make_completed(0)

    mock_run.side_effect = side_effect
    log_file = tmp_path / "log.txt"
    report_file = tmp_path / "report.txt"
    report_file.write_text("")  # empty

    result = run_scan("/src/foo.c", str(report_file), str(log_file))
    assert "scan ran but nothing found" in result


@patch("src.runner.subprocess.run")
def test_run_scan_returns_log_tail_when_report_missing(mock_run, tmp_path):
    mock_run.return_value = _make_completed(0)
    log_file = tmp_path / "log.txt"
    log_file.write_text("log line 1\nlog line 2\n")

    result = run_scan("/src/foo.c", str(tmp_path / "nonexistent.txt"), str(log_file))
    assert "empty or missing" in result


@patch("src.runner.subprocess.run")
def test_run_scan_uses_correct_cli_args(mock_run, tmp_path):
    mock_run.return_value = _make_completed(0)
    report_file = tmp_path / "report.txt"
    report_file.write_text("some report content")
    log_file = tmp_path / "log.txt"

    run_scan("/src/foo.c", str(report_file), str(log_file))

    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "claude"
    assert "--dangerously-skip-permissions" in call_args
    assert "-p" in call_args
    assert "--verbose" in call_args
