# Fresh-session handoff: E86 complete; E87 in progress

Repository root:

```text
<repository-root>
```

E86 is complete. Its only runtime change is the existing Hot Reload
`_reload_plugin_report()` helper: after successful capability resolution, a
thrown public `reload_plugin(plugin_id)` call becomes a mapping-shaped failed
report and follows its existing command result behavior. Resolver/interface
errors remain explicit. Choose-reload returns `plugin_reload_failed`; user-mod
batch returns `plugin_reload_batch_partial` while continuing valid targets.
Evidence: genuine red `3 failed`, focused `3 passed`, adjacent `68 passed`,
source check, root offscreen smoke `13/20`, four guardrails, and independent
signatures `2 passed`.

Continue only with E87, described in:

```text
docs/superpowers/plans/2026-07-30-runtime-ops-public-mutation-call-failure-containment-audit.md
```

Audit the distinct `PluginRuntimeOpsMixin` public mutation calls:
`reload_plugin()`, `unload_plugin()`, and project sync's
`sync_plugins_for_project()`. Preserve resolver errors, public Host authority,
valid catalog gating, Project World command authority, and failure-honest UI
behavior. Do not add private-state access, a cache, or a secondary sync path.

Use `.venv\python.exe -B` with `QT_QPA_PLATFORM=offscreen` and
`PYTHONDONTWRITEBYTECODE=1`. Do not use `py_compile`; use source-only
`compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`.
Signature proof uses `D:\app\anaconda3\python.exe` because `.venv` lacks
`cryptography`; do not install dependencies without user approval.

Preserve `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager`, `.pond`, Project World, Inspector
command binding, SR2D, SR/PS, Player/export, manifests, public imports, and
MRO. QPainter remains default; OpenGL/native acceleration is not
default-ready. Do not stage, commit, push, reset, restore, clean, or delete
unrelated user work.
