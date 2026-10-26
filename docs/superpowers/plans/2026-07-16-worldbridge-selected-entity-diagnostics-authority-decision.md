# VitaLoom Phase 6J — Selected-Entity WorldBridge Diagnostics Authority/Interface Decision

## Goal

Decide whether VitaLoom can expose selected-entity WorldBridge diagnostics through a trustworthy, command-backed Interface without inventing live component state, bypassing `.pond` semantics, or coupling Inspector widgets to SR/PS Implementation objects.

This is a **decision-only Gate**. It may produce a decision record, contract draft, risk matrix, tests of existing read-only Interfaces, and the next implementation plan. It must not add selected-entity command behavior, live component mapping, Inspector mutation, or `.pond` writes.

## Repository Truth to Preserve

- Product runtime remains under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- The five layers and two plugin scopes in `CONTEXT.md` remain unchanged.
- `runtime.worldbridge.component_projection_diagnostics` remains runtime-wide, summary-only, read-only, and has `{}` input.
- The Phase 6I Inspector foldout consumes the Qt-free diagnostics view-model and must not be reinterpreted as selected-entity state.
- SR_PLAY and PS_BATCH keep separate tick semantics. WorldBridge remains a narrow Seam rather than a claim of unified runtime identity.
- Existing `.pond`, Command Registry, Inspector edit binding, SR2D Adapter, package manifests, project manifests, QPainter default, and OpenGL opt-in rules stay intact.
- Preserve the existing migration worktree; do not stage, commit, reset, clean, revert, delete, or reorganize unrelated paths.

## Decision Questions

1. **Authority:** Which existing Module, if any, can truthfully answer a selected-entity diagnostics query: `.pond` scene data, `SceneRuntimeEntity`, an SR runtime registry, PS organisms, WorldBridge projection evidence, or a composed read-only Adapter?
2. **Identity:** What stable input can cross the Command Registry Seam without passing Python/Qt/live component objects: project identity, scene path/id, entity id, runtime track, run id, or an explicit projection snapshot id?
3. **Scope:** Can one Interface cover SR_PLAY and PS_BATCH without hiding their different identity and lifetime rules, or must selected-entity diagnostics be track-specific?
4. **Output:** Which fields are evidence-backed and JSON-safe? Which claims must remain forbidden, especially live behavior, lossless graph mapping, and selected-entity equivalence across SR/PS?
5. **Command shape:** Should a future phase add a new command, keep runtime-wide diagnostics only, or introduce an explicit query Adapter? Extending the existing `{}` command is not allowed unless semantic compatibility is proven.
6. **Failure semantics:** How should missing entity, stale scene/run identity, unavailable track, and unproven mapping be represented without removing ordinary Inspector properties?

## Options to Evaluate

| Option | Interface | Main risk |
|---|---|---|
| A. Keep runtime-wide only | No selected-entity command is introduced. | Less UI detail, but no false authority. |
| B. New read-only selected-entity command | Stable JSON identifiers in; evidence-backed summary out. | Requires a real authority and explicit SR/PS scope. |
| C. Track-specific commands/Adapters | SR and PS expose separate read-only query Interfaces. | More Interfaces, but avoids fake unification. |
| D. Extend the existing runtime-wide command | Add optional selected-entity input to the current command. | High semantic drift and compatibility risk; presume reject unless evidence overturns it. |

## Required Audit

1. Run `python -B tools/audit_worktree_groups.py` and record the dirty total.
2. Read `CONTEXT.md`, ADR-0005, the final Phase 6I plan/status/roadmap sections, and the Phase 6I diagnostics Adapter/UI tests.
3. Trace selected-object identity from Hierarchy/selection through Inspector into `.pond` scene data.
4. Trace SR runtime entity identity and lifecycle in SceneRuntime/GameViewport/SimulationTransport.
5. Trace PS organism/run identity and WorldBridge projection construction.
6. Inventory existing Command Registry schemas that accept project/scene/entity/run identifiers; reuse established vocabulary where truthful.
7. Build an authority matrix: source, lifetime, stable key, track, fields available, fields absent, stale/error modes, and whether it can support Headless tests.
8. Apply the deletion test to any proposed Adapter: it must concentrate validation/scope/error complexity rather than merely rename one call.

