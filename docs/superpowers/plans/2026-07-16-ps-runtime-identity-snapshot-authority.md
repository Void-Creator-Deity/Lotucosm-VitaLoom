# VitaLoom Phase 6M — PS Run/Organism Runtime Identity Snapshot Authority

## Goal

Create a truthful, Qt-free, thread-safe Authority Module for live PS batch organism snapshots, then connect both standard and unified-bridge runner lifetimes plus sync/async editor execution through narrow Adapters.

Phase 6M owns only run-scoped read-only runtime identity. It does not create a selected-organism command, unify SR and PS identity, persist live snapshots into `.pond`, or expose Pond/Organism/QThread implementation objects.

## Previous Gate Summary

Phase 6L completed the editor-selection-to-SR-runtime correlation chain and proved that edit identity and SR live identity remain correlated rather than unified. Its focused and expanded suites passed, architecture/release checks passed, and the protected dirty-worktree audit remained 990 entries.

The single next Gate named by Phase 6L was the PS run/organism runtime identity decision and implementation. Phase 6M begins from that Gate and does not reopen Phase 6L.

## Repository Truth to Preserve

- Product runtime remains under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- The architecture remains plugin-shaped; PyQt6 remains the editor shell; QPainter remains the default viewport; OpenGL remains opt-in.
- `.pond`, Command Registry, Inspector binding, SR2D Adapter, package manifests, and project manifests remain compatible.
- Existing dirty paths are prior migration/user work. Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated changes.
- Direct runner callers in tools and tests must remain compatible; any new constructor dependency is optional and keyword-only.

## Audited PS Runtime Truth

- `PsExperimentRunner` owns a Pond only inside one `run()` or `run_unified_bridge()` call.
- Standard organisms use IDs such as `exp_1`; unified-bridge organisms derive from entities such as `hub_1`.
- `Pond.update()` removes an organism in the same tick after `organism.update()` marks it dead. A snapshot published after the tick therefore truthfully represents extinction/removal.
- Comparability does not bypass runner lifetimes: it calls `run()` and then `run_unified_bridge()` on the runner.
- `PsExperimentService.run_sync()` and `_PsExperimentWorker.run()` currently create runners locally. The async Pond is owned in the worker thread.
- Current sync error handling and async worker construction/start handling can leave `is_running` or the PS simulation lane open.
- `Pond.organisms` is mutable implementation storage. Full `Organism.to_dict()` can expose components, scripts, memories, and non-JSON values and is not a valid public Interface.

## Identity Model

```json
{
  "track": "ps_batch",
  "run_id": "ps_<opaque uuid>",
  "organism_id": "exp_1"
}
```

Rules:

- `run_id` is issued only by the Authority and is opaque.
- A bare organism ID is never sufficient.
- Timestamp, output directory, summary path, Python object ID, or SR epoch must not be used as PS run identity.
- Identity relation is `run_scoped_not_cross_track`.
- An old run identity is `stale` while a newer run is active, even when the organism ID is reused.
- When no run is active, a previously valid identity is `not_running`.

## Deep Module and Interface

Preferred file:

```text
core/Lotucosm/runtime/ps_runtime_snapshot_authority.py
```

The Qt-free Module owns run identity, complete replacement, validation, copy isolation, revision ordering, status precedence, and locking:

```python
class PsRuntimeSnapshotAuthority:
    def begin(self) -> str: ...
    def current_run_id(self) -> str | None: ...
    def publish(self, run_id: str, organism_snapshots: list[dict[str, Any]]) -> int: ...
    def query(self, identity: Mapping[str, Any] | object) -> dict[str, Any]: ...
    def end(self, run_id: str) -> dict[str, Any]: ...
```

This is a deep Module: deleting it would force opaque identity, stale ordering, JSON validation, copying, and thread synchronization into runner, worker, service, and future command callers. Its leverage is a small deterministic Interface; its locality is one Qt-free implementation.

Authority metadata:

```text
authority = ps_runtime_snapshot_authority
scope = ps_runtime_organism
track = ps_batch
identity_relation = run_scoped_not_cross_track
source = read_only_json_snapshot
```

Deterministic query statuses:

```text
ok
not_running
stale
missing
invalid_identity
unsupported_track
```

Lifecycle `end()` additionally returns `ended` for a matching active run.

Validation rules:

- `publish()` accepts only a list of JSON objects.
- JSON values must reject NaN, infinity, keys that are not strings, and arbitrary Python objects.
- Every snapshot must contain one non-empty `organism_id`; duplicates are rejected.
- Authority-owned `source` cannot be supplied by an Adapter.
- Every successful publication fully replaces the previous population and increments revision.
- Publishing `[]` is meaningful and clears extinct organisms.
- Returned identities and snapshots are copy-isolated.
- A `threading.RLock` protects begin/publish/query/end because worker and GUI threads may access the same Module.
- Query evaluates malformed/unsupported identity first, then `not_running`, then stale run, then organism missing. Thus stale-before-missing is guaranteed.
- Ending a stale run must not end the current run.

## Runner Adapter

