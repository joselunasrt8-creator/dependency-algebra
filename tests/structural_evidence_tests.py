import dataclasses
from pathlib import Path

import pytest

from dependency_algebra.analysis import AnalysisPassMetadata, DependencyAnalysisPass
from dependency_algebra.analysis_registry import AnalysisRegistry, UnknownAnalysisPassError
from dependency_algebra.compiler import compile_artifact
from dependency_algebra.evidence import (
    RESULT_VALIDATION_CONTRACT,
    STRUCTURAL_EVIDENCE_SCHEMA_VERSION,
    StructuralEvidenceValidationError,
    compile_structural_evidence_artifact,
    structural_evidence_artifact,
    structural_evidence_artifact_hash,
    validate_analysis_result,
)
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import AnalysisResult, CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, canonical_json_bytes, canonical_json_text, sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "fixtures" / "valid" / "minimal-valid.json").read_bytes()
V2_FIXTURE = ROOT / "fixtures" / "structural_evidence" / "minimal-valid-v2.json"
V1_FIXTURE = ROOT / "fixtures" / "artifacts" / "minimal-valid-v1.json"


class SpoofDependencyPass:
    @property
    def metadata(self):
        return DependencyAnalysisPass().metadata

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
        return DependencyAnalysisPass().execute(ir)


def _ir_and_result(max_depth=None):
    topology = parse_topology(SOURCE.decode("utf-8"), "minimal-valid")
    ir_dict = validate_and_normalize(topology, "minimal-valid")
    ir = CanonicalIR.from_dict(ir_dict)
    analysis_pass = DependencyAnalysisPass(max_depth=max_depth)
    return ir, analysis_pass, analysis_pass.execute(ir)


def test_registered_dependency_analysis_emits_valid_structural_evidence():
    artifact = compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid")
    assert canonical_json_text(artifact) == V2_FIXTURE.read_text(encoding="utf-8")

    assert artifact["artifact_schema_version"] == STRUCTURAL_EVIDENCE_SCHEMA_VERSION
    assert artifact["analysis"]["analysis_id"] == "dependency-algebra.dependency-analysis"
    assert artifact["analysis"]["analysis_version"] == "1"
    assert artifact["analysis"]["deterministic_configuration"] == {}
    assert artifact["analysis"]["accepted_input"] == "dependency_algebra.ir.CanonicalIR"
    assert artifact["analysis"]["output_contract_identity"] == "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1"
    assert "SPEC.md" in artifact["analysis"]["specification_references"]
    assert artifact["input"]["source_topology_hash"] == sha256_bytes(SOURCE)
    assert artifact["input"]["normalized_ir_hash"] == artifact["result"]["payload"]["normalized_ir_hash"]
    assert artifact["result"]["validation_contract"] == RESULT_VALIDATION_CONTRACT
    assert artifact["result"]["validation_status"] == "VALIDATED"
    ir, _, result = _ir_and_result()
    assert artifact["result"]["result_hash"] == analysis_result_hash(result)
    assert artifact["artifact_hash"] == structural_evidence_artifact_hash(artifact)
    validate_analysis_result(DependencyAnalysisPass().metadata, ir, result, result_hash=artifact["result"]["result_hash"])


