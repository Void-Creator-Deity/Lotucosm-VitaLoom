# 2026-07-19 Project World Host Capability Catalog and Legacy Consumer Decoupling

## Purpose

Continue the confirmed recursive framework/plugin topology by replacing legacy consumer imports of the concrete PyQt `ProjectManager` with narrow Project World Host capability Interfaces. FrameCore remains L0; `lotucosm-vitaloom` remains the sole L1 engine/product plugin and downstream plugin-host framework; the versioned runtime remains the product boundary. This Gate does not turn Project World, `vitalloom.*`, or any UI Adapter into a peer FrameCore plugin.

## Starting evidence

- E9/E10 established explicit open/session Host seams, but other L2/L3 consumers still import `get_project_manager` to read the current World path/configuration, persist package state, read recent Worlds, create a World, or trigger manifest validation.
- `standard_ui_plugin.py` subscribes to a concrete PyQt signal and contains an unused recent-project menu even though World creation/open/switching belongs to Hub.
- `plugin_runtime_ops.py`, `game_viewport.py`, `asset_dependency.py`, `evolution_context.py`, and `sr_session_feedback.py` use the concrete manager as a read model.
- `package_manager_plugin.py` constructs `PackageOperationService` with the whole manager and reaches for a removed private manifest method, so its Interface is both over-broad and partly non-functional.
- `project_wizard.py` captures the manager singleton instead of receiving a creation capability.
- `EditorContext.services` already provides a runtime registry, but Project World keys, Protocols, narrow adapters, deterministic unavailable behavior, and one registration point do not yet exist.

## Architecture decisions

1. Add a Qt-free `project_world_capabilities.py` Module defining the capability catalog keys, narrow runtime-checkable Protocol Interfaces, resolver functions, deterministic unavailable Adapters, and one registration function.
2. Publish separate capabilities rather than a replacement god port:
   - current Project World read model: path + JSON-safe configuration snapshot;
   - Project World configuration Host: top-level field updates only;
   - recent Project World registry: read-only paths;
   - Project World creation Host: templates + creation;
   - current manifest validation Host: explicit refresh/report.
3. The catalog lives on the existing runtime service registry. It is a version-runtime capability catalog owned by the L1 engine plugin Host, not a new FrameCore plugin layer.
4. The concrete PyQt `ProjectManager` remains the current Host Adapter. Registration wraps it in narrow Adapter objects so consumers cannot recover the whole manager through a capability lookup.
5. Resolver functions accept an explicit editor/host context first. A no-context lookup may consult an already-existing editor context, but it must not instantiate a new GUI singleton and must return deterministic unavailable behavior when no Host exists.
6. Capability read results are copied into strict JSON-safe snapshots so callers cannot mutate the manager cache by alias.
7. Standard UI deletes its dead recent-project menu/subscription. Hub remains the authority for creation/open/switching; recent registry remains available to a Hub Adapter without leaking PyQt signals.
8. Package operations receive only the read/configuration capabilities they require. Manifest realignment uses a public manifest-validation capability and structured evidence; it does not call a private manager method or inspect `editor_context` through the manager.
9. Project wizard receives or resolves only the creation Host capability. Composition roots may still construct the concrete manager because Adapter construction is legal there.
10. Compatibility aliases may remain on `ProjectManager`, but migrated consumers are guarded against importing or naming the concrete manager.

## Defensive red tests

- Import `project_world_capabilities.py` and exercise its read-only/test Adapter while all PyQt imports are blocked.
- Verify catalog registration publishes distinct narrow Adapter objects, not the concrete manager, and that each object satisfies only its intended Interface.
- Verify read snapshots are detached, strict JSON-safe mappings and unavailable Adapters are deterministic.
- Verify a second functional test Adapter can drive read/configuration/creation/manifest consumers, proving real seams rather than nominal Protocols.
- Add source/AST guards preventing concrete manager imports in migrated consumers while allowing `editor_kernel.py`, `player_shell.py`, `project_manager.py`, and compatibility exports as composition/Adapter locations.
- Verify PackageOperationService uses narrow capabilities and project state writes still persist.
- Verify Standard UI no longer subscribes to concrete recent-project signals and still reads presentation/save behavior through capabilities.
- Verify GameViewport, asset dependency, evolution defaults, SR feedback, plugin runtime operations, package manager, and project wizard consume capability Interfaces without changing their public behavior.
- Regress Project World E9/E10, .pond, AI command registry, Inspector binding, SR2D seams, manifests, L3/L4 lifecycle, Player/export, and package operations.

## Compatibility and non-goals

