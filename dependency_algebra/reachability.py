"""Deterministic reachability traversal for normalized Dependency Algebra IR."""

from __future__ import annotations

from collections import deque
from typing import Mapping

from dependency_algebra.ir import CanonicalIR, Edge, ReachabilityResult, TraversalEdge, WorkloadReachability


def evaluate(ir: CanonicalIR, max_depth: int | None = None) -> ReachabilityResult:
    """Return deterministic reachability results for every workload in IR."""

    results = []
    for workload in ir.workloads:
        visited, traversed = traverse_edges(ir.adjacency, workload.roots, max_depth)
        reached_by = tuple(
            root
            for root in workload.roots
            if workload.target in traverse_edges(ir.adjacency, (root,), max_depth)[0]
        )
        results.append(WorkloadReachability(
            workload_id=workload.id,
            roots=workload.roots,
            target=workload.target,
            reachable=bool(reached_by),
            reached_by=tuple(sorted(reached_by)),
            visited_nodes=tuple(sorted(visited)),
            traversal_edges=tuple(sorted(traversed, key=lambda e: (e.edge_id, e.source, e.target))),
        ))
    return ReachabilityResult(
        schema_version="dependency-algebra.reachability.v1",
        topology_id=ir.topology_id,
        normalized_ir_hash=ir.normalized_ir_hash,
        results=tuple(results),
    )


def reachability(ir, max_depth: int | None = None) -> dict:
    """Backward-compatible dict reachability wrapper."""

    canonical = ir if isinstance(ir, CanonicalIR) else CanonicalIR.from_dict(ir)
    from dependency_algebra.serialization import reachability_result_to_dict

    return reachability_result_to_dict(evaluate(canonical, max_depth=max_depth))


def traverse_edges(
    adjacency: Mapping[str, tuple[Edge, ...]],
    roots: tuple[str, ...],
    max_depth: int | None,
) -> tuple[set[str], list[TraversalEdge]]:
    """Visit reachable nodes with deterministic deque-based BFS ordering."""

    visited: set[str] = set()
    traversed: list[TraversalEdge] = []
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
        for edge in adjacency.get(node, ()):
            traversed.append(TraversalEdge(edge_id=edge.edge_id, source=node, target=edge.component_id))
            if edge.component_id not in visited:
                next_level.append((edge.component_id, depth + 1))
        if not queue and next_level:
            queue.extend(sorted(next_level, key=lambda item: item[0]))
            next_level.clear()
    return visited, traversed


def traverse(adjacency, roots, max_depth: int | None):
    """Backward-compatible dict traversal wrapper."""

    typed_adjacency = {
        key: tuple(edge if isinstance(edge, Edge) else Edge.from_dict(edge) for edge in edges)
        for key, edges in adjacency.items()
    }
    visited, traversed = traverse_edges(typed_adjacency, tuple(roots), max_depth)
    from dependency_algebra.serialization import traversal_edge_to_dict

    return visited, [traversal_edge_to_dict(edge) for edge in traversed]
