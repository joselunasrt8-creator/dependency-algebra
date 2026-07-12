"""Canonical conformance evidence validation."""

from __future__ import annotations

from typing import Any

from conformance.status import TERMINAL_STATUSES

EVIDENCE_SCHEMA_VERSION = "structural-analysis-foundations.conformance-evidence.v1"
REQUIRED_FIELDS = (
    "schema_version",
    "adapter_id",
    "implementation",
    "implementation_version",
    "research_object_id",
    "fixture_id",
    "semantic_result",
    "canonical_outputs",
    "provenance",
    "diagnostics",
)


def validate_evidence(document: dict[str, Any], *, fixture_id: str, research_object_id: str, adapter_id: str) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for field in REQUIRED_FIELDS:
        if field not in document:
            errors.append(_error(field, "missing required field"))
    if errors:
        return errors
    if document["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        errors.append(_error("schema_version", "unsupported evidence schema version"))
    if document["fixture_id"] != fixture_id:
        errors.append(_error("fixture_id", "evidence fixture does not match executed fixture"))
    if document["research_object_id"] != research_object_id:
        errors.append(_error("research_object_id", "evidence research object does not match fixture"))
    if document["adapter_id"] != adapter_id:
        errors.append(_error("adapter_id", "evidence adapter does not match invoked adapter"))
    if document.get("semantic_result") not in TERMINAL_STATUSES:
        errors.append(_error("semantic_result", "unsupported conformance status"))
    if not isinstance(document.get("diagnostics"), list):
        errors.append(_error("diagnostics", "diagnostics must be an array"))
    if not isinstance(document.get("provenance"), dict):
        errors.append(_error("provenance", "provenance must be an object"))
    return errors


def _error(path: str, message: str) -> dict[str, str]:
    return {"path": path, "message": message}
