"""Per-workload dependency predicate evaluation."""

from __future__ import annotations

from dependency_algebra.ir import CanonicalIR, DependencyResult, Workload
from dependency_algebra.projection import project
from dependency_algebra.reachability import traverse_edges
from dependency_algebra.serialization import dependency_result_to_dict, projected_ir_identity_hash, projected_reachability_identity_hash


def evaluate(ir: CanonicalIR, workload: Workload, max_depth: int | None = None) -> DependencyResult:
    """Evaluate the dependency predicate for one workload."""

    projection = project(ir, workload)
    visited, _ = traverse_edges(projection.adjacency, projection.roots, max_depth)
    reachable_after = workload.target in visited if workload.target not in projection.removed else False
    result = DependencyResult(
        schema_version="dependency-algebra.dependency.v1",
        workload_id=workload.id,
        normalized_ir_hash=ir.normalized_ir_hash,
        roots=workload.roots,
        target=workload.target,
        candidate_set=workload.candidate_set,
        projected_ir_hash=projected_ir_identity_hash(ir.normalized_ir_hash, workload.candidate_set),
        reachability_result_hash=projected_reachability_identity_hash(tuple(sorted(visited)), workload.target),
        dependency=not reachable_after,
        dependency_reason="no_structurally_valid_path_after_projection" if not reachable_after else "structurally_valid_path_remaining_after_projection",
        reachable_after_projection=tuple(sorted(visited)),
        diagnostics=(),
    )
    return result


def dependency_result(ir, workload, max_depth: int | None = None) -> dict:
    """Backward-compatible dict dependency wrapper."""

    canonical = ir if isinstance(ir, CanonicalIR) else CanonicalIR.from_dict(ir)
    canonical_workload = workload if isinstance(workload, Workload) else Workload.from_dict(workload)
    return dependency_result_to_dict(evaluate(canonical, canonical_workload, max_depth=max_depth))
