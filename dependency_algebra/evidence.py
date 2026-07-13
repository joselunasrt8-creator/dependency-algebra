"""Canonical registered dependency-analysis evidence artifact emission.

This module owns the registered-analysis evidence boundary for the current
dependency analysis pass. It deliberately does not change the legacy
dependency-algebra.artifact.v1 compiler artifact contract; v2 evidence is an
explicit successor with a separate schema and hash boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from dependency_algebra.analysis import (
    ANALYSIS_RESULT_OUTPUT_CONTRACT,
    CANONICAL_IR_INPUT_CONTRACT,
    DEPENDENCY_ANALYSIS_ID,
    AnalysisPass,
    AnalysisPassMetadata,
    DependencyAnalysisPass,
)
from dependency_algebra.analysis_registry import AnalysisRegistry, UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import AnalysisResult, CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, analysis_result_to_dict, canonical_json_bytes, sha256_bytes, sha256_digest
from dependency_algebra.version import __version__

STRUCTURAL_EVIDENCE_SCHEMA_VERSION = "dependency-algebra.structural-evidence.v2"
RESULT_VALIDATION_CONTRACT = "dependency-algebra.result-validation.v1"
IMPLEMENTATION_IDENTITY = "dependency_algebra.analysis.DependencyAnalysisPass"
_SHA256_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class StructuralEvidenceValidationError(ValueError):
    """Raised when registered-analysis evidence cannot be emitted safely."""


def compile_structural_evidence_artifact(
    source: str | bytes,
    *,
    source_id: str = "stdin",
    max_depth: int | None = None,
    registry: AnalysisRegistry | None = None,
    analysis_id: str = DEPENDENCY_ANALYSIS_ID,
) -> dict[str, Any]:
    """Compile raw topology JSON into a v2 canonical structural evidence artifact."""

    source_text, source_bytes = _source_text_and_bytes(source)
    topology = parse_topology(source_text, source_id)
    ir_dict = validate_and_normalize(topology, source_id)
    ir = CanonicalIR.from_dict(ir_dict)
    pass_definition = (registry or core_analysis_registry()).get(analysis_id)
    if not isinstance(pass_definition, DependencyAnalysisPass):
        raise StructuralEvidenceValidationError(f"unsupported registered analysis implementation: {type(pass_definition).__name__}")
    configured_pass = pass_definition.with_configuration(max_depth=max_depth)
    result = configured_pass.execute(ir)
    return structural_evidence_artifact(
        analysis_pass=configured_pass,
        canonical_ir=ir,
        source_topology_hash=sha256_bytes(source_bytes),
        result=result,
        registry=registry or core_analysis_registry(),
    )


def structural_evidence_artifact(
    *,
    analysis_pass: AnalysisPass,
    canonical_ir: CanonicalIR,
    source_topology_hash: str,
    result: AnalysisResult,
    diagnostics: tuple[Mapping[str, Any], ...] = (),
    registry: AnalysisRegistry | None = None,
) -> dict[str, Any]:
    """Validate a registered deterministic result and wrap it in the v2 evidence envelope."""

    registry = registry or core_analysis_registry()
    metadata = _validate_registered_pass(analysis_pass, registry).metadata
    _validate_sha256_digest(source_topology_hash, "source_topology_hash")
    result_hash = analysis_result_hash(result)
    validation = validate_analysis_result(metadata, canonical_ir, result, result_hash=result_hash)
    payload = analysis_result_to_dict(result)
    artifact = {
        "artifact_schema_version": STRUCTURAL_EVIDENCE_SCHEMA_VERSION,
        "analysis": {
            "analysis_id": metadata.analysis_id,
            "analysis_version": metadata.analysis_version,
            "accepted_input": metadata.accepted_input,
            "deterministic_configuration": dict(metadata.deterministic_configuration),
            "specification_references": list(metadata.specification_references),
            "implementation_identity": IMPLEMENTATION_IDENTITY,
            "output_contract_identity": metadata.output_contract_identity,
        },
        "input": {
            "source_topology_hash": source_topology_hash,
            "normalized_ir_hash": canonical_ir.normalized_ir_hash,
        },
        "result": {
            "validation_contract": RESULT_VALIDATION_CONTRACT,
            "validation_status": validation["validation_status"],
            "result_hash": result_hash,
            "payload": payload,
        },
        "diagnostics": [dict(item) for item in sorted(diagnostics, key=lambda item: canonical_json_bytes(dict(item)))],
        "provenance": {
            "compiler_package_version": __version__,
        },
    }
    _validate_structural_evidence_artifact_contract(artifact, require_hash=False)
    artifact["artifact_hash"] = structural_evidence_artifact_hash(artifact)
    _validate_structural_evidence_artifact_contract(artifact, require_hash=True)
    return artifact


def validate_analysis_result(
    metadata: AnalysisPassMetadata,
    canonical_ir: CanonicalIR,
    result: AnalysisResult,
    *,
    result_hash: str | None = None,
) -> dict[str, str]:
    """Fail closed unless a result exactly matches the registered evidence contract."""

    _validate_metadata(metadata)
    if metadata.analysis_id != DEPENDENCY_ANALYSIS_ID:
        raise UnknownAnalysisPassError(f"unknown analysis id: {metadata.analysis_id}")
    if metadata.accepted_input != CANONICAL_IR_INPUT_CONTRACT:
        raise StructuralEvidenceValidationError("invalid accepted input contract")
    if metadata.output_contract_identity != ANALYSIS_RESULT_OUTPUT_CONTRACT:
        raise StructuralEvidenceValidationError("invalid output contract identity")
    if result.schema_version != "dependency-algebra.analysis.v1":
        raise StructuralEvidenceValidationError("invalid analysis result schema_version")
    if result.normalized_ir_hash != canonical_ir.normalized_ir_hash:
        raise StructuralEvidenceValidationError("result normalized_ir_hash does not match canonical input")
    if result.topology_id != canonical_ir.topology_id:
        raise StructuralEvidenceValidationError("result topology_id does not match canonical input")
    if result.reachability.normalized_ir_hash != canonical_ir.normalized_ir_hash:
        raise StructuralEvidenceValidationError("reachability normalized_ir_hash does not match canonical input")
    workload_ids = tuple(workload.id for workload in canonical_ir.workloads)
    dependency_ids = tuple(dependency.workload_id for dependency in result.dependencies)
    if dependency_ids != workload_ids:
        raise StructuralEvidenceValidationError("dependency workload ordering does not match canonical input")
    for dependency in result.dependencies:
        if dependency.normalized_ir_hash != canonical_ir.normalized_ir_hash:
            raise StructuralEvidenceValidationError("dependency normalized_ir_hash does not match canonical input")
        if dependency.dependency_result_hash and dependency.dependency_result_hash != sha256_digest({k: v for k, v in dependency.to_dict().items() if k != "dependency_result_hash"}):
            raise StructuralEvidenceValidationError("dependency result hash mismatch")
    computed_hash = analysis_result_hash(result)
    if result_hash is not None and result_hash != computed_hash:
        raise StructuralEvidenceValidationError("analysis result hash mismatch")
    return {"validation_status": "VALIDATED"}


def structural_evidence_artifact_hash(artifact: Mapping[str, Any]) -> str:
    """Hash a v2 artifact, excluding its own derived artifact_hash field."""

    return sha256_digest({key: value for key, value in artifact.items() if key != "artifact_hash"})


def _validate_registered_pass(analysis_pass: AnalysisPass, registry: AnalysisRegistry) -> AnalysisPass:
    metadata = _validate_metadata(analysis_pass.metadata)
    registered_pass = registry.get(metadata.analysis_id)
    if type(analysis_pass) is not type(registered_pass):
        raise StructuralEvidenceValidationError("analysis pass is not the canonical registered implementation")
    registered_metadata = _validate_metadata(registered_pass.metadata)
    if metadata.analysis_version != registered_metadata.analysis_version:
        raise StructuralEvidenceValidationError("analysis_version does not match registered pass")
    if metadata.accepted_input != registered_metadata.accepted_input:
        raise StructuralEvidenceValidationError("accepted_input does not match registered pass")
    if metadata.specification_references != registered_metadata.specification_references:
        raise StructuralEvidenceValidationError("specification_references do not match registered pass")
    if metadata.output_contract_identity != registered_metadata.output_contract_identity:
        raise StructuralEvidenceValidationError("output_contract_identity does not match registered pass")
    return analysis_pass


def _validate_metadata(metadata: AnalysisPassMetadata) -> AnalysisPassMetadata:
    if not metadata.analysis_id or not isinstance(metadata.analysis_id, str):
        raise StructuralEvidenceValidationError("analysis_id is required")
    if not metadata.analysis_version or not isinstance(metadata.analysis_version, str):
        raise StructuralEvidenceValidationError("analysis_version is required")
    if not metadata.specification_references:
        raise StructuralEvidenceValidationError("specification_references are required")
    for reference in metadata.specification_references:
        if not isinstance(reference, str) or not reference:
            raise StructuralEvidenceValidationError("specification_references must be non-empty strings")
    _validate_dependency_configuration(dict(metadata.deterministic_configuration))
    return metadata


def _validate_dependency_configuration(configuration: Mapping[str, Any]) -> None:
    if not isinstance(configuration, Mapping):
        raise StructuralEvidenceValidationError("deterministic_configuration must be an object")
    allowed_keys = {"max_depth"}
    extra_keys = sorted(set(configuration) - allowed_keys)
    if extra_keys:
        raise StructuralEvidenceValidationError(f"unsupported deterministic_configuration keys: {extra_keys}")
    if "max_depth" in configuration:
        max_depth = configuration["max_depth"]
        if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 0:
            raise StructuralEvidenceValidationError("max_depth must be a nonnegative integer")


def _validate_sha256_digest(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise StructuralEvidenceValidationError(f"{field_name} must match ^sha256:[a-f0-9]{{64}}$")


def _validate_structural_evidence_artifact_contract(artifact: Mapping[str, Any], *, require_hash: bool) -> None:
    required = {"artifact_schema_version", "analysis", "input", "result", "diagnostics", "provenance"}
    if require_hash:
        required.add("artifact_hash")
    missing = sorted(required - set(artifact))
    if missing:
        raise StructuralEvidenceValidationError(f"structural evidence artifact missing fields: {missing}")
    if artifact["artifact_schema_version"] != STRUCTURAL_EVIDENCE_SCHEMA_VERSION:
        raise StructuralEvidenceValidationError("invalid structural evidence schema version")
    if not isinstance(artifact["diagnostics"], list):
        raise StructuralEvidenceValidationError("diagnostics must be an array")

    analysis = artifact["analysis"]
    if not isinstance(analysis, Mapping):
        raise StructuralEvidenceValidationError("analysis must be an object")
    if analysis.get("analysis_id") != DEPENDENCY_ANALYSIS_ID:
        raise StructuralEvidenceValidationError("invalid analysis_id")
    if analysis.get("implementation_identity") != IMPLEMENTATION_IDENTITY:
        raise StructuralEvidenceValidationError("invalid implementation_identity")
    _validate_dependency_configuration(analysis.get("deterministic_configuration", {}))
    if not analysis.get("specification_references"):
        raise StructuralEvidenceValidationError("specification_references are required")

    input_identity = artifact["input"]
    if not isinstance(input_identity, Mapping):
        raise StructuralEvidenceValidationError("input must be an object")
    _validate_sha256_digest(input_identity.get("source_topology_hash", ""), "source_topology_hash")
    _validate_sha256_digest(input_identity.get("normalized_ir_hash", ""), "normalized_ir_hash")

    result = artifact["result"]
    if not isinstance(result, Mapping):
        raise StructuralEvidenceValidationError("result must be an object")
    if result.get("validation_contract") != RESULT_VALIDATION_CONTRACT:
        raise StructuralEvidenceValidationError("invalid validation_contract")
    if result.get("validation_status") != "VALIDATED":
        raise StructuralEvidenceValidationError("invalid validation_status")
    _validate_sha256_digest(result.get("result_hash", ""), "result_hash")
    if not isinstance(result.get("payload"), Mapping):
        raise StructuralEvidenceValidationError("result payload must be an object")
    if require_hash:
        _validate_sha256_digest(artifact.get("artifact_hash", ""), "artifact_hash")


def _source_text_and_bytes(source: str | bytes) -> tuple[str, bytes]:
    if isinstance(source, bytes):
        return source.decode("utf-8"), source
    return source, source.encode("utf-8")
