# VitaLoom Phase 6L — SR Selected Identity Acquisition and Selection Correlation

## Goal

Create a truthful, Qt-free path from the editor's current `.pond` entity selection to the active SR runtime identity and its read-only snapshot. The phase must preserve the distinction between edit identity and live identity: correlation is allowed; unified identity is not.

Phase 6L begins only after Phase 6K's epoch-scoped `SrRuntimeSnapshotAuthority` is stable. It does not revisit the authority lifecycle or widen its snapshot whitelist.

## Previous Gate Summary

Phase 6K completed the Qt-free SR runtime snapshot Authority Module and the `GameViewport` lifecycle Adapter. It proved opaque epochs, complete replacement, copy isolation, stale-before-missing semantics, serialized counterpart marking, empty-runtime publication, and start/reload/pause-resume/stop lifecycle behavior.

The optional command Gate was intentionally rejected in Phase 6K because callers had no formal way to acquire an opaque epoch from editor selection. Phase 6L closes that discovery/correlation gap before any command is considered.

## Repository Truth to Preserve

- The product runtime remains under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt6 remains the editor shell; QPainter remains the default viewport backend; OpenGL remains opt-in.
- `.pond`, Inspector command binding, Command Registry, SR2D Adapter, package manifests, project manifests, and the runtime-wide WorldBridge diagnostics command remain compatible.
- Existing dirty paths are prior migration/user work. Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated changes.
- `SIMULATION_SR_HOST` currently serves replay/ecology/transport. Do not casually widen its runtime-checkable Interface and break existing Adapters/fakes.

## Audited Selection Truth

The editor selection Seam is heterogeneous:

- `SceneViewport` publishes PyQt-bound `selection_tool.Node` objects. For serialized scene nodes, `Node.id` is the `.pond` entity ID.
- `HierarchyPanel` publishes dictionaries shaped like `{"type": "entity", "id": ..., "data": ...}` or pond dictionaries.
- Other command/tool paths can publish strings or arbitrary objects through `EditorContext.set_selection`.
- `EditorContext` stores `List[Any]` and emits the live objects through a Qt signal.
- `InspectorPanel` consumes the heterogeneous objects and must not become the identity Authority.
- `SceneManager.get_current_scene_path()` and `GameViewport._sr_runtime_scene_path` are the two scene facts that must be correlated using one deterministic path rule.

Therefore no Qt-free Module may import `EditorContext`, `Node`, `HierarchyPanel`, `InspectorPanel`, `GameViewport`, QObject, or QWidget. A GUI-side projection Adapter must first convert the current selection into JSON-only facts.

## Identity Model

### Edit identity

```json
{
  "scene_path": "...",
  "entity_id": "..."
}
```

### SR live identity

```json
{
  "track": "sr_play",
  "runtime_epoch": "sr_...",
  "scene_path": "...",
  "entity_id": "..."
}
```

### Relation

```text
scene_correlated_not_unified
```

The correlation is valid only when:

1. exactly one serialized `.pond` entity is selected;
2. the selected edit scene matches the active SR scene under the Module's path normalization rule;
3. an SR epoch is active;
4. the current epoch snapshot contains the selected ID; and
5. the snapshot explicitly says `serialized_scene_counterpart: true`.

Runtime-created entities cannot be synthesized from ordinary scene selection. A same-ID entity from another scene or an old epoch must not resolve.

## Planned Modules and Interfaces

### 1. Qt-free correlation Module

Preferred file:

```text
core/VitaLoom/simulation/sr_selected_identity.py
```

The Module should expose one deep Interface that concentrates selection validation, single-selection rules, path correlation, active lifetime validation, authority query, counterpart validation, JSON copying, and deterministic status envelopes.

A candidate Interface is:

```python
class SrSelectedIdentityCorrelation:
    def resolve(
        self,
        selection_snapshot: object,
        runtime_context: object,
        query_snapshot: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> dict[str, Any]: ...
```

The final signature may change during TDD, but callers must not need to reproduce validation or status precedence. Apply the deletion test: deleting the Module should force this complexity to reappear in multiple callers, not simply remove a pass-through.

