"""Public API for the Dependency Algebra compiler."""

from dependency_algebra.compiler import COMPILER_VERSION, CompilerDiagnosticException, compile

__all__ = ["COMPILER_VERSION", "CompilerDiagnosticException", "compile"]
