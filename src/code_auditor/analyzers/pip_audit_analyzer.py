"""pip-audit dependency vulnerability analyzer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from code_auditor.analyzers.base import find_tool
from code_auditor.models import Category, Finding, Severity


def _find_requirements(path: Path) -> str | None:
    for name in ("requirements.txt", "requirements.lock", "Pipfile.lock", "pyproject.toml"):
        p = path / name
        if p.exists():
            return str(p)
    return None


class PipAuditAnalyzer:
    name = "pip-audit"

    def analyze(self, path: Path) -> list[Finding]:
        tool = find_tool("pip-audit")
        if not tool:
            return []

        req = _find_requirements(path)
        cmd = [tool, "-f", "json"]
        if req and req.endswith(".txt"):
            cmd.extend(["-r", req])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        findings: list[Finding] = []
        for dep in data.get("dependencies", []):
            for vuln in dep.get("vulns", []):
                vid = vuln.get("id", "")
                fix_versions = vuln.get("fix_versions", [])
                fix_msg = f"Fix: upgrade to {fix_versions[0]}" if fix_versions else ""
                findings.append(
                    Finding(
                        tool="pip-audit",
                        rule_id=vid,
                        severity=Severity.HIGH,
                        category=Category.DEPENDENCY,
                        owasp_mapping="A06",
                        message=f"{dep['name']}=={dep.get('version', '?')}: {vid} — {vuln.get('description', '')}",
                        fix_suggestion=fix_msg,
                    )
                )

        return findings