The Module must be importable while `PyQt6` imports are blocked.

### 2. GUI-side selection projection Adapter

A narrow Adapter may live in a new editor-facing Module or beside the selection consumer. Its responsibility is only to project live selection wrappers and the current scene path to JSON facts, for example:

```json
{
  "selection_count": 1,
  "items": [
    {
      "kind": "scene_entity",
      "scene_path": "...",
      "entity_id": "..."
    }
  ]
}
```

It may recognize `Node` and Hierarchy entity dictionaries, but it must not leak those objects across the Seam. Pond rows, string-only IDs, malformed dictionaries, connection lines, runtime entities, and arbitrary objects must remain explicitly unavailable rather than guessed.

### 3. SR runtime context Adapter

`GameViewport` may expose one narrow JSON-only method that returns or resolves the current selection against its Authority. It must not return the Authority object, the live entity list, mutable registries, or a QWidget.

Prefer a deep method that owns current epoch + scene + authority query correlation over several shallow getters. If a separate Protocol/service key is required, add it without widening `ISimulationSrHost` unless every existing Adapter and fake is intentionally migrated and tested.

## Deterministic Status Vocabulary

The public result must be JSON-only and copy-isolated. Expected statuses are:

- `ok`: one selected serialized entity correlates to a current SR snapshot;
- `unavailable`: no selection, multi-selection, non-entity selection, or selection wrapper without trustworthy scene entity identity;
- `not_running`: selection is valid but no SR lifetime is active;
- `stale`: an explicitly supplied prior live identity targets an old epoch;
- `missing`: the selected serialized entity is absent from the current snapshot set;
- `invalid_identity`: malformed projected identity or scene mismatch;
- `unsupported_track`: a non-SR track was explicitly requested;
- `error`: Adapter/authority failure represented without leaking Python exceptions or objects.

Status precedence must be tested. In particular, stale remains before missing for explicit old identities, and scene mismatch must not be reinterpreted as missing.

## Implementation Gates

### Gate A — Selection flow audit and plan lock

- Record the concrete selection shapes from SceneViewport, Hierarchy, commands/tools, EditorContext, and Inspector.
- Confirm how current scene paths enter SceneManager and GameViewport.
- Fix the projected JSON vocabulary and status precedence.

### Gate B — Headless TDD

Write failing tests before implementation for:

- no selection;
- multi-selection;
- non-entity object;
- string-only ID and malformed projection;
- SceneViewport `Node` projection;
- Hierarchy entity dictionary projection;
- pond selection rejection;
- selection/runtime scene mismatch;
- no active SR runtime;
- current `.pond` ID + current epoch → `ok`;
- reload makes an old explicit identity `stale`;
- selected serialized entity absent after extinction/removal → `missing`;
- runtime-created entity cannot claim an edit counterpart;
- JSON-only/copy-isolated result;
- import with PyQt6 blocked.

### Gate C — Implement correlation and runtime Adapter

- Implement the Qt-free Module.
- Implement only the minimum GUI projection and GameViewport Adapter needed to satisfy the Interface.
- Preserve all Phase 6K lifecycle and authority behavior.
- Add explicit errors; do not silently coerce arbitrary wrappers.

### Gate D — Conditional Command Registry Interface

Evaluate a dedicated read-only command only after Gate C is usable without caller knowledge of an epoch. A candidate command is:

```text
runtime.sr.selected_entity_snapshot
```

If implemented, it must:

- be `mutates: false`;
- accept JSON-only input (normally `{}` for current editor selection, or an explicitly documented prior identity query if justified);
- acquire the current selection through the projection Adapter;
- return the deterministic correlation/snapshot envelope;
- never expose live objects or mutable registries;
- remain separate from `runtime.worldbridge.component_projection_diagnostics`.

If the Command would require GUI-only discovery, hidden global coupling, or a shallow collection of pass-through getters, reject it and document the exact unblock path.

### Gate E — Closure

