"""Per-workload dependency predicate evaluation.

This module evaluates exactly one workload at a time. It combines structural
complement projection with projected reachability to determine dependency,
dependency_reason, reachable_after_projection, and predicate diagnostics. It
never aggregates multiple workloads.
"""

from __future__ import annotations

from typing import Any

from dependency_algebra.projection import complement_projection
from dependency_algebra.reachability import traverse
from dependency_algebra.serialization import sha256_digest


def dependency_result(ir: dict[str, Any], workload: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Evaluate the dependency predicate for one workload."""

    projection = complement_projection(ir, workload)
    visited, _ = traverse(projection["adjacency"], projection["roots"], max_depth)
    reachable_after = workload["target"] in visited if workload["target"] not in projection["removed"] else False
    result = {
        "schema_version": "dependency-algebra.dependency.v1",
        "workload_id": workload["id"],
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "roots": workload["roots"],
        "target": workload["target"],
        "candidate_set": workload["candidate_set"],
        # Current compact projection boundary: the normalized IR identity plus
        # the canonical removed component set. It contains no projected_ir_hash.
        "projected_ir_hash": sha256_digest({"normalized_ir_hash": ir["normalized_ir_hash"], "removed": workload["candidate_set"]}),
        # Current compact projected-reachability boundary: canonical visited
        # nodes and target after projection. It contains no derived hash field.
        "reachability_result_hash": sha256_digest({"visited_nodes": sorted(visited), "target": workload["target"]}),
        "dependency": not reachable_after,
        "dependency_reason": "no_structurally_valid_path_after_projection" if not reachable_after else "structurally_valid_path_remaining_after_projection",
        "reachable_after_projection": sorted(visited),
        "diagnostics": [],
    }
    # Hash boundary: canonical per-workload dependency result payload,
    # excluding dependency_result_hash because it is added only after hashing.
    result["dependency_result_hash"] = sha256_digest(result)
    return result