def test_structural_evidence_is_byte_identical_across_repeated_execution():
    first = canonical_json_bytes(compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid"))
    second = canonical_json_bytes(compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid"))
    assert first == second
    assert b"generated_at" not in first
    assert b"/workspace" not in first


def test_registry_order_and_configuration_key_order_do_not_change_identity():
    first = canonical_json_text(compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid", registry=AnalysisRegistry([DependencyAnalysisPass()])))
    second = canonical_json_text(compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid", registry=AnalysisRegistry([DependencyAnalysisPass()])))
    assert first == second

    metadata_a = AnalysisPassMetadata("dependency-algebra.dependency-analysis", "1", "dependency_algebra.ir.CanonicalIR", {"z": 1, "a": 2}, ("SPEC.md",), "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1")
    metadata_b = AnalysisPassMetadata("dependency-algebra.dependency-analysis", "1", "dependency_algebra.ir.CanonicalIR", {"a": 2, "z": 1}, ("SPEC.md",), "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1")
    assert canonical_json_text({"configuration": dict(metadata_a.deterministic_configuration)}) == canonical_json_text({"configuration": dict(metadata_b.deterministic_configuration)})


def test_unknown_analysis_id_fails_closed():
    with pytest.raises(UnknownAnalysisPassError):
        compile_structural_evidence_artifact(SOURCE, source_id="minimal-valid", analysis_id="unknown.analysis")


def test_unregistered_spoof_pass_fails_closed():
    ir, _, result = _ir_and_result()
    with pytest.raises(StructuralEvidenceValidationError):
        structural_evidence_artifact(
            analysis_pass=SpoofDependencyPass(),
            canonical_ir=ir,
            source_topology_hash=sha256_bytes(SOURCE),
            result=result,
        )


def test_invalid_deterministic_configuration_and_source_hash_fail_closed():
    ir, _, result = _ir_and_result()
    with pytest.raises(StructuralEvidenceValidationError):
        structural_evidence_artifact(
            analysis_pass=DependencyAnalysisPass(max_depth=-1),
            canonical_ir=ir,
            source_topology_hash=sha256_bytes(SOURCE),
            result=result,
        )
    with pytest.raises(StructuralEvidenceValidationError):
        structural_evidence_artifact(
            analysis_pass=DependencyAnalysisPass(),
            canonical_ir=ir,
            source_topology_hash="not-a-sha256",
            result=result,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        AnalysisPassMetadata("", "1", "dependency_algebra.ir.CanonicalIR", {}, ("SPEC.md",), "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1"),
        AnalysisPassMetadata("dependency-algebra.dependency-analysis", "1", "dependency_algebra.ir.CanonicalIR", {}, (), "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1"),
        AnalysisPassMetadata("dependency-algebra.dependency-analysis", "1", "dependency_algebra.ir.CanonicalIR", {}, ("SPEC.md",), "invalid.contract"),
    ],
)
def test_malformed_analysis_metadata_fails_closed(metadata):
    ir, _, result = _ir_and_result()
    with pytest.raises((StructuralEvidenceValidationError, UnknownAnalysisPassError)):
        validate_analysis_result(metadata, ir, result)


def test_mismatched_normalized_ir_hash_and_result_hash_fail_closed():
    ir, analysis_pass, result = _ir_and_result()
    bad_result = dataclasses.replace(result, normalized_ir_hash="sha256:" + "0" * 64)
    with pytest.raises(StructuralEvidenceValidationError):
        validate_analysis_result(analysis_pass.metadata, ir, bad_result)
    with pytest.raises(StructuralEvidenceValidationError):
        validate_analysis_result(analysis_pass.metadata, ir, result, result_hash="sha256:" + "1" * 64)


def test_malformed_result_payload_fails_closed():
    ir, analysis_pass, result = _ir_and_result()
    bad_result = AnalysisResult(
        schema_version="invalid",
        topology_id=result.topology_id,
        normalized_ir_hash=result.normalized_ir_hash,
        classification=result.classification,
        reachability=result.reachability,
        dependencies=result.dependencies,
    )
    with pytest.raises(StructuralEvidenceValidationError):
        structural_evidence_artifact(analysis_pass=analysis_pass, canonical_ir=ir, source_topology_hash=sha256_bytes(SOURCE), result=bad_result)


def test_v1_dependency_artifact_remains_byte_identical_and_cli_schema_default_stable():
    before = V1_FIXTURE.read_text(encoding="utf-8")
    after = canonical_json_text(compile_artifact(SOURCE, source_id="minimal-valid"))
    assert before == after
    assert "dependency-algebra.artifact.v1" in before
    assert "structural-evidence.v2" not in before
