# Phase E62 -- Legacy Editor Shell Command-and-State Boundary Discovery

Date: 2026-07-30
Status: completed

## Previous gate

E61 made the optional SR OpenGL canvas wrapper lazy to import, so viewport
selection and immutable rendering contracts can load without PyQt. The actual
Qt canvas probe and creation path remain Adapter-local.

## Objective

Audit the bounded EditorKernel/LayoutManager command-and-state seam. Identify
which facts are portable runtime command/state outputs, which operations are
necessarily Qt shell projection, and one smallest testable extraction that does
not create a second editor Host, registry, command authority, or widget DSL.

## Constraints

Keep `FrameCore` L0, `lotucosm-vitaloom` the sole L1 engine/product mega-plugin,
and `versions/1.0.0/runtime` the product boundary. Preserve the existing
RuntimePluginHost, the sole LegacyEditorPluginAdapter, `.pond`, Project World,
Inspector command binding, SR2D, SR/PS, Player/export, package/signature
behavior, public imports, and entity/component MRO. Do not claim replacement
host or OpenGL default readiness without separate evidence.

## Required evidence before closure

Document source-level ownership and invoke targeted command/layout lifecycle
regression. Any proposed extraction must use plain data, preserve the current
Adapter as the only Qt projection authority, and include proof for load/unload
and saved-layout behavior where applicable.


## Audit findings

- `EditorKernel(QMainWindow)` remains the legacy Qt shell. It owns shell startup,
  close/save/restore timing, and its concrete `LayoutManager`; it is not a
  runtime Host or a candidate engine root.
- Runtime plugin lifecycle and command ownership remain with
  `RuntimePluginHost`. `LegacyEditorPluginAdapter` projects Host-copied editor
  contributions into concrete Qt payloads. `LayoutManager` owns only the local
  `QAction`, menu, toolbar, dock, viewport-tab, status-bar, and Qt window-state
  projection lifecycle.
- `QMainWindow.saveState()/restoreState()`, `QByteArray`, widget geometry,
  dock visibility/floating state, and tab application must remain in the Qt
  shell. The persisted JSON facts between capture and apply are portable.

## Implementation

- Added `core/VitaLoom/kernel/editor_layout_state.py` with frozen
  `EditorLayoutState`: a Qt-free, JSON-safe value object for exactly the
  persisted `window_state`, `geometry`, `dock_states`, and `viewport_state`
  contract.
- `LayoutManager` remains the sole caller that captures widget data, performs
  file I/O, converts `QByteArray`, and applies saved Qt state. It now converts
  only at the JSON persistence/load boundary through `EditorLayoutState`; no
  second LayoutManager, Host, command registry, or UI abstraction was added.
- Added `tests/test_editor_layout_state.py` for deep-copy behavior, legacy
  partial/invalid-data fallback, JSON-safe rejection, and a fresh `-S`
  interpreter import that proves the state contract loads without `PyQt6`.
  Extended LayoutManager behavior coverage to read its saved file through the
  portable contract while retaining the concrete Qt projection test setup.

## Non-goals

This phase does not change action invocation, menu/toolbar ownership, viewport
widget projection, `.pond`, Project World, Inspector command binding, SR2D,
SR/PS, Player/export, package/signature semantics, or default renderer policy.
It does not establish a replacement Editor Host or OpenGL default readiness.

## Evidence

- Portable-state plus LayoutManager regression: `12 passed in 0.67s`.
- Expanded state/Adapter/contribution regression: `22 passed in 0.95s`.
- Full project-local Qt regression excluding the separate signature collection:
  `1669 passed, 34 skipped, 34 subtests passed in 198.22s`.
- Standard/eager offscreen Editor smokes passed at `plugins=13/20` and
  `plugins=20/20`; each saved and unloaded its concrete layout/plugin shell.
- Project-plugin-model, core-boundary, GUI-boundary, and release-consistency
  guardrails passed; `git diff --check` passed (existing CRLF warnings only).
  The independent signature-only collection passed: `2 passed in 0.22s`.

## Closure

E62 is complete. The unique next gate is E63: Legacy Editor Shell Command
Projection Boundary Discovery. Audit the Qt `QAction`/menu/toolbar projection
path and verify that runtime command authority remains singular before any
further extraction is considered.
