"""Deterministic reachability traversal for normalized Dependency Algebra IR.

This module owns graph traversal only: deque-based breadth-first visitation,
lexical ordering between traversal levels, and reachability result assembly. It
makes no dependency-predicate decisions and performs no workload aggregation.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from dependency_algebra.serialization import sha256_digest


def reachability(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Return deterministic reachability results for every workload in IR."""

    results = []
    for workload in ir["workloads"]:
        visited, traversed = traverse(ir["adjacency"], workload["roots"], max_depth)
        reached_by = [
            root
            for root in workload["roots"]
            if workload["target"] in traverse(ir["adjacency"], [root], max_depth)[0]
        ]
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
    doc = {
        "schema_version": "dependency-algebra.reachability.v1",
        "topology_id": ir["topology_id"],
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "results": results,
    }
    # Hash boundary: canonical reachability result payload for all workloads,
    # excluding reachability_result_hash because it is added only after hashing.
    doc["reachability_result_hash"] = sha256_digest(doc)
    return doc


def traverse(
    adjacency: dict[str, list[dict[str, str]]],
    roots: list[str],
    max_depth: int | None,
) -> tuple[set[str], list[dict[str, str]]]:
    """Visit reachable nodes with deterministic deque-based BFS ordering."""

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
