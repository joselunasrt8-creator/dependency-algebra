"""Analysis engine for normalized Dependency Algebra IR.

Current architecture note:
    This module intentionally still contains orchestration plus the compact
    implementations of reachability traversal, complement projection for the
    dependency predicate, predicate evaluation, and workload aggregation. The
    desired long-term decomposition is frontend.py for parsing/validation/
    normalization, projection.py for complement projection, reachability.py for
    traversal, predicate.py for dependency semantics, classification.py for
    workload aggregation, and engine.py for orchestration only. That module split
    is intentionally deferred to repository Issue #60 so this hardening pass can
    preserve public APIs, schemas, hashes, fixtures, and externally observable
    behavior.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from dependency_algebra.serialization import sha256_digest


def analyze(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Analyze normalized IR and return deterministic dependency results."""

    reachability = _reachability(ir, max_depth=max_depth)
    dependencies = [_dependency_result(ir, workload, max_depth=max_depth) for workload in ir["workloads"]]
    classification = _classification(dependencies)
    result = {
        "schema_version": "dependency-algebra.analysis.v1",
        "topology_id": ir["topology_id"],
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "classification": classification,
        "reachability": reachability,
        "dependencies": dependencies,
    }
    # Hash boundary: canonical analysis result payload as currently emitted,
    # excluding dependency_result_hash because it is added only after hashing.
    result["dependency_result_hash"] = sha256_digest(result)
    return result


def _reachability(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    results = []
    for workload in ir["workloads"]:
        visited, traversed = _traverse(ir["adjacency"], workload["roots"], max_depth)
        reached_by = [root for root in workload["roots"] if workload["target"] in _traverse(ir["adjacency"], [root], max_depth)[0]]
        results.append({
            "workload_id": workload["id"],
            "roots": workload["roots"],
            "target": workload["target"],
            "reachable": bool(reached_by),
            "reached_by": sorted(reached_by),
            "visited_nodes": sorted(visited),
            "traversal_edges": sorted(traversed, key=lambda e: (e["edge_id"], e["from"], e["to"])),
            "diagnostics": [],
        })
    doc = {"schema_version": "dependency-algebra.reachability.v1", "topology_id": ir["topology_id"], "normalized_ir_hash": ir["normalized_ir_hash"], "results": results}
    # Hash boundary: canonical reachability result payload for all workloads,
    # excluding reachability_result_hash because it is added only after hashing.
    doc["reachability_result_hash"] = sha256_digest(doc)
    return doc


def _dependency_result(ir: dict[str, Any], workload: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    candidates = set(workload["candidate_set"])
    adjacency = {
        component["id"]: [edge for edge in ir["adjacency"][component["id"]] if edge["component_id"] not in candidates]
        for component in ir["components"]
        if component["id"] not in candidates
    }
    roots = [root for root in workload["roots"] if root not in candidates]
    visited, _ = _traverse(adjacency, roots, max_depth)
    reachable_after = workload["target"] in visited if workload["target"] not in candidates else False
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


def _traverse(adjacency: dict[str, list[dict[str, str]]], roots: list[str], max_depth: int | None) -> tuple[set[str], list[dict[str, str]]]:
    visited: set[str] = set()
    traversed: list[dict[str, str]] = []
    queue = deque((root, 0) for root in sorted(roots) if root in adjacency)
    next_level: list[tuple[str, int]] = []
    while queue:
        node, depth = queue.popleft()
        if node in visited:
            if not queue and next_level:
                queue.extend(sorted(next_level, key=lambda item: item[0]))
                next_level.clear()
            continue
        visited.add(node)
        if max_depth is not None and depth >= max_depth:
            if not queue and next_level:
                queue.extend(sorted(next_level, key=lambda item: item[0]))
                next_level.clear()
            continue
        for edge in adjacency.get(node, []):
            traversed.append({"edge_id": edge["edge_id"], "from": node, "to": edge["component_id"]})
            if edge["component_id"] not in visited:
                next_level.append((edge["component_id"], depth + 1))
        if not queue and next_level:
            queue.extend(sorted(next_level, key=lambda item: item[0]))
            next_level.clear()
    return visited, traversed


def _classification(dependencies: list[dict[str, Any]]) -> str:
    """Aggregate workload predicates with the current simplified contract.

    Current implementation contract:
    - NULL: all workloads evaluate as dependency.
    - DEGRADED: at least one workload evaluates as dependency, but not all.
    - VALID: no workload evaluates as dependency.

    Richer degradation metrics and workload-relative degradation semantics are
    deterministic future work and intentionally deferred; this simplified
    aggregation is deterministic and expected for the current compiler.
    """

    if all(item["dependency"] for item in dependencies):
        return "NULL"
    if any(item["dependency"] for item in dependencies):
        return "DEGRADED"
    return "VALID"
