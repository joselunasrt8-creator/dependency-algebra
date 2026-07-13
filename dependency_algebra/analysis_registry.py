"""Deterministic core analysis-pass registration."""

from __future__ import annotations

from dataclasses import dataclass

from dependency_algebra.analysis import (
    CORE_ANALYSIS_ID,
    DEPENDENCY_ANALYSIS_ID,
    AnalysisPass,
    CoreStructuralAnalysisPass,
    DependencyAnalysisPass,
)


class AnalysisRegistryError(ValueError):
    """Base error for deterministic analysis registry failures."""


class DuplicateAnalysisRegistrationError(AnalysisRegistryError):
    """Raised when a pass is registered more than once for the same analysis ID."""


class UnknownAnalysisPassError(AnalysisRegistryError):
    """Raised when lookup requests an unregistered analysis ID."""


@dataclass(frozen=True, slots=True)
class AnalysisRegistry:
    """Immutable deterministic registry for explicitly provided analysis passes."""

    _passes: tuple[AnalysisPass, ...]

    def __init__(self, passes: tuple[AnalysisPass, ...] | list[AnalysisPass]):
        by_id: dict[str, AnalysisPass] = {}
        for analysis_pass in passes:
            analysis_id = analysis_pass.analysis_id
            if analysis_id in by_id:
                raise DuplicateAnalysisRegistrationError(f"duplicate analysis registration: {analysis_id}")
            by_id[analysis_id] = analysis_pass
        object.__setattr__(self, "_passes", tuple(by_id[analysis_id] for analysis_id in sorted(by_id)))

    def analysis_ids(self) -> tuple[str, ...]:
        """Return registered analysis IDs in deterministic order."""

        return tuple(analysis_pass.analysis_id for analysis_pass in self._passes)

    def passes(self) -> tuple[AnalysisPass, ...]:
        """Return registered passes in deterministic order."""

        return self._passes

    def get(self, analysis_id: str) -> AnalysisPass:
        """Return a registered pass by explicit ID, failing closed for unknown IDs."""

        for analysis_pass in self._passes:
            if analysis_pass.analysis_id == analysis_id:
                return analysis_pass
        raise UnknownAnalysisPassError(f"unknown analysis id: {analysis_id}")


def core_analysis_registry() -> AnalysisRegistry:
    """Create the repository-defined deterministic core analysis registry."""

    return AnalysisRegistry((DependencyAnalysisPass(),))


__all__ = [
    "AnalysisRegistry",
    "AnalysisRegistryError",
    "DuplicateAnalysisRegistrationError",
    "UnknownAnalysisPassError",
    "CORE_ANALYSIS_ID",
    "DEPENDENCY_ANALYSIS_ID",
    "core_analysis_registry",
]
