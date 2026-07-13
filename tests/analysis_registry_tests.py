import unittest

from dependency_algebra.analysis import (
    CORE_ANALYSIS_ID,
    DEPENDENCY_ANALYSIS_ID,
    AnalysisPassMetadata,
    CoreStructuralAnalysisPass,
    DependencyAnalysisPass,
)
from dependency_algebra.analysis_registry import (
    AnalysisRegistry,
    DuplicateAnalysisRegistrationError,
    UnknownAnalysisPassError,
    core_analysis_registry,
)


class StubPass:
    def __init__(self, analysis_id):
        self._metadata = AnalysisPassMetadata(
            analysis_id=analysis_id,
            analysis_version="1",
            accepted_input="dependency_algebra.ir.CanonicalIR",
            deterministic_configuration={},
            specification_references=("SPEC.md",),
            output_contract_identity="test-output",
        )

    @property
    def metadata(self):
        return self._metadata

    @property
    def analysis_id(self):
        return self.metadata.analysis_id

    @property
    def analysis_version(self):
        return self.metadata.analysis_version

    @property
    def accepted_input(self):
        return self.metadata.accepted_input

    @property
    def deterministic_configuration(self):
        return self.metadata.deterministic_configuration

    @property
    def specification_references(self):
        return self.metadata.specification_references

    @property
    def output_contract_identity(self):
        return self.metadata.output_contract_identity

    def execute(self, ir):
        raise AssertionError("registry tests must not execute passes")


class AnalysisRegistryTests(unittest.TestCase):
    def test_core_registration_and_lookup(self):
        registry = core_analysis_registry()

        self.assertEqual(registry.analysis_ids(), (DEPENDENCY_ANALYSIS_ID,))
        self.assertEqual(CORE_ANALYSIS_ID, DEPENDENCY_ANALYSIS_ID)
        self.assertIs(CoreStructuralAnalysisPass, DependencyAnalysisPass)
        self.assertIsInstance(registry.get(DEPENDENCY_ANALYSIS_ID), DependencyAnalysisPass)

    def test_duplicate_registration_is_rejected(self):
        with self.assertRaises(DuplicateAnalysisRegistrationError):
            AnalysisRegistry((StubPass("duplicate"), StubPass("duplicate")))

    def test_unknown_id_fails_closed(self):
        registry = core_analysis_registry()

        with self.assertRaises(UnknownAnalysisPassError):
            registry.get("unknown")

    def test_enumeration_is_deterministic(self):
        registry = AnalysisRegistry((StubPass("zeta"), StubPass("alpha"), StubPass("middle")))

        self.assertEqual(registry.analysis_ids(), ("alpha", "middle", "zeta"))
        self.assertEqual(tuple(item.analysis_id for item in registry.passes()), ("alpha", "middle", "zeta"))

    def test_repeated_creation_yields_identical_registry_state(self):
        states = tuple(core_analysis_registry().analysis_ids() for _ in range(5))

        self.assertEqual(states, ((DEPENDENCY_ANALYSIS_ID,),) * 5)


if __name__ == "__main__":
    unittest.main()
