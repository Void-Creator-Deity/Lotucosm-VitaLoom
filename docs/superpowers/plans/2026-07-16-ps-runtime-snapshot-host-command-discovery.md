# VitaLoom Phase 6N - PS Runtime Snapshot Host/Command Discovery

**Status: complete**

**Date:** 2026-07-16

## Goal

Expose truthful, read-only discovery and explicit query Interfaces for the active PS runtime organism snapshots without importing the PyQt-bound experiment Service into Command handlers, inventing a selected-organism concept, or leaking live Pond/Organism/worker objects.

## Previous Gate

Phase 6M established a Qt-free `PsRuntimeSnapshotAuthority` with opaque `run_id`, complete population replacement, strict JSON/copy isolation, stale-before-missing ordering, and shared sync/async Service/Worker lifecycle integration.

Verified Phase 6M baseline:

- focused Authority/Runner/Service/Coordinator suite: 48 passed;
- expanded PS suite: 83 passed;
- combined PS + Phase 6K/6L SR/WorldBridge/Inspector suite: 125 passed;
- core boundaries and release consistency passed;
- protected worktree audit: 993 entries.

## Architecture Audit

### Existing ownership

- `PsExperimentPlugin` constructs one `PsExperimentService` and registers it only as `PS_EXPERIMENT`.
- `PsExperimentService` is PyQt-bound because it owns `_PsExperimentWorker` / `QThread`, but it already exposes narrow `current_runtime_run_id()` and `query_runtime_organism_snapshot(identity)` methods.
- `PsRuntimeSnapshotAuthority` is the only source that knows the current complete organism ID set after reproduction, extinction, or replacement.
- `PsExperimentPanel` exposes experiment configuration, progress metrics, and historical runs; it has no selected-organism Interface.

### Command and Headless behavior

- `CommandRegistry` and `runtime_commands.py` are importable without PyQt6.
- Command handlers receive an optional context. Editor calls may provide `editor_context`; standalone CLI/MCP calls generally do not.
- The existing SR selected-identity Host demonstrates a Qt-free Protocol + registered Adapter + deterministic null Adapter, but its selection semantics are SR-specific and must not be copied to PS.
- A standalone process cannot truthfully inspect a live editor worker in another process. Its correct result is deterministic `unavailable`, not guessed IDs.

### Discovery evidence

- Configured initial population is not an identity source: IDs can change through reproduction and can disappear through death/extinction.
- Progress metrics expose only population counts, not current IDs.
- Therefore current `run_id` and organism IDs must be acquired atomically from the Authority-owned snapshot table.

## Decision

Implement a deep, two-step read-only Interface:

1. **Discovery** returns the active opaque run and the sorted current organism identities from the Authority's complete replacement table.
2. **Explicit query** requires a full `{track, run_id, organism_id}` identity and returns the existing Authority query envelope.

No command will interpret `{}` or a bare `organism_id` as a selected organism.

## Module / Interface Design

### 1. Authority discovery Interface

Extend `PsRuntimeSnapshotAuthority` with:

```python
discover() -> dict[str, Any]
```

Contract:

- `not_running`: no active run, `run_id=None`, zero identities;
- `ok`: active run, current revision, sorted full identities, and exact organism count;
- an active empty population is `ok` with count zero, distinct from `not_running`;
- result is JSON-only and copy-isolated;
- acquisition of run and IDs occurs under the same `RLock` critical section.

### 2. Service Adapter seam

Add a narrow Service method:

```python
discover_runtime_organisms() -> dict[str, Any]
```

It delegates to the shared Authority without exposing the Authority, worker, callback, or Qt object.

### 3. Qt-free Host Module

Add `core/VitaLoom/simulation/ps_runtime_snapshot_host.py` with:

```python
class IPsRuntimeSnapshotHost(Protocol):
    def discover_ps_runtime_organisms(self) -> dict[str, Any]: ...
    def query_ps_runtime_organism_snapshot(self, identity: object) -> dict[str, Any]: ...
```

Adapters:

- `PsRuntimeSnapshotHostAdapter`: wraps only two narrow callables from the editor-owned Service, validates JSON object results, and returns copy-isolated values.
- deterministic null Adapter: returns `unavailable` for discovery/query and never imports PyQt6.

Service key:

```text
simulation.ps_runtime_snapshot_host
```

The PS editor plugin registers/unregisters the Host Adapter separately from `PS_EXPERIMENT`.

### 4. Command Registry Interfaces

