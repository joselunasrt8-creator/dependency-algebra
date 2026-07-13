# Issue #78 Artifact Compatibility Decision

## Decision

**B. EXPLICIT_VERSIONED_SUCCESSOR**

The canonical registered dependency-analysis evidence envelope is introduced as
`dependency-algebra.structural-evidence.v2`. The existing
`dependency-algebra.artifact.v1` compiler artifact remains byte-for-byte stable.

## Repository evidence

* `schemas/artifact.schema.json` sets `additionalProperties: false` and requires
  the legacy dependency-specific shape, so registered-analysis metadata cannot be
  added to v1 without schema incompatibility for existing consumers.
* `dependency_algebra.compiler.compile_artifact` derives `artifact_hash` over the
  complete v1 artifact payload excluding only `artifact_hash`; adding metadata to
  v1 would change canonical bytes and the hash boundary.
* `dependency_algebra.cli` defaults to and accepts only
  `dependency-algebra.artifact.v1`, so CLI output must not be silently redirected
  to a new artifact shape.

## Compatibility and migration rules

* v1 remains the default compiler and CLI artifact.
* v1 artifact canonical hashes, normalized IR hashes, dependency result hashes,
  workload ordering, unresolved-reference behavior, and current fixtures remain
  unchanged.
* v2 is emitted only through the explicit registered dependency-analysis
  evidence API.
* v2 wraps the validated registered dependency-analysis result in a
  dependency-analysis structural evidence envelope and hashes that envelope
  excluding only `artifact_hash`.
* Existing v1 consumers are not redirected. Consumers that need registered
  dependency-analysis identity must explicitly consume `dependency-algebra.structural-evidence.v2`.

## Under-specified field dispositions

* `redundancy_map`: **PARK** in v1 compatibility output only.
* `k_of_n_resilience_profile`: **PARK** in v1 compatibility output only.
* `annihilation_conditions`: **PARK** in v1 compatibility output only.

These fields are not promoted as canonical registered analyses in v2; dependency
specific evidence remains inside the dependency result payload.
