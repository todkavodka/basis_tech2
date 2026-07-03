"""Semgrep pattern/taint analyzer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_auditor.analyzers.base import find_tool
from code_auditor.models import Category, Finding, Severity

SEVERITY_MAP = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.INFO,
}


class SemgrepAnalyzer:
    name = "semgrep"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("semgrep")
        if not tool:
            return []

        result = subprocess.run(
            [tool, "--config=auto", "--json", "--quiet", str(path)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        findings: list[Finding] = []
        for match in data.get("results", []):
            extra = match.get("extra", {})
            findings.append(
                Finding(
                    tool="semgrep",
                    rule_id=match.get("check_id", ""),
                    severity=SEVERITY_MAP.get(extra.get("severity", ""), Severity.INFO),
                    category=Category.SECURITY,
                    file=match.get("path"),
                    line=match.get("start", {}).get("line"),
                    column=match.get("start", {}).get("col"),
                    message=extra.get("message", ""),
                )
            )

        return findings
