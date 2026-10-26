# Phase 6I Command-Backed WorldBridge Inspector Diagnostics Implementation Plan

## Summary

Implement the Phase 6H-approved read-only Inspector diagnostics foldout without creating a UI-only semantics path. The Command Registry remains authoritative; a pure view-model Adapter isolates command result validation and presentation from PyQt6 widgets.

## Architecture Decision Inherited From Phase 6H

- Authority command: `runtime.worldbridge.component_projection_diagnostics`.
- Scope: runtime-wide projection diagnostics, not selected-entity state.
- Presentation: dedicated read-only Inspector foldout with explicit authority and scope labels.
- No direct import of the WorldBridge projection builder from Inspector UI.
- No editable widgets, mutation commands, `.pond` writes, live objects, or behavior calls.

## Gate A: Headless View-Model Adapter

Create a Qt-free Module under `core/VitaLoom/inspector/` that:

1. accepts a Command Registry-shaped result;
2. validates `ok`, `read_only`, `maps_live_components`, and `default_ready`;
3. returns deterministic Inspector section/view-model data;
4. retains `coverage`, safe fields, forbidden behavior, and do-not-claim warnings;
5. labels `scope: runtime` and the authority command ID;
6. produces a safe unavailable state for command errors;
7. ignores or rejects a `components` list and live/non-JSON objects.

Write Headless tests first.

## Gate B: Command Runner Seam

Add a small Adapter that invokes exactly:

```text
runtime.worldbridge.component_projection_diagnostics
```

with `{}` through `get_command_registry().run(...)`.

Tests must prove:

- one command invocation;
- no projection-builder import;
- no edit binding or mutation command;
- error isolation.

## Gate C: Inspector UI Integration

Add a dedicated collapsed-by-default read-only foldout to `InspectorPanel` after normal object properties are built.

Requirements:

- title and hint state that evidence is runtime-wide;
- authority command ID is visible;
- all fields are read-only;
- `component_count: 0` is described as “no components in current projection evidence”, not “selected entity has no components”;
- diagnostics failure does not remove or disable ordinary Inspector fields;
- normal property edit/undo behavior is unchanged.

## Gate D: Verification

Required Headless checks:

- view-model tests;
- command runner tests;
- Inspector schema and edit-binding regressions;
- WorldBridge diagnostics command/tool/CLI parity;
- package import side-effect guard;
- core boundaries and release consistency.

Required UI evidence before claiming completion:

- PyQt6 import and Inspector construction;
- a real foldout renders with read-only controls;
- ordinary entity properties remain visible;
- command failure fallback renders without crashing;
- screenshot or widget-tree proof.

If PyQt6 remains unavailable, implement and verify only the pure Adapter/command Seam, record UI integration as unavailable, and do not claim Phase 6I complete.

## Non-Goals

- selected-entity component graph mapping;
- live component objects;
- `.pond` mutation;
- changing `world_bridge.py` or `Pond.update`;
- unified Pond default readiness;
- SR/PS tick merge;
- OpenGL or native acceleration work.

## Phase Closure

Update `docs/mainline_status.md`, ADR/roadmap if semantics change, this plan evidence, and a fresh-session prompt. Name exactly one next Gate.

## Phase 6I Gate A/B Completion Evidence (2026-07-15)

### Status

**Partially complete:** Gate A (Headless view-model Adapter) and Gate B (Command Runner Seam) are complete. Gate C (Inspector UI integration) remains unavailable because no working PyQt6 interpreter exists in the current environment.

### Implemented

- Added `core/VitaLoom/inspector/worldbridge_diagnostics.py` as a Qt-free deep Module.
- Added an immutable `WorldBridgeDiagnosticsViewModel` and deterministic JSON-safe `to_dict()` surface.
- The Adapter labels `scope: runtime`, exposes the authority command ID, preserves projection coverage/safe fields/forbidden behavior/do-not-claim warnings, and marks every Inspector field read-only.
- `component_count: 0` is described as no components in the **current runtime projection evidence** and never as selected-entity state.
- Guardrail mismatches for `read_only`, `maps_live_components`, or `default_ready` produce a read-only unavailable state.
- A `components` key is rejected. Non-JSON/live values are rejected before presentation.
- Command errors and registry exceptions are reduced to safe code/message-only unavailable states.
- The runner invokes `runtime.worldbridge.component_projection_diagnostics` exactly once with `{}`. It does not import the projection builder or Inspector edit binding.

