# Phase E71 -- Runtime Plugin Host Post-Registry Deactivation Observation Failure Semantics Audit

Date: 2026-07-30
Status: completed

## Previous gate

E70 made deactivation retryable through the final state-changing Host stages.
The Host privately records successful teardown preparation, Adapter cleanup,
`plugin.on_unload()`, and command release while the plugin remains active, then
clears that progress immediately after `loaded_plugins` removal.

## Objective

Audit the remaining deactivation seam after the Host has definitively removed
the plugin from `loaded_plugins`:

```text
loaded-plugin removal -> adapter.after_plugin_deactivated()
```

Establish correct unload, shutdown, and lifecycle/reload-plan reporting if this
post-removal observer raises. Prove whether returning a failed result despite a
removed plugin creates a false failure / non-convergent caller contract. Make
only the smallest Host-local correction, with no plugin resurrection and no
second authority.

## Required evidence

Add a focused Host regression with an Adapter whose
`after_plugin_deactivated()` raises after recording its invocation. Prove the
actual returned value/report, `loaded_plugins`, command release, and any retry
behavior. Cover shutdown or lifecycle-plan reporting if the code path makes it
necessary. Run focused lifecycle and reload regressions plus the standard
architecture/release guards and record skips.

## Explicit non-goals

Do not add a second Host, command registry, event bus, renderer, layout
manager, widget DSL, UI framework, or app shell. Do not change `.pond`, Project
World, Inspector command binding, SR2D, SR/PS, Player/export,
package/manifests, or public imports. Do not claim native/OpenGL default
readiness or whole-refactor completion.


## Audit result

The existing Host intentionally treats `after_plugin_deactivated()` as an observable lifecycle stage, not a retryable state-changing stage. If it raises, the result reports `ok=False, deactivated=True`: the callback fault remains visible while shutdown records the plugin as completed and reports remaining active plugins accurately. The already removed plugin cannot be retried, replayed, or resurrected.

E71 adds a direct `unload_plugin()` proof. After the observer raises, the call returns `False`, but command ownership, `loaded_plugins`, and E70 private progress are empty. A second unload returns `False` because the plugin is inactive and does not invoke the observer again. No production change is warranted: treating the observer error as success would hide a concrete notification failure, while resurrection or observer retry would violate Host registry authority.

## Evidence

- New direct Host regression: `test_post_registry_observer_failure_preserves_converged_removal` proves observer failure releases the exact command, empties active and progress facts, remains visible to the compatibility unload call, and cannot be replayed.
- Existing shutdown failure-matrix coverage confirms `unload_signal` failure lists the removed plugin among completed deactivations and excludes it from `remaining_active_plugin_ids`.
- Focused lifecycle/cleanup regression: `47 passed in 0.93s`; reload regression: `71 passed in 0.99s`.
- Changed-file `py_compile`, all four architecture/release guardrails, and `git diff --check` passed; independent package-signature proof: `2 passed in 0.17s`.

No new full offscreen Qt suite or application smoke was run: E71 adds a headless assertion only. E68 remains latest full Qt (`1678 passed, 34 skipped, 34 subtests`) and regular/eager smoke (`13/20` and `20/20`) evidence.

## Next gate

E72 -- Runtime Plugin Host Deactivation Metadata Snapshot Consistency Audit. Audit the live `plugin.get_plugin_info()` fallback before staged deactivation, especially after E70 progress exists, and establish an immutable Host-fact boundary only if a real regression requires it.
