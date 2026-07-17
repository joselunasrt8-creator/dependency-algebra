# Complement Projection Contract

## Status and scope

This contract defines the deliberately narrow, traversal-oriented complement projection emitted by `dependency_algebra.projection.project`. It is not a projected normalized IR document and must not be interpreted as one. The normalized `CanonicalIR` remains the source of topology identity, component records, workload definitions, reverse adjacency, and lineage.

The typed result and its compatibility serialization contain exactly three fields:

- `removed`: the candidate component identifiers;
- `adjacency`: outgoing adjacency for every remaining component, with edges to removed components omitted;
- `roots`: workload roots that remain after removal.

`schemas/projection.schema.json` describes the dictionary returned by the existing `complement_projection` compatibility wrapper. It does not describe a diagnostic envelope or a standalone compiler artifact.

## Canonical definition

```text
CanonicalIR + one normalized Workload
        ↓
Treat workload.candidate_set as the removal set
        ↓
Omit removed adjacency keys and edges whose target is removed
        ↓
Omit removed roots
        ↓
ProjectedIR(removed, adjacency, roots)
```

Because `CanonicalIR` adjacency stores outgoing edges under their source component, omitting removed source keys and edges whose target is removed eliminates every incident edge.

## Preconditions

Projection operates only on a validated, normalized `CanonicalIR` and one of its normalized workloads. Unknown candidates, duplicate candidates, empty candidate sets, unresolved endpoints, and noncanonical input ordering are frontend validation concerns and are outside this typed result. Projection therefore emits no diagnostics and has no unsuccessful result variant.

## Result invariants

A successful `ProjectedIR` guarantees:

1. `removed` is immutable in the typed object and contains the workload candidate set.
2. No removed identifier is an adjacency key, edge target, or remaining root.
3. Every remaining canonical component has exactly one adjacency key, including components with no outgoing edges.
4. Adjacency edges retain their normalized edge identifiers and targets.
5. The source `CanonicalIR` and `Workload` are not mutated.
6. No topology identity, normalized IR hash, component record, edge table, reverse adjacency, workload record, diagnostic, projected hash, runtime, authority, governance, proof, policy, execution, mutation, timestamp, machine path, random identifier, or environment-derived field is added.

The result is sufficient for deterministic reachability traversal. Consumers needing the full normalized model retain the source `CanonicalIR`; projection does not duplicate it.

## Deterministic ordering and equality

The frontend canonicalizes components, adjacency entries, roots, and candidate sets before projection. `project` preserves component/adjacency iteration order and root order while filtering. The serialization boundary sorts `removed` before converting its `frozenset` representation to JSON. Canonical JSON serialization sorts object keys, so equivalent normalized inputs produce byte-identical compatibility dictionaries and canonical JSON.

Two traversal projections are equivalent when their `removed`, `adjacency`, and `roots` values are equal. Candidate input order has no identity significance because the typed removal boundary is a set and compatibility serialization is sorted.

## Compatibility serialization

`dependency_algebra.serialization.projected_ir_to_dict` is the sole dictionary representation owner. For backward compatibility, `complement_projection` continues returning:

```json
{
  "removed": ["candidate"],
  "adjacency": {
    "remaining-component": []
  },
  "roots": ["remaining-root"]
}
```

No `schema_version` is added: doing so would change the established wrapper shape. `projected_ir_identity_hash` remains a separate predicate identity helper over the normalized IR hash and removed candidate tuple; it is not a hash of this traversal dictionary and is not part of `ProjectedIR`.

## Boundary confirmation

Projection is an internal structural transition between normalized IR and reachability. It does not parse, normalize, classify, serialize within the core `project` function, emit diagnostics or artifacts, invoke governance, or mutate external state. A future full projected-normalized-IR artifact would require a separate type, schema, serializer, hash definition, and versioned contract rather than silently widening `ProjectedIR`.
