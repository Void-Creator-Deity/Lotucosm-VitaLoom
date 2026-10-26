# Phase E22 -- Qt-free Manual Hot-Reload Orchestration Extraction and Legacy PluginLoader Reload Adapter

## Resume point

E21 is complete. The L4 Project World nested-plugin orchestration is Qt-free in `ProjectScopedPluginHost`, which composes E20 `RuntimePluginHost`. `kernel/plugin_loader.py` delegates Project-scoped operations while retaining legacy Editor/UI adapter duties.

Architecture remains immutable:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom (single engine/product plugin; recursive downstream plugin-host framework)
       -> versions/1.0.0/runtime
            -> L2 VitaLoom capability/domain
            -> L3 engine extension / host adapter
            -> L4 Project World addon
```

PyQt6/QPainter/OpenGL code is a legacy UI-host adapter, never the engine root or extension authority. Do not create another root framework, registry, manifest system, or plugin model. Do not migrate to Unity, Godot, Unreal, Electron, or another app shell.

## E22 single objective

Extract **manual hot-reload orchestration** from the legacy `PluginLoader` into one Qt-free module under:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/
```

The new module must compose existing E20/E21 authorities. It must not replace or duplicate their registry, discovery, activation contract, lifecycle planner, Project World ownership, manifests, or report schema.

## Required workflow

1. Write `docs/superpowers/plans/` E22 phase plan before editing production behavior.
2. Add red tests first for headless reload behavior and Loader compatibility delegation.
3. Extract candidate import, reload plan construction, affected-dependent closure, dependency-aware deactivate -> registry replacement -> activate transition, and reload report publication.
4. Preserve truthful outcomes: settled, blocked, partial, rollback, and recovery semantics must describe what actually happened. Never add a force bypass that defeats required confirmation or manifest/activation validation.
5. Keep `PluginLoader` limited to legacy UI cleanup/contribution transitions, signals, editor-ready handling, and explicit compatibility delegation.
6. Run targeted tests, architecture guardrails, then the full non-signature suite; record exact results and skips in `docs/mainline_status.md`.
7. Update this prompt chain and set exactly one next gate at E22 closure.

## Invariants

- Preserve `.pond` semantics, AI command registry flows, Inspector command binding, SR2D public seams, package/project manifests, Player/export, and L3/L4 lifecycle behavior.
- Preserve public reload report schema, canonical identifiers, manifest authorization, dependency ordering, and Project World switching behavior.
- Keep the extracted module Qt-free: no PyQt6, `EditorKernel`, `LayoutManager`, `PluginLoader`, or legacy plugin-interface imports.
- Treat existing uncommitted work as user/prior-migration work: do not reset, clean, stage, commit, revert, or delete unrelated files.
- Use `./.venv/python.exe` for Python commands. Do not install `cryptography`; signature test collection is an environment blocker until the controlled environment provides it.

## E21 evidence

- Focused E21 suite: `56 passed in 1.42s`.
- Expanded plugin/project/architecture regression: `118 passed, 1 skipped in 2.39s`.
- Guardrails: project-plugin model, core boundaries, GUI boundaries, and release consistency all passed.
- Full non-signature suite: `1237 passed, 25 skipped, 34 subtests passed in 124.26s`.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'`.

## Closure (2026-07-21)

E22 is completed with `ManualPluginReloadHost`, Loader delegation, focused/expanded regressions, all architecture guardrails, and a final full non-signature result of `1250 passed, 25 skipped, 34 subtests passed`. Signature collection remains blocked by missing `cryptography`.

The only next Gate is E23: Qt-free Nested Plugin Host Composition Root and Legacy `PluginLoader` UI Adapter.
