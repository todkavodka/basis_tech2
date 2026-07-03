"""JSON report generator."""

from __future__ import annotations

import json
from pathlib import Path

from code_auditor.models import Report


def write_json(report: Report, output: Path | str) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
