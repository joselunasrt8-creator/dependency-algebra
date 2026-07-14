import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

from dependency_algebra.analysis import AnalysisPassMetadata, DependencyAnalysisPass
from dependency_algebra.analysis_registry import AnalysisRegistry, DuplicateAnalysisRegistrationError, UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.evidence import StructuralEvidenceValidationError, compile_structural_evidence_artifact, structural_evidence_artifact, structural_evidence_artifact_hash, validate_analysis_result
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import AnalysisResult, CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, canonical_json_bytes, canonical_json_text, sha256_bytes
from conformance.research_objects import registry as research_registry

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "registry" / "analysis_integration_matrix.json"
SOURCE = (ROOT / "fixtures" / "valid" / "minimal-valid.json").read_bytes()


def _ir_result():
    topology = parse_topology(SOURCE.decode(), "minimal-valid")
    ir_dict = validate_and_normalize(topology, "minimal-valid")
    ir = CanonicalIR.from_dict(ir_dict)
    analysis_pass = core_analysis_registry().get("dependency-algebra.dependency-analysis")
    result = analysis_pass.execute(ir)
    return ir, analysis_pass, result


def test_authoritative_matrix_covers_required_boundaries_and_fields():
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert matrix["schema_version"] == "synapse.analysis-integration-matrix.v1"
    required_fields = {
        "boundary_id", "source_component", "destination_component", "preserved_invariant",
        "positive_test", "deterministic_negative_test", "fixture_family",
        "expected_output_or_failure_class", "implementation_status",
    }
    records = matrix["records"]
    assert [record["boundary_id"] for record in records] == [
        "B01-parser-to-validated-input",
        "B02-validation-to-canonical-normalization",
        "B03-normalization-to-canonical-ir",
        "B04-canonical-ir-to-registered-pass",
        "B05-registry-to-selected-pass",
        "B06-pass-to-result",
        "B07-result-to-validation",
        "B08-validated-result-to-canonical-artifact",
        "B09-artifact-to-cli-output",
        "B10-artifact-to-conformance-consumer",
    ]
    for record in records:
        assert required_fields <= set(record)
        assert record["implementation_status"] == "VERIFIED"


def test_matrix_positive_registered_pipeline_boundaries():
    ir, analysis_pass, result = _ir_result()
    validation = validate_analysis_result(analysis_pass.metadata, ir, result, result_hash=analysis_result_hash(result))
    artifact = compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid")
    assert ir.normalized_ir_hash == result.normalized_ir_hash == artifact["input"]["normalized_ir_hash"]
    assert artifact["analysis"]["analysis_id"] == analysis_pass.analysis_id
    assert artifact["analysis"]["analysis_version"] == analysis_pass.analysis_version
    assert artifact["result"]["validation_status"] == validation["validation_status"] == "VALIDATED"
    assert artifact["result"]["result_hash"] == analysis_result_hash(result)


_NEGATIVE_CASES = [
    "malformed-json", "invalid-topology-shape", "duplicate-declarations", "unresolved-references",
    "unknown-analysis-id", "malformed-analysis-configuration", "malformed-pass-result",
    "canonical-hash-mismatch", "artifact-schema-failure",
]


@pytest.mark.parametrize("case", _NEGATIVE_CASES)
def test_matrix_negative_failures_are_deterministic(case):
    first = _negative_fingerprint(case)
    second = _negative_fingerprint(case)
    assert first == second
    assert first["failure_class"]