`PsExperimentRunner` is the Pond-to-JSON Adapter at the Authority Seam.

Constructor compatibility:

```python
PsExperimentRunner(config, *, snapshot_authority=None)
```

If omitted, a private Authority is created so existing direct callers continue working. The runner exposes only narrow identity/query conveniences and never Pond or registry storage.

The organism whitelist is limited to JSON-safe facts:

```text
organism_id
entity_type
position
energy
max_energy
health
max_health
age
generation
developmental_stage
dead
```

No components, memory objects, scripts, Pond, Organism, entity wrapper, or live mutable list is included.

Standard and unified-bridge lifetimes use identical semantics:

1. construct/receive the Pond and establish its initial population;
2. `begin()` after the population exists and before the first tick;
3. publish initial population as revision 1;
4. after each completed tick, publish complete current population;
5. invoke progress callback only after that tick publication, so the callback can query the current revision;
6. on normal finish, cancel, callback failure, Pond/update failure, or unified bridge failure, call `end()` in `finally`;
7. cancellation takes effect at the next tick boundary;
8. a reused runner starts a new run ID and old identities become stale while it is active.

The runner must not retain a completed live identity as an active runtime fact. Persisted aggregate summaries remain historical results, not live snapshots.

## Service and Worker Adapter

`PsExperimentService` owns one shared `PsRuntimeSnapshotAuthority` and injects it into:

- sync `PsExperimentRunner`;
- async `_PsExperimentWorker` and its runner.

Narrow service Interface:

```python
def current_runtime_run_id(self) -> str | None: ...
def query_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]: ...
```

The service does not expose Authority storage, runner, Pond, Organism, or QThread as the runtime query Interface.

Lifecycle hardening is part of this Gate:

- sync normal/cancel/error always clears `is_running` and stops the PS lane;
- sync errors emit a deterministic error state, then an idle state, and re-raise to preserve existing exception visibility;
- async completion/cancel/error ends through the runner `finally`, clears worker/running state, and stops the lane;
- worker construction, signal wiring, or `start()` failure rolls service state and lane registration back immediately;
- error handling must be idempotent enough that stale cleanup cannot terminate a newer Authority run.

## Test-First Work

### Authority unit tests

Create `tests/test_ps_runtime_snapshot_authority.py` covering:

- unique opaque `ps_...` IDs;
- import while PyQt6 is blocked;
- begin-before-query semantics;
- malformed identity and unsupported track;
- publish/query and copy isolation;
- non-JSON, NaN/infinity, missing/duplicate organism IDs;
- complete replacement and empty publication;
- stale-before-missing across reused organism IDs;
- stale `end()` cannot end current run;
- matching `end()` returns `ended`, then queries return `not_running`.

### Runner Adapter tests

Create `tests/test_ps_experiment_runner_runtime_identity.py` covering:

- initial publication before first tick;
- callback query using run ID and organism ID;
- whitelist and no implementation-object leakage;
- revision growth after state changes;
- empty population after extinction;
- cancel cleanup;
- callback/update failure cleanup;
- unified bridge lifecycle parity;
- second run supersedes old run identity.

### Service/worker tests

Create `tests/test_ps_experiment_service_runtime_identity.py` covering:

- sync shared-Authority injection and callback query;
- normal/cancel/error cleanup;
- deterministic lane stop and state reset on sync failure;
- worker receives the shared Authority;
- async progress can query through service;
- async normal/cancel/error cleanup;
- worker construction/start failure rollback.

Tests may use narrow fakes and direct callback invocation where a real event loop would make lifecycle proof nondeterministic, but at least one worker-thread interaction must prove the shared Authority lock/interface behavior.

## Verification Ladder

1. New Authority unit tests.
2. New runner identity tests plus existing runner tests.
3. New service identity tests plus existing service/coordinator tests.
4. All PS/comparability/CLI/import-smoke tests.
5. Expanded Phase 6K/6L + PS regression to ensure SR seams remain unchanged.
6. Core boundary and release consistency checks.
7. `git diff --check`.
8. Protected worktree audit remains exactly 990 entries unless Phase 6M's new/modified files account for an explicitly documented delta without touching unrelated paths.

Every skipped check must record its reason and unblock path.

## Explicit Non-Goals

Phase 6M does not add:

- a PS selected-organism command;
- SR↔PS unified identity;
- selected WorldBridge component mapping;
- Inspector selected-entity UI or mutation;
- `.pond` runtime writeback;
- SR/PS tick merging;
- unified Pond default-ready claims;
- OpenGL default-ready claims;
- native acceleration completion claims.

## Completion Conditions

Phase 6M is complete only when:

- the Authority imports without Qt and passes its validation/lifecycle tests;
- both runner modes publish the same run-scoped snapshot semantics;
- sync and async paths share the Authority without leaking live objects;
- normal, cancel, error, and restart lifetimes are deterministic;
- focused, expanded, architecture, release, diff, and worktree evidence is recorded;
- `docs/mainline_status.md`, `docs/runtime_unification_roadmap.md`, `docs/INDEX.md`, this plan's Completion Record, and a fresh-session prompt are updated;
- exactly one next Gate is named.

