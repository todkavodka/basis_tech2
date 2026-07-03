"""Markdown report generator."""

from __future__ import annotations

from pathlib import Path

from code_auditor.models import Report


def generate_markdown(report: Report) -> str:
    lines: list[str] = []
    m = report.metadata
    s = report.summary

    lines.append("# Code Audit Report\n")
    lines.append(f"- **Target**: `{m.target}`")
    lines.append(f"- **Date**: {m.timestamp}")
    lines.append(f"- **Tools**: {', '.join(m.tools_used)}")
    lines.append("")

    # Summary
    lines.append("## Summary\n")
    lines.append(f"**Total findings**: {s.total_findings}\n")

    if s.by_severity:
        lines.append("### By Severity\n")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in ["critical", "high", "medium", "low", "info"]:
            if sev in s.by_severity:
                lines.append(f"| {sev.title()} | {s.by_severity[sev]} |")
        lines.append("")

    if s.by_category:
        lines.append("### By Category\n")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, count in sorted(s.by_category.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat.replace('_', ' ').title()} | {count} |")
        lines.append("")

    if s.by_owasp:
        lines.append("### OWASP Breakdown\n")
        lines.append("| OWASP | Count |")
        lines.append("|-------|-------|")
        for owasp, count in sorted(s.by_owasp.items()):
            lines.append(f"| {owasp} | {count} |")
        lines.append("")

    # Findings
    lines.append("## Findings\n")
    sorted_findings = sorted(report.findings, key=lambda f: f.severity.rank)
    for f in sorted_findings:
        severity_icon = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MED",
            "low": "LOW",
            "info": "INFO",
        }.get(f.severity.value, "?")

        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "N/A")
        lines.append(f"### [{severity_icon}] `{f.rule_id}` — {f.tool}\n")
        lines.append(f"- **Location**: `{loc}`")
        lines.append(f"- **Category**: {f.category.value}")
        if f.owasp_mapping != "N/A":
            lines.append(f"- **OWASP**: {f.owasp_mapping}")
        lines.append(f"- **Message**: {f.message}")
        if f.fix_suggestion:
            lines.append(f"- **Fix**: {f.fix_suggestion}")
        lines.append("")

    return "\n".join(lines)


def write_markdown(report: Report, output: Path | str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_markdown(report))
