"""Configuration loader for code-auditor.

Searches for config in this order:
  1. .code-auditor.toml in project root
  2. [tool.code-auditor] section in pyproject.toml
  3. Defaults
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    model: str = "openai/gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 4096
    api_key: str = ""
    api_base: str = ""


class AnalyzersConfig(BaseModel):
    skip: list[str] = Field(default_factory=list)
    bandit: dict[str, Any] = Field(default_factory=dict)
    radon: dict[str, Any] = Field(default_factory=dict)
    pylint: dict[str, Any] = Field(default_factory=dict)
    semgrep: dict[str, Any] = Field(default_factory=dict)


class ReportConfig(BaseModel):
    format: str = "markdown"
    severity_threshold: str = "info"
    max_file_size_kb: int = 500


class Config(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    analyzers: AnalyzersConfig = Field(default_factory=AnalyzersConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(project_root: Path | None = None) -> Config:
    """Load configuration from .code-auditor.toml or pyproject.toml."""
    root = project_root or Path.cwd()
    data: dict[str, Any] = {}

    # 1. Try .code-auditor.toml
    toml_path = root / ".code-auditor.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)

    # 2. Try pyproject.toml [tool.code-auditor]
    pyproject = root / "pyproject.toml"
    if pyproject.exists() and not data:
        with open(pyproject, "rb") as f:
            full = tomllib.load(f)
        data = full.get("tool", {}).get("code-auditor", {})

    return Config(**data) if data else Config()