### TDD and Verification

| Check | Result |
|---|---|
| TDD red | New test collection failed because `core.VitaLoom.inspector.worldbridge_diagnostics` did not exist. |
| New Headless Adapter/runner suite | `10 passed in 0.23s`. |
| Combined Phase 6I A/B regression | Package imports + WorldBridge command/projection/tool + Inspector schema/binding + new diagnostics Adapter → `39 passed in 1.81s`. |
| Diagnostics authority tool | Exited 0; summary-only, `read_only: true`, `maps_live_components: false`, `default_ready: false`, `component_count: 0`. |
| Direct CLI authority smoke | Exited 0 with the same command result and no `components` payload. |
| Architecture guardrails | `core boundaries OK`; `release consistency OK`. |
| Compile proof | Temporary-pycache `compileall` for the new Module and tests exited 0. |
| Scoped whitespace check | New Module and tests passed `git diff --check`. |
| Final worktree audit | Dirty total `983`; the new test path accounts for the one-path increase from the starting snapshot. No unrelated work was staged, committed, reset, cleaned, reverted, or deleted. |

### Gate C Environment Blocker

- Active Python: `D:\app\anaconda3\python.exe` (Python 3.13.5).
- `import PyQt6` fails with `ModuleNotFoundError`.
- `py -0p` exposes only the Python 3.13 interpreter.
- `conda env list` exposes only the base environment.
- Repository `.venv` is broken and still points to a missing `%LOCALAPPDATA%\Programs\Python\Python311\python.exe`.

Fallback: keep the new pure Adapter/runner unconnected to `InspectorPanel`; existing Inspector properties and edit/undo behavior therefore remain unchanged.

Unblock path: provide or repair a PyQt6-capable interpreter, then implement the collapsed-by-default foldout in `core/VitaLoom/docks/inspector.py` and collect real widget-tree/screenshot evidence for success and command-failure states.

No `.pond`, WorldBridge projection Implementation, command mutation surface, package manifest, project manifest, SR2D Adapter, QPainter/OpenGL policy, or five-layer plugin architecture semantics changed.

**Unique next Gate: Phase 6I-C — real PyQt6 Inspector foldout integration and rendering evidence.**

## Phase 6I-C Execution Addendum (2026-07-16)

### Environment Gate

1. Preserve the `983`-path migration worktree; do not stage, commit, reset, clean, revert, or reorganize unrelated files.
2. Replace only the ignored, broken repository `.venv` with an isolated Python 3.11 conda prefix.
3. Install the project with `-e ".[dev]"` and prove PyQt6 >= 6.10 can construct an offscreen `QApplication` before editing Inspector widgets.
4. If environment provisioning fails, stop UI work and record the blocker rather than claiming UI completion.

### UI Integration Decision

- Add one private `InspectorPanel._append_worldbridge_runtime_diagnostics()` Adapter.
- Invoke `load_worldbridge_diagnostics_view_model()` exactly once after ordinary single-selection or multi-selection properties are built.
- Keep no-selection Inspector behavior empty and do not invoke the diagnostics loader for an empty selection.
- Render only `view_model.section.fields`, plus a JSON warnings row when warnings exist.
- Use read-only controls and stable object names under the `worldbridgeRuntimeDiagnostics*` namespace.
- Add all rows before applying the view-model's collapsed-by-default state.
- Do not add refresh buttons, polling, selected-entity inputs, mutation bindings, projection imports, `.pond` writes, or component behavior calls.

### Required UI Evidence

- Offscreen PyQt6 construction with `panel.show()` and event processing.
- Ordinary Inspector fields remain present before and after diagnostics command failure.
- Runtime scope, authority command, guardrails, do-not-claim fields, warnings, and the runtime-projection meaning of `component_count: 0` are present.
- Single-selection, multi-selection, unavailable-command, and no-selection behavior are covered by deterministic widget-tree tests.
- Phase 6I may be closed only after focused tests, combined regression, command/tool checks, core/release checks, compileall, diff check, and a final worktree audit pass.

