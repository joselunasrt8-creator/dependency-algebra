"""Complement projection for normalized Dependency Algebra IR.

This module performs only structural projection: selecting removed candidates,
constructing projected adjacency, and filtering roots. It makes no dependency
semantic decisions, computes no hashes, and performs no classification.
"""

from __future__ import annotations

from dependency_algebra.ir import CanonicalIR, ProjectedIR, Workload


def project(ir: CanonicalIR, workload: Workload) -> ProjectedIR:
    """Return the workload complement projection as structural traversal inputs."""

    candidates = frozenset(workload.candidate_set)
    adjacency = {
        component_id: tuple(edge for edge in ir.adjacency[component_id] if edge.component_id not in candidates)
        for component_id in ir.components
        if component_id not in candidates
    }
    roots = tuple(root for root in workload.roots if root not in candidates)
    return ProjectedIR(removed=candidates, adjacency=adjacency, roots=roots)


def complement_projection(ir, workload):
    """Backward-compatible dict projection wrapper."""

    canonical = ir if isinstance(ir, CanonicalIR) else CanonicalIR.from_dict(ir)
    canonical_workload = workload if isinstance(workload, Workload) else Workload.from_dict(workload)
    from dependency_algebra.serialization import projected_ir_to_dict

    return projected_ir_to_dict(project(canonical, canonical_workload))
