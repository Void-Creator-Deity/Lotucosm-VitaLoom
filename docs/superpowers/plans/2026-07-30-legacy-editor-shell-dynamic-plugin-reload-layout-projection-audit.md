# Phase E67 -- Legacy Editor Shell Dynamic Plugin Reload Layout Projection Audit

Date: 2026-07-30
Status: completed

## Previous gate

E66 proved initial layered discovery and lifecycle activation finish
synchronously before the one deferred layout restoration callback is scheduled.
No parallel restore authority is needed for initial startup.

## Objective

Audit dynamic plugin activation, unload, and reload after startup: establish
whether a re-projected dock or viewport deterministically preserves appropriate
LayoutManager-owned layout facts without reviving stale Qt widgets or creating a
second restore/lifecycle authority. Make only a focused, test-proven lifecycle
or idempotence repair.

## Required evidence

Trace RuntimePluginHost lifecycle reports through LegacyEditorPluginAdapter and
LayoutManager, including Hot Reload and direct lifecycle calls. Cover reload
cleanup, same-title dock replacement, viewport replacement, and persisted-layout
interaction. Then run focused regressions, full Qt non-signature regression,
offscreen smoke, guardrails, diff check, and the separate signature suite. Do
not introduce another Host, registry, layout manager, renderer, UI framework,
widget DSL, or app shell.

## Audit result

`NestedPluginHost` delegates reload/lifecycle work to the existing
`RuntimePluginHost`. The existing `LegacyEditorPluginAdapter` remains the sole
concrete PyQt projection adapter: its unload hook calls
`cleanup_plugin_ui()`, which removes declarative docks and viewports through
the existing `LayoutManager`; its lifecycle completion hook only flushes
pending Dock tabification. No additional lifecycle, layout, or restore
authority is justified.

The focused audit found one real stale-projection failure path. Before this
phase, `add_viewport()` attempted to remove a same-id prior viewport, but
`remove_viewport()` returned early when the prior widget's
`dispose_runtime_capabilities()` failed. `add_viewport()` then overwrote the
mapping and inserted a second Qt tab, leaving a stale projection behind.

## Repair

`LayoutManager.remove_viewport()` now returns an explicit success result:
missing viewports and failed runtime capability cleanup return `False`; only a
completed Qt tab/map/provider/display-data removal returns `True`.
`add_viewport()` treats an unsuccessful same-id removal as a fail-closed
replacement: it schedules deletion of the incoming widget and raises a clear
`RuntimeError`, retaining the original mapping and sole Qt tab. This preserves
one LayoutManager authority and makes the caller retry/recover through the
existing Host lifecycle rather than silently corrupting the projection.

A direct regression proves that a cleanup-failing old viewport cannot be
replaced: the original map entry and single Qt tab remain intact, and the
incoming replacement is rejected.

## Evidence

- Layout/adapter regression set: `20 passed in 0.75s`.
- Reload-focused lifecycle/projection set: `67 passed in 1.78s`.
- Full offscreen Qt non-signature suite: `1676 passed, 34 skipped, 34 subtests
  passed in 191.80s`.
- Offscreen Editor smoke: regular discovery `13/20`; eager discovery `20/20`.
- `check_project_plugin_model.py`, `check_core_boundaries.py`,
  `check_gui_boundaries.py`, and `check_release_consistency.py`: all OK.
- `git diff --check`: exit 0 (pre-existing CRLF advisories only).
- Shared-Python signature suite: `2 passed in 0.24s`.

## Non-goals

This phase does not declare the overall refactor complete; it does not make
OpenGL default-ready, replace the legacy PyQt host, create any second Host,
registry, layout manager, renderer, widget DSL, UI framework, or app shell,
or change `.pond`, Project World, Inspector command binding, SR2D, package
manifests, or public import contracts.

## Next gate

E68 -- Legacy Editor Shell Runtime Contribution Failure-Containment and Reload
Recovery Audit.
