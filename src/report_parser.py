"""Parse the structured vulnerability report produced by the CTF scanner."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

NO_VULN_SENTINEL = "NO VULNERABILITIES DETECTED"

_SECTIONS = [
    "Vulnerability",
    "Location",
    "Description",
    "How to Replicate",
    "Proposed Fix",
    "Severity",
]


@dataclass
class VulnReport:
    vulnerability: str = ""
    location: str = ""
    description: str = ""
    how_to_replicate: str = ""
    proposed_fix: str = ""
    severity: str = ""
    no_vulnerability: bool = False
    raw: str = ""


def parse(text: str) -> VulnReport:
    report = VulnReport(raw=text)

    if NO_VULN_SENTINEL in text:
        report.no_vulnerability = True
        return report

    pattern = "|".join(re.escape(s) for s in _SECTIONS)
    parts = re.split(rf"##\s+({pattern})\s*\n", text)

    mapping: dict[str, str] = {}
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        mapping[heading] = body

    report.vulnerability = mapping.get("Vulnerability", "")
    report.location = mapping.get("Location", "")
    report.description = mapping.get("Description", "")
    report.how_to_replicate = mapping.get("How to Replicate", "")
    report.proposed_fix = mapping.get("Proposed Fix", "")
    report.severity = mapping.get("Severity", "")

    return report
