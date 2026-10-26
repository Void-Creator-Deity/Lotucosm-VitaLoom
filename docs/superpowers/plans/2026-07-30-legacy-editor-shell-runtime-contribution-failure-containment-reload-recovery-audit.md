# Phase E68 -- Legacy Editor Shell Runtime Contribution Failure-Containment and Reload Recovery Audit

Date: 2026-07-30
Status: completed

## Previous gate

E67 proved that same-id viewport re-projection fails closed when the previous
viewport cannot dispose its runtime capabilities. That repair prevents stale
Qt tabs and preserves the existing LayoutManager as the single concrete
projection authority.

## Objective

Audit failure containment across runtime-contributed legacy editor surfaces
(docks, viewports, themes, and command projections) during activation, unload,
and reload. Establish whether a failed contribution projection or cleanup
leaves partial Qt state, registry facts, or Host lifecycle state inconsistent;
add only minimal, test-proven recovery at the existing
RuntimePluginHost -> LegacyEditorPluginAdapter -> LayoutManager boundary.

## Required evidence

Trace one failing contribution type from Host lifecycle report to concrete
adapter and LayoutManager cleanup/recovery. Add deterministic regressions for
failure isolation and a successful retry/reload without stale docks, tabs,
menus, or provider state. Run focused tests, the full offscreen Qt
non-signature suite, regular and eager Editor smoke, project/core/GUI/release
guardrails, diff check, and the shared-Python signature suite. Preserve
FrameCore L0, VitaLoom L1, RuntimePluginHost lifecycle authority, the one Qt
adapter and LayoutManager projection route, `.pond`, Project World, Inspector
binding, SR2D, SR/PS, Player/export, packages, manifests, and public imports.

## Explicit non-goals

Do not add a second Host, registry, event bus, renderer, layout manager, widget
DSL, UI framework, or app shell. Do not claim native/OpenGL default readiness
without the required current-context rendering, parity, interaction, and
benchmark proof.


## Audit result

E67 had already made `LayoutManager.remove_viewport()` report `False` when a
viewport could not dispose its runtime capabilities. The dynamic
`LegacyEditorPluginAdapter.before_plugin_unload()` hook, however, used the
ordinary compatibility cleanup path. That path could swallow the cleanup error,
remove the declarative-owner fact too early, and allow `RuntimePluginHost` to
continue the unload. A failed cleanup could therefore leave a live Qt viewport
while Host lifecycle facts, command ownership, and retryability diverged.

## Repair

Dynamic unload now uses the same strict cleanup contract as shutdown:
`before_plugin_unload()` calls `cleanup_plugin_ui(..., fail_closed=True)`.
Declarative viewport cleanup treats an explicit `False` from the concrete
LayoutManager as failure, raises before releasing the adapter owner fact, and
only removes that owner fact after successful projection removal. The explicit
`is False` check preserves compatibility with older test doubles whose cleanup
method returns `None`, while honoring the real LayoutManager success/failure
contract. No second Host, registry, adapter, or layout authority was introduced.

A real Qt/Host regression proves the recovery semantics: when a viewport
capability disposer fails, unload returns `False`; the plugin remains loaded,
`on_unload()` does not run, command ownership remains, the LayoutManager map and
single Qt tab remain, and the adapter owner map remains. After repairing the
disposer, retrying the same unload clears every one of those facts.

## Evidence

- LayoutManager + adapter focused regression: `21 passed in 0.53s`.
- Direct real-Qt Host retry proof: `1 passed, 11 deselected in 0.36s`.
- Expanded cleanup/lifecycle contract set: `38 passed in 1.01s`.
- Reload-focused lifecycle/projection set: `69 passed in 1.34s`.
- Full offscreen Qt non-signature suite: `1678 passed, 34 skipped, 34 subtests
  passed in 191.97s`.
- Offscreen Editor smoke: regular discovery `13/20`; eager discovery `20/20`.
- `check_project_plugin_model.py`, `check_core_boundaries.py`,
  `check_gui_boundaries.py`, and `check_release_consistency.py`: all OK.
- `git diff --check`: exit 0 (pre-existing CRLF advisories only).
- Shared-Python signature suite: `2 passed in 0.24s`.

## Non-goals

This phase does not declare the overall refactor complete; it does not make
OpenGL default-ready, replace the legacy PyQt host, create any second Host,
registry, layout manager, renderer, widget DSL, UI framework, or app shell, or
change `.pond`, Project World, Inspector command binding, SR2D, package
manifests, or public import contracts.

## Next gate

E69 -- Legacy Editor Shell Multi-Surface Unload Cleanup Transactionality Audit.
