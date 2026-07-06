# Architecture Closure Report

## Scope and intent

This audit reviews the compiler as a 1.0-oriented artifact pipeline and records the remaining architectural debt without adding analysis features, changing schemas, changing public APIs, changing CLI behavior, or changing deterministic hash boundaries.

Canonical pipeline:

```text
Raw Input
  ↓
Frontend Validation
  ↓
Canonical IR
  ↓
Projection
  ↓
Reachability
  ↓
Predicate
  ↓
AnalysisResult
  ↓
Serialization
  ↓
Hash Receipt
  ↓
CLI / Public API
```

## Architecture score

**8.5 / 10**

The compiler is structurally close to complete: typed immutable artifacts exist for the core stages, the orchestration layer is thin, serialization owns canonical JSON and SHA-256 digest construction, and CLI code remains an adapter. The remaining debt is mostly compatibility-oriented boundary overlap rather than missing architecture.

## Pipeline audit

| Stage | Current owner | Producer | Consumer | Boundary assessment |
| --- | --- | --- | --- | --- |
| Raw input | `compiler.py`, `cli.py` | CLI or public API caller | frontend parser | Clean. CLI obtains bytes/text; compiler facade computes exact input-byte identity. |
| Frontend validation | `frontend.py`, `diagnostics.py` | `parse_topology`, `validate_and_normalize` | compiler facade / typed IR adapter | Mostly clean. Frontend validates and normalizes; it calls the serialization hash owner for `normalized_ir_hash` but does not own hash implementation. |
| Canonical IR | `ir.py` | frontend dictionary output, `CanonicalIR.from_dict` adapter | engine, projection, reachability, predicate | Clean typed ownership. Backward-compatible dictionaries remain only at API edges. |
| Projection | `projection.py` | `project` | predicate / compatibility wrapper | Clean structural concern. Projection does not classify, serialize, or hash. |
| Reachability | `reachability.py` | `evaluate`, `traverse_edges` | engine, predicate / compatibility wrapper | Clean structural observation. Compatibility wrapper serializes only by delegating to serialization. |
| Predicate | `predicate.py` | `evaluate` | engine / compatibility wrapper | Moderate coupling remains: predicate binds required projected/reachability identity fields by calling serialization-owned hash boundary helpers. It does not implement hashing. |
| AnalysisResult | `engine.py`, `classification.py`, `ir.py` | `analyze_artifact` | compiler facade / compatibility wrapper | Mostly clean. `engine.py` orchestrates analysis stages and only crosses serialization in the legacy `analyze` wrapper. |
| Serialization | `serialization.py` | serializer functions | compiler facade, CLI diagnostics, wrappers | Clean canonical representation owner. It owns dictionary conversion, canonical JSON text/bytes, and derived SHA-256 digests. |
| Hash receipt | `compiler.py` plus `serialization.py` | compiler facade | CLI / public API caller | Moderate coupling remains: compiler assembles the receipt payload while serialization owns the receipt hash. This preserves public API but should eventually move receipt shaping behind a typed artifact if compatibility allows. |
| CLI / public API | `cli.py`, `__init__.py` | argparse / import facade | users | Clean. CLI delegates compilation and canonical output formatting; public API exports only the compiler facade. |

## Artifact ownership audit

