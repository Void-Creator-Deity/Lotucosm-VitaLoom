# Phase E34 -- Qt-Free Command Toolbar Contribution and Dynamic Action-State Projection

Date: 2026-07-23
Status: complete

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

VitaLoom is the engine plugin and itself a recursive plugin framework. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the only Host authorities. The PyQt editor, `PluginLoader`, `LegacyEditorPluginAdapter`, `EditorKernel`, `LayoutManager`, QPainter, and Qt OpenGL remain current/legacy Host Adapter implementation details.

E34 must deepen the E33 contribution contract and the existing Adapter seam. It must not create a peer L1 engine plugin, second registry/catalog/manifest authority/composition root, universal UI DSL, renderer framework, or replacement shell, and it must not migrate the project into Unity, Godot, Unreal, Electron, or another app shell.

## Previous Gate summary

E33 completed the first real Qt-free editor contribution slice:

- `menu_command` contributions are immutable, JSON-safe, deterministically ordered, and Host-owned;
- `RuntimePluginHost` validates and caches copied contribution facts and reload refreshes the same metadata path;
- `LegacyEditorPluginAdapter` alone creates live Qt actions and invokes the canonical command registry;
- `LocalizationUIPlugin` is now Qt-free and `LocalizationPlugin` owns `editor.language.set`;
- final proof is `1430 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and all four architecture guardrails green;
- signature-only collection remains blocked because the exact project `.venv` lacks `cryptography`.

E33 did not migrate dock/viewport/theme providers, select another shell, or complete the whole engine.

## Current hypothesis

The next smallest useful shape is the command-backed toolbar action, using the active `StandardUIPlugin` simulation play/stop controls as the candidate vertical slice:

- canonical commands already exist (`simulation.toggle`, `simulation.stop`);
- the legacy toolbar currently publishes live callbacks and Qt icon names;
- the play label changes with authoritative simulation transport state;
- migrating this slice tests placement, localization, command parity, refresh/state observation, and deterministic cleanup without inventing a widget tree or migrating dock/viewport content.

The hypothesis is not permission to copy `StandardUIPlugin` wholesale into metadata. Task 1 must first prove the minimum state and placement semantics and identify whether existing simulation capability/query observations are sufficient.

## Tasks

### Task 1 -- Audit toolbar/state semantics and establish red tests

- Trace `StandardUIPlugin` play/stop toolbar construction, command handlers, simulation transport state publication, localization refresh, icon/shortcut behavior, ownership, reload, and cleanup.
- Separate stable engine/plugin facts from Qt-only `QAction`/`QToolButton` construction and host-native icon resolution.
- Add red contract tests for a minimal toolbar command kind and, only if required by the real slice, a read-only action-state reference.
- Reject callbacks, widget/icon objects, plugin instances, `EditorKernel`, `LayoutManager`, arbitrary state callables, forged ownership, duplicate ids, and alternate registries.
- Prove import and observation remain Qt-free and deterministic.

### Task 2 -- Extend the existing contribution contract minimally

- Extend `editor_contribution_contract` rather than creating another schema or catalog.
- Prefer stable command ids, payloads, localization keys/defaults, placement/group/order, portable icon tokens, and references to existing read-only state facts.
- Do not embed transport objects, event buses, command handlers, Qt icon instances, or arbitrary expression languages.
- Define fail-closed validation, deterministic sorting, JSON-safe observation, and exact lifecycle ownership.

### Task 3 -- Project through the current legacy Adapter

- Add Qt toolbar projection only inside `LegacyEditorPluginAdapter` or a subordinate Adapter Module it owns.
- Execute actions through the canonical command registry and observe state through an existing Host/capability/query seam; do not duplicate simulation behavior or create a state registry.
- Refresh localized/dynamic labels without plugin rediscovery and without duplicating or leaking actions across reload/unload.

### Task 4 -- Migrate one bounded StandardUI vertical slice

- Migrate only the proven simulation play/stop toolbar actions first.
- Preserve current command semantics, dynamic play label, localization, icon fallback, ordering, ownership, reload, and cleanup.
- Keep unrelated StandardUI menus and host-specific dialogs on the legacy path until separately proven.

### Task 5 -- Regression and closure

- Run focused contribution, simulation transport, command, Adapter, reload, startup/shutdown, and duplicate/stale projection tests.
- Run Project World, AI command, Inspector, viewport/SR2D, Player/export compatibility regressions, the full non-signature suite, real Editor smoke, and all four architecture guardrails.
- Attempt signature-only collection without silent installation and record the exact blocker/unblock path.
- Update plan/status/context/index and create exactly one next Gate.

## Completion bar

E34 is complete only when:

1. the real play/stop toolbar slice is declared and observed as validated Qt-free facts;
2. the current Qt Host projects it with command/state/localization parity and deterministic cleanup;
3. no live callback, Qt/native object, plugin instance, kernel/layout object, or second registry leaks into the contract;
4. `RuntimePluginHost` remains registration/lifecycle authority and existing simulation/command authorities remain unique;
5. reload/state refresh/startup/shutdown and all required regressions, smoke, and guardrails pass.

## Preserved contracts

Do not break `.pond`, AI command registry flows, Inspector command binding, SR2D, package/project manifests, L4 Project World addons, Player/export, plugin reload/startup/shutdown, viewport parity, or the one-L0/one-L1 recursive framework-plugin topology. Do not stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work.

## Completion checkpoint

E34 closed the intended vertical slice without changing the framework/plugin topology:

- the contract gained immutable, deterministic, JSON-safe `toolbar_command` facts plus a closed `EditorCommandStateProjection` vocabulary;
- Host-injected canonical ownership remains authoritative, while callbacks, plugin/native objects, forged owners, arbitrary expressions/state resolvers, unknown fields, and invalid portable tokens fail closed;
- `simulation.transport.status` is the canonical read-only query command for transport phase, pause/play flags, and speed; no UI-owned state registry was introduced;
- `LegacyEditorPluginAdapter` alone creates live Qt actions/icons, executes commands, queries state, subscribes to refresh events, deduplicates shared subscriptions, and performs exact owner cleanup across unload/reload;
- `StandardUIPlugin` now declares only the simulation play/stop toolbar slice while its unrelated save/menu/dialog behavior remains on the legacy path;
- hybrid refresh removes each plugin's old UI once, reprojects remaining legacy menu/toolbar items, then appends declarative contributions, allowing bounded migration without duplicate or missing actions.

Verification evidence:

- genuine red baseline: `13 failed, 6 passed`;
- completed E34 contract/projection tests: `20 passed`;
- focused contribution/toolbar/refresh verification: `39 passed`;
- expanded Host/Loader/simulation/localization/reload/shutdown verification: `94 passed`;
- complete non-signature regression: `1450 passed, 34 skipped, 34 subtests passed in 162.35s`;
- real offscreen Editor smoke: `Editor smoke OK`, `plugins=13/20`, with successful activation, layout exercise, and deterministic reverse shutdown;
- `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`;
- modified contract, Adapter, StandardUI, and runtime command Modules pass `compileall`.

Signature-only collection is still blocked in the exact project `.venv` by `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed and signature verification is not claimed. The unblock path is explicit user approval to install `cryptography` into that exact `.venv`, followed by rerunning the signature-only test.

E34 does not complete Dock/viewport/theme migration, a replacement UI Host, native GPU geometry acceleration, OpenGL default readiness, signature provisioning, or the whole-engine objective.

## Unique next Gate after E34

**Phase E35 -- Qt-Free Dock Contribution Contract and Host-Owned Dock Surface Projection, Task 1 only:** audit every active `IDockProvider` and separate stable dock identity/title/placement/visibility facts from Qt widget construction, domain commands/read models, event subscriptions, and ownership/reload/unload. Select one real vertical slice from evidence before defining any dock contribution Interface. Do not put live `QDockWidget` factories into Qt-free metadata, create a second Dock registry/UI framework, or select a replacement shell.
