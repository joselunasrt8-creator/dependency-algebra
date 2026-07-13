# Dependency Pass Compatibility Report — Issue #116

## Intent

Issue #116 proves that routing dependency analysis through the analysis-pass boundary preserves existing mathematics. It does not introduce a new dependency predicate, graph algorithm, artifact schema, CLI command, plugin mechanism, or compiler redesign.

## Equivalence Boundary

The compatibility proof compares these execution paths:

```text
Legacy Engine
  → Dependency Predicate
  → AnalysisResult

Registered Analysis Pass
  → Dependency Adapter
  → AnalysisResult
```

## Implementation Lineage

| Layer | File | Symbol | Role |
| --- | --- | --- | --- |
| Specification | `DEPENDENCY_PREDICATE_CONTRACT.md` | Dependency predicate definition and equivalence clauses | Freezes dependency semantics and invariance requirements. |
| Pass contract | `dependency_algebra/analysis.py` | `AnalysisPass`, `AnalysisPassMetadata` | Defines deterministic pass identity, accepted input, output contract, configuration, and spec references. |
| Adapter | `dependency_algebra/analysis.py` | `DependencyAnalysisPass` | Wraps the existing implementation and delegates to the legacy execution oracle. |
| Registry | `dependency_algebra/analysis_registry.py` | `core_analysis_registry` | Registers one canonical dependency pass identity without plugin loading or registry redesign. |
| Legacy oracle | `dependency_algebra/engine.py` | `_analyze_artifact_legacy` | Preserves the pre-boundary dependency analysis behavior for equivalence tests. |
| Registered route | `dependency_algebra/engine.py` | `analyze_artifact_registered`, `analyze_artifact` | Routes normal analysis through the registered pass interface. |
| Tests | `tests/dependency_pass_equivalence_tests.py` | `DependencyPassEquivalenceTests` | Proves fixture-level equivalence and repeated artifact determinism. |
| Traceability | `registry/traceability.json` | `DependencyAnalysisPass` entry | Links specification → pass → implementation → tests → artifacts. |

## Compared Artifacts

For every canonical topology fixture, and for synthesized canonical IR cases derived from every valid dependency fixture, the equivalence tests compare:

- dependency classification;
- workload ordering;
- dependency result dictionaries, including diagnostics, reachable sets, and dependency hashes;
- reachability result dictionaries;
- normalized IR hash;
- complete `AnalysisResult` serialization;
- repeated registered `AnalysisResult` serialization;
- legacy-vs-registered compiler artifact serialization;
- repeated compiler artifact serialization.

## Preserved Surfaces

- The compiler and CLI keep their existing public shape.
- The dependency predicate implementation remains unchanged.
- Reachability, projection, classification, serialization, and hash boundary semantics remain unchanged.
- The registry remains an explicit in-process registry with one canonical dependency analysis identity; no plugin loading is introduced.
- The adapter does not add authority, governance, runtime execution, timestamps, random identifiers, or external mutation surfaces.

## Residual Risk

The pass currently proves equivalence by adapting the existing implementation directly. Future issue work can build on this validated boundary, but any future pass that replaces the implementation must re-run the same equivalence suite and traceability validation.
