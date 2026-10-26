# Fresh-session handoff: E76 complete

Repository root:

```text
<repository-root>
```

## Closed gate

E76 -- **Runtime Plugin Host Catalog-Entry Serialization Contract Audit** is
complete. Its plan is retained at:

```text
docs/superpowers/plans/2026-07-30-runtime-plugin-host-catalog-entry-serialization-contract-audit.md
```

The public `NestedPluginHost.observe_plugins()` catalog path incorrectly passed
a `PluginHostCatalogEntry` dataclass to generic `_json_safe()`. The dataclass
route used `asdict()` and omitted the extra public `to_dict()` field
`activation_context_source`. The minimal Qt-free correction is:

```python
row = _json_safe(entry.to_dict())
```

This keeps `PluginHostCatalogEntry.to_dict()` as the only catalog-entry export
authority. Lifecycle reporting already used `item.to_dict()` and required no
change. Regressions cover complete explicit metadata, default legacy context,
JSON safety, lifecycle agreement, exact public shape, and mutation isolation.

## Evidence and environment note

- Direct E76 regression: `7 passed in 0.18s`.
- Focused Host/lifecycle/reload/catalog coverage: `50 passed, 1 skipped in
  0.59s`.
- Syntax passed; architecture/release guardrails plus signature: `18 passed in
  14.20s`; independent signature: `2 passed in 0.30s`; `git diff --check`
  passed (only existing LF-to-CRLF advisories).
- Qt-dependent consumer collection is blocked in the current environment:
  `D:\app\anaconda3\python.exe` lacks `PyQt6`, and no repository
  `.venv\Scripts\python.exe` exists. Do not install dependencies merely to
  close this headless serialization gate. Fallback is the headless E76 proof
  and E75's offscreen Adapter/context proof (`25 passed in 0.86s`); rerun Qt
  consumer tests in a configured PyQt6 environment when available.
- E68 remains the latest broad proof: full offscreen Qt `1678 passed, 34
  skipped, 34 subtests`; regular/eager smokes `13/20` and `20/20`. QPainter is
  default; OpenGL/native acceleration are not default-ready. Whole-refactor
  completion is not claimed.

## Unique next gate

Continue only E77 -- **Runtime Plugin Host Public Observation Consumer Schema
Compatibility Audit**. Start by reading:

```text
docs/superpowers/plans/2026-07-30-runtime-plugin-host-public-observation-consumer-schema-compatibility-audit.md
docs/prompts/2026-07-30-runtime-plugin-host-public-observation-consumer-schema-compatibility-audit-prompt.md
```

## Non-negotiable constraints

- Preserve `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
  LegacyEditorPluginAdapter -> LayoutManager`.
- PyQt6/QPainter/OpenGL are legacy UI-host Adapter territory; QPainter is the
  default path and OpenGL is not default-ready.
- Do not add a second Host, metadata registry, command registry, event bus,
  renderer, layout manager, widget DSL, UI framework, or app shell.
- Preserve `.pond`, Project World, Inspector command binding, SR2D, SR/PS,
  Player/export, manifests, public imports, and MRO.
- Treat all existing uncommitted content as user/prior migration work. Never
  stage, commit, reset, restore, clean, delete, or overwrite unrelated work.
- Do not rewrite untracked `layout_manager.py` wholesale; it has mojibake risk.
