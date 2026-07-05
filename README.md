# dependency-algebra

Structural Compiler for Dependency Analysis.

`dependency-algebra` is a planning-first repository for a deterministic structural compiler. Its responsibility is to convert topology descriptions into reproducible dependency-analysis artifacts once the specification is frozen.

## Boundary

Dependency Algebra owns structural analysis only:

- topology JSON contracts
- mathematical definitions
- parser, AST, and IR contracts
- reachability semantics
- complement projection semantics
- dependency predicate semantics
- structural classification semantics
- deterministic compiler artifact schemas
- canonical fixtures and conformance tests

Dependency Algebra does **not** own:

- ContinuityOS governance validation
- execution eligibility
- runtime authorization
- proof generation
- authority propagation
- runtime policy
- mutation execution
- external-state mutation

`VALID`, `DEGRADED`, and `NULL` are structural classifications only. They are not governance decisions, execution authorizations, runtime proofs, or legitimacy results.

## Current milestone

This repository is in **Milestone 1: Frozen Schemas and Canonical Fixtures**. The implemented surface is intentionally schema-only:

- `SPEC.md`
- `BOUNDARY.md`
- `DETERMINISM.md`
- JSON schemas under `schemas/`
- canonical fixtures under `fixtures/`
- schema and boundary conformance tests under `tests/`

No compiler engine, CLI, GitHub Action, ContinuityOS integration, proof system, authority module, runtime hook, or execution surface is included in this milestone.

## Canonical pipeline

The future compiler pipeline is:

```text
Topology JSON
  ↓
Parser
  ↓
AST
  ↓
IR
  ↓
Reachability
  ↓
Complement Projection
  ↓
Dependency Predicate
  ↓
Compiler Artifact
```

The current repository freezes the contracts needed before implementing that pipeline.

## Validation

Run the conformance tests with:

```bash
python -m unittest discover -s tests -p '*_tests.py'
```
