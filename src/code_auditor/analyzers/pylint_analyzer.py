"""Pylint quality analyzer — wraps pylint CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_auditor.analyzers.base import find_tool
from code_auditor.models import Category, Finding, Severity

# Pylint message IDs that map to specific categories
GOD_OBJECT_IDS = {"R0902", "R0904"}  # too-many-instance-attributes, too-many-public-methods
SOLID_IDS = {"R0901"}  # too-many-ancestors (LSP)
DUPLICATION_IDS = {"R0801"}
SECURITY_IDS = {"W0123", "W0122"}  # eval-used, exec-used

SEVERITY_MAP = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "convention": Severity.LOW,
    "refactor": Severity.LOW,
    "fatal": Severity.CRITICAL,
}


class PylintAnalyzer:
    name = "pylint"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("pylint")
        if not tool:
            return []

        result = subprocess.run(
            [
                tool,
                "--recursive=y",
                "--output-format=json",
                "--disable=C0114,C0115,C0116",  # missing docstrings
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        try:
            messages = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            return []

        findings: list[Finding] = []
        for msg in messages:
            msg_id = msg.get("message-id", "")

            if msg_id in GOD_OBJECT_IDS:
                cat = Category.ARCHITECTURE
            elif msg_id in SOLID_IDS:
                cat = Category.ARCHITECTURE
            elif msg_id in DUPLICATION_IDS:
                cat = Category.QUALITY
            elif msg_id in SECURITY_IDS:
                cat = Category.SECURITY
            else:
                cat = Category.QUALITY

            findings.append(
                Finding(
                    tool="pylint",
                    rule_id=msg_id,
                    severity=SEVERITY_MAP.get(msg.get("type", ""), Severity.INFO),
                    category=cat,
                    file=msg.get("path"),
                    line=msg.get("line"),
                    column=msg.get("column"),
                    message=msg.get("message", ""),
                )
            )

        return findings
