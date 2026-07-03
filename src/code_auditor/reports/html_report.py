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

SEVERITY_RU = {
    "critical": "Критический",
    "high": "Высокий",
    "medium": "Средний",
    "low": "Низкий",
    "info": "Инфо",
}

CATEGORY_RU = {
    "security": "Безопасность",
    "quality": "Качество",
    "complexity": "Сложность",
    "dead_code": "Мёртвый код",
    "dependency": "Зависимости",
    "architecture": "Архитектура",
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
                <div class="card-label">{SEVERITY_RU.get(sev, sev)}</div>
            </div>"""

    # Build OWASP table rows
    owasp_rows = ""
    for owasp, count in sorted(s.by_owasp.items()):
        owasp_rows += f"<tr><td>{owasp}</td><td>{count}</td></tr>"

    # Build category rows
    category_rows = ""
    for cat, count in sorted(s.by_category.items(), key=lambda x: -x[1]):
        cat_name = CATEGORY_RU.get(cat, cat.replace("_", " ").title())
        category_rows += f"<tr><td>{cat_name}</td><td>{count}</td></tr>"

    # Build finding rows
    finding_rows = ""
    for f in findings:
        color = SEVERITY_COLORS[f.severity.value]
        bg = SEVERITY_BG[f.severity.value]
        sev_name = SEVERITY_RU.get(f.severity.value, f.severity.value)
        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "—")
        owasp = f.owasp_mapping if f.owasp_mapping != "N/A" else ""
        fix = f.fix_suggestion or ""
        cat_name = CATEGORY_RU.get(f.category.value, f.category.value)
        finding_rows += f"""
        <tr style="background: {bg}" data-severity="{f.severity.value}" data-tool="{f.tool}" data-category="{f.category.value}">
            <td><span class="badge" style="background: {color}">{sev_name}</span></td>
            <td><code>{f.rule_id}</code></td>
            <td>{f.tool}</td>
            <td>{cat_name}</td>
            <td>{owasp}</td>
            <td class="msg">{_escape(f.message)}</td>
            <td class="loc"><code>{_escape(loc)}</code></td>
            <td class="fix">{_escape(fix)}</td>
        </tr>"""

    # Tool filter options
    tool_options = "".join(
        f'<option value="{t}">{t}</option>'
        for t in sorted(set(f.tool for f in findings))
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Аудит кода — {_escape(m.target)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }}
  .container {{ max-width: 1600px; margin: 0 auto; padding: 24px; }}
  .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
  .header h1 {{ font-size: 28px; margin-bottom: 8px; color: #f8fafc; }}
  .header .meta {{ color: #94a3b8; font-size: 14px; display: flex; gap: 20px; flex-wrap: wrap; }}
  .header .meta span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .header .meta strong {{ color: #e2e8f0; }}
  .cards {{ display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }}
  .card {{ background: #1e293b; border: 1px solid #334155; padding: 20px 24px; border-radius: 8px; min-width: 120px; }}
  .card-count {{ font-size: 36px; font-weight: 700; }}
  .card-label {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
  .section {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-bottom: 24px; overflow: hidden; }}
  .section-header {{ padding: 16px 20px; border-bottom: 1px solid #334155; font-weight: 600; font-size: 16px; display: flex; justify-content: space-between; align-items: center; }}
  .section-body {{ padding: 16px 20px; }}
  .badge-count {{ background: #334155; padding: 2px 10px; border-radius: 12px; font-size: 13px; font-weight: 500; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; background: #1e293b; border-bottom: 2px solid #334155; font-weight: 600; position: sticky; top: 0; cursor: pointer; user-select: none; color: #94a3b8; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }}
  th:hover {{ color: #e2e8f0; background: #334155; }}
  th::after {{ content: " ⇅"; font-size: 10px; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1e293b; vertical-align: top; }}
  tr {{ transition: background 0.15s; }}
  tr:hover {{ background: #334155 !important; }}
  .badge {{ padding: 3px 10px; border-radius: 4px; color: white; font-size: 11px; font-weight: 600; white-space: nowrap; }}
  code {{ background: #334155; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-family: 'SF Mono', 'Fira Code', monospace; }}
  .msg {{ max-width: 450px; line-height: 1.5; }}
  .loc {{ white-space: nowrap; font-size: 12px; color: #64748b; }}
  .fix {{ max-width: 300px; color: #34d399; font-size: 12px; line-height: 1.4; }}
  .filters {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
  .filters select, .filters input {{ padding: 8px 12px; border: 1px solid #475569; border-radius: 6px; font-size: 13px; background: #0f172a; color: #e2e8f0; }}
  .filters select:focus, .filters input:focus {{ outline: none; border-color: #60a5fa; box-shadow: 0 0 0 2px rgba(96,165,250,0.2); }}
  .filters input {{ width: 300px; }}
  .filters input::placeholder {{ color: #64748b; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  .stats-table {{ width: auto; }}
  .stats-table td, .stats-table th {{ padding: 8px 16px 8px 0; border: none; }}
  .stats-table th {{ background: transparent; color: #94a3b8; text-transform: uppercase; font-size: 11px; }}
  .findings-wrap {{ max-height: 70vh; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #475569 #1e293b; }}
  .findings-wrap::-webkit-scrollbar {{ width: 8px; }}
  .findings-wrap::-webkit-scrollbar-track {{ background: #1e293b; }}
  .findings-wrap::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
  .footer {{ text-align: center; padding: 24px; color: #475569; font-size: 13px; }}
  .progress {{ position: fixed; top: 0; left: 0; height: 3px; background: #3b82f6; z-index: 1000; transition: width 0.3s; }}
</style>
</head>
<body>

<div class="progress" id="progress"></div>

<div class="container">

<div class="header">
  <h1>&#128270; Аудит кода</h1>
  <div class="meta">
    <span>&#128193; <strong>{_escape(m.target)}</strong></span>
    <span>&#128197; {m.timestamp[:10]}</span>
    <span>&#128295; {', '.join(m.tools_used)}</span>
    <span>&#128200; v{m.tool_version}</span>
  </div>
</div>

<div class="cards">
  <div class="card" style="border-left: 4px solid #3b82f6">
    <div class="card-count" style="color: #3b82f6">{s.total_findings}</div>
    <div class="card-label">Всего</div>
  </div>
  {severity_cards}
</div>

<div class="two-col">
  <div class="section">
    <div class="section-header">По категориям</div>
    <div class="section-body">
      <table class="stats-table">{category_rows}</table>
    </div>
  </div>
  <div class="section">
    <div class="section-header">OWASP Top 10</div>
    <div class="section-body">
      <table class="stats-table">{owasp_rows if owasp_rows else '<tr><td colspan="2" style="color:#64748b">Нет OWASP-находок</td></tr>'}</table>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-header">
    <span>Находки</span>
    <span class="badge-count" id="visible-count">{s.total_findings}</span>
  </div>
  <div class="section-body">
    <div class="filters">
      <select id="filter-severity" onchange="filterTable()">
        <option value="">Все серьёзности</option>
        <option value="critical">Критический</option>
        <option value="high">Высокий</option>
        <option value="medium">Средний</option>
        <option value="low">Низкий</option>
        <option value="info">Инфо</option>
      </select>
      <select id="filter-tool" onchange="filterTable()">
        <option value="">Все инструменты</option>
        {tool_options}
      </select>
      <select id="filter-category" onchange="filterTable()">
        <option value="">Все категории</option>
        {"".join(f'<option value="{c}">{CATEGORY_RU.get(c, c)}</option>' for c in sorted(s.by_category.keys()))}
      </select>
      <input type="text" id="filter-search" placeholder="Поиск по сообщению..." oninput="filterTable()">
    </div>
    <div class="findings-wrap">
      <table id="findings-table">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Серьёзность</th>
            <th onclick="sortTable(1)">Правило</th>
            <th onclick="sortTable(2)">Инструмент</th>
            <th onclick="sortTable(3)">Категория</th>
            <th onclick="sortTable(4)">OWASP</th>
            <th onclick="sortTable(5)">Описание</th>
            <th onclick="sortTable(6)">Расположение</th>
            <th onclick="sortTable(7)">Исправление</th>
          </tr>
        </thead>
        <tbody>
          {finding_rows}
        </tbody>
      </table>
    </div>
  </div>
</div>

<div class="footer">
  Сгенерировано Code Auditor v{m.tool_version} | {m.timestamp[:10]}
</div>

</div>

<script>
const progress = document.getElementById('progress');
progress.style.width = '30%';

function filterTable() {{
  const sev = document.getElementById('filter-severity').value;
  const tool = document.getElementById('filter-tool').value;
  const cat = document.getElementById('filter-category').value;
  const search = document.getElementById('filter-search').value.toLowerCase();
  let visible = 0;
  document.querySelectorAll('#findings-table tbody tr').forEach(row => {{
    const show =
      (!sev || row.dataset.severity === sev) &&
      (!tool || row.dataset.tool === tool) &&
      (!cat || row.dataset.category === cat) &&
      (!search || row.textContent.toLowerCase().includes(search));
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('visible-count').textContent = visible;
}}

let sortDir = {{}};
function sortTable(col) {{
  const tbody = document.querySelector('#findings-table tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[col] = !sortDir[col];
  rows.sort((a, b) => {{
    const av = a.cells[col].textContent.trim();
    const bv = b.cells[col].textContent.trim();
    return sortDir[col] ? av.localeCompare(bv, 'ru') : bv.localeCompare(av, 'ru');
  }});
  rows.forEach(r => tbody.appendChild(r));
}}

progress.style.width = '100%';
setTimeout(() => {{ progress.style.opacity = '0'; }}, 500);
</script>
</body>
</html>"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_html(report: Report, output: Path | str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_html(report), encoding="utf-8")
