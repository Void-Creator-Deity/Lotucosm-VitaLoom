# VitaLoom Phase 6K — SR Runtime Identity Snapshot Authority Implementation

## Goal

Implement a Qt-free, JSON-only SR runtime identity snapshot authority so a future selected-entity diagnostics Adapter can distinguish one live SR lifetime from another without reaching into `GameViewport`, `_SceneRuntimeEntity`, QWidget state, or mutable `.pond` objects.

This phase establishes identity and read-only snapshot authority only. It does not add selected-entity WorldBridge component semantics, live component mapping, Inspector mutation, `.pond` writes, PS organism authority, or unified SR/PS identity.

## Repository Truth to Preserve

- Product runtime boundary remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt6 remains the editor shell; QPainter remains default and OpenGL remains opt-in.
- `.pond`, Command Registry flows, Inspector edit binding, SR2D Adapter, manifests, and Phase 6I runtime-wide diagnostics stay compatible.
- `runtime.worldbridge.component_projection_diagnostics` remains runtime-wide with `{}` input.
- SR_PLAY and PS_BATCH remain separate tracks; PS stays `unavailable` for selected live identity until its own run-scoped authority exists.
- Preserve the existing migration worktree; do not stage, commit, reset, clean, revert, delete, or reorganize unrelated paths.

## Architecture Decision Carried Forward

Phase 6J selected current Option A and future Option C:

- Current selected-entity WorldBridge diagnostics remain unavailable.
- SR gets the first track-specific identity/snapshot authority.
- Stable live identity is `runtime_epoch + runtime_entity_id`, with `scene_path + entity_id` retained only as scene correlation where applicable.
- `runtime_epoch` is an opaque authority-created unique token, not `_sr_session_stamp`, a timestamp contract, or Python object identity.
- Epoch mismatch returns `stale` before any same-ID lookup.

## Planned Module and Interfaces

Create a small Qt-free Module under the VitaLoom simulation/core boundary (final filename may follow nearby package conventions) with one authoritative Implementation responsible for:

1. beginning an SR runtime lifetime and issuing an opaque epoch;
2. publishing a complete JSON-safe entity snapshot set for that epoch;
3. ending/discarding the lifetime without leaking the prior registry;
4. querying an entity snapshot by epoch and local ID;
5. producing deterministic `ok`, `not_running`, `stale`, `missing`, `invalid_identity`, and `error` results;
6. rejecting QWidget/QObject, bound methods, component objects, mutable live registries, and non-JSON values.

The Interface should be narrow and testable Headless. Candidate operations:

```text
begin(scene_path) -> runtime_epoch
publish(runtime_epoch, entity_snapshots) -> revision
query({track, runtime_epoch, scene_path, entity_id}) -> JSON envelope
end(runtime_epoch) -> ended/not_running/stale
```

Exact Python naming should match repository conventions, but behavior and failure ordering are contractual.

## GameViewport Adapter

`GameViewport` remains the owner of mutable `_SceneRuntimeEntity` Implementation objects. Add only a narrow Adapter that:

- starts a new authority lifetime whenever SR runtime state is newly created/reloaded;
- publishes whitelisted scalar/JSON-safe snapshot fields after authoritative lifecycle changes;
- ends the authority lifetime on stop/discard/project or scene replacement;
- never exposes `_SceneRuntimeEntity`, QWidget/QColor, component objects, or the mutable `scene_runtime_entities` dict;
- keeps runtime-created entities distinct from serialized `.pond` counterparts.

The Adapter must not make `_sr_session_stamp` the epoch and must not move editor ownership into the authority Module.

## Command Registry Boundary

If a read-only query command is added in this phase, it must be SR-specific, require the full epoch-scoped identity, and call only the authority Interface. It must not be named or presented as completed selected-entity WorldBridge component diagnostics.

The existing runtime-wide WorldBridge diagnostics command and Phase 6I Inspector foldout must remain unchanged. No Inspector UI wiring is part of Phase 6K.

## Snapshot Vocabulary

Minimum authority-owned response fields:

```json
{
  "schema_version": 1,
  "status": "ok",
  "scope": "selected_sr_runtime_entity",
  "authority": "sr_runtime_snapshot_authority",
  "track": "sr_play",
  "identity_relation": "scene_correlated_not_unified",
  "identity": {
    "runtime_epoch": "opaque-runtime-token",
    "scene_path": "scenes/example.pond",
    "entity_id": "entity_1"
  },
  "snapshot": {
    "source": "read_only_json_snapshot",
    "serialized_scene_counterpart": true
  }
}
```

Additional snapshot fields require explicit whitelisting and tests. Do not include behavior callables, arbitrary `__dict__`, component objects, or mutable references.

## Implementation Gates

### Gate A — Qt-free authority TDD

- Write failing tests for unique epochs, begin/end transitions, publish/query, stale-before-missing, missing, invalid identity, JSON safety, and snapshot copy isolation.
- Implement the smallest deep Module that passes them.
- Prove it imports while PyQt6 is blocked.

### Gate B — SR lifecycle Adapter

- Write failing lifecycle tests around start/reload/stop/discard and runtime-created entities.
- Wire GameViewport through a narrow Adapter without changing `.pond` semantics or SimulationTransport public behavior.
- Prove a previous epoch cannot query a reloaded same-ID entity.

### Gate C — Optional read-only command surface

- Only if Gates A/B yield a stable authority, add an SR-specific read-only query command and CLI/MCP exposure where consistent with existing command conventions.
- Validate full JSON schema and deterministic error envelopes.
- Do not wire the Inspector or claim WorldBridge component mapping.

### Gate D — Closure

