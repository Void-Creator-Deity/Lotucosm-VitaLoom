# Phase E70 -- Runtime Plugin Host Post-Cleanup Deactivation Failure Retryability Audit

Date: 2026-07-30
Status: completed

## Previous gate

E69 made declarative viewport cleanup precede dock cleanup. A concrete failed
viewport disposer therefore stops strict adapter cleanup before any sibling
dock is removed, leaving the active Host, command owner, Qt surfaces,
LayoutManager facts, and adapter ownership facts aligned for retry.

## Objective

Audit `RuntimePluginHost._deactivate_plugin()` after
`adapter.before_plugin_unload()` has succeeded. Establish retry behavior if
`plugin.on_unload()` or exact Host command release then fails while the plugin
remains in `loaded_plugins`. Add real Qt/Host regression coverage and implement
the smallest lifecycle-local correction that preserves singular Host ownership
and never requires a second projection or lifecycle authority.

## Audit result

The old Host retried the complete deactivation sequence after any failure. If
strict Adapter cleanup had already removed declarative Qt contributions and
`plugin.on_unload()` then raised, the plugin stayed active but the next request
entered Adapter cleanup again. Its already-removed viewport could report its
explicit `False` failure, preventing the retry from reaching the original
`on_unload()` failure. The same replay risk applied after a successful
`on_unload()` followed by exact Host command-owner release failure.

## Repair

`RuntimePluginHost` now owns a private `_PluginDeactivationProgress` record for
an already-active plugin. It records only successfully completed Host stages:
`prepare_host_teardown`, Adapter cleanup, `plugin.on_unload()`, and exact
command release. A failed stage leaves the plugin active and preserves the
completed facts; the next request resumes at the failed stage instead of
replaying side effects. Once `loaded_plugins` removal succeeds, the Host clears
the progress record immediately before its existing post-deactivation Adapter
observation. No second Host, command registry, Adapter, or Qt/layout authority
was introduced.

## Evidence

- New real Qt/Host regression:
  `test_runtime_host_retries_after_post_cleanup_on_unload_failure`. It uses
  `QMainWindow + LayoutManager + LegacyEditorPluginAdapter +
  RuntimePluginHost`, with one declarative dock, viewport, and Host-owned
  command. A first `on_unload()` failure occurs after concrete cleanup; the
  plugin and command remain active while the removed Qt/Adapter facts are
  preserved as completed Host progress. The repaired retry reaches
  `on_unload()` directly and converges to command and loaded-plugin removal.
- New Host lifecycle regression:
  `test_command_release_failure_resumes_without_replaying_cleanup_or_on_unload`.
  A one-time exact command release failure leaves the plugin and command active,
  then proves retry invokes neither Adapter cleanup nor `on_unload()` again and
  clears the private progress record after success.
- Focused lifecycle/cleanup regression: `46 passed in 1.28s`.
- Reload-related regression: `71 passed in 1.23s`.
- `py_compile` for the changed Host and both changed tests passed.
- `check_project_plugin_model.py`, `check_core_boundaries.py`,
  `check_gui_boundaries.py`, and `check_release_consistency.py`: all passed.
- `git diff --check` exited successfully; its CRLF advisory output concerns
  pre-existing working-tree files. Independent package-signature proof passed:
  `2 passed in 0.30s`.

A new whole-project offscreen Qt regression and application smoke were
intentionally not rerun for E70. This phase changes the Host's private retry
progress and two lifecycle fixtures; E68 remains the latest full offscreen Qt
(`1678 passed, 34 skipped, 34 subtests`) and regular/eager smoke (`13/20` and
`20/20`) evidence. E70 closes with direct real Qt/Host, lifecycle, reload,
syntax, guardrail, diff, and signature proof instead.

## Explicit non-goals

Do not add a second Host, command registry, event bus, renderer, layout
manager, widget DSL, UI framework, or app shell. Do not change `.pond`, Project
World, Inspector command binding, SR2D, SR/PS, Player/export,
package/manifests, or public imports. Do not claim native/OpenGL default
readiness or whole-refactor completion. This phase does not define generic
retry guarantees for failures that happen after removal from `loaded_plugins`.

## Next gate

E71 -- Runtime Plugin Host Post-Registry Deactivation Observation Failure
Semantics Audit. Audit the existing `after_plugin_deactivated()` observation
seam after Host registry removal: establish reporting, shutdown/reload-plan
convergence, and retry semantics if a concrete observer raises, without
reintroducing a removed plugin or adding a parallel lifecycle authority.
