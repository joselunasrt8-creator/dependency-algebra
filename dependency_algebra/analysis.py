"""Deterministic analysis-pass contracts for SYNAPSE core analysis."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from dependency_algebra.ir import AnalysisResult, CanonicalIR


CORE_ANALYSIS_ID = "dependency-algebra.core-structural-analysis"
CORE_ANALYSIS_VERSION = "1"
DEPENDENCY_ANALYSIS_ID = "dependency-algebra.dependency-analysis"
DEPENDENCY_ANALYSIS_VERSION = "1"
CANONICAL_IR_INPUT_CONTRACT = "dependency_algebra.ir.CanonicalIR"
ANALYSIS_RESULT_OUTPUT_CONTRACT = "dependency_algebra.ir.AnalysisResult:dependency-algebra.analysis.v1"


@dataclass(frozen=True, slots=True)
class AnalysisPassMetadata:
    """Immutable deterministic identity and contract metadata for an analysis pass."""

    analysis_id: str
    analysis_version: str
    accepted_input: str
    deterministic_configuration: Mapping[str, Any]
    specification_references: tuple[str, ...]
    output_contract_identity: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "deterministic_configuration",
            MappingProxyType(dict(sorted(self.deterministic_configuration.items()))),
        )
        object.__setattr__(self, "specification_references", tuple(self.specification_references))


@runtime_checkable
class AnalysisPass(Protocol):
    """Minimal deterministic analysis-pass interface."""

    @property
    def metadata(self) -> AnalysisPassMetadata:
        """Return immutable pass identity, input, configuration, specs, and output contract metadata."""

    @property
    def analysis_id(self) -> str:
        """Stable deterministic pass identifier."""

    @property
    def analysis_version(self) -> str:
        """Stable deterministic pass version."""

    @property
    def accepted_input(self) -> str:
        """Canonical input contract accepted by this pass."""

    @property
    def deterministic_configuration(self) -> Mapping[str, Any]:
        """Deterministic configuration values that affect execution."""

    @property
    def specification_references(self) -> tuple[str, ...]:
        """Normative repository specifications that define the pass contract."""

    @property
    def output_contract_identity(self) -> str:
        """Canonical output contract identity produced by this pass."""

    def execute(self, ir: CanonicalIR) -> AnalysisResult:
        """Execute deterministically against CanonicalIR."""


@dataclass(frozen=True, slots=True)
class DependencyAnalysisPass:
    """Adapter exposing the existing dependency analysis implementation as a deterministic pass."""

    max_depth: int | None = None

    @property
    def metadata(self) -> AnalysisPassMetadata:
        configuration: dict[str, Any] = {}
        if self.max_depth is not None:
            configuration["max_depth"] = self.max_depth
        return AnalysisPassMetadata(
            analysis_id=DEPENDENCY_ANALYSIS_ID,
            analysis_version=DEPENDENCY_ANALYSIS_VERSION,
            accepted_input=CANONICAL_IR_INPUT_CONTRACT,
            deterministic_configuration=configuration,
            specification_references=(
                "SPEC.md#dependency-algebra",
                "DEPENDENCY_PREDICATE_CONTRACT.md#dependency-predicate-definition",
                "REACHABILITY_CONTRACT.md#reachability-semantics",
                "DETERMINISM.md#dependency-predicate-results",
                "registry/traceability.json#dependency-analysis-pass-equivalence",
            ),
            output_contract_identity=ANALYSIS_RESULT_OUTPUT_CONTRACT,
        )

    @property
    def analysis_id(self) -> str:
        return self.metadata.analysis_id

    @property
    def analysis_version(self) -> str:
        return self.metadata.analysis_version

    @property
    def accepted_input(self) -> str:
        return self.metadata.accepted_input

    @property
    def deterministic_configuration(self) -> Mapping[str, Any]:
        return self.metadata.deterministic_configuration

    @property
    def specification_references(self) -> tuple[str, ...]:
        return self.metadata.specification_references

    @property
    def output_contract_identity(self) -> str:
        return self.metadata.output_contract_identity

    def execute(self, ir: CanonicalIR) -> AnalysisResult:
        from dependency_algebra.engine import analyze_artifact_legacy

        return analyze_artifact_legacy(ir, max_depth=self.max_depth)


@dataclass(frozen=True, slots=True)
class CoreStructuralAnalysisPass(DependencyAnalysisPass):
    """Compatibility alias for the first core structural pass identity."""

    @property
    def metadata(self) -> AnalysisPassMetadata:
        configuration: dict[str, Any] = {}
        if self.max_depth is not None:
            configuration["max_depth"] = self.max_depth
        return AnalysisPassMetadata(
            analysis_id=CORE_ANALYSIS_ID,
            analysis_version=CORE_ANALYSIS_VERSION,
            accepted_input=CANONICAL_IR_INPUT_CONTRACT,
            deterministic_configuration=configuration,
            specification_references=(
                "SPEC.md#dependency-algebra",
                "DEPENDENCY_PREDICATE_CONTRACT.md",
                "REACHABILITY_CONTRACT.md",
                "DETERMINISM.md",
            ),
            output_contract_identity=ANALYSIS_RESULT_OUTPUT_CONTRACT,
        )
