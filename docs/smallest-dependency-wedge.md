# Smallest Dependency Wedge Assessment

**Status:** planning artifact; no feature implementation  
**Intent:** identify the smallest externally usable SYNAPSE capability most likely to become a workflow dependency.  
**Scope:** repository audit, candidate wedge scoring, one recommendation, minimal launch plan, and learning plan.  
**Non-scope:** no new runtime behavior, no platform expansion, no governance surface, no external-state mutation, no new repository, and no broad architecture change.

## Continuity framing

- **Affected files:** this assessment document only.
- **Preserved invariants:** structural-only boundary, deterministic artifact semantics, replay-safe compiler pipeline, existing CLI/API contracts, and absence of authority/execution/governance semantics.
- **Mutation-capable surfaces considered:** CLI command, Python public API, packaging metadata, schemas, fixtures, tests, conformance adapters, and documentation.
- **Replay implications:** the recommended wedge must preserve byte-identical artifact replay for the same accepted input and must not add timestamps, machine-local paths, random identifiers, or network calls.
- **Proof requirements:** external users must be able to install the package, run one command on a topology file, receive a canonical artifact, and verify deterministic re-run identity.
- **Validation requirements:** unit/conformance suite, CLI smoke test, package install smoke test, and artifact byte-stability check.
- **Unresolved ambiguity:** the repository currently describes a proprietary license, so public distribution readiness may require a licensing decision before a truly external launch.

## 1. Repository assessment

### What already exists

SYNAPSE is a deterministic structural analysis compiler centered on Dependency Algebra. It accepts topology JSON, validates and normalizes it into canonical IR, projects candidate removals, evaluates reachability, computes dependency predicates, classifies the result, serializes structural evidence, and emits deterministic hashes through a thin CLI/API facade.

Implemented surfaces include:

- topology, artifact, IR, reachability, projection, dependency, diagnostic, classification, representation-invariance, and structural-evidence schemas;
- canonical fixtures spanning valid, invalid, degraded, null, dependency, projection, reachability, determinism, diagnostics, structural evidence, and representation-invariance cases;
- a Python package named `synapse-structural-analysis` with a `synapse` console script;
- a stable CLI shape: `synapse compile --input ... --output ...`;
- public Python APIs for hash receipts, artifact compilation, and structural evidence artifacts;
- a registered analysis pass layer and conformance/research-object readers;
- a broad unittest conformance suite.

### What appears production-ready

The most production-ready surface is the compiler-as-evidence path:

```text
topology JSON -> canonical validation -> deterministic structural evidence artifact -> hash receipt / canonical JSON output
```

Reasons:

- The README states the architecture-closure milestone and enumerates implemented compiler stages.
- The normative specification defines the repository as owning deterministic structural objects, analysis, receipts, and evidence artifacts while excluding authority and execution decisions.
- The CLI has stable exit codes, machine-readable diagnostics, atomic output writing, and no success stdout/stderr noise.
- The package metadata already declares a console script named `synapse`.
- The integration matrix records verified boundaries from parser through CLI/conformance consumers.
- The test suite passes locally with skipped tests recorded by unittest.

### What appears experimental or less externally ready

The following surfaces are valuable but less suitable as the first external dependency wedge:

- **Registered analysis pass extensibility:** internally verified, but external engineers would need to understand SYNAPSE-specific abstractions before getting value.
- **Conformance research objects:** useful for downstream consumers and cross-repository alignment, but less likely to be used daily by a typical external engineer.
- **Cross-repository conformance:** important for ecosystem correctness, but too broad for the first wedge and closer to platform expansion.
- **Structural evidence v2 API:** promising for future consumers, but the existing CLI artifact path is easier to demonstrate and adopt immediately.
- **Future visualization, optimization, simulation, ContinuityOS, proof, policy, or execution integrations:** explicitly out of repository scope and not appropriate for a dependency-formation wedge.

### Installability and external usability

The repository is installable as a Python package in principle because `pyproject.toml` defines setuptools build metadata, package discovery, and a `synapse` console script. The smallest external usability gap is not core capability; it is a packaged, minute-one workflow that tells an engineer exactly how to generate and compare deterministic structural evidence for a real topology file.

## 2. Candidate wedges

Scores use a 1-5 scale where 5 is strongest. For **development effort**, 5 means lowest effort.

