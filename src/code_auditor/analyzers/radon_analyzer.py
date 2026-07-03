"""Radon complexity analyzer — wraps radon CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_auditor.analyzers.base import cc_to_severity, find_tool
from code_auditor.models import Category, Finding


class RadonAnalyzer:
    name = "radon"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("radon")
        if not tool:
            return []

        findings: list[Finding] = []

        # Cyclomatic complexity
        cc_result = subprocess.run(
            [tool, "cc", str(path), "-j", "-s"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        try:
            cc_data = json.loads(cc_result.stdout)
        except json.JSONDecodeError:
            cc_data = {}

        for filepath, blocks in cc_data.items():
            for block in blocks:
                cc = block.get("complexity", 0)
                findings.append(
                    Finding(
                        tool="radon",
                        rule_id=f"CC-{block.get('rank', '?')}",
                        severity=cc_to_severity(cc),
                        category=Category.COMPLEXITY,
                        file=filepath,
                        line=block.get("lineno"),
                        message=f"Cyclomatic complexity {cc} ({block.get('rank', '?')}) in {block.get('name', '?')}",
                    )
                )

        # Maintainability Index
        mi_result = subprocess.run(
            [tool, "mi", str(path), "-j"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        try:
            mi_data = json.loads(mi_result.stdout)
        except json.JSONDecodeError:
            mi_data = {}

        for filepath, mi_blocks in mi_data.items():
            if isinstance(mi_blocks, list):
                for block in mi_blocks:
                    mi = block.get("mi", 0)
                    rank = block.get("rank", "?")
                    if rank in ("D", "E", "F"):
                        from code_auditor.models import Severity
                        findings.append(
                            Finding(
                                tool="radon",
                                rule_id=f"MI-{rank}",
                                severity=Severity.MEDIUM if rank == "D" else Severity.HIGH,
                                category=Category.QUALITY,
                                file=filepath,
                                line=block.get("lineno"),
                                message=f"Maintainability Index {mi:.1f} (rank {rank}) in {block.get('name', '?')}",
                            )
                        )

        return findings
