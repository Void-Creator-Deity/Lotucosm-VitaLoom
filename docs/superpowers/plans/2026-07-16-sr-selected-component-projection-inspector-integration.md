# Phase 6P — Command-Backed SR Selected-Entity Component Projection Inspector Integration

**Date:** 2026-07-16  
**Status:** complete  
**Previous Gate:** Phase 6O — track-specific runtime snapshot WorldBridge component mapping Authority  
**Architecture focus:** add a deep, Qt-free selected-SR presentation Module and a thin read-only Inspector Adapter without weakening Command Registry authority

## 1. Gate objective

Integrate the existing read-only `runtime.sr.selected_entity_component_projection` Command Interface into the Inspector for exactly one current editor selection.

The result must let a maintainer inspect the currently correlated SR runtime entity's attachment-proven component projection while preserving ordinary Inspector properties and the existing runtime-wide WorldBridge diagnostics foldout. The UI must explain unavailable/not-proven/stale states truthfully; it must not infer live state from `.pond`, static entity type, configured counts, runtime-wide summary evidence, or historical metadata.

## 2. Previous Gate summary

Phase 6O established the live Authority path that this phase consumes:

- PS publishes strict `ps_component_registry` facts from the active organism registry.
- SR publishes strict `sr_attached_runtime_entity` facts only when runtime attachment registries prove sensor/actuator membership.
- `runtime_snapshot_component_projection.py` validates Mapping-only JSON envelopes, preserves track identity/revision/status, copy-isolates output, and returns `not_proven` when successful snapshots lack component evidence.
- `runtime.sr.selected_entity_component_projection` resolves selection through `ISrSelectedIdentityHost` and projects only the current SR Authority snapshot.
- SR projection identity relation remains `attached_projection_not_ps_component_equivalence`.

Phase 6O deliberately left the Inspector on runtime-wide diagnostics only.

## 3. Existing Inspector audit

### 3.1 Runtime-wide diagnostics remain a separate Module

`core/VitaLoom/inspector/worldbridge_diagnostics.py` owns the existing summary-only Adapter for:

```text
runtime.worldbridge.component_projection_diagnostics
```

Its scope is `runtime`, its payload rejects `components`, and its foldout explicitly states that it is not selected-entity component state. This Module and its public behavior remain compatible and unchanged.

### 3.2 Current UI flow

`InspectorPanel.update_properties()` currently:

- returns without loading diagnostics when there is no selection;
- appends ordinary properties and runtime-wide diagnostics for one selection;
- appends common properties and runtime-wide diagnostics once for multiple selections.

Selected-SR projection has exactly-one-selection semantics. The new Adapter is called only on the single-selection path, after ordinary properties and before/alongside the independent runtime-wide diagnostics append. Multiple selection and no selection must not invoke it.

## 4. Architecture decision

### 4.1 New deep Qt-free Module

Add:

```text
core/VitaLoom/inspector/sr_selected_component_projection.py
```

Public Interface:

```python
build_sr_selected_component_projection_view_model(command_result)
load_sr_selected_component_projection_view_model(registry=None)
```

The Interface owns:

- Command Registry-shaped result validation;
- strict JSON-only validation with no `repr()` fallback;
- command error normalization;
- SR guardrail validation;
- status/reason/identity/revision/component-count/coverage normalization;
- status-correlated validation of `maps_live_runtime_snapshot_facts`;
- deterministic component JSON presentation;
- `not_proven` semantics that never reinterpret missing evidence as zero components;
- copy isolation;
- warnings and read-only/collapse presentation metadata.

Deletion test: deleting this Module would scatter Command result validation, SR guardrails, identity/status semantics, component JSON formatting, and warnings into `InspectorPanel`; therefore it earns locality and leverage rather than acting as a pass-through.

### 4.2 Authority and guardrails

The only live Authority Interface is:

```text
runtime.sr.selected_entity_component_projection
```

Accepted successful payload guardrails:

```text
scope = runtime_snapshot_component_projection
track = sr_play
read_only = true
projection_state = runtime_snapshot_read_only_projection
maps_live_components = false
maps_live_runtime_snapshot_facts = true only when status = ok; false for not_proven/unavailable/error states
identity_relation = attached_projection_not_ps_component_equivalence
```

The Adapter does not import the projection Implementation, selected identity Host, viewport, Pond, organism, component objects, edit bindings, or PyQt.

### 4.3 View-model semantics

The view model exposes a read-only section titled:

```text
WorldBridge Components (Selected SR Runtime Entity)
```

It preserves these projected states when valid:

- `ok`
- `not_proven`
- `unavailable`
- `not_running`
- `stale`
- `missing`
- `invalid_identity`
- `unsupported_track`
- `error`

Core fields:

- scope;
- authority command;
- status and reason;
- track;
- projection state;
- identity relation;
- identity;
- revision;
- component count and count meaning;
- coverage;
- one deterministic JSON field per projected component;
- warnings.

For `status = ok`, `component_count = 0` means the selected SR Authority projection proved no attached projected components. For `status = not_proven`, component count remains unknown and the UI says evidence is unavailable rather than zero.

### 4.4 Inspector UI Adapter

Add a separate foldout:

```text
objectName = worldbridgeSrSelectedComponentProjectionGroup
```

Rules:

- append only for exactly one selection;
- keep ordinary properties visible if the command is unavailable or invalid;
- render unavailable/not-running/stale/missing/not-proven states as explicit read-only diagnostics rather than silently hiding them;
- default collapsed;
- all fields use read-only `QLineEdit` or `QPlainTextEdit` controls;
- do not add mutation callbacks;
- keep `worldbridgeRuntimeDiagnosticsGroup` unchanged and independently rendered.

