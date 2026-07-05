"""Structured compiler diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dependency_algebra.serialization import canonical_json_text

DIAGNOSTIC_SCHEMA_VERSION = "dependency-algebra.diagnostic.v1"


@dataclass(frozen=True)
class CompilerDiagnosticException(Exception):
    """Raised when deterministic compiler diagnostics should be emitted."""

    diagnostic: dict[str, Any]

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return canonical_json_text(self.diagnostic)


def diagnostic_document(diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": DIAGNOSTIC_SCHEMA_VERSION, "diagnostics": sorted(diagnostics, key=diagnostic_sort_key)}


def diagnostic_sort_key(diagnostic: dict[str, Any]) -> tuple[Any, ...]:
    source = diagnostic.get("source", {})
    subject = diagnostic["subject"]
    return (
        diagnostic["code"],
        subject["kind"],
        subject["id"],
        source.get("source_id", ""),
        source.get("source_order", 10**12),
    )


def make_diagnostic(code: str, phase: str, message: str, kind: str, subject_id: str, source_id: str, source_order: int | None = None, line: int | None = None, column: int | None = None) -> dict[str, Any]:
    source: dict[str, Any] = {"source_id": source_id}
    if source_order is not None:
        source["source_order"] = source_order
    if line is not None:
        source["line"] = line
    if column is not None:
        source["column"] = column
    return {
        "code": code,
        "phase": phase,
        "severity": "error",
        "message": message,
        "subject": {"kind": kind, "id": subject_id},
        "source": source,
    }
