# Fresh-session handoff: E81 complete; E82 in progress

Repository root:

```text
D:\files\VS Code projects\Lotucosm-VitaLoom-refactor-engineering
```

E81 is complete. Read its final evidence first:

```text
docs/superpowers/plans/2026-07-30-legacy-plugin-manager-public-observation-display-resilience-audit.md
```

E81 repaired only the legacy Plugin Manager's display projection. Real
offscreen PyQt6 tests reproduced `3 failed, 3 passed in 0.37s`; the completed
correction now passes focused `8 passed in 0.35s`, broader host/consumer
coverage `98 passed, 1 skipped`, adjacent Package Manager coverage `53 passed,
8 subtests`, guardrails `21 passed`, and independent signatures `2 passed`.
Unknown active-id facts render explicit unknown and malformed registry/failed
facts create no fake plugin facts. It issues no reload/unload and reads no Host
private state.

The sole next Gate is E82 -- Hot Reload Plugin Public Observation Display
Resilience Audit. Begin by mapping every `hot_reload_plugin.py`
public-observation use, explicitly labeling each as display-only or action
authorization. Reproduce any display-only malformed-fact failure in real
offscreen tests before making the smallest public-seam-only correction. Keep
reload actions fail-closed: do not let display normalization grant command
permission. Do not create a second Host, registry, catalog, command authority,
event bus, serializer, renderer, layout manager, widget DSL, UI framework, or
app shell.

Preserve `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager`, `.pond`, Project World, Inspector
command binding, SR2D, SR/PS, Player/export, manifests, public imports, and
MRO. QPainter is default; OpenGL/native is not default-ready. Do not claim
whole-refactor completion, and do not stage, commit, reset, restore, clean, or
delete unrelated work.