- Do not remove PyQt6/QPainter/OpenGL or select a successor UI Host.
- Do not migrate to Unity, Godot, Unreal, Electron, or another shell.
- Do not move runtime code outside `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Do not change `.pond` semantics, command registry contracts, Inspector binding, SR2D public seams, package/project manifests, or Project World transition ordering.
- Do not expand this Gate into rendering, native acceleration, OpenGL-default, plugin watcher, or unrelated package transaction work.
- Do not replace one concrete singleton with another all-powerful global Project World facade.

## Verification and completion

1. Run focused E11 capability/import tests, including PyQt-blocked import smoke and real PyQt Adapter compatibility.
2. Run E9/E10 Project World transition regressions and each migrated consumer's focused tests.
3. Run broader command/Inspector/SR2D/package/L3-L4/Player regressions.
4. Run project plugin model, core boundary, GUI boundary, and release consistency guardrails.
5. Run `py_compile`, AST/import checks, strict JSON checks, and changed-region trailing-whitespace checks.
6. Record exact proof/skips in `docs/mainline_status.md` and name exactly one next Gate in one fresh-session prompt.

## Implementation evidence

- Added Qt-free `core/VitaLoom/project/project_world_capabilities.py` inside the existing L1 plugin version runtime. It defines five narrow capability Interfaces, strict JSON snapshot/path normalization, deterministic unavailable Adapters, legacy Host Adapters, registration, and resolvers.
- Capability groups are detected and published independently. A Host may expose only the read model; a multi-method group with partial implementation fails explicitly instead of creating a hidden god Host.
- `EditorKernel` and `PlayerShell` publish only the capabilities their concrete/injected Host actually exposes. Ordinary consumers no longer import `project.project_manager` or `get_project_manager`.
- Standard UI removed its dead recent-project menu and concrete PyQt recent-signal subscription; Hub remains the creation/open/switch authority.
- Package operations now consume read/configuration/manifest-validation capabilities. Durable transaction store creation first reads `operation_service.project_world_read_model`, with a narrow legacy fallback only for transaction-focused compatibility Adapters.
- Asset dependency uses delayed capability resolution so a singleton created before composition does not permanently capture an unavailable Adapter.
- `ProjectManager.refresh_current_project_manifest_validation()` is the public Host seam; package code no longer reaches a missing/private validation method.

## Verification evidence

- Defensive red stage: `4 failed, 1 skipped` before the capability catalog and consumer migration.
- E11 focused capability/package/asset/PyQt/receipt suite: `41 passed in 1.67s`.
- E9/E10 plus Project/package compatibility: `105 passed in 2.26s`.
- Eight migrated-consumer regressions: `143 passed in 2.85s`.
- Package collection excluding the interpreter-specific cryptography test: `80 passed, 1 skipped, 17 subtests passed in 4.22s`.
- Command registry and Inspector: `139 passed in 10.40s`.
- L3/L4 plugin Host, Player, Hub, and export: `81 passed, 1 skipped in 7.19s`.
- SR2D, QPainter, OpenGL, and viewport: `232 passed, 23 skipped in 9.05s`.
- Package signature warn-only tests under the system interpreter: `2 passed in 0.21s`; `.venv` has PyQt6 but no `cryptography`, while the system interpreter has `cryptography` but no PyQt6.
- Project plugin model, core boundary, GUI boundary, and release consistency guardrails all passed.
- Full-suite first run under `.venv` (signature file excluded): `1141 passed, 25 skipped, 34 subtests passed, 5 failed in 147.27s`. One failure was the E11 package-receipt regression and was fixed. The other four (loaded asset-index timing, selected-projection order pollution, plugin-model gate, and headless selected-entity subprocess) passed in isolated reruns. A second full-suite run was not performed, so this Gate does not claim a fresh whole-suite all-green result.
- Final syntax verification: `AST OK: 20 files`. Final capability plus receipt check on 2026-07-20: `17 passed in 1.20s`.

## Completion decision

E11 is complete: ordinary Project World consumers now depend on narrow runtime capability Interfaces, while concrete `ProjectManager` construction remains limited to composition/Adapter locations. This does not mean the whole engine is complete, PyQt has been removed, a successor UI Host has been selected, OpenGL is default-ready, or native acceleration is complete.

**Unique next Gate: Phase E12 — Project World Host Adapter Factory, Ownership and Disposal Composition Authority.** It will remove entry-point/private-singleton lifecycle manipulation from `runtime/main.py` and `player_shell.py` by introducing an explicit factory/ownership/disposal seam. It must preserve the L0–L4 topology and must not delete PyQt or choose a new GUI Host.

## Worktree discipline

The repository already contains extensive user/prior migration work. Do not stage, commit, reset, restore, clean, delete, re-encode, or broadly whitespace-clean unrelated files. Change only E11-owned regions and inspect those regions explicitly.
