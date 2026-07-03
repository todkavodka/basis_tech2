"""Tests for analyzers (run against test-project fixture)."""

from pathlib import Path

from code_auditor.analyzers.base import cc_to_severity, find_tool, severity_from_string
from code_auditor.models import Severity

TEST_PROJECT = Path("/tmp/test-project")


def test_find_tool_bandit():
    tool = find_tool("bandit")
    assert tool is not None
    assert "bandit" in tool


def test_find_tool_radon():
    tool = find_tool("radon")
    assert tool is not None


def test_cc_to_severity():
    assert cc_to_severity(1) == Severity.INFO
    assert cc_to_severity(5) == Severity.INFO
    assert cc_to_severity(8) == Severity.LOW
    assert cc_to_severity(15) == Severity.MEDIUM
    assert cc_to_severity(25) == Severity.HIGH
    assert cc_to_severity(50) == Severity.CRITICAL


def test_severity_from_string():
    assert severity_from_string("high") == Severity.HIGH
    assert severity_from_string("MEDIUM") == Severity.MEDIUM
    assert severity_from_string("unknown") == Severity.INFO


def test_bandit_analyzer():
    from code_auditor.analyzers.bandit_analyzer import BanditAnalyzer

    a = BanditAnalyzer()
    findings = a.analyze(TEST_PROJECT)
    assert len(findings) > 0
    assert all(f.tool == "bandit" for f in findings)
    assert any(f.severity == Severity.HIGH for f in findings)


def test_radon_analyzer():
    from code_auditor.analyzers.radon_analyzer import RadonAnalyzer

    a = RadonAnalyzer()
    findings = a.analyze(TEST_PROJECT)
    assert len(findings) > 0
    assert all(f.tool == "radon" for f in findings)


def test_vulture_analyzer():
    from code_auditor.analyzers.vulture_analyzer import VultureAnalyzer

    a = VultureAnalyzer()
    findings = a.analyze(TEST_PROJECT)
    assert len(findings) > 0
    assert all(f.tool == "vulture" for f in findings)


def test_pylint_analyzer():
    from code_auditor.analyzers.pylint_analyzer import PylintAnalyzer

    a = PylintAnalyzer()
    findings = a.analyze(TEST_PROJECT)
    assert len(findings) > 0
    assert all(f.tool == "pylint" for f in findings)


def test_semgrep_analyzer():
    from code_auditor.analyzers.semgrep_analyzer import SemgrepAnalyzer

    a = SemgrepAnalyzer()
    findings = a.analyze(TEST_PROJECT)
    assert len(findings) > 0
    assert all(f.tool == "semgrep" for f in findings)


def test_registry():
    from code_auditor.registry import all_analyzers, list_names

    names = list_names()
    assert "bandit" in names
    assert "radon" in names
    assert "vulture" in names
    assert "pylint" in names
    assert "semgrep" in names
    assert "pip-audit" in names

    registry = all_analyzers()
    assert len(registry) == 6
