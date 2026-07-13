import unittest
from types import MappingProxyType

from dependency_algebra.analysis import (
    ANALYSIS_RESULT_OUTPUT_CONTRACT,
    CANONICAL_IR_INPUT_CONTRACT,
    CORE_ANALYSIS_ID,
    CORE_ANALYSIS_VERSION,
    AnalysisPass,
    CoreStructuralAnalysisPass,
)
from dependency_algebra.ir import CanonicalIR, Edge, Workload


class AnalysisPassTests(unittest.TestCase):
    def test_core_pass_has_stable_identity(self):
        analysis_pass = CoreStructuralAnalysisPass()

        self.assertIsInstance(analysis_pass, AnalysisPass)
        self.assertEqual(analysis_pass.analysis_id, CORE_ANALYSIS_ID)
        self.assertEqual(analysis_pass.analysis_version, CORE_ANALYSIS_VERSION)
        self.assertEqual(analysis_pass.accepted_input, CANONICAL_IR_INPUT_CONTRACT)
        self.assertEqual(analysis_pass.output_contract_identity, ANALYSIS_RESULT_OUTPUT_CONTRACT)

    def test_deterministic_configuration_is_immutable_and_sorted(self):
        analysis_pass = CoreStructuralAnalysisPass(max_depth=4)

        self.assertIsInstance(analysis_pass.deterministic_configuration, MappingProxyType)
        self.assertEqual(tuple(analysis_pass.deterministic_configuration.items()), (("max_depth", 4),))
        with self.assertRaises(TypeError):
            analysis_pass.deterministic_configuration["max_depth"] = 5

    def test_metadata_is_immutable(self):
        metadata = CoreStructuralAnalysisPass().metadata

        with self.assertRaises(AttributeError):
            metadata.analysis_id = "changed"
        with self.assertRaises(TypeError):
            metadata.deterministic_configuration["new"] = "value"

    def test_specification_references_are_explicit_and_immutable(self):
        analysis_pass = CoreStructuralAnalysisPass()

        self.assertEqual(
            analysis_pass.specification_references,
            (
                "SPEC.md",
                "DEPENDENCY_PREDICATE_CONTRACT.md",
                "REACHABILITY_CONTRACT.md",
                "DETERMINISM.md",
            ),
        )
        self.assertIsInstance(analysis_pass.specification_references, tuple)

    def test_execute_returns_existing_analysis_result_contract(self):
        ir = CanonicalIR(
            topology_id="analysis-pass-test",
            normalized_ir_hash="sha256:test-normalized-ir",
            components=("root", "target"),
            adjacency={"root": (Edge("root-to-target", "target"),), "target": ()},
            workloads=(Workload("workload", ("root",), "target", ("root",)),),
        )

        result = CoreStructuralAnalysisPass().execute(ir)

        self.assertEqual(result.schema_version, "dependency-algebra.analysis.v1")
        self.assertEqual(result.topology_id, "analysis-pass-test")
        self.assertEqual(result.normalized_ir_hash, "sha256:test-normalized-ir")


if __name__ == "__main__":
    unittest.main()
