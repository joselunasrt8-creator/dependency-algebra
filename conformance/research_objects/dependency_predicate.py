"""Dependency predicate research object projection."""

from __future__ import annotations

from conformance.research_objects.registry import register


RESEARCH_OBJECT_ID = "definition.dependency.dependency-predicate"


def dependency_projection(artifact):
    dependency = artifact["dependency_lattice"][0]
    is_dependency = dependency["dependency"]

    return {
        "dependency_relations": [{
            "candidate_set": dependency["candidate_set"],
            "holds": is_dependency,
            "predicate": "removal_eliminates_root_to_target_reachability",
        }],
        "structural_invariants": {
            "reachable_before_removal": True,
            "reachable_after_removal": not is_dependency,
            "removed_components": dependency["candidate_set"],
        },
        "required_diagnostics": [{
            "code": "DEPENDENCY_PREDICATE_EVALUATED",
            "level": "info",
        }],
        "proof_obligations": {
            "root_to_target_reachability_eliminated": is_dependency,
        },
        "canonical_outputs": {
            "is_dependency": is_dependency,
        },
    }


register(RESEARCH_OBJECT_ID, dependency_projection)
