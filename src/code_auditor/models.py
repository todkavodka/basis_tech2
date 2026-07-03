"""Data models for audit findings and reports."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }[self]


class Category(str, Enum):
    SECURITY = "security"
    QUALITY = "quality"
    COMPLEXITY = "complexity"
    DEAD_CODE = "dead_code"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"


class Finding(BaseModel):
    tool: str
    rule_id: str
    severity: Severity
    category: Category
    owasp_mapping: str = "N/A"
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    message: str
    fix_suggestion: str = ""
    confidence: str = ""


class Summary(BaseModel):
    total_findings: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_owasp: dict[str, int] = Field(default_factory=dict)


class Metadata(BaseModel):
    tool_version: str = "0.1.0"
    target: str = ""
    timestamp: str = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat()
    )
    tools_used: list[str] = Field(default_factory=list)


class Report(BaseModel):
    metadata: Metadata
    summary: Summary = Field(default_factory=Summary)
    findings: list[Finding] = Field(default_factory=list)

    def compute_summary(self) -> None:
        by_sev: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        by_owasp: dict[str, int] = {}
        for f in self.findings:
            by_sev[f.severity.value] = by_sev.get(f.severity.value, 0) + 1
            by_cat[f.category.value] = by_cat.get(f.category.value, 0) + 1
            if f.owasp_mapping != "N/A":
                by_owasp[f.owasp_mapping] = by_owasp.get(f.owasp_mapping, 0) + 1
        self.summary = Summary(
            total_findings=len(self.findings),
            by_severity=by_sev,
            by_category=by_cat,
            by_owasp=by_owasp,
        )
