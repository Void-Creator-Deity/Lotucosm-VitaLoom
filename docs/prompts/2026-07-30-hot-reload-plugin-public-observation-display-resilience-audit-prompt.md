# Fresh-session handoff: E82 complete; E83 in progress

Repository root:

```text
D:\files\VS Code projects\Lotucosm-VitaLoom-refactor-engineering
```

E82 is complete. Read its final evidence first:

```text
docs/superpowers/plans/2026-07-30-hot-reload-plugin-public-observation-display-resilience-audit.md
```

The audit found no passive Hot Reload display path. All observed reloadable and
catalog facts shape either choose-command candidates or user-mod reload
targets, and the existing implementation already fails closed for non-mapping,
`None`, and string facts. E82 added regression proof that malformed facts show
no dialog and perform no reload; it did not change Hot Reload runtime code.

The sole next Gate is E83 -- Editor Smoke Public Observation Failure-Semantics
Audit. Begin with:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/main.py
```

Map its smoke-only `observe_plugins()` use. Reproduce malformed/unavailable
public observations under the existing smoke test seam, then make the smallest
read-model-only correction so smoke exits deterministically rather than raising
on `.get()` or `counts`. Do not turn it into an alternate Host, a plugin facts
cache, or a behavior change for the normal editor.

Preserve `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager`, `.pond`, Project World, Inspector
command binding, SR2D, SR/PS, Player/export, manifests, public imports, and
MRO. QPainter is default; OpenGL/native is not default-ready. Do not claim
whole-refactor completion, and do not stage, commit, reset, restore, clean, or
delete unrelated work.