| Rank | Candidate wedge | Engineering pain solved | Time-to-value | Installation friction | Workflow frequency | Repeated use | Dependency formation | Development effort | Existing maturity | Total |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Deterministic dependency artifact CLI for CI/pre-merge topology checks | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 39 |
| 2 | Python API for deterministic dependency evidence in internal tooling | 4 | 4 | 4 | 4 | 4 | 4 | 5 | 5 | 34 |
| 3 | Golden fixture/conformance pack for topology-analysis implementations | 4 | 4 | 3 | 3 | 4 | 4 | 4 | 5 | 31 |
| 4 | Artifact hash receipt verifier / diff helper | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 30 |
| 5 | Registered analysis pass template for custom structural checks | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 25 |

### 1. Deterministic dependency artifact CLI for CI/pre-merge topology checks

- **Problem solved:** engineers need a cheap, repeatable way to know whether a declared component removal or candidate set is structurally load-bearing before a merge, deploy, migration, or architecture review.
- **Target user:** platform engineers, SREs, infra engineers, architecture reviewers, and developers maintaining service dependency maps.
- **Existing implementation status:** mostly complete; CLI, schemas, deterministic artifacts, diagnostics, atomic output, package script, fixtures, and tests already exist.
- **Estimated effort:** very low; mostly external-facing workflow polish, install smoke validation, one example topology, and a minimal CI snippet.
- **Time-to-value:** minutes; install, run one command, inspect artifact classification/failure surface/hash.
- **Dependency potential:** high; once placed in pre-merge checks, architecture review, or migration review, removal makes the workflow worse because deterministic structural evidence disappears.
- **Dependency test:** an engineer would notice if CI stopped producing the artifact, their review workflow would become less trustworthy, they would likely reinstall it to regain deterministic evidence, and a successful first use is easy to recommend.

### 2. Python API for deterministic dependency evidence in internal tooling

- **Problem solved:** internal tools need deterministic structural evidence without shelling out.
- **Target user:** engineers building developer portals, topology inventories, reliability dashboards, and review bots.
- **Existing implementation status:** complete public API exports exist for `compile`, `compile_artifact`, and `compile_structural_evidence_artifact`.
- **Estimated effort:** low; add API-focused examples and package smoke tests.
- **Time-to-value:** fast for Python users, slower for non-Python workflows.
- **Dependency potential:** medium-high; embedded API use can become sticky, but onboarding requires writing code before value appears.
- **Dependency test:** users would notice if their internal tool broke, but fewer users will reach that embedded state than with the CLI wedge.

### 3. Golden fixture/conformance pack for topology-analysis implementations

- **Problem solved:** teams implementing their own topology analysis need canonical fixtures to avoid semantic drift.
- **Target user:** compiler/tooling engineers, standards/conformance maintainers, and downstream analysis consumers.
- **Existing implementation status:** strong fixture and schema coverage already exists.
- **Estimated effort:** low-medium; package fixtures, document expected outputs, and stabilize fixture discovery.
- **Time-to-value:** moderate; users must already care about implementing compatible analysis.
- **Dependency potential:** medium-high for implementers, lower for everyday engineers.
- **Dependency test:** conformance implementers would miss it, but the audience is narrower and less frequent than CI users.

### 4. Artifact hash receipt verifier / diff helper

- **Problem solved:** reviewers need to verify whether topology changes alter structural evidence and why.
- **Target user:** code reviewers, release engineers, infra reviewers.
- **Existing implementation status:** partial; hash receipt and canonical artifact output exist, but a dedicated verifier/diff command does not.
- **Estimated effort:** medium; would require a new CLI subcommand and tests.
- **Time-to-value:** fast after implementation.
- **Dependency potential:** high if adopted, but not as small as the compile workflow because it adds new behavior.
- **Dependency test:** users would miss it if it became their review diff tool, but it is one step beyond the already implemented artifact generator.

### 5. Registered analysis pass template for custom structural checks

- **Problem solved:** advanced users may want to add structural analyses under a deterministic pass boundary.
- **Target user:** infrastructure framework builders and analysis extension authors.
- **Existing implementation status:** internally verified registry and pass architecture exists.
- **Estimated effort:** medium; requires documentation, examples, extension contract, and compatibility story.
- **Time-to-value:** slower; value appears only after extension authoring.
- **Dependency potential:** medium; extensions can become sticky, but the wedge optimizes capability expansion more than immediate workflow dependency.
- **Dependency test:** advanced adopters might miss it, but the adoption path is too abstract for the first wedge.

## 3. Recommended wedge

Select exactly one: **Deterministic dependency artifact CLI for CI/pre-merge topology checks.**

