# Phase E50 -- Qt-Free Standard Editor Menu/Save Toolbar Commands and Exact Project/Layout/Dock/Status Bridge Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. Reuse the existing Host-owned editor contribution Interface, RuntimePluginHost copied metadata, canonical command Registry, `LegacyEditorPluginAdapter`, Project World session Host capability, scene command Registry, command stack, `LayoutManager`, Project World read model, event bus, and the two already-declarative simulation toolbar contributions. Do not add another Host, menu/toolbar/command/layout/Dock/project/session/status Registry, contribution catalog, composition root, UI framework, app shell, or peer engine root.

PyQt `QMessageBox`, native toolbar/menu objects, Docks, statusbar, viewport providers, and the application window remain concrete current-Host implementation. They must not become engine/plugin contract metadata.

## Previous Gate

E49 completed EditorWorkflow's five copied menu-command facts, five canonical commands, bounded lazy Qt file-dialog/message-box/clipboard bridges, exact `.pond`/Cosmos/dependency/Console/Player behavior, and exact unload/reload cleanup. Evidence: stable red `8 failed`; dedicated `12 passed`; protected `76 passed`; fresh full non-signature `1617 passed, 34 skipped, 34 subtests passed`; compile, four guardrails, and standard/eager Editor smokes. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- `StandardUIPlugin` is the final built-in live `IMenuProvider`.
- Its current live menu contains 16 actions: Save Project, Save Scene, Exit, Undo, Redo, Scene View, Game View, Save/Restore/Reset Layout, reveal Simulation/Ecology/PS Experiment Docks, toggle Inspector/Console floating, and About. The View menu also contains two structural separators.
- Its legacy toolbar contains one Save Project action and one separator. Its `simulation.toggle` and `simulation.stop` toolbar contributions are already immutable/declarative and must not be reimplemented or assigned a second simulation authority.
- Existing shortcuts must be copied exactly. `Ctrl+Shift+P` is currently assigned to both Save Project and Show PS Experiment Dock; E50 must preserve and explicitly test current projection behavior rather than silently choosing a new shortcut.
- Save Project delegates to the existing `project_world_session_host.save_project()` capability. Save Scene gathers the current SceneViewport snapshot when available and invokes canonical `scene.save`. These are deep existing authorities; E50 must not move their policy into contribution metadata or the Adapter.
- Undo/redo use the existing command stack. Scene/Game switching, layout save/restore/reset, Dock reveal, and floating toggles use the existing `LayoutManager` and current Dock objects.
- `ps_experiment_state` projects progress into the current statusbar. `project_opened` projects Project World presentation hints. These lifecycles remain necessary after live menu localization refresh is removed.
- `language_changed` currently exists only to rebuild live menus/toolbars. Declarative Host refresh should replace that narrow role, while the other two event subscriptions must remain exact and idempotent.
- About plus save warning/error feedback are current Qt bridges. They should be lazy and bounded, not expanded into a universal dialog/widget Interface.
- The contribution contract currently has `menu_command` and `toolbar_command`, but no structural separator fact. Exact removal of legacy callbacks requires one explicit minimal decision for two menu separators and one toolbar separator.

## Tasks

### Task 1 -- Executable red contract and exact inventory

1. Prove the exact 16 menu actions, two View separators, one save toolbar action, one toolbar separator, and the two unchanged simulation toolbar commands with deterministic identity/order/localization/shortcut facts.
2. Prove all copied metadata is immutable and JSON-safe, with Host-injected canonical owner, no callback, Qt/menu/toolbar/Dock/statusbar/viewport/plugin object, command stack, Project World Host, or LayoutManager value.
3. Prove declarative projection does not call `get_menu_items()` or `get_toolbar_items()`, and exact unload/reload cleanup leaves no stale action, separator, toolbar item, or command.
4. Prove the existing `Ctrl+Shift+P` collision and current Adapter projection behavior explicitly; do not resolve product UX policy in this migration Gate.

### Task 2 -- Narrow structural separator decision

1. If red parity proves separators are part of the retained surface, deepen the existing editor contribution Interface with only closed `menu_separator` and `toolbar_separator` facts.
2. Menu separator facts may contain only canonical owner, stable id, parent menu path, and deterministic order. Toolbar separator facts may contain only canonical owner, stable id, group/placement facts needed by the existing Adapter, and deterministic order.
3. Reject labels, commands, payloads, callbacks, native objects, unknown fields, forged ownership, and unsupported nesting. Project only through `LegacyEditorPluginAdapter`.
4. Do not generalize this into arbitrary menu nodes, widget schemas, renderer-neutral UI trees, conditions, expressions, callback DSLs, or a second catalog/Registry.

### Task 3 -- Canonical StandardUI commands and save toolbar reuse

1. Change StandardUI from `IMenuProvider` to the existing command-provider Interface and publish command-backed facts for the 16 actions plus one save-project toolbar fact. The toolbar action must reuse the same canonical Save Project command as the File menu action.
2. Preserve the two existing simulation toolbar contributions exactly; do not register or duplicate `simulation.toggle`, `simulation.stop`, or `simulation.transport.status` ownership.
3. Register only the canonical StandardUI commands required by the migrated actions, with accurate GUI/mutation/undo metadata and portable deterministic result envelopes.
4. Keep direct compatibility methods where existing callers/tests require them, but route canonical handlers through the same Implementation rather than duplicating Project, scene, layout, Dock, status, or exit policy.