def _negative_fingerprint(case):
    try:
        if case == "malformed-json":
            parse_topology("{", "malformed")
        elif case == "invalid-topology-shape":
            validate_and_normalize({"schema_version": "dependency-algebra.topology.v1", "topology_id": "bad"}, "bad")
        elif case == "duplicate-declarations":
            source = (ROOT / "fixtures" / "invalid" / "duplicate-identifiers.json").read_text(encoding="utf-8")
            validate_and_normalize(parse_topology(source, "duplicate"), "duplicate")
        elif case == "unresolved-references":
            source = (ROOT / "fixtures" / "invalid" / "unknown-node-reference.json").read_text(encoding="utf-8")
            validate_and_normalize(parse_topology(source, "unresolved"), "unresolved")
        elif case == "unknown-analysis-id":
            core_analysis_registry().get("unknown.analysis")
        elif case == "malformed-analysis-configuration":
            DependencyAnalysisPass().with_configuration(max_depth=True)
        elif case == "malformed-pass-result":
            ir, analysis_pass, result = _ir_result()
            validate_analysis_result(analysis_pass.metadata, ir, dataclasses.replace(result, schema_version="bad"))
        elif case == "canonical-hash-mismatch":
            ir, analysis_pass, result = _ir_result()
            validate_analysis_result(analysis_pass.metadata, ir, result, result_hash="sha256:" + "0" * 64)
        elif case == "artifact-schema-failure":
            artifact = compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid")
            artifact["artifact_schema_version"] = "bad"
            structural_evidence_artifact_hash(artifact)
            structural_evidence_artifact(
                analysis_pass=DependencyAnalysisPass(),
                canonical_ir=_ir_result()[0],
                source_topology_hash="not-a-hash",
                result=_ir_result()[2],
            )
    except (CompilerDiagnosticException, UnknownAnalysisPassError, ValueError, StructuralEvidenceValidationError) as exc:
        diagnostic = getattr(exc, "diagnostic", None)
        return {"failure_class": type(exc).__name__, "detail": canonical_json_text(diagnostic) if diagnostic else str(exc)}
    raise AssertionError(f"negative case did not fail: {case}")


def test_registry_import_order_independence_and_duplicate_rejection():
    alpha = _StubPass("alpha")
    zeta = _StubPass("zeta")
    assert AnalysisRegistry([zeta, alpha]).analysis_ids() == AnalysisRegistry([alpha, zeta]).analysis_ids()
    with pytest.raises(DuplicateAnalysisRegistrationError):
        AnalysisRegistry([alpha, _StubPass("alpha")])


class _StubPass:
    def __init__(self, analysis_id):
        self._metadata = AnalysisPassMetadata(analysis_id, "1", "dependency_algebra.ir.CanonicalIR", {}, ("SPEC.md",), "test-output")
    @property
    def metadata(self): return self._metadata
    @property
    def analysis_id(self): return self.metadata.analysis_id
    @property
    def analysis_version(self): return self.metadata.analysis_version
    @property
    def accepted_input(self): return self.metadata.accepted_input
    @property
    def deterministic_configuration(self): return self.metadata.deterministic_configuration
    @property
    def specification_references(self): return self.metadata.specification_references
    @property
    def output_contract_identity(self): return self.metadata.output_contract_identity
    def execute(self, ir): raise AssertionError("not executed")


def test_canonical_ir_mutation_is_rejected():
    ir, _, _ = _ir_result()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ir.components = ("mutated",)
    with pytest.raises(TypeError):
        ir.adjacency["new"] = ()


def test_artifact_identity_is_canonical_and_byte_identical():
    first = compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid")
    second = compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid")
    assert first["input"]["source_topology_hash"] == sha256_bytes(SOURCE)
    assert first["analysis"]["analysis_id"] == "dependency-algebra.dependency-analysis"
    assert first["analysis"]["analysis_version"] == "1"
    assert first["result"]["validation_status"] == "VALIDATED"
    assert first["artifact_hash"] == structural_evidence_artifact_hash(first)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert b"timestamp" not in canonical_json_bytes(first)
    assert b"generated_at" not in canonical_json_bytes(first)


def test_cli_registered_pass_internals_do_not_leak(tmp_path):
    output = tmp_path / "artifact.json"
    completed = subprocess.run([sys.executable, "-m", "dependency_algebra.cli", "compile", "--input", str(ROOT / "fixtures" / "valid" / "minimal-valid.json"), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    payload = output.read_text(encoding="utf-8")
    assert "dependency-algebra.artifact.v1" in payload
    assert "structural-evidence.v2" not in payload
    assert "registered" not in payload.lower()


def test_existing_conformance_consumers_remain_discoverable():
    research_registry.discover_handlers()
    objects = tuple(sorted(research_registry._HANDLERS))
    assert objects
    assert tuple(research_registry.get_handler(object_id) for object_id in objects)