| Artifact | Producer | Consumer | Serialization owner | Hash owner | Public exposure |
| --- | --- | --- | --- | --- | --- |
| Diagnostic document | `diagnostics.py` | CLI stderr, tests | `diagnostics.py` shape, `serialization.canonical_json_text` bytes/text | None beyond canonical emission | Error API through `CompilerDiagnosticException` and CLI stderr |
| Canonical IR dictionary | `frontend.py` | `compiler.py`, `CanonicalIR.from_dict` | `frontend.py` currently shapes the normalized dictionary; `serialization.normalized_ir_hash` owns hash bytes | `serialization.normalized_ir_hash` | Indirectly through legacy APIs/tests |
| `CanonicalIR` | `ir.py` adapter from frontend output | engine, projection, reachability, predicate | Not serialized directly; legacy dictionary remains source representation | `normalized_ir_hash` already present | Internal typed artifact |
| `ProjectedIR` | `projection.py` | predicate, projection wrapper | `serialization.projected_ir_to_dict` | `serialization.projected_ir_identity_hash` | Legacy `complement_projection` wrapper |
| `ReachabilityResult` | `reachability.py` | engine, serializer | `serialization.reachability_result_to_dict` | `serialization.reachability_result_hash` | Legacy `reachability` wrapper and analysis output |
| `DependencyResult` | `predicate.py` | engine, classification, serializer | `serialization.dependency_result_to_dict` | `serialization.dependency_result_hash` plus identity helpers | Legacy `dependency_result` wrapper and analysis output |
| `ClassificationResult` | `classification.py` | engine | Embedded by `serialization.analysis_result_to_dict` | Covered by analysis/result receipt boundaries | Legacy `classify` wrapper and receipt classification |
| `AnalysisResult` | `engine.py` | compiler facade / serializer | `serialization.analysis_result_to_dict` | `serialization.analysis_result_hash` exposed as existing `dependency_result_hash` aggregate field | Legacy `analyze` wrapper |
| Hash receipt dictionary | `compiler.py` | CLI / public API | `compiler.py` shapes payload; CLI uses `canonical_json_text` for output | `serialization.hash_receipt_hash` | Primary `compile()` return and CLI output |

## Module boundary audit

- `frontend.py`: owns parsing, validation, and normalization for the frontend boundary. Coupling note: it shapes the normalized IR dictionary directly and requests `normalized_ir_hash`; a future typed `NormalizedIRPayload` could reduce dictionary ownership overlap, but the current shape is schema-preserving and stable.
- `projection.py`: owns graph projection only. No remaining semantic or serialization ownership except the explicit compatibility wrapper.
- `reachability.py`: owns structural graph observation only. It returns typed reachability artifacts and delegates dictionary conversion in compatibility wrappers.
- `predicate.py`: owns semantic dependency interpretation for one workload. Remaining coupling: it invokes serialization-owned identity helpers to populate schema-required identity fields.
- `classification.py`: owns aggregate structural classification only.
- `serialization.py`: owns representation and cryptographic identity boundaries. It does not perform graph analysis or semantic interpretation.
- `engine.py`: owns analysis orchestration only. The legacy `analyze()` API crosses the serialization boundary by delegation.
- `compiler.py`: owns facade orchestration and hash receipt assembly. Remaining coupling: hash receipt payload construction is still dictionary-shaped in the facade for API compatibility.
- `cli.py`: owns interface behavior only. It delegates compiler logic and canonical text output.
- `ir.py`: owns immutable typed artifacts. Remaining coupling: `to_dict()` convenience methods delegate to serialization; these are compatibility conveniences, not representation ownership.

## Determinism audit

Verified deterministic mechanisms:

- Canonical JSON uses sorted object keys, compact separators, UTF-8 bytes, and no trailing newline.
- Frontend normalization sorts components, edges, adjacency keys, reverse-adjacency keys, roots, candidate sets, and workloads before hashing.
- Reachability traversal sorts roots, level queues, visited nodes, reached roots, and traversal-edge output.
- Predicate outputs sort projected reachable nodes before identity binding and result emission.
- Diagnostics are sorted before diagnostic-document emission.
- Hashes are derived from explicit canonical payloads and exclude their own derived hash fields.

Remaining nondeterminism risks:

1. `ProjectedIR.removed` is stored as a `frozenset`; any public dictionary projection must serialize it through a canonical list boundary, not expose raw set iteration.
2. Compatibility wrappers that return dictionaries are safe only while they continue delegating representation to `serialization.py`.
3. Python dict insertion order is deterministic for constructed normalized payloads, and canonical serialization sorts keys; code should continue avoiding filesystem-order-dependent fixture discovery for artifact construction.

## Architectural invariant audit

