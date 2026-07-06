"""Aggregate workload dependency predicates into structural classifications.

Current implementation contract:
- NULL: all workloads evaluate as dependency.
- DEGRADED: some workloads evaluate as dependency.
- VALID: no workloads evaluate as dependency.

Richer degradation metrics and workload-relative degradation semantics remain
future work; this module preserves the current compact aggregation contract.
"""

from __future__ import annotations

from typing import Any


def classify(dependencies: list[dict[str, Any]]) -> str:
    """Aggregate per-workload dependency predicates."""

    if all(item["dependency"] for item in dependencies):
        return "NULL"
    if any(item["dependency"] for item in dependencies):
        return "DEGRADED"
    return "VALID"
