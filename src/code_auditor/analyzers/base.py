"""Base protocol and helpers for analyzers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Protocol

from code_auditor.models import Category, Finding, Severity


class Analyzer(Protocol):
    name: str

    def analyze(self, path: Path) -> list[Finding]: ...


def find_tool(name: str) -> str | None:
    """Find a tool executable, checking venv bin first, then system PATH."""
    # Check venv bin directory (relative to current Python)
    python_dir = Path(sys.executable).parent
    venv_tool = python_dir / name
    if venv_tool.exists():
        return str(venv_tool)
    # Check system PATH
    import shutil
    return shutil.which(name)


def severity_from_string(s: str) -> Severity:
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    return mapping.get(s.lower(), Severity.INFO)


def cc_to_severity(complexity: int) -> Severity:
    if complexity <= 5:
        return Severity.INFO
    if complexity <= 10:
        return Severity.LOW
    if complexity <= 20:
        return Severity.MEDIUM
    if complexity <= 30:
        return Severity.HIGH
    return Severity.CRITICAL
