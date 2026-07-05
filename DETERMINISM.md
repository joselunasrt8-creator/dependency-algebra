# Determinism Contract

Compiler artifacts must be reproducible from the validated input topology and frozen compiler contracts.

## Canonical serialization rules

- JSON object keys are serialized in lexicographic order.
- Arrays representing sets are sorted by canonical identifier.
- Component identifiers, edge identifiers, workload identifiers, and diagnostic identifiers are stable strings.
- Hashes use SHA-256 over explicitly defined canonical JSON byte boundaries.
- Wall-clock timestamps are forbidden in compiler artifacts.
- Random identifiers are forbidden in compiler artifacts.
- Machine-local absolute paths are forbidden in compiler artifacts.
- Environment-derived values are forbidden in compiler artifacts.
- Diagnostics are deterministically ordered by code, location, and identifier.

## Hash boundaries

- `input_hash` is computed from canonical topology JSON.
- `normalized_ir_hash` is computed from canonical normalized IR JSON.
- `artifact_hash` is computed from the canonical artifact with `artifact_hash` omitted.

## Replay safety

Repeated validation of the same fixture must produce byte-identical structural outputs once artifact emission exists. The schema-only milestone verifies that no runtime execution, proof generation, authority token, or external mutation surface is present.

## Milestone 1 test reflection

Milestone 1 does not emit compiler artifacts. Its determinism tests are therefore limited to schema-level guarantees that can be checked without implementing a compiler: canonical JSON key ordering is stable for fixture inputs, fixture diagnostics are ordered deterministically by the semantic validator, artifact hashes are constrained to explicit SHA-256 strings, and volatile fields such as wall-clock generation timestamps are rejected by the artifact schema.
