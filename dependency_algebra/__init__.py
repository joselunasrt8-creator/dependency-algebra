"""Public API for the Dependency Algebra compiler."""

from dependency_algebra.compiler import (
    ARTIFACT_SCHEMA_VERSION,
    COMPILER_VERSION,
    CompilerDiagnosticException,
    compile,
    compile_artifact,
)
from dependency_algebra.evidence import (
    STRUCTURAL_EVIDENCE_SCHEMA_VERSION,
    StructuralEvidenceValidationError,
    compile_structural_evidence_artifact,
)
from dependency_algebra.version import __version__

__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "COMPILER_VERSION",
    "CompilerDiagnosticException",
    "STRUCTURAL_EVIDENCE_SCHEMA_VERSION",
    "StructuralEvidenceValidationError",
    "__version__",
    "compile",
    "compile_artifact",
    "compile_structural_evidence_artifact",
]
