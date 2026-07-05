# Fixture Catalog

Fixtures are canonical schema-stabilization inputs.

- `fixtures/valid/minimal-valid.json`: a single reachable workload with no dependency collapse.
- `fixtures/valid/redundant-valid.json`: redundant paths where removing one non-critical component preserves reachability.
- `fixtures/degraded/minimal-degraded.json`: redundancy is reduced while at least one path remains.
- `fixtures/null/minimal-null.json`: the declared candidate removal collapses workload reachability.
- `fixtures/invalid/unknown-node-reference.json`: invalid edge reference for deterministic diagnostics.
- `fixtures/invalid/duplicate-identifiers.json`: duplicate component and edge identifiers for deterministic diagnostics.
- `fixtures/invalid/malformed-json.json`: malformed JSON parser failure fixture.
- `fixtures/determinism/stable-ordering.json`: intentionally unordered input for deterministic normalization tests.

## AST and IR contract fixtures

- `fixtures/ast/minimal-valid-ast.json`: source-faithful AST for the minimal topology contract.
- `fixtures/ast/reordered-equivalent-ast.json`: equivalent AST with reordered object keys, reordered arrays, and duplicate set-like workload declarations.
- `fixtures/ir/minimal-valid-ir.json`: canonical normalized IR expected for both equivalent AST fixtures.
- `fixtures/ir/cyclic-ir.json`: cycle representation without traversal-derived fields.
- `fixtures/ir/disconnected-ir.json`: disconnected and isolated component representation without error.
- `fixtures/ir/deduplicated-roots-candidates-ir.json`: duplicate roots and duplicate candidates represented after set normalization.

Invalid unresolved references and duplicate table identifiers remain represented by `fixtures/invalid/unknown-node-reference.json` and `fixtures/invalid/duplicate-identifiers.json`; those fixtures are rejected before IR construction.

## Frontend diagnostic fixtures

Fixtures under `fixtures/diagnostics/` are diagnostics-only conformance vectors for future parser, AST construction, and normalization failures. They cover malformed JSON, unsupported topology schema versions, duplicate component and workload identifiers, unresolved edge endpoints, unresolved workload roots, empty candidate sets, and deterministic multi-diagnostic ordering. These fixtures are not produced by implementation code in this repository state.


## Reachability contract fixtures

Fixtures under `fixtures/reachability/` are schema-only conformance vectors for `REACHABILITY_CONTRACT.md` and `schemas/reachability.schema.json`. They do not implement traversal.

- `fixtures/reachability/reachable-single-root.json`: single-root directed path reaches the workload target.
- `fixtures/reachability/unreachable-disconnected.json`: target is in a disconnected component, preserving the graph while emitting an unreachable result.
- `fixtures/reachability/multi-root-partial.json`: multiple roots are evaluated per workload and reachability succeeds when one root reaches the target.
- `fixtures/reachability/cycle-termination.json`: directed cycle evidence terminates by visited-component tracking.
- `fixtures/reachability/self-loop.json`: self-loop edge is traversable while root-equals-target reachability succeeds by zero-length path semantics.
