"""Analysis orchestration for normalized Dependency Algebra IR.

The engine coordinates the dedicated analysis modules without owning graph
algorithms or dependency semantics: reachability.py performs deterministic
traversal, projection.py performs complement projection, predicate.py evaluates
one workload dependency predicate, and classification.py aggregates workload
results. Public compiler behavior, schemas, and hash boundaries are assembled
here unchanged.
"""

from __future__ import annotations

from typing import Any

from dependency_algebra.classification import classify
from dependency_algebra.predicate import dependency_result
from dependency_algebra.reachability import reachability
from dependency_algebra.serialization import sha256_digest


def analyze(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Analyze normalized IR and return deterministic dependency results."""

    reachability_result = reachability(ir, max_depth=max_depth)
    dependencies = [dependency_result(ir, workload, max_depth=max_depth) for workload in ir["workloads"]]
    classification = classify(dependencies)
    result = {
        "schema_version": "dependency-algebra.analysis.v1",
        "topology_id": ir["topology_id"],
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "classification": classification,
        "reachability": reachability_result,
        "dependencies": dependencies,
    }
    # Hash boundary: canonical analysis result payload as currently emitted,
    # excluding dependency_result_hash because it is added only after hashing.
    result["dependency_result_hash"] = sha256_digest(result)
    return result
