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


def _try_load(root: Path) -> dict[str, Any]:
    """Try to load config from a single directory."""
    # 1. .code-auditor.toml
    toml_path = root / ".code-auditor.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            return tomllib.load(f)

    # 2. pyproject.toml [tool.code-auditor]
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, "rb") as f:
            full = tomllib.load(f)
        data = full.get("tool", {}).get("code-auditor", {})
        if data:
            return data

    return {}


def load_config(project_root: Path | None = None) -> Config:
    """Load configuration from .code-auditor.toml or pyproject.toml.

    Search order:
      1. project_root (target directory being scanned)
      2. current working directory
      3. defaults
    """
    cwd = Path.cwd()
    root = project_root or cwd

    # Load from target dir first, then overlay from cwd
    data: dict[str, Any] = {}
    if root != cwd:
        data = _try_load(root)
    cwd_data = _try_load(cwd)

    # CWD config takes priority over target dir config
    merged = {**data, **cwd_data}
    # Deep merge LLM section if both exist
    if "llm" in data and "llm" in cwd_data:
        merged["llm"] = {**data["llm"], **cwd_data["llm"]}

    return Config(**merged) if merged else Config()