Add two read-only, GUI-optional, capability-scoped commands:

```text
runtime.ps.organism_discovery
runtime.ps.organism_snapshot
```

`runtime.ps.organism_discovery` accepts `{}` and returns discovery only. It does not select or query an organism.

`runtime.ps.organism_snapshot` requires:

```json
{
  "identity": {
    "track": "ps_batch",
    "run_id": "ps_<opaque uuid>",
    "organism_id": "exp_1"
  }
}
```

Missing `identity`, bare `organism_id`, malformed identity, unsupported track, stale run, and missing organism remain deterministic and distinct.

## Deletion Test

Without this Host Module, Command handlers would need to know:

- the editor Service key and lifecycle;
- PyQt-bound Service import constraints;
- global versus explicit editor context lookup;
- unavailable behavior for standalone Headless calls;
- result JSON/copy validation;
- the separation between ID discovery and explicit snapshot query.

Deleting the Host would spread this knowledge into Command handlers and future AI/CLI/MCP adapters. The Module therefore provides locality and leverage rather than acting as a pass-through.

Two concrete Adapters make the Seam real:

1. editor Service-backed Adapter;
2. deterministic null Adapter for unavailable/Headless contexts.

## TDD Plan

### Authority tests

- discovery before begin;
- sorted identities and exact count after publish;
- copy isolation;
- replacement and active-empty distinction;
- ended run returns `not_running`;
- discovery remains Qt-free.

### Host/Command tests

- Host metadata and null results are deterministic;
- Service-backed Adapter forwards only discovery/query and copy-isolates results;
- plugin registers and unregisters a separate Host key;
- discovery command metadata is read-only, GUI-optional, and capability-scoped;
- snapshot command requires full `identity`;
- discovery then explicit query works through one registered Host;
- stale/missing/invalid/unsupported statuses pass through unchanged;
- command results expose no Service, Authority, Runner, Worker, Pond, Organism, QObject, QThread, callbacks, or mutable registry;
- both commands import and return deterministic unavailable results with PyQt6 blocked;
- existing `runtime.sr.selected_entity_snapshot` and WorldBridge commands remain unchanged.

## Intended Files

Runtime:

- `core/Lotucosm/runtime/ps_runtime_snapshot_authority.py`
- `core/VitaLoom/simulation/ps_experiment_service.py`
- `core/VitaLoom/simulation/ps_runtime_snapshot_host.py` (new)
- `core/VitaLoom/core/service_keys.py`
- `core/VitaLoom/core/editor_context.py` (non-creating current-context lookup)
- `core/VitaLoom/commands/runtime_commands.py`
- `core/VitaLoom/commands/mcp_adapter.py`
- `builtin/editor_extensions/ps_experiment_plugin.py`

Tests:

- `tests/test_ps_runtime_snapshot_authority.py`
- `tests/test_ps_runtime_snapshot_host_command.py` (new)
- relevant existing PS/SR/Command regressions.

Documentation closure:

- this plan Completion Record;
- `docs/mainline_status.md`;
- `docs/runtime_unification_roadmap.md`;
- `docs/INDEX.md`;
- a fresh-session prompt under `docs/prompts/`.

## Non-goals

- no PS selected-organism concept;
- no implicit `{}` snapshot query;
- no SR-to-PS unified identity;
- no selected WorldBridge component mapping;
- no Inspector mutation or selected-PS UI;
- no `.pond` writeback;
- no SR/PS tick merge;
- no native/OpenGL/default-ready claim;
- no cross-process live-editor transport.

## Verification Gate

- focused new Authority/Host/Command/plugin tests;
- existing Phase 6M Runner/Service tests;
- SR selected-entity and WorldBridge command regressions;
- Command Registry/CLI/MCP Headless smoke;
- core boundary and release consistency checks;
- syntax, diff, whitespace, documentation consistency, and protected worktree audit.

## Completion Record

### Architecture closure

- The active organism ID set is owned only by the complete-replacement table inside `PsRuntimeSnapshotAuthority`; configured initial population and progress counts are not identity Authorities after reproduction, death, or extinction.
- Discovery and query remain separate Interfaces. `runtime.ps.organism_discovery` accepts `{}` only to acquire the active opaque run and current identities. `runtime.ps.organism_snapshot` requires the full `track + run_id + organism_id` identity and never guesses selection.
- A standalone CLI/MCP process cannot inspect another process's editor worker. The deterministic null Adapter therefore returns `unavailable`; it does not fabricate cross-process state.
- The Host Module passes the deletion test: deleting it would spread editor-context lookup, Service lifecycle knowledge, Headless fallback, JSON-object validation, copy isolation, and discovery/query separation into Command handlers and future adapters.
- The Seam is real rather than hypothetical because it has two Adapters: the editor Service-backed Adapter and the deterministic null Adapter.

