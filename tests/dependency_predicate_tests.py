"""Executable conformance tests for the dependency predicate contract."""

from __future__ import annotations

import unittest

from dependency_algebra.ir import CanonicalIR, Edge, Workload
from dependency_algebra.predicate import evaluate
from dependency_algebra.serialization import dependency_result_to_dict


SCHEMA_VERSION = "dependency-algebra.dependency.v1"
NORMALIZED_IR_HASH = "sha256:test-normalized-ir"
DEPENDENCY_REASON = "no_structurally_valid_path_after_projection"
NON_DEPENDENCY_REASON = "structurally_valid_path_remaining_after_projection"


def edge(edge_id: str, component_id: str) -> Edge:
    return Edge(edge_id=edge_id, component_id=component_id)


def workload(
    *,
    roots: tuple[str, ...] = ("root",),
    target: str = "target",
    candidate_set: tuple[str, ...],
    workload_id: str = "workload-under-test",
) -> Workload:
    return Workload(id=workload_id, roots=roots, target=target, candidate_set=candidate_set)


def canonical_ir(
    *,
    components: tuple[str, ...],
    adjacency: dict[str, tuple[Edge, ...]],
    subject: Workload,
) -> CanonicalIR:
    return CanonicalIR(
        topology_id="predicate-conformance-topology",
        normalized_ir_hash=NORMALIZED_IR_HASH,
        components=components,
        adjacency=adjacency,
        workloads=(subject,),
    )


class DependencyPredicateConformanceTests(unittest.TestCase):
    def assert_common_fields(
        self,
        result,
        subject: Workload,
        *,
        dependency: bool,
        reason: str,
        reachable_after_projection: tuple[str, ...],
    ) -> None:
        self.assertEqual(result.schema_version, SCHEMA_VERSION)
        self.assertEqual(result.workload_id, subject.id)
        self.assertEqual(result.normalized_ir_hash, NORMALIZED_IR_HASH)
        self.assertEqual(result.roots, subject.roots)
        self.assertEqual(result.target, subject.target)
        self.assertEqual(result.candidate_set, subject.candidate_set)
        self.assertEqual(result.dependency, dependency)
        self.assertEqual(result.dependency_reason, reason)
        self.assertEqual(result.reachable_after_projection, reachable_after_projection)
        self.assertTrue(result.projected_ir_hash.startswith("sha256:"))
        self.assertTrue(result.reachability_result_hash.startswith("sha256:"))
        self.assertEqual(result.diagnostics, ())

    def test_bridge_dependency_candidate_removal_eliminates_only_path(self) -> None:
        subject = workload(candidate_set=("bridge",))
        ir = canonical_ir(
            components=("root", "bridge", "target"),
            adjacency={
                "root": (edge("root-to-bridge", "bridge"),),
                "bridge": (edge("bridge-to-target", "target"),),
                "target": (),
            },
            subject=subject,
        )

        result = evaluate(ir, subject)

        self.assert_common_fields(
            result,
            subject,
            dependency=True,
            reason=DEPENDENCY_REASON,
            reachable_after_projection=("root",),
        )

    def test_non_dependency_when_redundant_path_remains(self) -> None:
        subject = workload(candidate_set=("candidate",))
        ir = canonical_ir(
            components=("root", "candidate", "alternate", "target"),
            adjacency={
                "root": (edge("root-to-candidate", "candidate"), edge("root-to-alternate", "alternate")),
                "candidate": (edge("candidate-to-target", "target"),),
                "alternate": (edge("alternate-to-target", "target"),),
                "target": (),
            },
            subject=subject,
        )

        result = evaluate(ir, subject)

        self.assert_common_fields(
            result,
            subject,
            dependency=False,
            reason=NON_DEPENDENCY_REASON,
            reachable_after_projection=("alternate", "root", "target"),
        )

    def test_root_dependency_candidate_set_removes_workload_root(self) -> None:
        subject = workload(candidate_set=("root",))
        ir = canonical_ir(
            components=("root", "target"),
            adjacency={
                "root": (edge("root-to-target", "target"),),
                "target": (),
            },
            subject=subject,
        )

        result = evaluate(ir, subject)

        self.assert_common_fields(
            result,
            subject,
            dependency=True,
            reason=DEPENDENCY_REASON,
            reachable_after_projection=(),
        )

    def test_target_dependency_candidate_set_removes_target(self) -> None:
        subject = workload(candidate_set=("target",))
        ir = canonical_ir(
            components=("root", "target"),
            adjacency={
                "root": (edge("root-to-target", "target"),),
                "target": (),
            },
            subject=subject,
        )

        result = evaluate(ir, subject)

        self.assert_common_fields(
            result,
            subject,
            dependency=True,
            reason=DEPENDENCY_REASON,
            reachable_after_projection=("root",),
        )

    def test_multiple_candidate_dependency_removes_complete_redundant_cut(self) -> None:
        subject = workload(candidate_set=("left", "right"))
        ir = canonical_ir(
            components=("root", "left", "right", "target"),
            adjacency={
                "root": (edge("root-to-left", "left"), edge("root-to-right", "right")),
                "left": (edge("left-to-target", "target"),),
                "right": (edge("right-to-target", "target"),),
                "target": (),
            },
            subject=subject,
        )

        result = evaluate(ir, subject)

        self.assert_common_fields(
            result,
            subject,
            dependency=True,
            reason=DEPENDENCY_REASON,
            reachable_after_projection=("root",),
        )

    def test_equivalent_canonical_inputs_produce_identical_structural_results(self) -> None:
        subject_one = workload(candidate_set=("candidate",))
        subject_two = workload(candidate_set=("candidate",))
        adjacency_one = {
            "root": (edge("root-to-candidate", "candidate"), edge("root-to-alternate", "alternate")),
            "candidate": (edge("candidate-to-target", "target"),),
            "alternate": (edge("alternate-to-target", "target"),),
            "target": (),
        }
        adjacency_two = {
            "root": (edge("root-to-candidate", "candidate"), edge("root-to-alternate", "alternate")),
            "candidate": (edge("candidate-to-target", "target"),),
            "alternate": (edge("alternate-to-target", "target"),),
            "target": (),
        }
        ir_one = canonical_ir(
            components=("root", "candidate", "alternate", "target"),
            adjacency=adjacency_one,
            subject=subject_one,
        )
        ir_two = canonical_ir(
            components=("root", "candidate", "alternate", "target"),
            adjacency=adjacency_two,
            subject=subject_two,
        )

        result_one = evaluate(ir_one, subject_one)
        result_two = evaluate(ir_two, subject_two)

        self.assertEqual(result_one.projected_ir_hash, result_two.projected_ir_hash)
        self.assertEqual(result_one.reachability_result_hash, result_two.reachability_result_hash)
        self.assertEqual(dependency_result_to_dict(result_one), dependency_result_to_dict(result_two))
        self.assert_common_fields(
            result_one,
            subject_one,
            dependency=False,
            reason=NON_DEPENDENCY_REASON,
            reachable_after_projection=("alternate", "root", "target"),
        )


if __name__ == "__main__":
    unittest.main()
