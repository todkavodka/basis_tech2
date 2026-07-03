# Code Auditor

AI-powered code auditor: security, quality, and architecture analysis in one CLI tool.

Combines 6 static analyzers (bandit, radon, vulture, pylint, semgrep, pip-audit) with LLM-based deep analysis to find vulnerabilities, code smells, and architectural issues — outputting structured JSON/Markdown reports with OWASP Top 10 mapping.

## Features

- **Security Audit** — SQL injection, XSS, hardcoded secrets, weak crypto, path traversal, SSRF, insecure deserialization (OWASP Top 10)
- **Code Quality** — Cyclomatic complexity, maintainability index, God objects, SOLID violations, dead code, duplication
- **Dependency Scanning** — Known CVEs via pip-audit
- **AI Deep Analysis** — LLM-powered review for architectural issues and subtle vulnerabilities
- **Multi-provider LLM** — OpenAI, Anthropic Claude, local Ollama via LiteLLM
- **Structured Reports** — JSON and Markdown with severity breakdown and OWASP mapping
- **Plugin Architecture** — Add custom analyzers by implementing the `Analyzer` protocol

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/todkavodka/basis_tech2.git
cd basis_tech2

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with all analyzer dependencies
pip install -e ".[analyzers]"

# Install dev dependencies (optional, for running tests)
pip install -e ".[dev]"
```

### Verify Installation

```bash
code-auditor --help
code-auditor list-analyzers
```

## Usage

### Basic Scan

```bash
# Scan a project (all analyzers, no AI)
code-auditor scan ./my-project --no-ai

# Full scan with AI analysis
code-auditor scan ./my-project
```

### Options

```
code-auditor scan <path> [OPTIONS]

Arguments:
  PATH                          Path to project directory

Options:
  -a, --analyzer TEXT           Analyzers to run. Repeatable.
                                [bandit|radon|vulture|pylint|semgrep|pip-audit|ai|all]
                                Default: all
  -o, --output TEXT             Output file path (.json or .md)
  -f, --format TEXT             Report format: json, markdown, both [default: markdown]
  -s, --severity TEXT           Minimum severity: critical, high, medium, low, info
                                [default: info]
  -m, --model TEXT              LLM model for AI analysis
                                [default: openai/gpt-4o]
  --no-ai                       Skip AI-powered analysis (offline mode)
  -v, --verbose                 Verbose output
  --help                        Show this message and exit
```

### Examples

```bash
# Run only security analyzers
code-auditor scan ./src -a bandit -a semgrep --no-ai

# Full scan, save both JSON and Markdown reports
code-auditor scan ./src -o audit-report -f both

# Filter: show only high and critical findings
code-auditor scan ./src -s high --no-ai

# Use Claude instead of GPT-4o for AI analysis
code-auditor scan ./src -m anthropic/claude-sonnet-4-20250514

# Use local Ollama (no API key needed)
code-auditor scan ./src -m ollama/llama3

# Verbose mode — shows which analyzer is running and progress
code-auditor scan ./src -v --no-ai
```

## AI Analysis Setup

AI analysis requires an API key for your chosen provider.

### OpenAI (default)

```bash
export OPENAI_API_KEY=sk-your-key-here
code-auditor scan ./src
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
code-auditor scan ./src -m anthropic/claude-sonnet-4-20250514
```

### Ollama (local, free)

```bash
# 1. Install Ollama: https://ollama.com
# 2. Pull a model
ollama pull llama3

# 3. Run auditor (no API key needed)
code-auditor scan ./src -m ollama/llama3
```

### Offline Mode (no LLM)

```bash
code-auditor scan ./src --no-ai
```

## Configuration

Code Auditor reads configuration from `.code-auditor.toml` or `[tool.code-auditor]` in `pyproject.toml`.

### Quick Setup

```bash
# Copy the example config to your project root
cp .code-auditor.example.toml .code-auditor.toml
```

### Config File (`.code-auditor.toml`)

```toml
[llm]
# Supported: openai/gpt-4o, openai/o3-mini, anthropic/claude-sonnet-4-20250514,
#            ollama/llama3, deepseek/deepseek-chat, groq/llama-3.1-70b-versatile
model = "openai/gpt-4o"
temperature = 0.1       # 0.0 = deterministic, 1.0 = creative
max_tokens = 4096       # Max tokens per LLM response
# api_key = "sk-..."    # Overrides OPENAI_API_KEY env var
# api_base = "http://localhost:11434"  # For Ollama, proxies, etc.

