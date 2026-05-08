"""CTF Vulnerability Hunter — subprocess runner."""
from __future__ import annotations

import subprocess
from pathlib import Path

DEFAULT_OUTPUT = "/tmp/vuln_report.txt"
DEFAULT_LOG = "/tmp/claude_vuln.log"

_PROMPT_TEMPLATE = """\
You are a senior security researcher participating in a CTF challenge.

Your mission:
1. Read and analyze the source code at: {source_path}
2. Identify ALL potential vulnerabilities (buffer overflows, format string bugs, use-after-free,
   integer overflows, injection flaws, race conditions, insecure crypto, etc.)
3. Select the MOST CRITICAL vulnerability found.
4. Produce a structured security report written to {output_path} with EXACTLY this format:

---
VULNERABILITY REPORT
====================

## Vulnerability
[Name and CWE ID if applicable]

## Location
[File, function name, line number(s)]

## Description
[Clear technical explanation of the flaw and why it is dangerous]

## How to Replicate
[Step-by-step instructions or a minimal PoC payload/exploit to trigger the vulnerability]

## Proposed Fix
[Corrected code snippet or patch, with explanation of why the fix works]

## Severity
[CRITICAL / HIGH / MEDIUM / LOW — with brief justification]
---

If NO vulnerability is found, write 'NO VULNERABILITIES DETECTED' to the report file.\
"""


class InstallationError(RuntimeError):
    pass


class NonZeroExitError(RuntimeError):
    pass


def build_prompt(source_path: str, output_path: str) -> str:
    return _PROMPT_TEMPLATE.format(source_path=source_path, output_path=output_path)


def run_scan(
    source_path: str,
    output_path: str = DEFAULT_OUTPUT,
    log_path: str = DEFAULT_LOG,
) -> str:
    """Run the claude CLI scan and return the report text.

    Raises InstallationError if claude is not on PATH.
    Raises NonZeroExitError if the CLI exits with a non-zero code.
    Returns the report text, or the last 20 log lines if the report is empty.
    """
    prompt = build_prompt(source_path, output_path)
    cmd = ["claude", "--dangerously-skip-permissions", "-p", prompt, "--verbose"]

    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with log_file.open("w") as lf:
            result = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise InstallationError(
            "claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
        )

    if result.returncode != 0:
        tail = _tail_log(log_path)
        raise NonZeroExitError(
            f"claude exited with code {result.returncode}.\n\nLog tail:\n{tail}"
        )

    report_path = Path(output_path)
    if report_path.exists() and report_path.stat().st_size > 0:
        return report_path.read_text()

    tail = _tail_log(log_path)
    return f"Report file was empty or missing.\n\nLog tail:\n{tail}"


def _tail_log(log_path: str, lines: int = 20) -> str:
    path = Path(log_path)
    if not path.exists():
        return "(log file not found)"
    all_lines = path.read_text().splitlines()
    return "\n".join(all_lines[-lines:])
