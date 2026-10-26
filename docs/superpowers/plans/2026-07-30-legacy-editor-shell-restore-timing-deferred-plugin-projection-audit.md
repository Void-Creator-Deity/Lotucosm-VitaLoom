# Phase E66 -- Legacy Editor Shell Restore-Timing and Deferred Plugin Projection Audit

Date: 2026-07-30
Status: completed

## Previous gate

E65 verified the concrete dock projection and repaired the JSON-only fallback:
a partial layout can now restore a docked/floating state, validated dock area,
and visibility without overriding a successful Qt `saveState()` restoration.

## Audit result

- `EditorKernel.load_plugins_layered()` delegates to the layered NestedPluginHost
  synchronously. NestedPluginHost scans every configured layer, resolves
  dependencies, executes the full lifecycle target, and only then returns to
  EditorKernel.
- Only after that synchronous return does EditorKernel schedule its one 500 ms
  post-plugin callback. The callback restores layout first, applies the default
  workspace only when no layout is restored, and then opens Project World.
- The adapter's per-lifecycle `after_lifecycle_transition()` settles deferred
  dock tabification. It does not create or need a separate restore path, because
  initial discovery has already completed before the restore callback is queued.
- Added direct timing regressions that prove the Host-finalization-before-schedule
  order and restore/default-workspace-before-project-open order. No runtime repair
  was justified: adding another late-projection restore authority would duplicate
  LayoutManager and risk overwriting valid Qt topology.

## Evidence

- E66 timing, EditorKernel capability, and layout regression: `16 passed in
  1.06s`.
- Full project-local Qt non-signature regression: `1675 passed, 34 skipped,
  34 subtests passed in 203.21s`.
- Guardrails: project-plugin model, core boundaries, GUI boundaries, and release
  consistency all passed. `git diff --check` exited 0 (existing CRLF warnings
  only). Shared Python 3.13 signature suite: `2 passed in 0.22s`.
- E65's immediately preceding offscreen Editor smoke remains applicable to this
  no-runtime-code-change timing audit: standard discovery `plugins=13/20` and
  eager discovery `plugins=20/20` both completed with clean projected UI unload.

## Non-goals and boundary retained

No second host, layout manager, registry, renderer, UI framework, widget DSL, or
app shell was added. RuntimePluginHost remains lifecycle authority;
LegacyEditorPluginAdapter and LayoutManager remain the only concrete Qt
projection route. `.pond`, Project World, Inspector command binding, SR2D,
SR/PS, Player/export, package/signature, public imports, and the
QPainter-default/OpenGL-not-default-ready policy remain intact.

## Next gate

E67 -- Legacy Editor Shell Dynamic Plugin Reload Layout Projection Audit.
