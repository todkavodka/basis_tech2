"""Bandit security analyzer — wraps bandit CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_auditor.analyzers.base import find_tool
from code_auditor.models import Category, Finding, Severity

# Bandit test ID → OWASP Top 10 mapping
OWASP_MAP: dict[str, str] = {
    "B101": "N/A",
    "B102": "A03",
    "B103": "N/A",
    "B104": "N/A",
    "B105": "A07",
    "B106": "A07",
    "B107": "A07",
    "B108": "N/A",
    "B110": "A09",
    "B112": "A09",
    "B201": "A05",
    "B301": "A08",
    "B302": "A08",
    "B303": "A02",
    "B304": "A02",
    "B305": "A02",
    "B306": "A02",
    "B307": "A03",
    "B310": "N/A",
    "B311": "A02",
    "B312": "A09",
    "B313": "A03",
    "B314": "A03",
    "B315": "A03",
    "B316": "A03",
    "B317": "A03",
    "B318": "A03",
    "B319": "A03",
    "B320": "A03",
    "B321": "A02",
    "B323": "A03",
    "B324": "A02",
    "B501": "A02",
    "B502": "A02",
    "B503": "A02",
    "B504": "A02",
    "B505": "A02",
    "B506": "A08",
    "B507": "A02",
    "B601": "A03",
    "B602": "A03",
    "B603": "A03",
    "B604": "A03",
    "B605": "A03",
    "B606": "A03",
    "B607": "A03",
    "B608": "A03",
    "B609": "A03",
    "B610": "A03",
    "B611": "A03",
    "B612": "A05",
    "B701": "A03",
    "B702": "A03",
    "B703": "A03",
}

SEVERITY_MAP = {
    "UNDEFINED": Severity.INFO,
    "LOW": Severity.LOW,
    "MEDIUM": Severity.MEDIUM,
    "HIGH": Severity.HIGH,
}


class BanditAnalyzer:
    name = "bandit"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("bandit")
        if not tool:
            return []

        result = subprocess.run(
            [tool, "-r", str(path), "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        findings: list[Finding] = []
        for item in data.get("results", []):
            test_id = item.get("test_id", "")
            findings.append(
                Finding(
                    tool="bandit",
                    rule_id=test_id,
                    severity=SEVERITY_MAP.get(item.get("issue_severity", ""), Severity.INFO),
                    category=Category.SECURITY,
                    owasp_mapping=OWASP_MAP.get(test_id, "N/A"),
                    file=item.get("filename"),
                    line=item.get("line_number"),
                    message=item.get("issue_text", ""),
                    confidence=item.get("issue_confidence", "").lower(),
                )
            )
        return findings
