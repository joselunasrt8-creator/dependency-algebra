# Repository Boundary

## Owned responsibilities

This repository owns structural compiler contracts and future structural analysis implementation:

- topology JSON schema
- compiler artifact schema
- classification schema
- deterministic serialization rules
- canonical fixtures
- schema conformance tests
- parser, AST-to-IR normalization, reachability, dependency predicate, hash receipt emission, and thin CLI adapter code

## Excluded responsibilities

This repository must not include modules or behavior for:

- governance validation
- execution eligibility
- runtime authorization
- proof generation
- authority propagation
- ContinuityOS legitimacy decisions
- runtime policy enforcement
- external-state mutation

Any future module named `authority`, `proof`, `execution`, `runtime`, `policy`, or `governance` is a boundary smell unless explicitly scoped as documentation proving absence of that responsibility.

## Classification boundary

`VALID`, `DEGRADED`, and `NULL` are structural classifications only. They do not represent execution eligibility, governance legitimacy, runtime authorization, runtime proof, or ContinuityOS policy outcomes.

## Compiler artifact boundary

The compiler pipeline is a sequence of immutable artifact transitions:

1. `CanonicalIR` is the normalized topology artifact consumed by structural passes.
2. `ProjectedIR` is the complement-projection artifact produced from `CanonicalIR` plus one workload.
3. `ReachabilityResult` is the reachability artifact produced by deterministic graph traversal.
4. `DependencyResult` is the predicate artifact produced from projection plus projected reachability.
5. `ClassificationResult` is the semantic classification artifact produced from dependency predicates.
6. The serialization boundary converts typed artifacts into dictionaries and canonical JSON.
7. The hash receipt boundary assigns cryptographic identity to serialized artifact payloads.

Analysis determines structural truth. Serialization determines representation. Hashing determines artifact identity. These responsibilities must not overlap: analysis modules do not own JSON encoding, canonical dictionary assembly, or SHA-256 digest construction for derived artifacts.

Backward-compatible wrappers may still return dictionaries, but those wrappers cross into the serialization boundary explicitly. They must not reimplement representation rules inside structural analysis stages.