[analyzers]
# Skip specific analyzers
skip = ["vulture", "pip-audit"]

[report]
format = "markdown"     # json, markdown, or both
severity_threshold = "info"  # critical, high, medium, low, info
max_file_size_kb = 500  # Max file size to send to LLM
```

### Config via `pyproject.toml`

```toml
[tool.code-auditor.llm]
model = "anthropic/claude-sonnet-4-20250514"
temperature = 0.0

[tool.code-auditor.analyzers]
skip = ["semgrep"]

[tool.code-auditor.report]
format = "both"
severity_threshold = "medium"
```

### Ready-to-Use Configs

#### DeepSeek (замените только ключ)

```toml
# .code-auditor.toml
[llm]
model = "deepseek/deepseek-chat"
api_key = "sk-ваш-ключ-здесь"
temperature = 0.1
max_tokens = 4096
```

#### OpenAI

```toml
[llm]
model = "openai/gpt-4o"
api_key = "sk-ваш-ключ-здесь"
```

#### Anthropic Claude

```toml
[llm]
model = "anthropic/claude-sonnet-4-20250514"
api_key = "sk-ant-ваш-ключ-здесь"
```

#### Groq (быстрый, бесплатный тир)

```toml
[llm]
model = "groq/llama-3.1-70b-versatile"
api_key = "gsk_ваш-ключ-здесь"
```

#### Ollama (локальный, без ключа)

```toml
[llm]
model = "ollama/llama3"
api_base = "http://localhost:11434"
```

### Config Priority

1. CLI arguments (highest priority)
2. `.code-auditor.toml` in project root
3. `[tool.code-auditor]` in `pyproject.toml`
4. Defaults

### Supported LLM Providers

| Provider | Model String | API Key Env Var |
|----------|-------------|-----------------|
| OpenAI | `openai/gpt-4o`, `openai/o3-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| Groq | `groq/llama-3.1-70b-versatile` | `GROQ_API_KEY` |
| Ollama (local) | `ollama/llama3`, `ollama/codellama` | (none needed) |

### Custom API Base (Ollama, Proxies)

```toml
[llm]
model = "ollama/llama3"
api_base = "http://localhost:11434"
```

Or via environment:

```bash
export OLLAMA_API_BASE=http://localhost:11434
code-auditor scan ./src -m ollama/llama3
```

## Analyzers

| Analyzer | Type | What it finds |
|----------|------|---------------|
| **bandit** | Security | SQL injection, XSS, hardcoded secrets, weak crypto, command injection |
| **radon** | Complexity | Cyclomatic complexity, maintainability index, Halstead metrics |
| **vulture** | Dead code | Unused functions, classes, imports, variables |
| **pylint** | Quality | God objects (R0902/R0904), SOLID violations (R0901), duplication (R0801) |
| **semgrep** | Security | Taint analysis, pattern-based vulnerability detection |
| **pip-audit** | Dependencies | Known CVEs in Python packages |
| **ai** | Deep analysis | Architecture review, subtle vulnerabilities, design patterns |

### OWASP Top 10 Mapping

| OWASP | Category | Detected by |
|-------|----------|-------------|
| A02 | Cryptographic Failures | bandit (B3xx, B5xx) |
| A03 | Injection (SQL, XSS, CMD) | bandit (B6xx, B7xx), semgrep |
| A05 | Security Misconfiguration | bandit (B201, B612) |
| A06 | Vulnerable Components | pip-audit |
| A07 | Authentication Failures | bandit (B105-B107) |
| A08 | Integrity Failures | bandit (B301, B506) |
| A09 | Logging & Monitoring | bandit (B110, B112) |

## Report Formats

### Terminal Output

