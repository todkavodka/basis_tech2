"""Vulture dead code analyzer."""

from __future__ import annotations

import subprocess
from pathlib import Path

from code_auditor.analyzers.base import find_tool
from code_auditor.models import Category, Finding, Severity


class VultureAnalyzer:
    name = "vulture"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("vulture")
        if not tool:
            return []

        result = subprocess.run(
            [tool, str(path), "--min-confidence", "60"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        findings: list[Finding] = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            # Parse: filepath:line: message (confidence%)
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            filepath = parts[0]
            rest = parts[1]
            line_rest = rest.split(" ", 1)
            try:
                lineno = int(line_rest[0].rstrip())
            except (ValueError, IndexError):
                lineno = None
            message = line_rest[1].strip() if len(line_rest) > 1 else parts[2].strip()

            findings.append(
                Finding(
                    tool="vulture",
                    rule_id="dead-code",
                    severity=Severity.LOW,
                    category=Category.DEAD_CODE,
                    file=filepath,
                    line=lineno,
                    message=message,
                )
            )

        return findings