## Phase 6I-C Completion Evidence (2026-07-16)

### Status

**Complete:** the real PyQt6 Inspector foldout Gate is implemented and verified. Phase 6I is closed.

### Environment Proof

- Replaced only the ignored, broken repository `.venv` with an isolated conda prefix.
- Runtime used for UI proof: Python `3.11.15`, PyQt6 `6.11.0`, Qt `6.11.0`.
- `QT_QPA_PLATFORM=offscreen` constructed and showed a real widget (`widget_visible True size 320 200`) before Inspector UI implementation.

### Implemented UI Adapter

- `InspectorPanel.update_properties()` appends diagnostics only after ordinary single-selection or multi-selection properties exist.
- Empty selection keeps the Inspector empty and does not call the diagnostics loader.
- `_append_worldbridge_runtime_diagnostics()` calls the existing Qt-free loader once, renders only the view-model section fields and warnings, assigns stable `worldbridgeRuntimeDiagnostics*` object names, and applies collapsed-by-default state after row construction.
- The foldout explicitly says the evidence is runtime-wide and is not selected-entity component state.
- All diagnostics controls are read-only. The UI Adapter does not call the projection Implementation, Command Registry directly, Inspector edit binding, mutation commands, component behavior, or `.pond` writes.

### TDD and Regression Evidence

| Check | Result |
|---|---|
| UI TDD red | New UI suite initially produced `6 failed` because the loader import and `_append_worldbridge_runtime_diagnostics()` were absent. |
| UI suite green | `tests/test_inspector_worldbridge_diagnostics_ui.py` -> `6 passed in 0.33s`. |
| Focused Inspector regression | Headless Adapter + UI + property mapping + schema + command binding -> `27 passed in 0.55s`. |
| Test-order isolation | Property mapping before UI -> `10 passed in 0.44s`; UI before property mapping is included in the focused `27 passed`. The QApplication fixture is session-scoped so Qt singleton wrappers survive the whole pytest process. |
| Combined Phase 6I regression | Package imports + WorldBridge status/mapping/decision/projection/diagnostics commands and tools + Inspector suites + release consistency -> `69 passed, 8 subtests passed in 8.15s`. |
| Direct authority proof | CLI command `runtime.worldbridge.component_projection_diagnostics` exited 0 with `ok: true`, summary-only fields, `component_count: 0`, and no `components` payload; focused CLI test -> `1 passed, 19 deselected in 0.27s`. |
| Tool proof | Runtime status, mapping audit, component decision, component projection, and component diagnostics tools all exited 0. |
| Architecture proof | `core boundaries OK`; `release consistency OK`. |
| Compile/whitespace proof | Temporary-pycache `compileall` passed for the Adapter, Inspector, and diagnostics tests; `git diff --check` exited 0 with existing LF/CRLF warnings only; scoped new-code whitespace check passed. |
| Final worktree audit | `tools/audit_worktree_groups.py` and `git status --short` both report dirty total `984`. Relative to the documented Phase 6I A/B snapshot (`983`), the final net increase is one path; this final snapshot includes the Phase 6I-C UI test and the Phase 6J plan/prompt materials, so it is recorded as a whole-worktree evidence snapshot rather than unsafe per-file cleanup arithmetic. No unrelated migration work was staged, committed, reset, cleaned, reverted, deleted, or reorganized. |

### Architecture Impact and Limits

The five-layer plugin shape, product runtime location, PyQt6/QPainter/OpenGL policy, `.pond` semantics, Command Registry authority, Inspector mutation binding, SR2D Adapter seams, package manifests, and project manifests are unchanged.

Stable now: runtime-wide, command-backed, summary-only WorldBridge diagnostics can be rendered in a real read-only Inspector foldout without breaking ordinary properties.

Still not implemented: selected-entity diagnostics authority, live component graph mapping, per-component objects, `.pond` mutation, lossless WorldBridge mapping, unified Pond default-readiness, SR/PS tick merge, native acceleration completion, or OpenGL default-readiness.

**Unique next Gate: Phase 6J — selected-entity WorldBridge diagnostics authority/interface decision.** This is a decision-only Gate; it must not implement live component mapping or `.pond` mutation.