```
Code Auditor v0.1.0
Target: /home/user/my-project

   Audit Summary
┏━━━━━━━━━━┳━━━━━━━┓
┃ Severity ┃ Count ┃
┡━━━━━━━━━━╇━━━━━━━┩
│ High     │     3 │
│ Medium   │    12 │
│ Low      │    28 │
│ Info     │    15 │
└──────────┴───────┘

Total: 58 findings from 6 tools

Top findings:

  [    HIGH] bandit/B605 — Starting a process with a shell...
           at /home/user/my-project/app.py:42

  [  MEDIUM] bandit/B608 — Possible SQL injection...
           at /home/user/my-project/db.py:18
```

### JSON Report

```json
{
  "metadata": {
    "tool_version": "0.1.0",
    "target": "/home/user/my-project",
    "timestamp": "2026-07-03T12:00:00+00:00",
    "tools_used": ["bandit", "radon", "vulture", "pylint", "semgrep", "pip-audit"]
  },
  "summary": {
    "total_findings": 58,
    "by_severity": { "high": 3, "medium": 12, "low": 28, "info": 15 },
    "by_category": { "security": 8, "quality": 20, "complexity": 15, "dead_code": 12, "dependency": 3 },
    "by_owasp": { "A03": 5, "A02": 2, "A07": 1 }
  },
  "findings": [
    {
      "tool": "bandit",
      "rule_id": "B608",
      "severity": "medium",
      "category": "security",
      "owasp_mapping": "A03",
      "file": "db.py",
      "line": 18,
      "message": "Possible SQL injection vector through string-based query construction.",
      "fix_suggestion": "Use parameterized queries instead of string formatting."
    }
  ]
}
```

### Markdown Report

```markdown
# Code Audit Report

- **Target**: `/home/user/my-project`
- **Date**: 2026-07-03T12:00:00+00:00
- **Tools**: bandit, radon, vulture, pylint, semgrep, pip-audit

## Summary

**Total findings**: 58

### By Severity

| Severity | Count |
|----------|-------|
| High | 3 |
| Medium | 12 |
| Low | 28 |
| Info | 15 |

### OWASP Breakdown

| OWASP | Count |
|-------|-------|
| A03 | 5 |
| A02 | 2 |
| A07 | 1 |

## Findings

### [HIGH] `B605` — bandit

- **Location**: `app.py:42`
- **Category**: security
- **OWASP**: A03
- **Message**: Starting a process with a shell, possible injection detected.
- **Fix**: Use subprocess.run() with a list of arguments instead of shell=True.
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No critical or high severity findings |
| 1 | High severity findings detected |
| 2 | Critical severity findings detected |

Use in CI/CD to fail builds on security issues:

```bash
code-auditor scan ./src --no-ai -s high || exit 1
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[analyzers]"
      - run: code-auditor scan . --no-ai -o audit-report -f both
      - uses: actions/upload-artifact@v4
        with:
          name: audit-report
          path: audit-report.*
```

### GitLab CI

```yaml
code-audit:
  image: python:3.12
  script:
    - pip install -e ".[analyzers]"
    - code-auditor scan . --no-ai -o audit-report.json -f json
  artifacts:
    reports:
      artifact: audit-report.json
```

## Architecture

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (Typer)                             │
│                    cli.py → config.py                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │     Analyzer Registry   │
          │      registry.py        │
          └────────────┬────────────┘
                       │
    ┌──────────┬───────┼───────┬──────────┬──────────┐
    ▼          ▼       ▼       ▼          ▼          ▼
 bandit     radon   vulture  pylint    semgrep   pip-audit
 (security) (cc)    (dead)   (quality) (taint)   (deps)
    │          │       │       │          │          │
    └──────────┴───────┴───────┴──────────┴──────────┘
                       │
              Normalized Findings
              (Pydantic models)
                       │
          ┌────────────┴────────────┐
          │      Report Generators   │
          │  JSON │ Markdown │ HTML  │
          └─────────────────────────┘
```

**AI Analysis** runs in parallel with static analyzers, sending code chunks to LLM via LiteLLM:

```
┌──────────────┐      ┌──────────────────────────────────┐
│ AI Analyzer  │─────▶│ LiteLLM (multi-provider)          │
│ ai_analyzer  │      │  OpenAI / Claude / DeepSeek /     │
│              │◀─────│  Groq / Ollama                    │
└──────────────┘      └──────────────────────────────────┘
```

### Data Flow

