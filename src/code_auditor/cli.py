"""CLI interface for code-auditor."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from code_auditor import __version__
from code_auditor.analyzers.ai_analyzer import AIAnalyzer
from code_auditor.models import Finding, Report, Metadata, Severity
from code_auditor.registry import all_analyzers
from code_auditor.reports.json_report import write_json
from code_auditor.reports.markdown_report import write_markdown

app = typer.Typer(
    name="code-auditor",
    help="AI-powered code auditor: security, quality, and architecture analysis.",
    no_args_is_help=True,
)
console = Console()


def _filter_findings(findings: list[Finding], min_severity: str) -> list[Finding]:
    if min_severity == "info":
        return findings
    sev = Severity(min_severity)
    return [f for f in findings if f.severity.rank <= sev.rank]


@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to project directory"),
    analyzer: list[str] = typer.Option(
        ["all"], "-a", "--analyzer",
        help="Analyzers to run (bandit, radon, vulture, pylint, semgrep, pip-audit, ai, all)",
    ),
    output: Optional[str] = typer.Option(
        None, "-o", "--output",
        help="Output file path (.json or .md). If omitted, prints to terminal.",
    ),
    output_format: str = typer.Option(
        "markdown", "-f", "--format",
        help="Report format: json, markdown, both",
    ),
    severity: str = typer.Option(
        "info", "-s", "--severity",
        help="Minimum severity to include: critical, high, medium, low, info",
    ),
    model: str = typer.Option(
        "openai/gpt-4o", "-m", "--model",
        help="LLM model for AI analysis (e.g., openai/gpt-4o, anthropic/claude-sonnet-4-20250514, ollama/llama3)",
    ),
    no_ai: bool = typer.Option(
        False, "--no-ai", help="Skip AI-powered analysis"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Verbose output"
    ),
) -> None:
    """Scan a codebase and generate an audit report."""
    target = Path(path)
    if not target.is_dir():
        console.print(f"[red]Error: {target} is not a directory[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Code Auditor v{__version__}[/bold]")
    console.print(f"Target: {target.resolve()}\n")

    # Discover analyzers
    registry = all_analyzers()
    selected_names = set(analyzer)
    run_all = "all" in selected_names

    if not run_all:
        available = list(registry.keys())
        invalid = selected_names - set(available) - {"ai"}
        if invalid:
            console.print(f"[yellow]Unknown analyzers: {', '.join(invalid)}[/yellow]")
            console.print(f"Available: {', '.join(available)} + ai")
            raise typer.Exit(1)

    # Collect findings from static analyzers
    all_findings: list[Finding] = []
    tools_used: list[str] = []

    for name, analyzer_instance in registry.items():
        if not run_all and name not in selected_names:
            continue
        if verbose:
            console.print(f"  Running [cyan]{name}[/cyan]...")
        try:
            findings = analyzer_instance.analyze(target)
            all_findings.extend(findings)
            tools_used.append(name)
            if verbose and findings:
                console.print(f"    Found {len(findings)} issues")
        except Exception as e:
            console.print(f"  [yellow]Warning: {name} failed: {e}[/yellow]")

    # AI analysis
    if not no_ai and (run_all or "ai" in selected_names):
        if verbose:
            console.print(f"  Running [cyan]ai ({model})[/cyan]...")
        try:
            ai = AIAnalyzer(model=model)
            findings = ai.analyze(target)
            all_findings.extend(findings)
            tools_used.append(f"ai ({model})")
            if verbose and findings:
                console.print(f"    Found {len(findings)} issues")
        except Exception as e:
            console.print(f"  [yellow]Warning: AI analysis failed: {e}[/yellow]")

    # Filter by severity
    all_findings = _filter_findings(all_findings, severity)

    # Build report
    report = Report(
        metadata=Metadata(target=str(target.resolve()), tools_used=tools_used),
        findings=all_findings,
    )
    report.compute_summary()

    # Output
    if output:
        out_path = Path(output)
        if output_format in ("json", "both"):
            json_path = out_path.with_suffix(".json") if output_format == "both" else out_path
            write_json(report, json_path)
            console.print(f"\n[green]JSON report saved to {json_path}[/green]")
        if output_format in ("markdown", "both"):
            md_path = out_path.with_suffix(".md") if output_format == "both" else out_path
            write_markdown(report, md_path)
            console.print(f"[green]Markdown report saved to {md_path}[/green]")
    else:
        # Print summary table
        s = report.summary
        table = Table(title="Audit Summary", show_header=True)
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = s.by_severity.get(sev, 0)
            if count:
                style = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "cyan"}.get(sev, "")
                table.add_row(sev.title(), str(count), style=style)
        console.print(table)
        console.print(f"\nTotal: {s.total_findings} findings from {len(tools_used)} tools\n")

        # Print top findings
        if all_findings:
            console.print("[bold]Top findings:[/bold]\n")
            for f in sorted(all_findings, key=lambda x: x.severity.rank)[:20]:
                loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "")
                console.print(
                    f"  [{f.severity.value.upper():>8}] {f.tool}/{f.rule_id} — {f.message}"
                )
                if loc:
                    console.print(f"           at {loc}")
                console.print()

    # Exit code based on severity
    if report.summary.by_severity.get("critical", 0) > 0:
        raise typer.Exit(2)
    if report.summary.by_severity.get("high", 0) > 0:
        raise typer.Exit(1)


@app.command()
def list_analyzers() -> None:
    """List available analyzers."""
    registry = all_analyzers()
    table = Table(title="Available Analyzers", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Description")
    for name in sorted(registry):
        table.add_row(name, "static", _analyzer_descriptions.get(name, ""))
    table.add_row("ai", "llm", "AI-powered deep analysis (requires API key)")
    console.print(table)


_analyzer_descriptions = {
    "bandit": "Security vulnerabilities (OWASP, hardcoded secrets)",
    "radon": "Cyclomatic complexity, maintainability index",
    "vulture": "Dead/unused code detection",
    "pylint": "Code quality, SOLID, God objects, duplication",
    "semgrep": "Pattern/taint-based security analysis",
    "pip-audit": "Dependency vulnerability scanning",
}


if __name__ == "__main__":
    app()
