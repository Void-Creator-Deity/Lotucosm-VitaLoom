# Phase E80 -- Qt Package Manager Public Observation Display Resilience Audit

Date: 2026-07-30
Status: complete

## Previous gate

E79 used real offscreen PyQt6 regression to close Package Manager destructive
action authorization: selected-plugin and package disable now require complete,
trustworthy public catalog facts and fail closed otherwise. The same source
still has two direct `observe_plugins()` reads in display-only paths:
`_populate_plugin_list_tab()` and `_render_plugin_detail()`.

## Objective

Make those remaining Package Manager display reads robust to an unavailable,
partial, non-mapping, or malformed Runtime Plugin Host public observation.
Unknown facts must render as empty/unknown display state rather than crash or
claim loaded/success. Runtime Plugin Host remains the single authority;
display normalization must not read private Host state, infer facts, cache a
second catalog, or alter destructive-action rules.

## Required evidence

1. Map both direct reads and distinguish list loaded-state display from detail
   catalog-row display. Confirm they do not authorize commands or unload.
2. Add real offscreen PyQt6 capability-stub regressions exposing no Host
   internals. Cover non-mapping snapshot, invalid/`None` active-id list,
   unavailable empty observation, invalid catalog, malformed rows, and absent
   target row.
3. First reproduce the crash or misleading state. Then make the smallest
   existing-adapter or existing-mixin normalization correction. A non-string
   sequence is the only acceptable iterable public id/catalog list.
4. Prove no command/unload/private-state access occurs, then run focused E79
   coverage, adjacent Package Manager Qt lifecycle/adapter coverage, syntax,
   guardrails, signature, and diff/whitespace checks.
5. Record exact interpreter and offscreen configuration. Close with E68 broad
   evidence, QPainter/OpenGL status, fallback/unblock facts, and exactly one
   next Gate.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
serializer, renderer, layout manager, widget DSL, UI framework, or app shell.
Do not turn the legacy PyQt6/QPainter/OpenGL adapter into engine or plugin-rule
authority. Preserve `.pond`, Project World, Inspector command binding, SR2D,
SR/PS, Player/export, manifests, public imports, and MRO. QPainter remains
default; OpenGL/native acceleration is not default-ready. Do not claim
whole-refactor completion.

## Current approach

Use `.venv\python.exe` with `QT_QPA_PLATFORM=offscreen` and
`PYTHONDONTWRITEBYTECODE=1`. Start by extending
`tests/test_package_manager_plugin_host_capability.py`; confirm a red run
before changing runtime code. The expected minimal repair is safe public
observation normalization at the existing capability seam, reused only for
read-only display and never as action authorization.

## Completion record

- Reproduction: the new real offscreen PyQt6 capability-stub cases first failed
  with `6 failed, 14 passed in 0.85s`. A non-mapping observation caused an
  `AttributeError`, while `None` or string `active_plugin_ids` could cause a
  `TypeError` or a misleading loaded/inactive assertion.
- Repair: the existing `PluginRuntimeOpsMixin` now accepts only a public
  mapping snapshot and only a non-string `Sequence` of active ids. It reports
  untrustworthy active-id facts as `None`; Package Manager's existing list and
  detail display paths render that state with the explicit
  `package_manager.plugin.unknown` label. A trusted empty sequence still means
  not loaded. Catalog rows continue to be normalized from public facts only.
- Safety: the display paths issue no command, unload, refresh, or selection
  refresh and do not read Host private state. No fallback catalog, cache, or
  authority was added. Malformed catalog rows and an absent target row render
  no fabricated metadata.
- Evidence, using `.venv\python.exe` with `QT_QPA_PLATFORM=offscreen` and
  `PYTHONDONTWRITEBYTECODE=1`: focused E80 `20 passed in 0.51s`; Host/control/
  lifecycle/reload/activation regression `94 passed, 1 skipped in 2.45s`;
  adjacent Package Manager coverage `53 passed, 8 subtests passed in 3.31s`;
  guardrails `21 passed in 15.73s`, plus all three direct boundary tools OK;
  shared-base-interpreter signature proof `2 passed in 0.24s`. Changed source
  and test files passed source-only `compile(..., "exec")` plus a trailing
  whitespace check, and Package Manager has no direct `observe_plugins(` call.
- Bounded status: E68 remains the latest broad offscreen Qt proof (`1678
  passed, 34 skipped, 34 subtests`) and regular/eager application smoke proof
  (`13/20` and `20/20`). QPainter remains default. OpenGL/native acceleration
  is not default-ready. Whole-refactor completion is not claimed.
- Unique next Gate: E81 -- Legacy Plugin Manager Public Observation Display
  Resilience Audit.

