"""Analysis orchestration for normalized Dependency Algebra IR."""

from __future__ import annotations

from typing import Any

from dependency_algebra.classification import classify_result
from dependency_algebra.ir import AnalysisResult, CanonicalIR
from dependency_algebra.predicate import evaluate as evaluate_dependency
from dependency_algebra.reachability import evaluate as evaluate_reachability
from dependency_algebra.serialization import analysis_result_to_dict


def analyze_artifact(ir: CanonicalIR, max_depth: int | None = None) -> AnalysisResult:
    """Analyze normalized IR and return an immutable structural artifact."""

    canonical_ir = ir
    reachability_result = evaluate_reachability(canonical_ir, max_depth=max_depth)
    dependencies = tuple(
        evaluate_dependency(canonical_ir, workload, max_depth=max_depth)
        for workload in canonical_ir.workloads
    )
    classification = classify_result(dependencies)
    return AnalysisResult(
        schema_version="dependency-algebra.analysis.v1",
        topology_id=canonical_ir.topology_id,
        normalized_ir_hash=canonical_ir.normalized_ir_hash,
        classification=classification.classification,
        reachability=reachability_result,
        dependencies=dependencies,
    )


def analyze(ir: dict[str, Any], max_depth: int | None = None) -> dict[str, Any]:
    """Backward-compatible analysis wrapper returning serialized results."""

    return analysis_result_to_dict(analyze_artifact(CanonicalIR.from_dict(ir), max_depth=max_depth))
