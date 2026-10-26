# Phase E35 -- Qt-Free Dock Contribution Contract and Host-Owned Dock Surface Projection

Date: 2026-07-23
Status: complete

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (versioned product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

The engine is the L1 plugin and is itself the recursive derived plugin framework. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the only Host authorities. `LegacyEditorPluginAdapter` is the current PyQt Host Adapter. `IDockProvider`, `QDockWidget`, Qt enums, `EditorKernel`, and `LayoutManager` are legacy/current Host implementation details, not the future engine-plugin Interface.

E35 must deepen the existing editor contribution Interface and current Adapter seam. It must not create a second Host, Dock registry, contribution catalog, manifest authority, composition root, widget DSL, UI framework, renderer framework, peer L1 engine plugin, or replacement shell. It must not migrate the project to Unity, Godot, Unreal, Electron, or another app shell.

## Previous Gate summary

E34 is complete:

- the existing Qt-free editor contribution Interface now supports command-backed menu and toolbar facts;
- `simulation.transport.status` is the canonical read-only transport observation;
- `LegacyEditorPluginAdapter` alone creates live Qt actions/icons and owns refresh-event subscriptions/cleanup;
- `StandardUIPlugin` migrated only the simulation toggle/stop toolbar slice;
- closure evidence is red `13 failed, 6 passed`, E34 `20 passed`, focused `39 passed`, expanded `94 passed`, complete non-signature `1450 passed, 34 skipped, 34 subtests passed in 162.35s`, Editor smoke `plugins=13/20`, and four green architecture guardrails;
- signature-only collection remains blocked because the exact project `.venv` lacks `cryptography`.

E34 did not migrate docks, viewports, themes, or implement a replacement Host.

## Task 1 audit checkpoint

The default package graph activates eight concrete `IDockProvider` implementations. Their current responsibilities are:

| Provider | Stable dock facts | Qt/current-Host implementation | Domain/event/lifecycle facts | First-slice assessment |
|---|---|---|---|---|
| `HierarchyPlugin` | `Hierarchy`; localized title; left; visible; closable | constructs `QDockWidget` and `HierarchyPanel`/fallback tree | six scene/entity/language subscriptions; direct panel mutation; one audited mismatch: `scene_hierarchy_updated` is subscribed but not unsubscribed | not first; event ownership and stale subscription need a dedicated slice |
| `InspectorPlugin` | `Inspector`; localized title; right; visible; closable | constructs `QDockWidget` and rich `InspectorPanel`/fallback | wrapper owns only language-title refresh; panel already uses canonical command/read-model/selection seams | **selected first slice**: smallest stable shell Interface over a large real Implementation |
| `ProjectBrowserPlugin` | `Project`; localized title; bottom; visible; closable | constructs `QDockWidget` and `ProjectPanel` | project/asset/refresh/language events; canonical `scene.open` and `asset.create`; language refresh directly removes/adds docks through `LayoutManager` | not first; contains an Adapter-ownership violation to remove later |
| `ConsolePlugin` | `Console`; localized title; bottom; visible; closable; tabbed with `Project` | constructs dock/panel and logging bridge | publishes exact `UI_CONSOLE_PANEL` capability and owns logging handler/publication cleanup | later slice must preserve exact capability and logging lifetime |
| `PackageManagerPlugin` | `Package Manager`; localized title; right; hidden; closable; no default tab | constructs a large dock/floating-window UI and menus | package capabilities, Project World read/configuration Hosts, project/plugin events, kernel signals, floating geometry, language rebuild | not first; too many coupled lifecycles for contract discovery |
| `EcologyDashboardPlugin` | `EcologyDashboard`; right; hidden; closable | constructs dock and pull-based SR dashboard/fallback | no event subscription; panel reads current SR snapshot through current context | viable later static slice; title localization facts are currently incomplete |
| `SimulationControlPlugin` | `SimulationControl`; localized title; left; hidden; closable; tabbed with `Hierarchy` | constructs dock and `SimulationControlPanel` | transport/language subscriptions; widget reference ownership is inconsistent because the created dock is not retained on the plugin | later slice after lifecycle normalization |
| `PsExperimentPlugin` | `PsExperiment`; localized title; right; hidden; closable; tabbed with `EcologyDashboard` | constructs dock and PS experiment panel/fallback | publishes PS experiment/runtime snapshot capabilities and owns cancellation/unbind/release | later slice must preserve service lifetime independently from surface lifetime |

The optional community `CustomDockPlugin` remains a legacy compatibility consumer and is not active in the default package graph. E35 must preserve that path while migrating built-ins incrementally.

### Stable facts proven by the audit

The minimum cross-Host vocabulary is bounded to:

- canonical owner plus contribution id;
- stable `dock_id` used for layout persistence and cleanup;
- localization key/default title;
- portable area token (left/right/top/bottom);
- default visibility;
- close/float/move permissions;
- optional stable `tabbed_with` dock id;
- deterministic order and refresh-event names where the title must update.

The following are explicitly **not** contribution facts:

- `QDockWidget`, `QWidget`, Qt enum/flag/icon objects, factories, callbacks, import paths, plugin instances, `EditorKernel`, `LayoutManager`, event buses, service objects, command registries, arbitrary expressions, or replacement-Host widget trees.

### Selected first vertical slice

`InspectorPlugin` is selected because the dock shell has minimal stable facts while the content Implementation is substantial and already exercises canonical Inspector commands/read models. This demonstrates Depth: a small contribution Interface yields a full real surface through the current Adapter.

The first slice migrates **dock shell authority only**. It does not claim that the Qt `InspectorPanel` is cross-Host or that replacement-Host content parity exists. The existing `IDockProvider` implementation may remain as a temporary current-Adapter content bridge during this phase, but no live factory or Qt object may enter Qt-free contribution observations and no new Qt-specific framework Interface may be promoted as engine authority.

## Tasks

### Task 2 -- Establish red contract and projection tests

- Add red tests for one minimal `dock_surface` contribution with the proven stable facts only.
- Reject Qt/native values, callables/factories, plugin instances, forged owners, duplicate ids/dock ids, invalid area/tab tokens, unknown fields, and mutable/non-JSON-safe observations.
- Prove deterministic ordering and Qt-free import/observation.
- Add current Adapter red tests for portable-area mapping, localized title, feature/default-visibility projection, exact owner cleanup, reload replacement, shared refresh-event deduplication, and coexistence with legacy providers.
- Add a real Inspector slice red test proving no duplicate dock, no direct layout refresh in the plugin, and preserved content/command/read-model behavior.

### Task 3 -- Extend the existing contribution Interface minimally

- Add `dock_surface` to `editor_contribution_contract`; do not create another schema/catalog/registry.
- Keep Host-injected canonical ownership, immutable copied metadata, deterministic sorting, and fail-closed diagnostics.
- Use portable tokens and booleans only; do not encode Qt enum numbers or widget construction.
- Extend the existing Runtime Host metadata/reload path rather than adding another discovery or lifecycle authority.

### Task 4 -- Project dock shell facts through the current Adapter

- Map portable placement/features to Qt only inside `LegacyEditorPluginAdapter` or a small subordinate concrete Adapter Module it owns.
- Make declarative dock identity authoritative for registration and cleanup while preserving a fallback path for unmigrated legacy `IDockProvider` plugins and the community example.
- Keep content construction in the current legacy implementation during this first slice; do not pretend it is host-neutral and do not put the callable/object into metadata.
- Localize/refresh titles in place without plugin rediscovery, direct plugin access to `LayoutManager`, duplicate docks, or leaked subscriptions.
- Preserve exact reload/unload/shutdown ownership and delayed tabification semantics.

### Task 5 -- Migrate the Inspector shell slice

- Declare the Inspector dock shell as Qt-free facts and remove duplicated stable shell configuration/title-refresh ownership from `InspectorPlugin`.
- Preserve the current `InspectorPanel`, selection flow, command binding, SR selected-component projection, WorldBridge diagnostics, fallback behavior, layout persistence id, default placement/visibility, reload, and shutdown.
- Do not migrate Inspector content to a generic widget DSL or select a replacement shell.

### Task 6 -- Regression and closure

- Run focused contract, Runtime Host metadata/reload, Adapter projection/cleanup, Inspector command/read-model/UI, LayoutManager, localization, startup/shutdown, and community compatibility tests.
- Run protected Project World, `.pond`, AI command, Inspector, SR2D/viewport, Player/export, package/project manifest, and plugin lifecycle regressions.
- Run the complete non-signature suite, real offscreen Editor smoke, `compileall`, and all four architecture guardrails.
- Attempt signature-only collection without silent installation and record the exact blocker/unblock path.
- Update plan/status/context/index and create exactly one next Gate only after E35 evidence closes.

## Completion bar

E35 is complete only when:

1. Inspector dock identity/title/placement/visibility/features are validated Qt-free contribution facts;
2. the current Adapter projects those facts with real Inspector content and exact lifecycle ownership;
3. no Qt/native object, widget factory, callback, plugin instance, kernel/layout object, alternate registry, or widget DSL leaks into the contribution Interface;
4. unmigrated legacy/community dock providers continue to work;
5. Inspector commands/read models, localization, layout persistence, reload/unload/shutdown, full regression, Editor smoke, and architecture guardrails pass.

E35 still will not prove a replacement Host implementation, cross-Host Inspector content parity, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or the whole engine complete.

## Preserved contracts

Do not break `.pond`, AI command registry flows, Inspector command binding, SR2D, package/project manifests, L4 Project World addons, Player/export, plugin reload/startup/shutdown, viewport parity, or the one-L0/one-L1 recursive framework-plugin topology. Do not stage, commit, reset, restore, clean, delete, or overwrite unrelated dirty work.

## Closure evidence

E35 is closed with the bounded Inspector Dock shell slice implemented and verified:

- Red contract/projection baseline: `13 failed, 2 passed`.
- E35 contract plus legacy contribution/Adapter projection focus: `67 passed`.
- Expanded Host/reload/layout/Inspector/localization/lifecycle focus: `185 passed`.
- Protected cross-domain regression (Project World, `.pond`, AI command/Inspector binding, SR2D/viewport, Player/export, manifests, community compatibility, reload/startup/shutdown): `164 passed in 10.30s`.
- Complete non-signature suite: `1465 passed, 34 skipped, 34 subtests passed in 160.72s`.
- Modified Modules and E35 tests pass `compileall`.
- Real offscreen Editor smoke: `suite=lotucosm.vitaloom product=lotucosm-vitaloom@1.0.0 plugins=13/20`; Inspector registration, layout exercise, refresh, and reverse shutdown all succeeded with zero discovery errors.
- Architecture guardrails: `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK`.
- Signature-only collection remains blocked at collection by `ModuleNotFoundError: No module named 'cryptography'` in the exact repository `.venv`; no dependency was installed.

The truthful completion boundary is the Inspector Dock shell projection through the current `LegacyEditorPluginAdapter`. The Inspector Qt content remains a legacy implementation bridge; E35 does not prove a replacement Host, cross-Host content parity, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature provisioning, or whole-engine completion.

## Unique next Gate

**Phase E36 -- Qt-Free Hierarchy Dock Contribution and Host-Owned Hierarchy Refresh Ownership.** Reuse the existing `dock_surface` Interface for the bounded `HierarchyPlugin` shell, then close the audited `scene_hierarchy_updated` subscription ownership gap without creating a second Host, registry, Dock/UI framework, widget DSL, or replacement shell. First write the red lifecycle/refresh tests; keep hierarchy content and canonical scene/entity authorities behind the current Adapter seam.