The warning text must state:

```text
SR attachment projection; not PS Component equivalence.
```

## 5. TDD sequence

### 5.1 Qt-free Adapter red tests

Create:

```text
tests/test_inspector_sr_selected_component_projection.py
```

Red tests must prove:

1. the new Module does not yet exist;
2. the loader executes the Authority command exactly once;
3. malformed Command Registry envelopes are rejected;
4. non-JSON values, non-finite numbers, and live objects are rejected;
5. wrong track or guardrail violations are rejected;
6. a valid `ok` projection preserves identity/revision/count/coverage/components;
7. `not_proven` does not become zero components;
8. unavailable/error states remain deterministic and read-only;
9. input mutation after build cannot mutate the view model;
10. the Module imports no PyQt or live runtime Implementation.

### 5.2 Inspector UI red tests

Create:

```text
tests/test_inspector_sr_selected_component_projection_ui.py
```

Red tests must prove:

1. one selection appends the selected-SR foldout after ordinary properties;
2. the foldout is distinct from and coexists with runtime-wide diagnostics;
3. multiple selection does not call the selected-SR loader;
4. no selection does not call the selected-SR loader;
5. unavailable command state preserves ordinary properties;
6. controls are read-only and default-collapsed;
7. component JSON and warning semantics are visible when expanded;
8. the UI Adapter does not directly access Command Registry, edit binding, projection Implementation, selected identity Host, `.pond`, or mutation callbacks;
9. offscreen PyQt show/process-events/grab produces a non-null rendering artifact.

## 6. Verification gate

Minimum closure evidence:

- focused Qt-free Adapter tests pass;
- focused Inspector UI tests pass under `QT_QPA_PLATFORM=offscreen` using `.\.venv\python.exe`;
- existing runtime-wide Inspector diagnostics tests remain green;
- Phase 6O command/projection tests remain green;
- broader Inspector/selection/Command/CLI/MCP regression passes;
- a real offscreen `InspectorPanel.show()`, event processing, expansion, visibility assertion, and non-null `grab()` proves the widgets render;
- core boundary check passes;
- release consistency check passes;
- Python syntax/import smoke passes for changed runtime files;
- `git diff --check` exits 0 apart from already-known line-ending warnings;
- protected dirty-worktree audit is recorded without stage/commit/reset/clean/revert/delete.

## 7. Non-goals

This phase does not add:

- PS selection or PS Inspector projection;
- component mutation or Inspector edit binding;
- `.pond` writeback;
- live object exposure;
- PS/SR Component equivalence;
- lossless graph mapping;
- runtime-wide and selected projection merging;
- SR/PS tick merge;
- unified Pond default-ready claims;
- native acceleration completion claims;
- OpenGL default-ready claims;
- editor-shell migration away from PyQt6/QPainter.

## 8. Completion record

### 8.1 Implementation

- Added Qt-free `sr_selected_component_projection.py` as the deep presentation Module behind the Command Registry Seam.
- The Module validates strict JSON, SR track/scope/authority/identity guardrails, status-correlated `maps_live_runtime_snapshot_facts`, component counts, coverage totals, unique component IDs, component source/relation, and copy isolation.
- Added a distinct read-only Inspector foldout with object name `worldbridgeSrSelectedComponentProjectionGroup`.
- Exactly-one selection loads the selected-SR projection; multi-selection and no selection do not call it.
- Ordinary properties remain first, and the existing `worldbridgeRuntimeDiagnosticsGroup` remains separate and compatible.
- `not_proven` displays an unknown count rather than authoritative zero; unavailable/error states remain visible diagnostics instead of hiding ordinary properties.

### 8.2 TDD and rendering proof

- Baseline Phase 6O plus existing diagnostics suite: `27 passed in 0.99s`.
- Red evidence: both new test modules failed collection because `core.VitaLoom.inspector.sr_selected_component_projection` did not exist.
- Initial focused green: `30 passed in 0.61s`.
- Added real default-loader Headless Authority coverage; final focused composition: `58 passed in 1.11s`.
- Offscreen PyQt tests call `InspectorPanel.show()`, expand the selected foldout, process events, assert visibility, and prove `panel.grab().isNull() is False`.

### 8.3 Regression and guardrails

- Broad Inspector/SR/PS/snapshot/Command/CLI/MCP suite: `197 passed in 10.77s`.
- `core boundaries OK`.
- `GUI boundaries OK`.
- `release consistency OK`.
- Python syntax/import smoke passed for the two changed runtime files.
- `git diff --check` exited 0 with only pre-existing LF-to-CRLF warnings.
- Protected worktree total: `999`, net `+2` from Phase 6O's `997`; no stage/commit/reset/clean/revert/delete or unrelated reorganization occurred.

### 8.4 Stable versus unfinished

Stable now:

- command-backed selected-SR component projection presentation;
- strict Qt-free view-model validation and copy isolation;
- single-selection-only read-only foldout;
- explicit attachment-not-PS-equivalence warning;
- truthful `ok`, `not_proven`, unavailable, stale, missing, and error presentation;
- coexistence with runtime-wide diagnostics.

Still unfinished and not claimed:

- PS selection/Inspector projection;
- component mutation or `.pond` writeback;
- PS/SR Component equivalence or lossless graph mapping;
- SR/PS tick merge;
- unified Pond default readiness;
- native acceleration completion;
- OpenGL default readiness.

## 9. Unique next Gate after successful closure

**Phase 7 — asset database, export, and project-scale baseline/Authority decision.**