## Completion Record — 2026-07-16

### Outcome

Phase 6M is complete. PS batch execution now has a truthful run-scoped identity and a Qt-free, thread-safe read-only organism snapshot Authority. Standard Pond runs, unified-bridge runs, sync editor execution, and async worker execution use the same lifetime semantics without exposing Pond, Organism, QThread, QObject, callbacks, or mutable registries.

### Architecture decisions closed

- PS live identity is `track + run_id + organism_id`, where `track` is `ps_batch` and `run_id` is an opaque Authority-issued `ps_<uuid>` value.
- `PsRuntimeSnapshotAuthority` is the deep Module. Its small Interface concentrates opaque lifetime issuance, complete population replacement, strict JSON validation, copy isolation, revision ordering, deterministic status envelopes, stale-before-missing ordering, and `RLock` synchronization.
- The Authority lives under `core/Lotucosm/runtime` because Pond organisms are Lotucosm runtime facts. It imports with PyQt6 blocked.
- `PsExperimentRunner` is the Pond-to-JSON Adapter. It publishes only the fixed whitelist and never calls full `to_dict()` or exposes components, memories, scripts, Pond, Organism, or entity wrappers.
- A run begins only after its initial population exists. Revision 1 is published before tick 1; every completed standard or unified tick publishes a complete replacement before progress notification; empty extinction publishes `[]`.
- Normal finish, cooperative cancel, callback failure, Pond/update failure, unified bridge failure, and export/service failures end the active lifetime. Completed aggregate summaries remain historical and cannot answer live queries.
- Reusing a runner resets run-local disaster/snapshot state and issues a new run ID. An old identity is `stale` while the replacement run is active and `not_running` after no run remains.
- `PsExperimentService` owns one shared Authority and injects it into sync runners and `_PsExperimentWorker`. The service exposes only `current_runtime_run_id()` and `query_runtime_organism_snapshot(...)`.
- Async terminal callbacks are worker-identity guarded, so a late stale worker cannot clean up a newer worker. Worker construction/start failure now rolls back Authority, `is_running`, worker storage, lane registration, and state.
- Sync execution now has a real `try/except/finally` lifecycle: error state is emitted, the exception remains visible, and idle/lane/Authority cleanup always occurs.

### Implemented Interfaces

- `core/Lotucosm/runtime/ps_runtime_snapshot_authority.py`
  - `PsRuntimeSnapshotAuthority.begin()`
  - `current_run_id()`
  - `publish(...)`
  - `query(...)`
  - `end(...)`
- `builtin/systems/ps_experiment_runner.py`
  - optional keyword-only `snapshot_authority`
  - `current_runtime_run_id()`
  - `query_runtime_organism_snapshot(...)`
  - standard/unified complete-population publication Adapter
- `core/VitaLoom/simulation/ps_experiment_service.py`
  - shared Authority ownership
  - sync/async injection and terminal cleanup
  - worker-thread-safe query Seam

### Verification evidence

- Authority contract: `17 passed`.
- Authority + runner Adapter contract: `26 passed`.
- Service/worker shared-Authority and rollback contract: `7 passed`.
- Focused new + existing runner/service/coordinator regression: `48 passed in 0.90s`.
- Expanded PS/developmental/verify/import/replay/CLI/comparability regression: `83 passed in 2.36s`.
- Combined PS identity + Phase 6K/6L SR/WorldBridge/Inspector regression: `125 passed in 4.22s`.
- `tools/check_core_boundaries.py`: `core boundaries OK`.
- `tools/check_release_consistency.py`: `release consistency OK`.
- Temporary-pycache compileall for all Phase 6M runtime/test files passed with no output.
- Final diff/whitespace checks passed; global Git output contains only pre-existing line-ending warnings where applicable.
- Final protected worktree audit: `993` status entries. The Phase 6L baseline was `990`; the net `+3` is exactly the three new test files. New runtime/docs live under already-untracked aggregate roots and do not add separate top-level audit entries. No unrelated path was staged, committed, reset, cleaned, reverted, deleted, or reorganized.

### Stable after this phase

- Opaque, run-scoped PS organism identity with stale-before-missing ordering.
- Complete replacement, extinction clearing, JSON/copy isolation, and worker-thread-safe read-only queries.
- Standard/unified runner parity for Authority lifetime.
- Sync/async editor Adapter parity and deterministic terminal cleanup.
- Existing `.pond`, SR identity, Command Registry, Inspector binding, SR2D Adapter, manifests, PyQt6/QPainter defaults, and opt-in OpenGL direction remain unchanged.

### Explicitly unfinished

- There is no PS selected-organism command or editor selection source.
- No Command Registry Host Seam currently exposes the active PS Authority.
- SR and PS identities remain track-specific and are not unified.
- Selected WorldBridge component mapping, Inspector mutation, `.pond` writeback, SR/PS tick merge, unified Pond default-readiness, native acceleration completion, and OpenGL default-readiness remain unclaimed.

**Unique next Gate: Phase 6N — PS runtime organism snapshot Host/Command discovery Interface decision/implementation.**
