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
