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
