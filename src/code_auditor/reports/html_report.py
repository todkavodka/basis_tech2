"""HTML report generator with interactive sorting and filtering."""

from __future__ import annotations

from pathlib import Path

from code_auditor.models import Report

SEVERITY_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#3b82f6",
    "info": "#6b7280",
}

SEVERITY_BG = {
    "critical": "rgba(239,68,68,0.08)",
    "high": "rgba(249,115,22,0.08)",
    "medium": "rgba(234,179,8,0.06)",
    "low": "rgba(59,130,246,0.06)",
    "info": "transparent",
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

    severity_cards = ""
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = s.by_severity.get(sev, 0)
        if count:
            color = SEVERITY_COLORS[sev]
            severity_cards += f"""
            <div class="stat-card">
              <div class="stat-num" style="color:{color}">{count}</div>
              <div class="stat-label">{SEVERITY_RU.get(sev, sev)}</div>
              <div class="stat-bar" style="background:{color};width:{max(count*100//max(s.total_findings,1),2)}%"></div>
            </div>"""

    owasp_rows = ""
    for owasp, count in sorted(s.by_owasp.items()):
        owasp_rows += f"<tr><td>{owasp}</td><td><b>{count}</b></td></tr>"

    category_rows = ""
    for cat, count in sorted(s.by_category.items(), key=lambda x: -x[1]):
        cat_name = CATEGORY_RU.get(cat, cat.replace("_", " ").title())
        category_rows += f"<tr><td>{cat_name}</td><td><b>{count}</b></td></tr>"

    finding_rows = ""
    for idx, f in enumerate(findings):
        color = SEVERITY_COLORS[f.severity.value]
        bg = SEVERITY_BG[f.severity.value]
        sev_name = SEVERITY_RU.get(f.severity.value, f.severity.value)
        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "—")
        owasp = f.owasp_mapping if f.owasp_mapping != "N/A" else ""
        fix = f.fix_suggestion or ""
        cat_name = CATEGORY_RU.get(f.category.value, f.category.value)
        finding_rows += f"""
        <tr style="background:{bg}" data-severity="{f.severity.value}" data-tool="{f.tool}" data-category="{f.category.value}">
          <td><span class="sev-badge" style="background:{color}">{sev_name}</span></td>
          <td><code>{f.rule_id}</code></td>
          <td class="tool-cell">{f.tool}</td>
          <td>{cat_name}</td>
          <td>{owasp}</td>
          <td class="msg-cell">{_escape(f.message)}</td>
          <td class="loc-cell"><code>{_escape(loc)}</code></td>
          <td class="fix-cell">{_escape(fix)}</td>
        </tr>"""

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
:root {{
  --bg: #0b0f19;
  --surface: #111827;
  --surface2: #1a2234;
  --border: #1e2d3d;
  --border2: #2a3a4d;
  --text: #e2e8f0;
  --text2: #94a3b8;
  --text3: #64748b;
  --accent: #3b82f6;
  --accent2: #60a5fa;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
.wrap {{ max-width: 1600px; margin: 0 auto; padding: 32px 24px; }}

/* Header */
.hdr {{ background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%); border: 1px solid var(--border); border-radius: 16px; padding: 40px 48px; margin-bottom: 32px; position: relative; overflow: hidden; }}
.hdr::before {{ content: ''; position: absolute; top: -50%; right: -20%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%); pointer-events: none; }}
.hdr h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 12px; letter-spacing: -0.5px; }}
.hdr .meta {{ color: var(--text2); font-size: 14px; display: flex; gap: 24px; flex-wrap: wrap; }}
.hdr .meta span {{ display: inline-flex; align-items: center; gap: 6px; }}

/* Stats row */
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; position: relative; overflow: hidden; }}
.stat-num {{ font-size: 36px; font-weight: 800; line-height: 1; }}
.stat-label {{ font-size: 13px; color: var(--text2); margin-top: 6px; }}
.stat-bar {{ position: absolute; bottom: 0; left: 0; height: 3px; border-radius: 0 2px 0 0; transition: width 0.6s ease; }}

/* Two col */
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }}
@media (max-width: 900px) {{ .cols {{ grid-template-columns: 1fr; }} }}

