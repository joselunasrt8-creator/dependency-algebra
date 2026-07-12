"""Canonical semantic comparison for normalized conformance evidence."""

from __future__ import annotations

from typing import Any

from conformance.jsonutil import canonical_json_text

SEMANTIC_KEYS = ("canonical_outputs", "structural_invariants", "required_diagnostics")


def normalize_evidence(document: dict[str, Any]) -> dict[str, Any]:
    return {key: document.get(key) for key in SEMANTIC_KEYS if key in document}


def compare(expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    expected_normalized = normalize_evidence(expected)
    observed_normalized = normalize_evidence(observed)
    mismatches = []
    for key in sorted(set(expected_normalized) | set(observed_normalized)):
        expected_value = expected_normalized.get(key, "__MISSING__")
        observed_value = observed_normalized.get(key, "__MISSING__")
        if canonical_json_text(expected_value) != canonical_json_text(observed_value):
            mismatches.append({"path": key, "expected": expected_value, "observed": observed_value})
    return not mismatches, mismatches
