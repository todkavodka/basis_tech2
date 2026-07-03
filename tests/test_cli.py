"""Tests for CLI commands."""

from typer.testing import CliRunner

from code_auditor.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AI-powered code auditor" in result.output


def test_list_analyzers():
    result = runner.invoke(app, ["list-analyzers"])
    assert result.exit_code == 0
    assert "bandit" in result.output
    assert "radon" in result.output


def test_scan_no_ai():
    result = runner.invoke(app, ["scan", "/tmp/test-project", "--no-ai"])
    # Exit code 1 = HIGH findings found (expected), 0 = no issues
    assert result.exit_code in (0, 1)
    assert "findings" in result.output.lower()


def test_scan_json_output(tmp_path):
    out = tmp_path / "report.json"
    result = runner.invoke(app, ["scan", "/tmp/test-project", "--no-ai", "-o", str(out), "-f", "json"])
    assert result.exit_code in (0, 1)
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert "findings" in data
    assert data["summary"]["total_findings"] > 0


def test_scan_markdown_output(tmp_path):
    out = tmp_path / "report.md"
    result = runner.invoke(app, ["scan", "/tmp/test-project", "--no-ai", "-o", str(out), "-f", "markdown"])
    assert result.exit_code in (0, 1)
    assert out.exists()
    content = out.read_text()
    assert "# Code Audit Report" in content
    assert "## Summary" in content


def test_scan_severity_filter():
    result = runner.invoke(app, ["scan", "/tmp/test-project", "--no-ai", "-s", "high"])
    # 2 HIGH findings exist, so exit code is 1
    assert result.exit_code == 1
    assert "Total: 2" in result.output


def test_scan_specific_analyzer():
    result = runner.invoke(app, ["scan", "/tmp/test-project", "--no-ai", "-a", "bandit"])
    assert result.exit_code in (0, 1)
    assert "bandit" in result.output.lower()


def test_scan_invalid_path():
    result = runner.invoke(app, ["scan", "/nonexistent", "--no-ai"])
    assert result.exit_code == 1