| Invariant | Status | Notes |
| --- | --- | --- |
| Analysis never performs serialization | Mostly true | Legacy wrappers in analysis modules return dictionaries by delegating to serialization. Core typed functions do not assemble JSON shapes. |
| Analysis never computes hashes | Mostly true | Analysis modules call serialization-owned identity helpers where schema-required identity fields must be populated. They do not import `hashlib` or implement digest construction. |
| Serialization never performs graph analysis | True | Serializers only convert typed artifacts and hash canonical payloads. |
| Frontend never performs semantic analysis | True | Frontend validates graph integrity and normalizes input; it does not run reachability/projection/predicate/classification. |
| CLI never contains compiler logic | True | CLI delegates to `compile()` and only handles argparse, output, and diagnostics. |
| Hashes are derived exclusively from canonical serialized artifacts | True | Digest construction is centralized in `serialization.py`; input bytes are the only exact-byte hash boundary. |

## Typed artifact model review

No broad dictionary-to-dataclass migration is recommended now. The current typed artifacts cover the analysis pipeline and reduce accidental mutation. Remaining dictionaries are justified at boundaries:

- raw parsed topology documents;
- normalized IR schema payloads emitted by the frontend;
- diagnostic payloads;
- backward-compatible public wrapper returns;
- final hash receipt public API return.

Recommended future typed artifacts only if API compatibility permits:

1. `NormalizedIRPayload` or a direct frontend-produced `CanonicalIR` with a serializer-owned dictionary projection.
2. `HashReceipt` typed artifact with serializer-owned payload construction and hash finalization.
3. Immutable diagnostic artifact if diagnostic dictionaries start accumulating more schema responsibility.

## Documentation audit

Documentation now consistently describes the implemented compiler as a typed artifact pipeline rather than a schema-only plan. Remaining historical contract documents intentionally describe pre-implementation planning issues; they should remain as historical contracts unless superseded by a versioned architecture document.

Obsolete descriptions corrected in this closure pass:

- README milestone language that described the surface as intentionally schema-only.
- README canonical pipeline that skipped the current frontend validation, typed analysis artifact, serialization, hash receipt, and public API stages.
- determinism language that described `input_hash` as canonical topology JSON instead of exact input bytes.
- determinism language that described `artifact_hash` instead of the current receipt and result hash boundaries.

## Remaining architectural debt

1. **Hash receipt is dictionary-shaped in `compiler.py`.** This is acceptable for API compatibility but leaves final receipt shape partly outside `serialization.py`.
2. **Frontend emits canonical IR as a dictionary.** This preserves schemas and tests but means frontend owns more representation shape than ideal.
3. **Predicate binds hash identity fields.** Hash construction is centralized, but the predicate stage still knows when identity fields are needed.
4. **Compatibility wrappers blur pure-stage boundaries.** They are intentionally retained for backwards compatibility and currently delegate serialization instead of reimplementing it.
5. **Historical planning docs coexist with implementation docs.** This is manageable but can confuse readers unless future docs clearly distinguish frozen planning contracts from current implementation architecture.

## Suggested follow-up issues

1. Introduce an internal `HashReceipt` typed artifact and serializer-owned receipt finalizer while preserving `compile()`'s dictionary return.
2. Consider a typed frontend output boundary so `validate_and_normalize()` can remain backward-compatible while a new internal function returns `CanonicalIR` directly.
3. Add architecture tests forbidding direct `hashlib` and `json.dumps` usage outside `serialization.py`, except exact input-byte hashing through serializer helpers.
4. Add a regression test for `complement_projection()` dictionary output to ensure set-like fields are canonical JSON-compatible lists.
5. Add a short `ARCHITECTURE.md` that supersedes historical planning-only language without deleting old contracts.

## Closure decision

The compiler architecture can be considered **structurally complete for a 1.0 baseline** if the remaining compatibility overlaps are accepted as boundary adapters rather than stage responsibilities. The core responsibilities are decoupled: structural analysis, semantic interpretation, serialization, cryptographic identity, and external interfaces each have a single authoritative implementation owner.