## Acceptance Criteria

- One option is selected with evidence, or the decision explicitly remains “runtime-wide only” because no trustworthy selected-entity authority exists.
- The decision defines exact JSON input vocabulary, scope labels, output claims, guardrails, and error modes for any future Interface.
- No QWidget, QObject, live component object, bound method, or mutable scene object crosses the proposed Seam.
- The decision states whether SR and PS identities are unified, correlated, or intentionally separate.
- Existing Phase 6I tests remain green; relevant WorldBridge/Inspector command tests and architecture checks pass.
- `docs/mainline_status.md`, `docs/runtime_unification_roadmap.md`, this plan, and a fresh-session prompt record the result and name exactly one next Gate.

## Verification Baseline

At minimum, rerun:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\python.exe -B -m pytest -q -p no:cacheprovider `
  tests/test_inspector_worldbridge_diagnostics.py `
  tests/test_inspector_worldbridge_diagnostics_ui.py `
  tests/test_runtime_worldbridge_command_surfaces.py `
  tests/test_worldbridge_component_projection.py `
  tests/test_inspector_schema.py `
  tests/test_inspector_command_binding.py
.\.venv\python.exe -B tools/check_worldbridge_component_projection_diagnostics.py
.\.venv\python.exe -B tools/check_core_boundaries.py
.\.venv\python.exe -B tools/check_release_consistency.py
```

Decision documentation must distinguish verified current behavior from proposed future behavior. Do not claim a selected-entity Interface exists merely because Inspector has a selected object.

## First Action

Run `python -B tools/audit_worktree_groups.py`, then inspect the selected-object identity flow and WorldBridge projection authority before proposing a command schema.
## Final Decision — 2026-07-16

### Executive Result

Phase 6J selects a staged answer:

1. **Current product behavior remains Option A: runtime-wide only.** No selected-entity WorldBridge diagnostics command is approved because neither SR_PLAY nor PS_BATCH currently exposes a trustworthy, run-scoped, JSON-safe live-object authority.
2. **The approved future architecture is Option C: track-specific read-only Interfaces/Adapters.** SR and PS must establish their own lifetime authority before either track can expose selected-object diagnostics.
3. **Option D is rejected.** `runtime.worldbridge.component_projection_diagnostics` keeps its stable `{}` input and runtime-wide/static evidence semantics; selected identity must never be added as an optional interpretation of that command.
4. **Option B is deferred rather than approved.** A single cross-track selected-entity command would hide materially different identity and lifetime rules and would encourage a false unified-identity claim.

The identities are **intentionally separate but optionally correlated**. WorldBridge may carry an explicit correlation inside a known live lifetime, but it is not an identity authority.

### Evidence Trace

The audit followed the real Implementations rather than the Inspector presentation:

- `.pond` selection: `core/VitaLoom/docks/scene_outline.py` wraps mutable scene data as `{"type": "entity", "data": ..., "id": ...}` and sends it through `EditorContext`; the reliable edit-time key is `scene_path + entity_id`, not the wrapper object.
- SR_PLAY: `core/VitaLoom/viewports/game_viewport.py` owns `scene_runtime_entities` and its private `_SceneRuntimeEntity` objects. Initial entities reuse `.pond` IDs, while runtime-only entities receive IDs such as `game_spawn_00001` and `evo_organism_00001`. Stop, project change, and scene reload discard and rebuild the registry. `_sr_session_stamp` is logging state, is reset on discard, has only second-level time precision, and is not a public epoch Interface.
- SR transport/host: `simulation_transport.py` exposes play/pause/speed only; `simulation/sr_host.py` exposes aggregate ecology data only. Neither is a per-entity authority.
- PS_BATCH: `core/Lotucosm/pond.py` owns `Pond.organisms` only within one Pond lifetime. The experiment runner keeps the live Pond inside a local runner or worker thread, while `ps_experiment_service.py` exposes aggregate progress/summary state. There is no live organism registry Interface and no run-scoped `run_id`.
- WorldBridge: `core/Lotucosm/runtime/world_bridge.py` stores `_world_bridge_organism_id` on a live SR Python object and resolves it in the current Pond. `bridge_{entity_id}` is a lifetime-local correlation, not a global or persistent identity.
- Projection diagnostics: `world_bridge_component_projection.py` builds runtime-wide decision/projection evidence. The command handler invokes it without live components, so `component_count = 0`, `maps_live_components = false`, and `default_ready = false` do not describe the selected Inspector object.

### Authority Matrix

| Candidate source | Lifetime / owner | Available stable key | Evidence available | Missing authority | Headless suitability | Decision |
|---|---|---|---|---|---|---|
| `.pond` scene entity | Serialized scene / `SceneManager` | `scene_path + entity_id` | Edit-time entity data | No live run, epoch, runtime-only entity, or live component state | Yes | Valid edit identity and correlation only |
| Inspector selection wrapper | GUI selection event | Nested scene/entity data only | Current presentation object | Mutable dict, no scene/run lifetime, Qt/GUI ownership | No | Must not cross Command Registry Seam |
| `GameViewport.scene_runtime_entities` | One SR GameViewport run | Current registry key / entity ID | Real mutable SR state | No public unique epoch; private QWidget-owned entity type | No, as implemented | Current Implementation authority, not a stable Interface |
| `SimulationTransport` / `ISimulationSrHost` | Editor simulation service | Lane state only | Play/pause/speed and aggregate ecology | No entity registry, epoch, or per-entity snapshot | Partial | Insufficient |
| `Pond.organisms` | One Pond instance | Pond-local `organism_id` | Real mutable PS organism state | No service-visible Pond lifetime token or thread-safe snapshot | No, as exposed | Current Implementation authority, not a command Interface |
| `PsExperimentService` | One service / worker lifecycle | No formal run ID | Aggregate metrics, last summary/output | No live organism lookup or stable run identity | Yes for aggregates | Insufficient |
| `_world_bridge_organism_id` | One pair of live Python objects / Pond | `bridge_{entity_id}` | Optional SR→PS lookup correlation | No scene, epoch, run ID, persistence, or stale detection | No | Correlation only |
| Projection diagnostics command | Runtime-wide static decision evidence | Command ID with `{}` | Coverage/guardrails/do-not-claim summary | No selected identity or live components | Yes | Remains stable runtime-wide authority |

### Identity and Lifetime Decision

| Domain | Required future identity | Meaning | Reuse rule |
|---|---|---|---|
| `.pond` edit entity | `scene_path + entity_id` | Serialized edit-time object | May correlate to SR, but does not identify a live lifetime |
| SR live entity | `runtime_epoch + scene_path + entity_id` or `runtime_epoch + runtime_entity_id` | Entity snapshot inside exactly one SR runtime lifetime | Epoch mismatch is `stale`; never fall through to the current same-name entity |
| PS live organism | `run_id + organism_id` | Organism snapshot inside exactly one PS run/Pond lifetime | Run mismatch is `stale`; Pond-local ID alone is insufficient |
| SR↔PS relationship | Explicit correlation record scoped by both live lifetimes | Optional bridge association | Never promoted to unified identity |

`runtime_epoch` and `run_id` must be opaque tokens created by their runtime authorities. They must not be timestamps supplied by the Inspector, Python object IDs, or values reconstructed from scene/entity names.

### Option Resolution

| Option | Resolution | Reason |
|---|---|---|
| A. Keep runtime-wide only | **Selected now** | This is the only truthful current behavior while no run-scoped authority exists. |
| B. One new selected-entity command | **Deferred / not approved** | One schema cannot currently cover SR and PS without hiding different lifetime semantics. |
| C. Track-specific read-only Interfaces | **Approved future direction** | Preserves track semantics, locality, Headless testing, and explicit stale handling. |
| D. Extend current `{}` command | **Rejected** | Would mix stable runtime-wide evidence with selected live state and silently change the established Interface. |

### Future JSON Interface Vocabulary

These are contracts for future track-specific Adapters; **they are not implemented by Phase 6J**.

#### SR request

```json
{
  "track": "sr_play",
  "runtime_epoch": "opaque-runtime-token",
  "scene_path": "project-relative-or-normalized-scene-path",
  "entity_id": "scene-or-runtime-entity-id"
}
```

Required invariants:

- `track` is exactly `sr_play`.
- `runtime_epoch` is issued by the SR authority and is mandatory.
- `scene_path + entity_id` is correlation vocabulary, not a substitute for the epoch.
- Runtime-created entities may have no serialized `.pond` counterpart; the response must label that explicitly rather than inventing one.

#### PS request

```json
{
  "track": "ps_batch",
  "run_id": "opaque-run-token",
  "organism_id": "pond-local-organism-id"
}
```

This request remains unavailable until PS has an explicit run authority and a thread-safe organism snapshot Adapter.

#### Common response envelope

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
  },
  "diagnostics": {
    "selected_component_projection_available": false,
    "maps_live_components": false
  },
  "warnings": []
}
```