### Implemented Interfaces

- `PsRuntimeSnapshotAuthority.discover()` atomically returns `not_running` or the active run revision plus sorted full organism identities under one `RLock` critical section. Active extinction is represented as `ok` with zero identities, distinct from `not_running`.
- `PsExperimentService.discover_runtime_organisms()` is the narrow PyQt-bound source Interface; it does not expose Authority, Runner, Worker, Pond, Organism, QObject, QThread, callbacks, or registries.
- `ps_runtime_snapshot_host.py` defines Qt-free source/Host Protocols, `PsRuntimeSnapshotHostAdapter`, strict JSON-object/copy validation, and deterministic unavailable behavior.
- `PS_RUNTIME_SNAPSHOT_HOST = "simulation.ps_runtime_snapshot_host"` is registered independently from `PS_EXPERIMENT`; unload removes the Host before the Service.
- `runtime.ps.organism_discovery` and `runtime.ps.organism_snapshot` are read-only, GUI-optional, capability-scoped Command Registry Interfaces. MCP helpers use the same commands.
- `get_existing_editor_context()` performs non-creating context lookup. This fixes a real Headless lifecycle bug where a command helper could construct a half-initialized `EditorContext` without `QApplication` and later break panel construction.

### TDD and verification evidence

- Initial red collection failed as intended with `ImportError: cannot import name 'PS_RUNTIME_SNAPSHOT_HOST'`.
- Focused Authority/Service/Host/Command implementation suite: `39 passed in 0.71s`.
- Headless singleton fix plus PS panel smoke: `15 passed in 0.60s`.
- Broad PS/SR/Command/CLI/MCP regression: `133 passed, 8 subtests passed in 8.94s`.
- Phase 6K/6L/6N plus Inspector/WorldBridge combined regression: `146 passed in 2.95s`.
- Final targeted PS Authority/Runner/Service/Host/panel plus SR/WorldBridge/MCP composition run: `80 passed in 1.62s`.
- CLI describe/discovery smoke passed. Explicit snapshot smoke passed through `--json-file`; the first direct PowerShell JSON attempts failed only because shell quoting produced `invalid_json_payload`, not because of a runtime defect.
- Core boundaries, release consistency, Python syntax, strict UTF-8/replacement-character/literal-newline checks, scoped new-code whitespace checks, and `git diff --check` passed. Existing space-only docstring lines in `editor_context.py` were identified as prior formatting and were not mass-reformatted; the new non-creating lookup is clean.
- Final protected worktree audit is recorded as `995` entries, a net `+2` from Phase 6M: the Phase 6N plan and new Host/Command test are separate audit entries, while runtime changes and the handoff prompt remain inside existing aggregate paths. No unrelated path was staged, committed, reset, cleaned, reverted, deleted, or reorganized.

### Stable after this phase

- Truthful PS active-run/organism discovery and explicit run-scoped snapshot query.
- A Qt-free deep Host Interface with editor and null Adapters.
- Shared semantics across Command Registry, AI command CLI, and MCP helpers.
- Deterministic unavailable/not-running/stale/missing/invalid/unsupported states, strict JSON-only payloads, and copy isolation.
- Existing `.pond`, SR selected-identity command, WorldBridge runtime-wide diagnostics, Inspector binding, SR2D Adapter, manifests, PyQt6/QPainter defaults, and opt-in OpenGL direction remain unchanged.

### Explicitly unfinished

- No PS selected-organism concept or implicit snapshot query exists.
- SR and PS identities remain track-specific; there is no cross-track selected command or unified identity.
- Current SR/PS runtime snapshots have not yet been proven to map truthfully into the WorldBridge component vocabulary. Existing projection diagnostics remain read-only decision evidence, not live/lossless selected-entity component state.
- Inspector selected-entity component UI, mutation, `.pond` writeback, SR/PS tick merge, unified Pond default-readiness, native acceleration completion, and OpenGL default-readiness remain unclaimed.

**Unique next Gate: Phase 6O — track-specific runtime snapshot WorldBridge component projection mapping Authority decision/implementation.**