- Run focused tests plus Phase 6I regression, core/release checks, diff check, and worktree audit.
- Record skips and evidence in `docs/mainline_status.md` and `docs/runtime_unification_roadmap.md`.
- Update this plan and the fresh-session prompt.
- Name exactly one next Gate.

## Acceptance Criteria

- A true opaque runtime epoch distinguishes reload/stop/start lifetimes, including same scene/entity IDs.
- The authority is Qt-free and JSON-only and owns no live GUI/runtime objects.
- `stale` is resolved before `missing`.
- Snapshot publication and query are copy-isolated from mutable source objects.
- GameViewport lifecycle wiring is narrow and preserves current play/stop/reload behavior.
- Runtime-created entities can be represented without inventing a `.pond` counterpart.
- Existing Phase 6I Inspector/runtime-wide diagnostics tests remain green.
- PS selected identity remains explicitly unavailable.
- No selected component mapping, mutation, `.pond` write, unified identity, native/OpenGL claim, stage, commit, reset, clean, or unrelated migration edit occurs.

## Verification Baseline

At minimum:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\python.exe -B -m pytest -q -p no:cacheprovider <new authority tests> <new lifecycle tests>
.\.venv\python.exe -B -m pytest -q -p no:cacheprovider `
  tests/test_inspector_worldbridge_diagnostics.py `
  tests/test_inspector_worldbridge_diagnostics_ui.py `
  tests/test_runtime_worldbridge_command_surfaces.py `
  tests/test_inspector_schema.py `
  tests/test_inspector_command_binding.py
.\.venv\python.exe -B tools/check_core_boundaries.py
.\.venv\python.exe -B tools/check_release_consistency.py
git diff --check
.\.venv\python.exe -B tools/audit_worktree_groups.py
git status --short
```

## First Action

Run `.\.venv\python.exe -B tools/audit_worktree_groups.py`, then write the Qt-free authority tests before modifying GameViewport.

## Completion Record — 2026-07-16

### Implemented Modules and Interfaces

- Added Qt-free `SrRuntimeSnapshotAuthority` at `core/VitaLoom/simulation/sr_runtime_snapshot_authority.py`. Its narrow Interface owns opaque epochs, complete snapshot replacement, copy-isolated JSON query, deterministic lifecycle/query statuses, and stale-before-missing ordering.
- Added the `GameViewport` Adapter methods `_begin_sr_snapshot_lifetime()`, `_publish_sr_runtime_snapshots()`, `_end_sr_snapshot_lifetime()`, `_build_sr_entity_snapshot()`, and `query_sr_runtime_entity_snapshot()`.
- Lifecycle wiring begins only after SR playback is accepted, preserves the epoch across ordinary pause/resume, replaces it on reload, and ends it on stop/discard.
- Initial serialized entity IDs are captured before runtime membrane/bootstrap creation. Runtime-created organisms, sensors, actuators, nutrients, and other generated entities therefore do not invent a serialized `.pond` counterpart.
- Publication uses a strict whitelist: identity/type, counterpart flag, position, velocity, radius, energy, generation, pinned, and membrane-locked state. Scripts, QColor, HUD dictionaries, component objects, callables, arbitrary attributes, and mutable registries do not cross the Seam.
- Snapshot publication occurs after the per-frame unified bridge tick and also on the empty-runtime path, so extinction replaces the prior snapshot set instead of leaving ghost entities.

### Optional Command Gate Decision

Gate C was evaluated and intentionally not implemented. The existing `SIMULATION_SR_HOST` Interface provides replay/ecology/transport behavior but no selected-SR identity acquisition or selection-correlation contract. Because the authority epoch is deliberately opaque, a standalone query command would require callers to possess an undiscoverable token and would be a shallow Interface.

The unblock path is explicit: first add a Qt-free SR selection identity Adapter that correlates current editor selection with `{track, runtime_epoch, scene_path, entity_id}` without exporting QWidget/live entities; then evaluate an SR-specific read-only Command Registry Interface. The existing `runtime.worldbridge.component_projection_diagnostics` command remains unchanged and runtime-wide.

### Verification Evidence

- Initial Authority suite: `16 passed in 0.12s`.
- Initial Adapter red: `5 failed` on missing lifecycle methods/epoch; first green: Authority + Adapter `21 passed in 0.92s`.
- Extinction consistency red: empty runtime still returned `ok`; after wiring empty snapshot publication, the combined Authority/Adapter/viewport suite passed `41 passed in 1.43s`.
- The first combined module-order run exposed a test-only deleted `EditorContext` QObject because the new QApplication fixture was module-scoped. Changing only the new fixture to the established session scope fixed test-order isolation.
- Final combined Phase 6K + GameViewport + Phase 6I/WorldBridge/Inspector regression: `79 passed in 1.43s`.
- `tools/check_core_boundaries.py` -> `core boundaries OK`.
- `tools/check_release_consistency.py` -> `release consistency OK`.
- `git diff --check` exited 0 with existing LF/CRLF conversion warnings only.
- Worktree audit before documentation closure: `986` dirty paths; no unrelated path was staged, committed, reset, cleaned, reverted, deleted, or reorganized.

### Stable and Unfinished

Stable: the epoch/snapshot Authority Module, GameViewport lifecycle Adapter, strict JSON whitelist, same-ID reload rejection, runtime-created counterpart semantics, and runtime-wide Phase 6I diagnostics.

Unfinished by design: selected-SR identity acquisition from editor selection, SR-specific command/CLI/MCP exposure, selected-entity WorldBridge projection, PS run/organism authority, SR↔PS correlation, mutation, and `.pond` writeback.

Phase 6K is complete. **Unique next Gate: Phase 6L — SR selected-identity acquisition and selection-correlation Interface decision/implementation.**
