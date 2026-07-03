"""Analyzer registry — discovers and manages analyzer instances."""

from __future__ import annotations

from code_auditor.analyzers.base import Analyzer


_registry: dict[str, Analyzer] = {}


def register(analyzer: Analyzer) -> None:
    _registry[analyzer.name] = analyzer


def get(name: str) -> Analyzer | None:
    return _registry.get(name)


def all_analyzers() -> dict[str, Analyzer]:
    return dict(_registry)


def list_names() -> list[str]:
    return list(_registry.keys())


def _auto_register() -> None:
    from code_auditor.analyzers.bandit_analyzer import BanditAnalyzer
    from code_auditor.analyzers.pip_audit_analyzer import PipAuditAnalyzer
    from code_auditor.analyzers.pylint_analyzer import PylintAnalyzer
    from code_auditor.analyzers.radon_analyzer import RadonAnalyzer
    from code_auditor.analyzers.semgrep_analyzer import SemgrepAnalyzer
    from code_auditor.analyzers.vulture_analyzer import VultureAnalyzer

    for a in [
        BanditAnalyzer(),
        RadonAnalyzer(),
        VultureAnalyzer(),
        PylintAnalyzer(),
        SemgrepAnalyzer(),
        PipAuditAnalyzer(),
    ]:
        register(a)


_auto_register()