1. **CLI** parses args, loads config from `.code-auditor.toml` or `pyproject.toml`
2. **Registry** iterates over selected analyzers (each is a plugin)
3. Each **Analyzer** runs its tool via `subprocess`, parses output, normalizes to `Finding` model
4. **AI Analyzer** collects Python files, sends to LLM with security/architecture prompts
5. All findings are merged, filtered by severity, and wrapped in a `Report`
6. **Report Generators** serialize to JSON/Markdown/HTML

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Plugin system | Protocol-based (`Analyzer`) | Zero coupling — add analyzers without touching core |
| Tool discovery | `find_tool()` checks venv bin, then PATH | Works in venvs without modifying PATH |
| Config cascade | CLI args > `.code-auditor.toml` > `pyproject.toml` > defaults | Flexibility without complexity |
| LLM abstraction | LiteLLM | One API, 100+ providers, no vendor lock-in |
| Data models | Pydantic v2 | Validation, serialization, structured output |
| Report formats | JSON + Markdown + HTML | Machine-readable + human-readable + interactive |

### Adding a New Analyzer

```python
# src/code_auditor/analyzers/my_analyzer.py
from pathlib import Path
from code_auditor.analyzers.base import Analyzer
from code_auditor.models import Finding, Category, Severity

class MyAnalyzer:
    name = "my-analyzer"

    def analyze(self, path: Path) -> list[Finding]:
        # Run your tool, parse output, return normalized findings
        return [Finding(
            tool=self.name,
            rule_id="MY-001",
            severity=Severity.MEDIUM,
            category=Category.QUALITY,
            file="example.py",
            line=10,
            message="Something found",
        )]
```

Register in `registry.py`:
```python
from code_auditor.analyzers.my_analyzer import MyAnalyzer
register(MyAnalyzer())
```

## Project Structure

```
code-auditor/
├── .code-auditor.example.toml         # Example configuration
├── pyproject.toml                     # Package config + dependencies
├── src/code_auditor/
│   ├── cli.py                         # Typer CLI: scan, list-analyzers
│   ├── config.py                      # Config loader (.toml / pyproject)
│   ├── models.py                      # Pydantic: Finding, Report, Summary
│   ├── registry.py                    # Analyzer plugin registry
│   ├── analyzers/
│   │   ├── base.py                    # Analyzer Protocol + find_tool()
│   │   ├── bandit_analyzer.py         # Security → OWASP mapping
│   │   ├── radon_analyzer.py          # CC, Maintainability Index
│   │   ├── vulture_analyzer.py        # Dead code (confidence-scored)
│   │   ├── pylint_analyzer.py         # SOLID, God objects, duplication
│   │   ├── semgrep_analyzer.py        # Taint/pattern analysis
│   │   ├── pip_audit_analyzer.py      # Dependency CVEs (OWASP A06)
│   │   └── ai_analyzer.py            # LLM deep analysis
│   ├── llm/
│   │   ├── provider.py               # LiteLLM wrapper (5 providers)
│   │   └── prompts.py                # Security + architecture prompts
│   └── reports/
│       ├── json_report.py            # JSON output
│       ├── markdown_report.py        # Markdown with tables
│       └── html_report.py            # Interactive HTML with filters
└── tests/
    ├── test_models.py                # Model serialization tests
    ├── test_analyzers.py             # Analyzer integration tests
    └── test_cli.py                   # CLI command tests
```

## Adding Custom Analyzers

Implement the `Analyzer` protocol:

```python
from pathlib import Path
from code_auditor.analyzers.base import Analyzer
from code_auditor.models import Finding, Category, Severity

class MyAnalyzer:
    name = "my-analyzer"

    def analyze(self, path: Path) -> list[Finding]:
        findings = []
        # Your analysis logic here
        findings.append(Finding(
            tool=self.name,
            rule_id="MY-001",
            severity=Severity.MEDIUM,
            category=Category.QUALITY,
            file="example.py",
            line=10,
            message="Something found",
        ))
        return findings
```

Register it in `registry.py`:

```python
from code_auditor.analyzers.my_analyzer import MyAnalyzer
register(MyAnalyzer())
```

## Development

```bash
# Install dev dependencies
pip install -e ".[analyzers,dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=code_auditor --cov-report=term-missing
```

## License

MIT