/* Sections */
.sec {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
.sec-hdr {{ padding: 16px 24px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }}
.sec-body {{ padding: 20px 24px; }}
.badge {{ background: var(--surface2); border: 1px solid var(--border2); padding: 3px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}

/* Stats tables */
.stbl {{ width: 100%; }}
.stbl td {{ padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px; }}
.stbl tr:last-child td {{ border-bottom: none; }}

/* Filters */
.filters {{ display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
.filters select, .filters input {{ padding: 8px 14px; border: 1px solid var(--border2); border-radius: 8px; font-size: 13px; background: var(--bg); color: var(--text); transition: border-color 0.2s; }}
.filters select:focus, .filters input:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }}
.filters input {{ width: 320px; }}
.filters input::placeholder {{ color: var(--text3); }}

/* Table */
.tbl-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
thead th {{ position: sticky; top: 0; background: var(--surface); z-index: 10; text-align: left; padding: 12px 14px; border-bottom: 2px solid var(--border2); font-weight: 600; color: var(--text2); text-transform: uppercase; font-size: 11px; letter-spacing: 0.6px; cursor: pointer; user-select: none; white-space: nowrap; }}
thead th:hover {{ color: var(--accent2); }}
thead th::after {{ content: ' ⇅'; font-size: 10px; opacity: 0.4; }}
tbody td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
tbody tr {{ transition: background 0.15s; }}
tbody tr:hover {{ background: var(--surface2) !important; }}

.sev-badge {{ display: inline-block; padding: 3px 10px; border-radius: 6px; color: white; font-size: 11px; font-weight: 700; white-space: nowrap; letter-spacing: 0.3px; }}
code {{ background: var(--surface2); border: 1px solid var(--border); padding: 2px 7px; border-radius: 5px; font-size: 12px; font-family: 'JetBrains Mono', 'Fira Code', monospace; }}
.msg-cell {{ max-width: 420px; line-height: 1.5; }}
.loc-cell {{ white-space: nowrap; font-size: 12px; color: var(--text3); }}
.tool-cell {{ color: var(--text2); }}
.fix-cell {{ max-width: 320px; color: #34d399; font-size: 12px; line-height: 1.5; }}

/* Footer */
.ftr {{ text-align: center; padding: 32px 0 16px; color: var(--text3); font-size: 13px; }}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <h1>&#128269; Аудит кода</h1>
  <div class="meta">
    <span>&#128193; {_escape(m.target)}</span>
    <span>&#128197; {m.timestamp[:10]}</span>
    <span>&#9881; {', '.join(m.tools_used)}</span>
  </div>
</div>

<div class="stats">
  <div class="stat-card" style="border-left:3px solid var(--accent)">
    <div class="stat-num" style="color:var(--accent)">{s.total_findings}</div>
    <div class="stat-label">Всего</div>
  </div>
  {severity_cards}
</div>

<div class="cols">
  <div class="sec">
    <div class="sec-hdr">По категориям</div>
    <div class="sec-body"><table class="stbl">{category_rows}</table></div>
  </div>
  <div class="sec">
    <div class="sec-hdr">OWASP Top 10</div>
    <div class="sec-body"><table class="stbl">{owasp_rows if owasp_rows else '<tr><td style="color:var(--text3)">Нет OWASP-находок</td></tr>'}</table></div>
  </div>
</div>

<div class="sec">
  <div class="sec-hdr">
    <span>Находки</span>
    <span class="badge" id="vcnt">{s.total_findings}</span>
  </div>
  <div class="sec-body">
    <div class="filters">
      <select id="fs" onchange="ft()">
        <option value="">Все серьёзности</option>
        <option value="critical">Критический</option>
        <option value="high">Высокий</option>
        <option value="medium">Средний</option>
        <option value="low">Низкий</option>
        <option value="info">Инфо</option>
      </select>
      <select id="ftl" onchange="ft()">
        <option value="">Все инструменты</option>
        {tool_options}
      </select>
      <select id="fc" onchange="ft()">
        <option value="">Все категории</option>
        {"".join(f'<option value="{c}">{CATEGORY_RU.get(c,c)}</option>' for c in sorted(s.by_category.keys()))}
      </select>
      <input type="text" id="fss" placeholder="Поиск по сообщению..." oninput="ft()">
    </div>
    <div class="tbl-wrap">
      <table id="tbl">
        <thead><tr>
          <th onclick="st(0)">Серьёзность</th>
          <th onclick="st(1)">Правило</th>
          <th onclick="st(2)">Инструмент</th>
          <th onclick="st(3)">Категория</th>
          <th onclick="st(4)">OWASP</th>
          <th onclick="st(5)">Описание</th>
          <th onclick="st(6)">Расположение</th>
          <th onclick="st(7)">Исправление</th>
        </tr></thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </div>
  </div>
</div>

<div class="ftr">Code Auditor v{m.tool_version} &middot; {m.timestamp[:10]}</div>
</div>

<script>
function ft(){{
  const s=document.getElementById('fs').value,
        t=document.getElementById('ftl').value,
        c=document.getElementById('fc').value,
        q=document.getElementById('fss').value.toLowerCase();
  let n=0;
  document.querySelectorAll('#tbl tbody tr').forEach(r=>{{
    const ok=(!s||r.dataset.severity===s)&&(!t||r.dataset.tool===t)&&(!c||r.dataset.category===c)&&(!q||r.textContent.toLowerCase().includes(q));
    r.style.display=ok?'':'none';
    if(ok)n++;
  }});
  document.getElementById('vcnt').textContent=n;
}}
let sd={{}};
function st(c){{
  const tb=document.querySelector('#tbl tbody'),
        rs=Array.from(tb.querySelectorAll('tr'));
  sd[c]=!sd[c];
  rs.sort((a,b)=>{{
    const x=a.cells[c].textContent.trim(),y=b.cells[c].textContent.trim();
    return sd[c]?x.localeCompare(y,'ru'):y.localeCompare(x,'ru');
  }});
  rs.forEach(r=>tb.appendChild(r));
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