The envelope may expose only JSON-safe, authority-captured fields. Phase 6K may establish identity/lifecycle snapshots, but selected component payload vocabulary remains closed until a later mapping-authority Gate proves it.

### Failure Semantics

| Status | Meaning | Required behavior |
|---|---|---|
| `unavailable` | Track authority does not exist or is not initialized | Return a safe read-only envelope; do not infer from `.pond` or UI state |
| `not_running` | The track has no current live run | Do not treat serialized scene data as live runtime state |
| `stale` | Supplied epoch/run token differs from the active lifetime | Stop before entity lookup; never resolve the current object with the same local ID |
| `missing` | Lifetime token is valid, but the named entity/organism is absent | Return identity and code only; do not fabricate an empty component list |
| `unsupported_track` | Track is not `sr_play` or `ps_batch` | Reject deterministically |
| `invalid_identity` | Required identity field is absent or malformed | Reject before authority access |
| `error` | Authority failed internally | Preserve ordinary Inspector properties and surface a sanitized code/message |

`stale` has precedence over `missing`: an old lifetime request cannot be reinterpreted against the current registry.

### Allowed and Forbidden Claims

Allowed after an authority has proved them:

- which track and authority produced the snapshot;
- the opaque lifetime token and local entity/organism ID;
- whether a serialized scene counterpart exists;
- JSON-safe fields captured by that authority;
- explicit optional correlation state scoped to known lifetimes.

