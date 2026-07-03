"""HTML report generator with interactive sorting and filtering."""

from __future__ import annotations

from pathlib import Path

from code_auditor.models import Report

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#0284c7",
    "info": "#6b7280",
}

SEVERITY_BG = {
    "critical": "#fef2f2",
    "high": "#fff7ed",
    "medium": "#fefce8",
    "low": "#f0f9ff",
    "info": "#f9fafb",
}


def generate_html(report: Report) -> str:
    m = report.metadata
    s = report.summary
    findings = sorted(report.findings, key=lambda f: f.severity.rank)

    # Build summary cards
    severity_cards = ""
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = s.by_severity.get(sev, 0)
        if count:
            color = SEVERITY_COLORS[sev]
            severity_cards += f"""
            <div class="card" style="border-left: 4px solid {color}">
                <div class="card-count" style="color: {color}">{count}</div>
                <div class="card-label">{sev.title()}</div>
            </div>"""

    # Build OWASP table rows
    owasp_rows = ""
    for owasp, count in sorted(s.by_owasp.items()):
        owasp_rows += f"<tr><td>{owasp}</td><td>{count}</td></tr>"

    # Build category rows
    category_rows = ""
    for cat, count in sorted(s.by_category.items(), key=lambda x: -x[1]):
        category_rows += f"<tr><td>{cat.replace('_', ' ').title()}</td><td>{count}</td></tr>"

    # Build finding rows
    finding_rows = ""
    for f in findings:
        color = SEVERITY_COLORS[f.severity.value]
        bg = SEVERITY_BG[f.severity.value]
        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "N/A")
        owasp = f.owasp_mapping if f.owasp_mapping != "N/A" else ""
        fix = f.fix_suggestion or ""
        finding_rows += f"""
        <tr style="background: {bg}" data-severity="{f.severity.value}" data-tool="{f.tool}" data-category="{f.category.value}">
            <td><span class="badge" style="background: {color}">{f.severity.value.upper()}</span></td>
            <td><code>{f.rule_id}</code></td>
            <td>{f.tool}</td>
            <td>{f.category.value.replace('_', ' ').title()}</td>
            <td>{owasp}</td>
            <td class="msg">{_escape(f.message)}</td>
            <td class="loc"><code>{_escape(loc)}</code></td>
            <td class="fix">{_escape(fix)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Audit Report — {_escape(m.target)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 24px; }}
  .header {{ background: #0f172a; color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
  .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
  .header .meta {{ color: #94a3b8; font-size: 14px; }}
  .header .meta span {{ margin-right: 16px; }}
  .cards {{ display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }}
  .card {{ background: white; padding: 20px 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 120px; }}
  .card-count {{ font-size: 32px; font-weight: 700; }}
  .card-label {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
  .section {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; overflow: hidden; }}
  .section-header {{ padding: 16px 20px; border-bottom: 1px solid #e2e8f0; font-weight: 600; font-size: 16px; }}
  .section-body {{ padding: 16px 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; background: #f1f5f9; border-bottom: 2px solid #e2e8f0; font-weight: 600; position: sticky; top: 0; cursor: pointer; user-select: none; }}
  th:hover {{ background: #e2e8f0; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
  tr:hover {{ background: #f8fafc !important; }}
  .badge {{ padding: 2px 8px; border-radius: 4px; color: white; font-size: 11px; font-weight: 600; white-space: nowrap; }}
  code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 12px; }}
  .msg {{ max-width: 400px; }}
  .loc {{ white-space: nowrap; font-size: 12px; color: #64748b; }}
  .fix {{ max-width: 300px; color: #059669; font-size: 12px; }}
  .filters {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
  .filters select, .filters input {{ padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }}
  .filters input {{ width: 250px; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  .stats-table {{ width: auto; }}
  .stats-table td, .stats-table th {{ padding: 6px 16px 6px 0; }}
  .findings-wrap {{ max-height: 70vh; overflow-y: auto; }}
</style>
</head>
<body>

<div class="header">
  <h1>Code Audit Report</h1>
  <div class="meta">
    <span>Target: <strong>{_escape(m.target)}</strong></span>
    <span>Date: {m.timestamp}</span>
    <span>Tools: {', '.join(m.tools_used)}</span>
  </div>
</div>

<div class="cards">
  <div class="card" style="border-left: 4px solid #0f172a">
    <div class="card-count">{s.total_findings}</div>
    <div class="card-label">Total</div>
  </div>
  {severity_cards}
</div>

<div class="two-col">
  <div class="section">
    <div class="section-header">By Category</div>
    <div class="section-body">
      <table class="stats-table">{category_rows}</table>
    </div>
  </div>
  <div class="section">
    <div class="section-header">OWASP Top 10</div>
    <div class="section-body">
      <table class="stats-table">{owasp_rows if owasp_rows else '<tr><td colspan="2" style="color:#94a3b8">No OWASP findings</td></tr>'}</table>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-header">Findings ({s.total_findings})</div>
  <div class="section-body">
    <div class="filters">
      <select id="filter-severity" onchange="filterTable()">
        <option value="">All Severity</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
        <option value="info">Info</option>
      </select>
      <select id="filter-tool" onchange="filterTable()">
        <option value="">All Tools</option>
        {"".join(f'<option value="{t}">{t}</option>' for t in sorted(report.metadata.tools_used))}
      </select>
      <select id="filter-category" onchange="filterTable()">
        <option value="">All Categories</option>
        {"".join(f'<option value="{c}">{c.replace("_"," ").title()}</option>' for c in sorted(s.by_category.keys()))}
      </select>
      <input type="text" id="filter-search" placeholder="Search message..." oninput="filterTable()">
    </div>
    <div class="findings-wrap">
      <table id="findings-table">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Severity</th>
            <th onclick="sortTable(1)">Rule</th>
            <th onclick="sortTable(2)">Tool</th>
            <th onclick="sortTable(3)">Category</th>
            <th onclick="sortTable(4)">OWASP</th>
            <th onclick="sortTable(5)">Message</th>
            <th onclick="sortTable(6)">Location</th>
            <th onclick="sortTable(7)">Fix</th>
          </tr>
        </thead>
        <tbody>
          {finding_rows}
        </tbody>
      </table>
    </div>
  </div>
</div>

<script>
function filterTable() {{
  const sev = document.getElementById('filter-severity').value;
  const tool = document.getElementById('filter-tool').value;
  const cat = document.getElementById('filter-category').value;
  const search = document.getElementById('filter-search').value.toLowerCase();
  document.querySelectorAll('#findings-table tbody tr').forEach(row => {{
    const show =
      (!sev || row.dataset.severity === sev) &&
      (!tool || row.dataset.tool === tool) &&
      (!cat || row.dataset.category === cat) &&
      (!search || row.textContent.toLowerCase().includes(search));
    row.style.display = show ? '' : 'none';
  }});
}}

let sortDir = {{}};
function sortTable(col) {{
  const tbody = document.querySelector('#findings-table tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[col] = !sortDir[col];
  rows.sort((a, b) => {{
    const av = a.cells[col].textContent.trim();
    const bv = b.cells[col].textContent.trim();
    return sortDir[col] ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_html(report: Report, output: Path | str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_html(report), encoding="utf-8")
