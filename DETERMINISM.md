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

## Normalized IR serialization

For `dependency-algebra.ir.v1`, `normalized_ir_hash` is SHA-256 over canonical UTF-8 JSON bytes of the normalized IR hash payload. The payload omits `normalized_ir_hash` itself and any transient diagnostics. Serialization uses lexicographically sorted object keys, canonical ordering for set-like arrays, compact JSON separators, and no trailing newline.

Hash-participating IR fields are the normalized structural fields: schema version, topology identity, canonical component table, canonical edge table, forward adjacency, reverse adjacency, normalized workload table, retained string metadata, and stable source lineage identifiers. Volatile source locations, local machine paths, environment-derived values, wall-clock timestamps, random identifiers, governance fields, authority fields, proof fields, runtime fields, policy fields, execution fields, and mutation fields are excluded.
## Milestone 1 test reflection

Milestone 1 does not emit compiler artifacts. Its determinism tests are therefore limited to schema-level guarantees that can be checked without implementing a compiler: canonical JSON key ordering is stable for fixture inputs, fixture diagnostics are ordered deterministically by the semantic validator, artifact hashes are constrained to explicit SHA-256 strings, and volatile fields such as wall-clock generation timestamps are rejected by the artifact schema.

## Dependency predicate determinism

Dependency predicate results are deterministic structural result objects. The identity boundary is the normalized IR, candidate set, projected IR, and reachability result over that projected IR. Set-like fields are canonically ordered before hashing, and input ordering differences must not change dependency identity.

`dependency_result_hash` is the SHA-256 digest of canonical UTF-8 JSON for the dependency result after removing only `dependency_result_hash`. Canonical JSON uses lexicographically sorted object keys and compact separators. Runtime state, authority fields, governance fields, proof fields, execution fields, timestamps, local paths, random identifiers, and external-state values are excluded from the schema and therefore excluded from the hash boundary.
## Projected IR serialization

For `dependency-algebra.projection.v1`, `projected_ir_hash` is SHA-256 over canonical UTF-8 JSON bytes of the projected IR payload. The payload omits `projected_ir_hash` itself and all projection diagnostics. Serialization uses lexicographically sorted object keys, compact separators, canonical set ordering, no trailing newline, and no timestamps, machine-local paths, random identifiers, runtime fields, authority fields, governance fields, proof fields, policy fields, execution fields, or mutation fields.
