"""Tests for data models."""

from code_auditor.models import (
    Category,
    Finding,
    Metadata,
    Report,
    Severity,
    Summary,
)


def test_severity_ranking():
    assert Severity.CRITICAL.rank < Severity.HIGH.rank
    assert Severity.HIGH.rank < Severity.MEDIUM.rank
    assert Severity.MEDIUM.rank < Severity.LOW.rank
    assert Severity.LOW.rank < Severity.INFO.rank


def test_severity_from_string():
    assert Severity("critical") == Severity.CRITICAL
    assert Severity("high") == Severity.HIGH
    assert Severity("medium") == Severity.MEDIUM


def test_finding_creation():
    f = Finding(
        tool="bandit",
        rule_id="B608",
        severity=Severity.HIGH,
        category=Category.SECURITY,
        owasp_mapping="A03",
        file="app.py",
        line=42,
        message="SQL injection",
    )
    assert f.tool == "bandit"
    assert f.severity == Severity.HIGH
    assert f.owasp_mapping == "A03"


def test_finding_serialization():
    f = Finding(
        tool="radon",
        rule_id="CC-C",
        severity=Severity.MEDIUM,
        category=Category.COMPLEXITY,
        file="utils.py",
        line=10,
        message="High complexity",
    )
    data = f.model_dump()
    assert data["tool"] == "radon"
    assert data["severity"] == "medium"
    restored = Finding(**data)
    assert restored == f


def test_report_compute_summary():
    report = Report(
        metadata=Metadata(target="/test"),
        findings=[
            Finding(tool="a", rule_id="R1", severity=Severity.HIGH, category=Category.SECURITY, message="x"),
            Finding(tool="b", rule_id="R2", severity=Severity.LOW, category=Category.QUALITY, message="y"),
            Finding(tool="c", rule_id="R3", severity=Severity.HIGH, category=Category.SECURITY, message="z", owasp_mapping="A03"),
        ],
    )
    report.compute_summary()
    assert report.summary.total_findings == 3
    assert report.summary.by_severity["high"] == 2
    assert report.summary.by_severity["low"] == 1
    assert report.summary.by_category["security"] == 2
    assert report.summary.by_owasp["A03"] == 1


def test_report_json_roundtrip():
    report = Report(
        metadata=Metadata(target="/test", tools_used=["bandit"]),
        findings=[
            Finding(tool="bandit", rule_id="B105", severity=Severity.LOW, category=Category.SECURITY, message="hardcoded pwd"),
        ],
    )
    report.compute_summary()
    data = report.model_dump()
    restored = Report(**data)
    assert len(restored.findings) == 1
    assert restored.summary.total_findings == 1
