# Fresh-session prompt — Phase E25 Qt-free Nested Plugin Host Shutdown Authority and Legacy Editor Close Adapter

Continue VitaLoom from the completed E24 checkpoint on 2026-07-21.

## Architecture that must remain true

`FrameCore` is the only L0 root. `FrameCore/plugins/lotucosm-vitaloom` is the sole L1 engine/product plugin and is itself a recursive downstream plugin-host framework. Its product implementation boundary remains:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       sole engine/product plugin and recursive downstream plugin-host framework
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon
```

PyQt6/QPainter/OpenGL are only the current legacy UI-host Adapter implementation. They are not the engine root, nested plugin authority, or rule source for a future UI Host. Do not migrate the project to Unity, Godot, Unreal, Electron, or another shell.

## Completed E24 baseline

- `LegacyEditorPluginAdapter` is the concrete Adapter satisfying the Qt-free `RuntimePluginHostAdapter` seam.
- `PluginLoader` is a compatibility facade over one `NestedPluginHost` plus that Adapter.
- `NestedPluginHost`, `ProjectScopedPluginHost`, and `ManualPluginReloadHost` share one exact `RuntimePluginHost` registry.
- Command registration/unregistration uses the canonical runtime plugin ID.
- E24 proof: focused `84 passed`; expanded `383 passed, 1 skipped`; complete non-signature `1266 passed, 25 skipped, 34 subtests passed`; project/core/gui/release guardrails passed.
- Signature-only collection is still blocked because `.venv` lacks `cryptography`; do not install dependencies or claim signature verification.

## E25 single objective

Create one explicit Qt-free shutdown Interface for all active plugins recursively hosted by the L1 engine plugin, then adapt the legacy Editor close path to call that Interface through `PluginLoader` rather than enumerate `loaded_plugins`.

The shutdown Interface must be deep: callers request one shutdown operation and receive one deterministic report. Registry knowledge, dependency ordering, protected-plugin shutdown exception, callback ordering, failure facts, and lifecycle report publication remain local to the Host Modules.

## Protected-plugin rule

Do not weaken `RuntimePluginHost.unload_plugin(plugin_id)` or manual reload behavior: protected/core plugins remain non-unloadable during ordinary runtime operations.

Process shutdown is a distinct lifecycle authority. It must be able to deactivate every active plugin, including protected/core plugins, because the Host itself is terminating and must run Adapter cleanup plus plugin unload callbacks. Implement this through an explicit internal/shutdown mode or dedicated method, not by making ordinary unload accept protected plugins.

## Required first actions

1. Read AGENTS.md, CONTEXT.md, docs/adr/, the E24 plan/closure, and this prompt.
2. Write the E25 phase plan under `docs/superpowers/plans/` before production edits.
3. Audit `RuntimePluginHost.unload_plugin`, `execute_lifecycle_target`, lifecycle planner deactivation order, `NestedPluginHost` report publication, `PluginLoader` compatibility methods, and `EditorKernel.closeEvent` tests/callers.
4. Add red tests before implementation.

## Required red-test behavior

1. Headless shutdown of a dependency graph deactivates dependents before dependencies and leaves no active plugins.
2. Shutdown includes protected/core active plugins, while ordinary unload and manual reload still reject them.
3. Each successful plugin preserves established order: concrete Adapter cleanup -> `plugin.on_unload()` -> command owner release -> registry removal -> unload signal.
4. The shutdown report is strict/deterministic, records exact completed deactivations and the first failed action, and is published through `NestedPluginHost.last_lifecycle_report` exactly once.
5. A callback/cleanup failure is fail-closed: remaining state and completed actions are truthful; the legacy Editor does not accept close after an unsettled shutdown.
6. Empty/already-closed shutdown is deterministic and does not trigger fake layout settling or duplicate callbacks.
7. `PluginLoader` exposes a narrow compatibility delegate such as `shutdown_plugins()`; `EditorKernel.closeEvent()` calls it and no longer reads `loaded_plugins` or loops over `unload_plugin`.
8. Static architecture gates keep Qt/PyQt/EditorKernel/legacy plugin Interfaces out of Qt-free Host Modules and prevent a second registry or shutdown authority.

## Ordering and compatibility invariants

- Reuse the existing lifecycle planner or its existing deterministic dependency facts; do not invent a second planner.
- Preserve reverse dependency teardown.
- Preserve Adapter cleanup, runtime callback, command release, registry removal, and signal ordering.
- Keep `.pond`, AI command registry, Inspector command binding, SR2D public seams, package/project manifests, Player/export behavior, Project World L4 lifecycle, activation schema, reload reports, and operator recovery unchanged.
- Keep exactly one Runtime Host registry and one Nested Host composition root.
- Keep `PluginLoader` a compatibility facade; do not move Qt behavior back into it.
- If shutdown failure handling exposes an existing ambiguous UI behavior, document the fallback path, unblock path, and one next Gate rather than silently accepting close.

## Non-goals

- no replacement UI shell or generic UI framework;
- no Unity/Godot/Unreal/Electron migration;
- no renderer/SR2D/native/OpenGL migration in E25;
- no second registry, composition root, manifest authority, lifecycle planner, or plugin hierarchy;
- no broad removal of compatibility seams;
- no dependency installation for `cryptography`;
- no Git reset, restore, clean, stage, commit, or deletion of unrelated migration work.

## Verification required before closure

- focused shutdown/runtime/nested/Loader/Editor-close tests;
- expanded plugin/command/Inspector/Player/startup/export/layout/FrameCore/Project World regression;
- complete non-signature suite;
- project plugin model, core boundary, GUI boundary, and release consistency guardrails;
- separate truthful recording of the signature blocker.

Close E25 by updating its plan, `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and exactly one fresh-session prompt for the next Gate. Do not claim PyQt Host replacement, native acceleration completion, OpenGL default-readiness, signature verification, or whole-engine completion without the required evidence.
