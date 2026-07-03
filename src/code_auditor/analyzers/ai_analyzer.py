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
from code_auditor.llm.provider import chat_completion
from code_auditor.models import Category, Finding, Severity

# Max bytes per file to send to LLM
MAX_FILE_BYTES = 30_000
# Max files to include in a single prompt
MAX_FILES = 15


def _collect_python_files(path: Path) -> list[Path]:
    return sorted(
        p
        for p in path.rglob("*.py")
        if p.is_file()
        and "__pycache__" not in str(p)
        and ".venv" not in str(p)
        and "node_modules" not in str(p)
    )


def _read_chunks(files: list[Path]) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    for f in files[:MAX_FILES]:
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
            rel = p.relative_to(path)
            lines.append(str(rel))
    return "\n".join(lines[:100])


def _parse_llm_json(text: str) -> list[dict]:
    text = text.strip()
    # Extract JSON array from markdown fences if present
    if "```" in text:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []


class AIAnalyzer:
    name = "ai"

    def __init__(self, model: str = "openai/gpt-4o") -> None:
        self.model = model

    def analyze(self, path: Path) -> list[Finding]:
        files = _collect_python_files(path)
        if not files:
            return []

        chunks = _read_chunks(files)
        findings: list[Finding] = []

        # Security analysis
        try:
            prompt = build_security_prompt(chunks)
            response = chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": SECURITY_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            for item in _parse_llm_json(response):
                sev_str = item.get("severity", "medium")
                findings.append(
                    Finding(
                        tool="ai-security",
                        rule_id=item.get("rule_id", "AI-SEC"),
                        severity=Severity(sev_str) if sev_str in Severity.__members__.values() else Severity.MEDIUM,
                        category=Category.SECURITY,
                        owasp_mapping=item.get("owasp", "N/A"),
                        file=item.get("file"),
                        line=item.get("line"),
                        message=item.get("message", ""),
                        fix_suggestion=item.get("fix_suggestion", ""),
                    )
                )
        except Exception:
            pass  # LLM failure is non-fatal

        # Architecture analysis
        try:
            file_tree = _make_file_tree(path)
            prompt = build_architecture_prompt(file_tree, chunks)
            response = chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": ARCHITECTURE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            for item in _parse_llm_json(response):
                sev_str = item.get("severity", "medium")
                findings.append(
                    Finding(
                        tool="ai-architecture",
                        rule_id=item.get("rule_id", "AI-ARCH"),
                        severity=Severity(sev_str) if sev_str in Severity.__members__.values() else Severity.MEDIUM,
                        category=Category.ARCHITECTURE,
                        owasp_mapping="N/A",
                        file=item.get("file"),
                        line=item.get("line"),
                        message=item.get("message", ""),
                        fix_suggestion=item.get("fix_suggestion", ""),
                    )
                )
        except Exception:
            pass

        return findings