- Run focused Headless, GameViewport, Phase 6K, Phase 6I/WorldBridge/Inspector, schema, and binding regression.
- Run core boundary and release consistency checks.
- Run `git diff --check` and final worktree audit.
- Update this plan with a completion record, `docs/mainline_status.md`, `docs/runtime_unification_roadmap.md`, `docs/INDEX.md`, and the fresh-session prompt.
- Record skips/blockers with fallback and unblock paths.
- Name exactly one next Gate.

## Acceptance Criteria

- A caller can resolve the current editor-selected `.pond` entity to the active SR identity without knowing the opaque epoch in advance.
- The Qt-free Module owns validation, path correlation, status precedence, and result isolation behind a small Interface.
- SceneViewport and Hierarchy selections resolve consistently; heterogeneous or ambiguous selections fail deterministically.
- Runtime-created entities cannot be selected through fabricated `.pond` correlation.
- No QObject, QWidget, Node wrapper, live `_SceneRuntimeEntity`, Authority object, callable, or mutable registry crosses the JSON Seam.
- Existing Phase 6K Authority semantics and the runtime-wide WorldBridge diagnostics command remain unchanged.
- Any new command has direct tests for discovery, metadata, Headless behavior, statuses, and copy isolation; otherwise the rejection and unblock path are explicit.
- The phase closes with evidence and exactly one next Gate.

## Verification Baseline

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\python.exe -B -m pytest -q -p no:cacheprovider `
  tests/test_sr_selected_identity.py `
  tests/test_game_viewport_sr_selected_identity.py
.\.venv\python.exe -B -m pytest -q -p no:cacheprovider `
  tests/test_sr_runtime_snapshot_authority.py `
  tests/test_game_viewport_sr_runtime_snapshot_authority.py `
  tests/test_game_viewport_unified_bridge.py `
  tests/test_game_viewport_play_goals.py `
  tests/test_game_viewport_ecology_snapshot.py `
  tests/test_simulation_driver.py `
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

Audit the exact selection wrapper shapes and scene-path facts, then write the Headless failing tests before changing runtime code.

## Completion Record — 2026-07-16

### Outcome

Phase 6L is complete. The editor can now correlate one trustworthy serialized `.pond` selection with the active SR epoch and read a copy-isolated runtime snapshot without requiring the caller to know the opaque epoch. The result remains explicitly `scene_correlated_not_unified`; no cross-track or unified identity was introduced.

### Architecture decisions closed

- The heterogeneous editor selection flow is projected in a GUI-side Adapter before it reaches any Qt-free Module. `SceneViewport` `Node` selections and consistent Hierarchy entity wrappers are supported; pond rows, strings, arbitrary objects, malformed wrappers, missing scene paths, zero selection, and multi-selection are never guessed.
- `SrSelectedIdentityCorrelation` is the deep Qt-free Module. Its Interface owns selection validation, scene-path correlation, runtime-context validation, opaque epoch acquisition, Authority queries, explicit old-identity handling, serialized-counterpart validation, deterministic envelopes, and JSON/copy isolation.
- Edit identity remains `scene_path + entity_id`. SR live identity remains `track + runtime_epoch + scene_path + entity_id`.
- `ISimulationSrHost` was not widened. A separate `ISrSelectedIdentityHost` Protocol and `SR_SELECTED_IDENTITY_HOST` service key preserve replay/ecology/transport Adapters and fakes.
- `GameViewport` is the GUI/runtime Adapter. It reads current editor selection and SceneManager path, combines them with its active SR epoch/scene, and delegates to the Qt-free correlation Module plus the Phase 6K Authority query Interface.
- Runtime-created SR entities cannot claim a serialized edit counterpart; a snapshot must explicitly contain `serialized_scene_counterpart: true`.
- Scene mismatch is `invalid_identity`, current absence is `missing`, and explicit old epochs retain the Authority's stale-before-missing ordering.

### Implemented Interfaces

- `core/VitaLoom/simulation/sr_selected_identity.py`
  - `SrSelectedIdentityCorrelation.resolve(...)`
- `core/VitaLoom/simulation/sr_editor_selection_adapter.py`
  - `project_editor_selection(...)`
- `core/VitaLoom/simulation/sr_selected_identity_host.py`
  - `ISrSelectedIdentityHost`
  - deterministic null Adapter for Headless/unregistered contexts
- `core/VitaLoom/core/service_keys.py`
  - `SR_SELECTED_IDENTITY_HOST`
- `core/VitaLoom/viewports/game_viewport.py`
  - `resolve_selected_sr_runtime_entity(...)`
  - registration under both the existing SR host key and the independent selected-identity host key

### Conditional Command Gate

The command Gate passed because `{}` can discover current selection through the dedicated host Seam without caller knowledge of the opaque epoch. Added:

```text
runtime.sr.selected_entity_snapshot
```

The command is `mutates: false`, `requires_gui: false`, capability-scoped to `vitalloom.engine.sr2d`, JSON-only, read-only, and separate from `runtime.worldbridge.component_projection_diagnostics`. `{}` performs current-selection discovery when a real editor Adapter is registered. Optional `identity` forwards an explicit prior SR identity so reload behavior can be proven as `stale`. Headless or unregistered contexts return deterministic `unavailable` rather than importing GUI code or raising.

A real end-to-end test proves:

```text
Command Registry
  -> SR_SELECTED_IDENTITY_HOST Seam
  -> GameViewport Adapter
  -> SrSelectedIdentityCorrelation
  -> SrRuntimeSnapshotAuthority