Forbidden until separately proven:

- `selected_pond_entity_live_components`;
- `unified_sr_ps_identity`;
- `lossless_component_mapping`;
- `live_component_graph`;
- selected PS organism state without `run_id` authority;
- treating `.pond` selection, QWidget/QObject state, Python `id(obj)`, a mutable entity/organism dict, or `_world_bridge_organism_id` as a stable cross-Seam identity.

### Locality, Leverage, and Deletion Test

The next Module must concentrate runtime-epoch generation, lifecycle transitions, JSON snapshot validation, stale-before-missing ordering, and lookup semantics behind a small Qt-free Interface. GameViewport is an Adapter that publishes state; it must not become the command schema.

Deletion test: if removing the Module would force epoch/stale/snapshot logic back into GameViewport, command handlers, and Inspector code, the Module has real leverage. A wrapper that merely renames `scene_runtime_entities.get(entity_id)` fails this test.

## Phase 6J Closure

Phase 6J adds no runtime command, selected-entity behavior, live component mapping, Inspector mutation, or `.pond` write. Existing runtime-wide diagnostics remain the only shipped WorldBridge diagnostics Interface.

**Unique next Gate: Phase 6K — SR runtime identity snapshot authority implementation.**

## Verification Evidence

- Starting worktree audit: `tools/audit_worktree_groups.py` and `git status --short` both reported `984` dirty paths. No unrelated path was staged, committed, reset, cleaned, reverted, deleted, or reorganized.
- Focused Phase 6I/WorldBridge regression: `38 passed in 3.09s`.
- `tools/check_worldbridge_component_projection_diagnostics.py` exited 0 and confirmed runtime-wide read-only evidence with `component_count: 0`, `maps_live_components: false`, and `default_ready: false`.
- `tools/check_core_boundaries.py` -> `core boundaries OK`.
- `tools/check_release_consistency.py` -> `release consistency OK`.
- Final diff/worktree evidence: `git diff --check` passed; final audit total `984` (the only newly named paths are the Phase 6K plan and prompt; pre-existing migration state remains untouched).
