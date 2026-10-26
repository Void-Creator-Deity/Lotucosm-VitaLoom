# Phase E72 -- Runtime Plugin Host Deactivation Metadata Snapshot Consistency Audit

Date: 2026-07-30
Status: completed

## Previous gate

E71 closed the post-registry observer seam. A failing
`after_plugin_deactivated()` remains visible to the caller but cannot replay,
restore, or resurrect a plugin that the singular Host has already removed.

## Objective

Audit the metadata seam before staged deactivation:

```text
registered Host metadata -> staged deactivation retry -> Adapter lifecycle inputs
```

E70 keeps successful cleanup/unload/release progress while the plugin remains
active. Establish whether an active retry can be blocked or semantically
altered by a later mutable or failing `plugin.get_plugin_info()` call, despite
the Host already owning registered declarative metadata. Make the smallest
Host-local correction only if a regression proves it necessary.

## Required evidence

Add a direct Host regression where the first deactivation completes Adapter
cleanup then fails during `on_unload()`. Make the plugin's later
`get_plugin_info()` call fail or return changed data before retrying. Prove
whether the retry reaches the pending stage, Adapter lifecycle calls receive
the Host-owned registered snapshot, command ownership converges, and no
completed side effect is replayed. Run focused lifecycle/reload coverage and
standard syntax, boundary, release, diff, and signature checks; record any
unrun wider suite explicitly.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
renderer, layout manager, widget DSL, UI framework, or app shell. Do not change
`.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export,
package/manifests, public imports, or plugin contracts. Do not claim
native/OpenGL default readiness or whole-refactor completion.

## Audit result

E72 proved two inconsistencies at the deactivation metadata boundary. The Host
passed its owned `plugin_metadata[plugin_id]` dictionary directly to
`after_plugin_load()`, allowing Adapter mutation to alter the later cleanup and
post-removal observer inputs. `_deactivate_plugin()` also used a truthiness
fallback, so a deliberately present empty Host record (`{}`) could incorrectly
invoke mutable live `plugin.get_plugin_info()` during deactivation or retry.

The minimal Host-local repair adds `_plugin_metadata_snapshot()`: membership,
not truthiness, decides whether the Host owns a record; the live fallback is
lazy and used only when no Host record exists; and every lifecycle recipient
gets an independent deep-copied snapshot. `plugin_metadata` remains the sole
registered-metadata authority. No second Host, registry, event bus, renderer,
layout manager, UI framework, or public contract was introduced.

## Evidence

- Direct E72 metadata regressions: `2 passed, 8 deselected in 0.18s`. They
  prove Adapter mutation cannot corrupt Host facts, an `on_unload()` retry does
  not re-run cleanup or read later failing live metadata, and present-empty
  Host metadata remains authoritative for cleanup and observation.
- Runtime Host lifecycle plus shutdown coverage: `18 passed in 0.46s`.
- E70 real Qt retry regression: `1 passed, 13 deselected in 0.22s`.
- Reload-related coverage: `52 passed in 1.72s`; core RuntimePluginHost:
  `5 passed in 0.17s`.
- Changed-file `py_compile`, project-plugin, core-boundary, GUI-boundary, and
  release-consistency guardrails passed. Shared-Python package-signature proof:
  `2 passed in 0.27s`. `git diff --check` passed after removing one trailing
  blank line; remaining CRLF notices are pre-existing worktree advisory noise.
- E72 did not rerun a full offscreen Qt suite or application smokes because it
  changes only the Qt-free Host metadata boundary and headless regressions.
  The latest such broad evidence remains E68: `1678 passed, 34 skipped,
  34 subtests` offscreen Qt; regular/eager smoke `13/20` and `20/20`.

## Next gate

**E73 -- Runtime Plugin Host Activation Metadata Snapshot Consistency Audit.**
Audit activation separately: determine from real regressions whether a
registered plugin's mutable or failing live metadata can wrongly alter or block
activation/reload before Host-owned declarative facts are selected, and whether
activation rollback receives a consistent Host snapshot. Do not presume a code
change; retain the single Host and existing activation-context contract unless
an executable regression proves a minimal Host-local correction is required.