```

### Verification evidence

- Qt-free correlation and GUI projection tests: `17 passed`.
- GameViewport Adapter plus dedicated service registration and Registry-to-Viewport end-to-end proof: `5 passed`.
- Command metadata, discovery, explicit stale query, copy isolation, null Adapter, and PyQt6-blocked subprocess proof: `6 passed`.
- Final focused Phase 6L + Phase 6K Authority regression: `50 passed in 1.29s`.
- Final expanded SR/WorldBridge/Inspector/schema/binding regression: `103 passed in 2.27s`.
- `tools/check_core_boundaries.py`: `core boundaries OK`.
- `tools/check_release_consistency.py`: `release consistency OK`.
- `git diff --check`: exit `0`; only pre-existing LF-to-CRLF warnings were emitted.
- Final protected worktree audit: `990` dirty paths; no stage, commit, reset, clean, revert, deletion, or unrelated migration reorganization was performed.
- The plan's historical `tests/test_simulation_driver.py` baseline path does not exist. Verification used the actual same-contract file `tests/test_simulation_driver_viewport_tick.py`; this was a path correction, not a skipped behavior.

### Stable after this phase

- Phase 6K opaque SR epoch and snapshot Authority semantics.
- Trustworthy Node/Hierarchy edit-selection projection to JSON facts.
- Current selection to active SR identity correlation without epoch input.
- Explicit old SR identity queries with stale-before-missing behavior.
- Independent selected-identity host Seam and deterministic Headless fallback.
- Read-only SR selected-entity snapshot Command Registry Interface.
- Existing runtime-wide WorldBridge diagnostics command, Inspector command binding, `.pond` semantics, manifests, SR2D Adapter seams, PyQt6 editor shell, QPainter default viewport, and opt-in OpenGL path remain unchanged.

### Explicitly unfinished

- PS `run_id + organism_id` lifetime authority and snapshot Interface.
- SR-to-PS live identity correlation or unified identity.
- Selected-entity WorldBridge component mapping.
- Inspector selected-runtime-entity UI.
- Runtime mutation, `.pond` writeback, SR/PS tick merge, unified Pond default-ready status, native acceleration completion, or OpenGL default-ready status.

## Unique Next Gate

**Phase 6M — PS run/organism runtime identity snapshot Authority decision/implementation.**

Phase 6M must first audit the true `PsExperimentRunner`/`PsExperimentService` ownership and sync/async lifecycle. It may establish an opaque `run_id`, a Qt-free JSON-only snapshot Authority, and the narrowest truthful Adapter. It must not jump to SR↔PS unified identity, selected WorldBridge component mapping, Inspector mutation, `.pond` writeback, or a cross-track selected command.
