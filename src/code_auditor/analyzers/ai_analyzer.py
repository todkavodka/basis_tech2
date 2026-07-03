"""AI-powered deep code analysis via LLM."""

from __future__ import annotations

import json
from pathlib import Path

from code_auditor.llm.prompts import (
    ARCHITECTURE_SYSTEM,
    SECURITY_SYSTEM,
    build_architecture_prompt,
    build_security_prompt,
)
from code_auditor.config import LLMConfig, load_config
from code_auditor.llm.provider import chat_completion
from code_auditor.models import Category, Finding, Severity

MAX_FILE_BYTES = 20_000
MAX_FILES = 10

CODE_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".php"}
CONFIG_EXTENSIONS = {".toml", ".yaml", ".yml", ".cfg", ".ini"}
SKIP_DIRS = {"__pycache__", ".venv", "node_modules", ".git", "dist", "build", ".tox", ".eggs"}


def _collect_files(path: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        if any(skip in p.parts for skip in SKIP_DIRS):
            continue
        ext = p.suffix.lower()
        if ext in CODE_EXTENSIONS or ext in CONFIG_EXTENSIONS:
            files.append(p)
    return files[:MAX_FILES]


def _read_chunks(files: list[Path]) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    for f in files:
        try:
            content = f.read_text(errors="replace")[:MAX_FILE_BYTES]
            chunks.append((str(f), content))
        except OSError:
            continue
    return chunks


def _make_file_tree(path: Path) -> str:
    lines: list[str] = []
    for p in sorted(path.rglob("*")):
        if p.is_file() and "__pycache__" not in str(p) and ".venv" not in str(p):
            lines.append(str(p.relative_to(path)))
    return "\n".join(lines[:100])


def _parse_llm_json(text: str) -> list[dict]:
    text = text.strip()
    # Remove markdown code fences
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    text = "\n".join(lines).strip()

    # Find JSON array bounds
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end > start:
        text = text[start : end + 1]
    elif start != -1:
        # Truncated - try to close it
        last_brace = text.rfind("}")
        if last_brace > start:
            text = text[start : last_brace + 1] + "]"

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []


class AIAnalyzer:
    name = "ai"

    def __init__(self, model: str = "", config: LLMConfig | None = None) -> None:
        self.model = model
        self.config = config or load_config().llm

    def analyze(self, path: Path) -> list[Finding]:
        files = _collect_files(path)
        if not files:
            return []

        chunks = _read_chunks(files)
        findings: list[Finding] = []
        model = self.model or self.config.model

        # Security analysis
        try:
            prompt = build_security_prompt(chunks)
            response = chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": SECURITY_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                config=self.config,
            )
            for item in _parse_llm_json(response):
                sev_str = item.get("severity", "medium")
                findings.append(Finding(
                    tool="ai-security",
                    rule_id=item.get("rule_id", "AI-SEC"),
                    severity=Severity(sev_str) if sev_str in Severity.__members__.values() else Severity.MEDIUM,
                    category=Category.SECURITY,
                    owasp_mapping=item.get("owasp", "N/A"),
                    file=item.get("file"),
                    line=item.get("line"),
                    message=item.get("message", ""),
                    fix_suggestion=item.get("fix_suggestion", ""),
                ))
        except Exception:
            pass

        # Architecture analysis
        try:
            file_tree = _make_file_tree(path)
            prompt = build_architecture_prompt(file_tree, chunks)
            response = chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": ARCHITECTURE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                config=self.config,
            )
            for item in _parse_llm_json(response):
                sev_str = item.get("severity", "medium")
                findings.append(Finding(
                    tool="ai-architecture",
                    rule_id=item.get("rule_id", "AI-ARCH"),
                    severity=Severity(sev_str) if sev_str in Severity.__members__.values() else Severity.MEDIUM,
                    category=Category.ARCHITECTURE,
                    owasp_mapping="N/A",
                    file=item.get("file"),
                    line=item.get("line"),
                    message=item.get("message", ""),
                    fix_suggestion=item.get("fix_suggestion", ""),
                ))
        except Exception:
            pass

        return findings
