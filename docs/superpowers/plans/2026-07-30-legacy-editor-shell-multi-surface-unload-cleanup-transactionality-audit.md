# Phase E69 -- Legacy Editor Shell Multi-Surface Unload Cleanup Transactionality Audit

Date: 2026-07-30
Status: completed

## Previous gate

E68 established fail-closed cleanup and retry recovery for a declarative
viewport that cannot dispose runtime capabilities during dynamic unload. The
Host, command owner, adapter ownership, LayoutManager mapping, and only Qt tab
remain aligned until the failed cleanup can be retried successfully.

## Objective

Audit dynamic unload when one runtime plugin contributes more than one legacy
editor surface (for example a dock plus a viewport, command projection,
refresh subscription, or theme). Establish the intended behavior when cleanup
succeeds for one contribution and fails for a later one: whether the plugin
remains active with a partially removed Qt projection, whether deterministic
compensation or ordering is required, and whether a retry can converge without
stale or duplicate widgets. Implement only the smallest test-proven correction
at the existing `RuntimePluginHost -> LegacyEditorPluginAdapter ->
LayoutManager` boundary.

## Audit result

`LegacyEditorPluginAdapter.cleanup_plugin_ui()` previously processed a
contribution owner's dock before its declarative viewport. `LayoutManager`
provides a real, explicit, retryable failure signal only for
`remove_viewport()`: it returns `False` when runtime-capability disposal does
not finish. Therefore a failed viewport cleanup could leave the Host active
while the earlier dock projection had already disappeared.

The other observed cleanup paths do not currently expose an equivalent,
concrete retryable surface-failure contract: `remove_dock()` and
`remove_plugin_ui()` do not return success/failure, refresh unsubscription has
no reproduced Qt-projection loss, and theme application already has a local
style-state rollback path. This phase does not generalize an unproven
all-Qt-operations distributed transaction.

## Repair

The declarative cleanup order is now viewport, dock, menu/toolbar, refresh,
and theme. The legacy fallback viewport branch also turns an explicit `False`
into `RuntimeError` when `fail_closed=True`. Thus the known, retryable viewport
failure occurs before the dock is touched: strict unload keeps the Host,
Host-owned command, Qt surfaces, LayoutManager facts, and adapter ownership
facts aligned until the disposer is repaired and unload is retried.

## Evidence

- New real Qt/Host regression:
  `test_runtime_host_preserves_dock_until_viewport_cleanup_retry_succeeds`.
  It exercises `QMainWindow + LayoutManager + LegacyEditorPluginAdapter +
  RuntimePluginHost` with one plugin that contributes a dock, a viewport, and a
  Host-owned command. A first failing viewport disposer leaves the plugin
  loaded, `on_unload()` uncalled, both surfaces and the one Qt tab present, both
  adapter ownership maps intact, and the command registered; a repaired second
  unload removes every fact without stale or duplicate projection.
- Direct offscreen Qt/Host proof: `1 passed, 12 deselected in 0.39s`.
- Focused lifecycle/cleanup regression: `39 passed in 1.21s`.
- Reload-related regression: `70 passed in 1.31s`.
- `check_project_plugin_model.py`, `check_core_boundaries.py`,
  `check_gui_boundaries.py`, and `check_release_consistency.py`: all passed.
- `py_compile` for the changed adapter and test passed; `git diff --check`
  exited successfully (its CRLF advisory output is pre-existing); independent
  package-signature proof passed: `2 passed in 0.29s`.

A new whole-project Qt regression and application smoke were intentionally not
rerun for E69: the implementation is limited to cleanup ordering and one test
fixture, while E68 already recorded the latest full offscreen Qt and regular /
eager smoke proof. E69 instead closes with the directly relevant lifecycle,
reload, guardrail, syntax, diff, and signature evidence above.

## Explicit non-goals

Do not add a second Host, registry, event bus, renderer, layout manager, widget
DSL, UI framework, or app shell. Do not claim native/OpenGL default readiness
without current-context rendering, parity, interaction, and benchmark proof.
Do not change `.pond`, Project World, Inspector command binding, SR2D, SR/PS,
Player/export, package/manifests, or public import contracts. Do not claim that
the whole refactor is complete or that every arbitrary Qt exception has a
universal rollback transaction.

## Next gate

E70 -- Runtime Plugin Host Post-Cleanup Deactivation Failure Retryability
Audit. Audit the singular Host lifecycle after adapter cleanup has succeeded
but `plugin.on_unload()` or command release fails, and establish the smallest
real-Qt/Host retry contract without adding a second lifecycle or projection
authority.