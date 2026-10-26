# Phase E33 -- Qt-Free Editor Contribution Contract and Replacement Host Adapter Migration Readiness

Date: 2026-07-23
Status: complete

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

VitaLoom is a self-developed Unity/Godot-class engine. The engine is not a PyQt project. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the recursive plugin authorities. `PluginLoader`, `LegacyEditorPluginAdapter`, `EditorKernel`, `LayoutManager`, PyQt6, QPainter, and Qt OpenGL are current legacy UI Host Adapter details; they must not define the future extension contract.

E33 does not select Unity, Godot, Unreal, Electron, or any replacement shell. It creates no peer L1 plugin, no second plugin Host/registry/manifest authority/composition root, and no parallel renderer or UI framework. A later Host may exist only as another Adapter consuming the same proven Qt-free engine-plugin contracts.

## Previous Gate summary

E32 is complete:

- strict real current-context non-background OpenGL pixels;
- logical QPainter/OpenGL parity for representative scenes;
- immutable pan/zoom/selection/repeat/resize interaction continuity;
- deterministic target recreation, teardown, and context release;
- comparable end-to-end policy evidence keeping `auto -> QPainter`;
- full non-signature `1412 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and all four architecture guardrails green;
- signature-only remains blocked by missing `cryptography`.

## Current audit baseline

1. `RuntimePluginHost` is already Qt-free and exposes one narrow `RuntimePluginHostAdapter` lifecycle seam. This is the authority to deepen, not replace.
2. `LegacyEditorPluginAdapter` is the current concrete projection point for docks, viewports, menus/toolbars, themes, and editor-ready callbacks.
3. The compatibility Interfaces `IDockProvider` and `IViewportProvider` return `QDockWidget`/`QWidget`; `IMenuProvider` returns dictionaries containing live Python callbacks. Builtin editor extensions therefore import PyQt directly and cannot be consumed by another Host Adapter.
4. `LayoutManager` currently accepts widget instances and callback dictionaries. It is a Qt Adapter implementation detail, not a reusable engine Interface.
5. The command registry, AI command flows, Inspector command binding, immutable viewport snapshots/draw commands, Project World reports, and plugin catalog observations already provide Qt-free facts that a contribution contract can reference instead of duplicating behavior.
6. No replacement shell has been chosen. The first requirement is a minimal, proven extension-facing contribution Interface and one legacy Qt projection, not a speculative universal UI schema.

## Task 1 inventory checkpoint (2026-07-23)

The active builtin editor-extension inventory has now been read against the
actual recursive Host topology rather than treating the legacy Qt editor as the
engine root:

- `21` concrete `*Plugin` classes were found under `builtin/editor_extensions`;
- `19` are represented by the current package/catalog paths;
- `HotReloadPlugin` and `PluginManagerPlugin` are currently uncataloged;
- `16` modules import PyQt directly;
- `9` modules reference `LayoutManager` mechanics directly;
- `5` menu providers publish dictionaries containing live action callbacks;
- `13` plugins consume language-change behavior;
- contribution shapes currently observed are `3` viewports, `8` docks, `5`
  menus, `1` toolbar, `1` theme, `1` runtime-types contribution, and `4`
  lifecycle/runtime-only plugins;
- the default `vitalloom.editor_essentials` bootstrap set contains `13`
  plugins: `ConsolePlugin`, `DownloaderPlugin`, `EditorWorkflowPlugin`,
  `GameViewportPlugin`, `HierarchyPlugin`, `InspectorPlugin`,
  `LocalizationPlugin`, `LocalizationUIPlugin`, `PackageManagerPlugin`,
  `ProjectBrowserPlugin`, `SceneViewportPlugin`, `StandardUIPlugin`, and
  `UnityDarkThemePlugin`;
- `PsReplayOverlayPlugin` remains planned and `CellEditorPlugin` remains
  optional rather than default-bootstrap proof.

The first vertical slice is `LocalizationUIPlugin`. It is active by default and
does not itself import PyQt, but its `IMenuProvider` Interface still leaks live
callbacks and its language-change path reaches into `kernel.layout_manager`.
That makes it the smallest representative proof that a Qt-free plugin can still
be coupled to a legacy Host Interface.

Dock and viewport providers are deliberately not first. Their current
Interfaces construct native widgets, so migrating them before proving command-
backed plain-data ownership would either create a speculative universal UI
schema or merely rename Qt factories. E33 will first prove one deep
`editor_contribution_contract` Module with a small Interface, JSON-safe facts,
canonical Host ownership, and a concrete legacy Adapter projection.

This checkpoint completes the static inventory portion of Task 1 only. It does
not claim that Task 1, E33, the Qt migration, or the engine is complete.

Red architecture proof was then established before production implementation:

```text
.\.venv\python.exe -B -m pytest tests\test_editor_contribution_contract.py -q
10 failed in 0.31s
```

All ten failures are the intended
`ModuleNotFoundError: core.VitaLoom.core.editor_contribution_contract`. The red
suite fixes the first Interface vocabulary and proves the required rejection of
forged ownership, live callbacks, live plugin/native objects, duplicate ids,
unsupported kinds, non-JSON-safe payloads, mutable observations, Qt imports,
and alternate Host/registry authority. The next implementation step is now
bounded to making this exact contract green; it must not widen into dock,
viewport, or replacement-shell design.

## Implementation plan

### Task 1 -- Inventory contribution shapes and establish red architecture tests

- Enumerate every active builtin contribution shape: dock, viewport, menu, toolbar, theme, editor-ready callback, localization refresh, shortcut, command binding, and plugin-owned cleanup.
- Record which facts are stable engine/plugin semantics and which are Qt-only construction details.
- Add red tests proving a future contribution catalog cannot contain Qt objects, live callbacks, `EditorKernel`, `LayoutManager`, or live plugin instances; ownership must be canonical plugin id and lifecycle order must remain the exact runtime Host order.
- Add import/boundary tests proving the new contract Module is Qt-free and does not create a second registry or Host.

### Task 2 -- Define the minimal deterministic contribution Interface

- Introduce immutable/plain-data contribution facts only after Task 1 fixes the required vocabulary. Prefer command ids, capability ids, localization keys/default text, stable placement ids, ordering, visibility policy, and owner plugin id over host-native objects or functions.
- Keep view content behind existing engine seams (command/query/view-model/viewport snapshot) rather than embedding a second UI toolkit or arbitrary render tree.
- Define explicit validation, duplicate-id handling, unsupported-kind behavior, deterministic ordering, lifecycle ownership, and JSON-safe observation.

### Task 3 -- Project contributions through the existing legacy Qt Adapter

- Extend `LegacyEditorPluginAdapter` (or one subordinate Adapter Module owned by it) to translate validated plain-data contributions into current `LayoutManager` actions/widgets.
- Command-backed actions must invoke the canonical command registry; the Adapter must not duplicate business logic.
- Publication/removal must follow `RuntimePluginHost` load/unload order and remain failure-isolated. Localization refresh must rebuild Adapter projections without re-discovering plugins or reading alternate registries.

### Task 4 -- Migrate one complete vertical slice

- Migrate one representative command-backed menu/toolbar slice and one lifecycle-owned editor surface selected from the Task 1 inventory.
- Preserve command ids, shortcuts, labels/localization behavior, plugin ownership, unload cleanup, Editor smoke behavior, and AI/CLI/MCP parity where the command is shared.
- Keep compatibility shims only at the legacy Adapter seam and mark remaining Qt-native providers explicitly as unmigrated; do not claim whole-editor migration from one slice.

### Task 5 -- Regression, parity evidence, and next decision

- Prove headless catalog/import behavior without PyQt, legacy Qt projection parity, deterministic reload/startup/shutdown, and no duplicate/stale contributions.
- Run focused contribution/host tests, Project World/plugin lifecycle/AI command/Inspector/viewport regressions, full non-signature suite, real Editor smoke, and all four guardrails.
- Attempt signature-only collection without silent installation; record the blocker/unblock path if unchanged.
- Update plan/status/context/index and create exactly one next prompt.

## Completion bar

E33 is complete only when:

1. at least one real plugin-contributed editor surface is declared as validated Qt-free plain data and observed without importing PyQt;
2. the current Qt editor renders/projects that same contribution through the existing legacy Adapter with parity and deterministic cleanup;
3. no Qt object, live callback, live plugin instance, `EditorKernel`, or `LayoutManager` leaks into the contribution Interface;
4. `RuntimePluginHost` remains the lifecycle/registration authority and no second Host/registry/catalog/composition root is introduced;
5. reload, localization refresh, startup/shutdown, command parity, focused/full regressions, Editor smoke, and architecture guardrails pass.

A document-only schema, an unused dataclass, a fake Host, or moving Qt factories behind a new name is insufficient.

## Preserved contracts

Do not break `.pond`, AI command registry flows, Inspector binding, SR2D, package/project manifests, L4 Project World addons, Player/export, plugin reload/startup/shutdown, viewport parity, or the one-L0/one-L1 recursive framework-plugin topology. Do not stage, commit, revert, clean, delete, or overwrite unrelated dirty work.

## Implementation and closure checkpoint (2026-07-23)

- Added the Qt-free `editor_contribution_contract` Module at the versioned L1 runtime boundary. Its first proven contribution kind is immutable, deterministic, JSON-safe `menu_command` data. Host-injected canonical ownership is mandatory; forged ownership, duplicate ids, live callbacks, live plugin/native objects, unsupported kinds, non-finite values, and mutable observations are rejected.
- Deepened the existing `RuntimePluginHost` metadata path rather than adding a registry. The Host parses and copies contribution facts at registration/reload time, keeps canonical `name` plus copied `declared_name` for legacy event compatibility, and passes the cached metadata to the Adapter. `ManualPluginReloadHost` refreshes that same metadata when replacing a candidate.
- Extended only `LegacyEditorPluginAdapter` to localize and project command-backed contributions into the current Qt `LayoutManager`. Generated live actions exist only inside the Adapter and invoke the single canonical command registry. Refresh uses exact Host active order; unload remains plugin-owned cleanup.
- Migrated `LocalizationUIPlugin` from `IMenuProvider` to Qt-free `IRuntimePlugin` declarative contributions. `LocalizationPlugin` now owns `editor.language.set`, so Qt UI, CLI/MCP/Agent callers can share one command handler after activation. The migrated plugin no longer imports PyQt, publishes live callbacks, subscribes to language changes, or reaches `EditorKernel`/`LayoutManager`.
- A full run initially exposed one genuine compatibility regression: Host canonical id `GoodPlugin` replaced the historical load-event name `good_plugin`. The fix preserves canonical internal identity while storing a copied `declared_name` fact used only by the legacy Adapter event seam. Focused compatibility tests then passed.
- Verification: contribution/Host focused `20 passed`; pre-fix broad focused groups were `58 passed, 8 subtests passed` and `77 passed, 9 subtests passed`; final non-signature suite `1430 passed, 34 skipped, 34 subtests passed in 163.12s`; real offscreen Editor smoke `plugins=13/20` with `LocalizationPlugin` and `LocalizationUIPlugin` activated, zero discovery errors, contribution refresh, and deterministic reverse shutdown.
- Guardrails: `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK`.
- Signature-only collection still stops at `ModuleNotFoundError: No module named 'cryptography'`. No dependency was installed, and signature verification is not claimed. Unblock path: explicitly provision `cryptography` into this repository's exact `.venv`, then rerun the signature test and full suite.
- E33 proves one real action contribution vertical slice. It does not prove dock/viewport migration, a replacement shell, native GPU geometry, or whole-engine completion.

## Unique next Gate

**Phase E34 -- Qt-Free Command Toolbar Contribution and Dynamic Action-State Projection.** Start with red tests and an audit of the `StandardUIPlugin` simulation play/stop toolbar slice. Extend the same Host-owned contribution contract only with the minimum command/placement/state facts proven necessary; consume existing command and simulation-state authorities, keep all Qt action/widget construction in `LegacyEditorPluginAdapter`, and do not create a second Host, registry, UI framework, renderer, or replacement shell.
