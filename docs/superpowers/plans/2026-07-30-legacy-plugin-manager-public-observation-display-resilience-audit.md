# Phase E81 -- Legacy Plugin Manager Public Observation Display Resilience Audit

Date: 2026-07-30
Status: complete

## Previous gate

E80 closed the Qt Package Manager's two display-only observation paths. Its
existing public-observation helpers now distinguish a trustworthy empty active
id list from unavailable, malformed, or non-mapping facts, and make the latter
explicitly unknown without changing action authorization.

`plugin_manager_plugin.py` remained a separate legacy UI-host adapter consumer.
Its `_refresh_plugin_list()` directly read the public Runtime Plugin Host
observation and assumed both a mapping snapshot and iterable id collections.
This display-only path could crash or assert a false active state when public
facts were unavailable or malformed.

## Objective

Audit and minimally repair the legacy Plugin Manager's display-only public
observation handling. It must tolerate non-mapping, partial, and malformed
public facts in real offscreen PyQt6 tests. Unknown active facts must render as
an explicit unknown/empty display state, never as loaded/success. Runtime
Plugin Host remains the sole plugin and catalog authority.

## Result

- The focused offscreen capability-stub regression reproduced the product
  defect before the correction: `3 failed, 3 passed in 0.37s`. A non-mapping
  snapshot raised `AttributeError`; `None` active ids raised `TypeError`; and a
  string active-id fact was split as characters and projected as false
  inactive.
- `_refresh_plugin_list()` now uses the existing
  `PluginRuntimeOpsMixin._runtime_plugin_observation()` and
  `_runtime_active_plugin_ids()` public-observation seams. The legacy adapter
  no longer directly calls `observe_plugins()`.
- Adapter-local `_public_observed_plugin_ids()` accepts only documented
  non-string `Sequence` facts for registry and failed ids. Malformed facts are
  omitted with a warning; they create neither a second catalog nor invented
  plugin metadata. An untrustworthy active-id fact remains `None` and projects
  as the explicit `plugin_manager.status.unknown` display state, ahead of
  loaded/failed/inactive status checks.
- The regression covers a non-mapping snapshot, `None` active ids, string
  active ids, `None` registry ids, and `None` failed ids. Its formal
  `PluginHostControlObservation` capability stub exposes no Host private state
  and proves refresh issues neither reload nor unload.

## Evidence

Run with `.venv\python.exe`, `QT_QPA_PLATFORM=offscreen`, and
`PYTHONDONTWRITEBYTECODE=1` unless noted otherwise:

1. Focused E81 regression: `tests/test_manager_refresh.py` passed
   `8 passed in 0.35s` after the correction.
2. Related legacy-consumer, Package Manager, Host control/lifecycle/reload,
   runtime command lifecycle, and activation coverage passed
   `98 passed, 1 skipped in 2.23s`.
3. Adjacent Package Manager lifecycle/adapter/domain regression passed
   `53 passed, 8 subtests passed in 3.16s`, protecting the shared mixin seam.
4. Source-only compile (without creating bytecode) and trailing-whitespace
   checks passed for both changed files. A direct
   `observe_plugins(` search in the legacy adapter returned no match; the only
   observation boundary used there is the pre-existing public mixin seam.
5. Boundary/import/manifest/release guardrail tests passed `21 passed in
   16.54s`; standalone core, GUI, and release tools all reported `OK`.
   The independent base-interpreter warn-only signature proof passed
   `2 passed in 0.26s`.
6. E68 remains the latest broad offscreen Qt evidence: `1678 passed,
   34 skipped, 34 subtests`; regular/eager editor smoke evidence is `13/20`
   and `20/20`.

## Scope and limits

No command authorization, unload, refresh action, selection refresh, Host
private-state access, fallback catalog, cache, or new authority was added.
The sole chain remains `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager`. `.pond`, Project World, Inspector
command binding, SR2D, SR/PS, Player/export, manifests, public imports, and
MRO are unchanged. QPainter remains default; OpenGL/native acceleration is not
default-ready. This is a bounded resilience gate, not whole-refactor
completion.

## Next gate

E82 -- Hot Reload Plugin Public Observation Display Resilience Audit. First map
`hot_reload_plugin.py` public-observation reads and separate display projection
from reload/action authorization before altering behavior. Preserve fail-closed
action rules and the single Runtime Plugin Host authority.