### Task 4 -- Exact Project/scene/command-stack/layout/Dock/status lifecycle

1. Preserve current-project validation and `project_world_session_host.save_project()` authority, including warning/error/log behavior and Project World state transitions.
2. Preserve SceneViewport snapshot lookup, canonical `scene.save` invocation, current-scene-path guard, and error feedback without creating a second scene serializer/save authority.
3. Preserve command-stack undo/redo and LayoutManager Scene/Game viewport switching, layout save/restore/reset, Dock reveal/raise, and floating toggle fallback.
4. Preserve `ps_experiment_state` status text/timing and `project_opened` Project World presentation hint projection, with exact subscribe/unsubscribe idempotency and retry-safe cleanup where current behavior requires it.
5. Remove only obsolete language-time live menu/toolbar rebuilding after declarative localization refresh is proved.

### Task 5 -- Bounded Qt bridges and closure

1. Keep About, warning, critical, and Hub-required notices as lazy concrete current-Host bridges. No PyQt/native object may enter contribution or command metadata/results.
2. Run focused red/green tests, contribution/command/Adapter/reload protection, Project World/session/scene-save/toolbar/status/layout/Dock protection, and the complete non-signature suite.
3. Run modified-Module `compileall`, all four architecture guardrails, standard/eager real Editor smoke, and signature-only collection. Record exact blockers without silently installing dependencies.
4. Update this plan to completed, convert its prompt to historical closure, update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`, and name exactly one next Gate after a fresh post-E50 audit.

## Completion boundary

E50 may complete only the final built-in StandardUI live menu and legacy save-toolbar migration, a narrowly closed separator fact if required for exact parity, canonical command execution, exact Project/scene/command-stack/LayoutManager/Dock/statusbar/event behavior, bounded current-Qt feedback, and exact unload/reload cleanup. It does not redesign shortcuts or product UX; rewrite Project World, scene, simulation, layout, Dock, status, localization, or command authorities; migrate concrete editor content; select/build a replacement Host; make native/OpenGL default-ready; provision signatures; or complete the editor/engine.

## Closure evidence

- Stable executable red: `7 failed in 0.32s`.
- Focused StandardUI/contribution/Adapter/toolbar/Project World session green: `73 passed in 1.85s`.
- Stale supported-kind protection was updated after the first full run; its focused rerun passed `60 passed in 1.40s`.
- Expanded command/localization/layout/Project World/scene bridge/plugin lifecycle protection: `163 passed, 1 skipped in 2.87s`.
- First full non-signature run: `1 failed, 1623 passed, 34 skipped, 34 subtests passed in 189.72s`; the sole failure was the stale supported-kind assertion, not runtime behavior.
- Fresh second full non-signature run: `1624 passed, 34 skipped, 34 subtests passed in 190.42s`.
- Modified runtime Modules and tests pass `compileall`.
- Architecture guardrails pass: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Real offscreen Editor smoke passes in standard mode (`plugins=13/20`) and eager mode (`plugins=20/20`), with zero discovery/load failures and deterministic reverse shutdown.
- Signature-only collection remains environmentally blocked: `ModuleNotFoundError: No module named 'cryptography'`, `1 error in 0.23s`, exit code `2`. No dependency was installed and signature verification is not claimed.

## Completed result

`StandardUIPlugin` now publishes exactly 22 immutable Host-copied facts: 16 `menu_command`, two `menu_separator`, three `toolbar_command`, and one `toolbar_separator`. The Save toolbar and File/Save Project share the same canonical command; the two pre-existing simulation toolbar commands retain their existing authority. The narrowly closed separator facts preserve exact menu/toolbar structure without introducing a general UI DSL. Save Project, scene save, command-stack undo/redo, LayoutManager viewport/layout/Dock operations, Project World presentation hints, PS experiment status, exit, and bounded Qt feedback continue through their existing deep Modules and current-Host Adapter seams. Obsolete live menu/toolbar getters and language-time rebuilding were removed from StandardUI, while exact project/status event cleanup remains idempotent.

## Next audited Gate

Fresh post-E50 audit found no runtime plugin implementing `IMenuProvider` and no runtime implementation of `get_menu_items()` or `get_toolbar_items()`. The only remaining live-provider seam is dormant compatibility code in `plugin_interfaces.py` and `LegacyEditorPluginAdapter`; localization still calls legacy-named `refresh_legacy_menu_contributions()` / `refresh_menu_providers()` even though all built-in menu/toolbar shells are declarative.

**Unique next Gate: Phase E51 -- Qt-Free Declarative Menu/Toolbar Refresh and Obsolete Live Provider Interface Retirement.** Remove only the now-unused `IMenuProvider` live callback Interface and its Adapter registration/refresh branches; rename the narrow localization refresh seam around copied declarative contributions; and prove exact Host order, localization, state refresh, unload/reload, and current Qt projection parity. Keep `LegacyEditorPluginAdapter` as the current concrete UI Host Adapter and do not migrate/remove Dock, viewport, theme, Project World, scene, command, layout, status, or simulation authorities.