This wedge has the highest probability of becoming load-bearing because it is already implemented, installable in principle, demonstrable in minutes, and maps to a recurring engineering workflow: reviewing whether declared architecture/topology changes create or remove load-bearing dependencies. It does not ask users to adopt a platform, understand all SYNAPSE abstractions, write integration code, or trust runtime authority. It asks for one small habit:

```bash
synapse compile --input topology.json --output synapse-artifact.json
```

That habit can become dependency-forming when teams use the artifact in pull requests, CI jobs, migration reviews, incident retrospectives, and architecture-change review packets. The output is useful because it is deterministic, hash-addressed, machine-readable, and bounded to structural evidence. If it disappeared, users would lose a repeatable artifact that answers: what becomes unreachable when this candidate set disappears, and can I prove the answer replayed exactly?

The reason not to choose a broader wedge is that more capability would dilute the dependency test. The compile artifact path is already the narrowest behavior that can become part of another engineer's routine.

## 4. Minimal execution plan

### Launch slice

1. **Package smoke path**
   - Verify `pip install .` exposes `synapse`.
   - Verify `synapse compile --input fixtures/basic.json --output /tmp/synapse-artifact.json` exits 0.
   - Verify repeated runs produce byte-identical output for the same input.

2. **Minute-one example**
   - Add or promote one tiny `examples/topology.json` showing a service graph with one candidate set.
   - Add a README section titled `Dependency Wedge Quickstart` with exactly one install command, one compile command, and three fields to inspect: `classification`, `failure_surface`, and `artifact_hash`.

3. **CI adoption snippet**
   - Add a minimal copy-paste shell snippet that runs the compile command and stores `synapse-artifact.json` as a build artifact.
   - Do not add GitHub Actions or platform-specific integration yet; provide the snippet only.

4. **Determinism proof**
   - Add a documented two-run comparison command using `cmp` or SHA-256 over two generated artifacts.
   - Keep proof external and observable; do not add new proof semantics.

5. **Boundary guardrails**
   - Repeat in the quickstart that the artifact is structural evidence, not execution authorization, policy approval, or governance legitimacy.

### Explicit non-goals

- No new analysis pass.
- No UI.
- No hosted service.
- No runtime hooks.
- No repository mutation outside docs/examples/tests required for the launch slice.
- No governance, authority, policy, execution eligibility, or proof module.
- No ecosystem roadmap before adoption evidence exists.

## 5. Learning plan

Every external interaction should be treated as research into dependency formation, not feature appetite.

### What should be observed

- Did the engineer install successfully without support?
- Did they run the CLI on a real topology rather than only the fixture?
- Did they commit the topology or generated artifact to a repository?
- Did they place the command in CI, a pre-merge checklist, or an architecture-review process?
- Did they inspect `classification`, `failure_surface`, `redundancy_map`, or `artifact_hash`?
- Did they rerun it after changing topology?
- Did they ask for integrations only after repeated manual use?
- Did they share the artifact with another reviewer?
- Did they compare artifacts across commits?
- Did they come back unprompted after the first use?

### Assumptions being tested

- Engineers have recurring uncertainty about whether topology changes create load-bearing dependencies.
- Deterministic structural evidence is valuable even without governance/execution semantics.
- A one-command CLI is easier to adopt than an API or extension framework.
- Hash-stable artifacts are trusted enough to enter review workflows.
- Users prefer immediate evidence over a broader platform promise.
- The current topology JSON shape is simple enough for a first external user to author or translate into.

### Evidence that would validate the wedge

- At least one external engineer runs the CLI on a real topology within the first session.
- At least one external repository adds the command to CI, a pre-merge checklist, or a review script.
- A user reruns the command on changed topology without being prompted.
- A user compares two generated artifacts or references the artifact in a review conversation.
- A user reports that removal would make architecture or migration review worse.
- Requests cluster around easier installation, examples, CI snippets, and artifact comparison rather than broad platform features.

### Evidence that would invalidate the wedge

- Users understand the concept but do not run it on real topology.
- Users run it once on the fixture but do not rerun it.
- Users ask primarily for visualization, hosted UI, or governance/execution semantics before seeing value in the artifact.
- Topology authoring friction prevents first real use.
- Generated artifacts are viewed as interesting but not useful in review, CI, or migration workflows.
- Users would not notice if the CLI disappeared after trial.

## Final decision rule

The next product move should optimize for one repeatable habit: **compile declared topology into deterministic dependency evidence before structural changes are merged or reviewed.**

That is the smallest current wedge with the strongest path from interesting to useful, repeatedly used, workflow integrated, load-bearing, and dependency-forming.
