# Phase E49 -- Qt-Free Editor Workflow Menu Commands and Exact Pond/File-Dialog/Clipboard Bridge Lifecycle

Date: 2026-07-26
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host -> versions/1.0.0/runtime L2-L4`. Reuse the existing `menu_command` contribution Interface, canonical command Registry, RuntimePluginHost copied metadata, Console capability, `.pond`/Cosmos/serializer Modules, dependency scanner, Player exporter, and current `LegacyEditorPluginAdapter`. Do not add another Host, command/menu Registry, contribution catalog, file-dialog/clipboard/widget DSL, Project World authority, Player/export authority, composition root, UI framework, or peer engine root.

PyQt `QFileDialog`, `QMessageBox`, and `QApplication.clipboard()` remain concrete current-Host implementation bridges. They must not become framework/plugin contract metadata.

## Previous Gate

E48 completed PackageManager's one portable reveal menu shell, one canonical command, and exact preservation of its existing Dock/fallback visibility and geometry lifecycle. Evidence: red `7 failed`; dedicated `8 passed`; protected `87 passed`; full non-signature `1605 passed, 34 skipped, 34 subtests passed`; compile, four guardrails, and standard/eager Editor smokes. Signature-only remains blocked because `.venv` lacks `cryptography`.

## Audited current truth

- Two built-in plugins still expose legacy live `IMenuProvider` callbacks: `EditorWorkflowPlugin` and `StandardUIPlugin`.
- `EditorWorkflowPlugin` is the smaller bounded slice: exactly five menu actions and no toolbar items.
- The five actions are: copy active `.pond` summary; export active `.pond` JSON; import `.pond` JSON with replace-active/new-world choice; scan scene dependencies and publish the report to the existing `UI_CONSOLE_PANEL`; and export the current project as a runnable Player.
- The plugin subscribes to `language_changed` only to remove and re-enumerate its live menu/empty toolbar callbacks. Once declarative menu facts are Host-refreshed, this subscription and live rebuild should disappear rather than become a second localization authority.
- The Module imports PyQt dialogs/clipboard at import time. E49 should make contribution/command metadata observable without importing PyQt by moving concrete Qt access behind bounded lazy bridge methods, without moving `.pond`/dependency/Player implementation authority into the Adapter.
- `StandardUIPlugin` is broader: 18 menu paths, two separators, a retained legacy save toolbar slice, Dock/layout actions, and wider event lifecycle. It remains out of scope.
- There are currently no dedicated EditorWorkflow lifecycle tests. E49 must establish executable behavior evidence before refactoring.

## Tasks

### Task 1 -- Red portable declarations and canonical command ownership

1. Prove exactly five immutable JSON-safe Host-copied `menu_command` contributions with stable File/Edit paths, localized label facts, deterministic order, empty payloads, canonical command IDs, no callbacks, no Qt/live objects, and no invented shortcuts.
2. Prove RuntimePluginHost copies metadata and canonicalizes ownership; declarative projection must not call `get_menu_items()` or empty toolbar enumeration.
3. Prove exactly five GUI-required canonical command specs and exact Adapter owner canonicalization, action invocation, unload/reload cleanup, and stale-action failure.
4. Prove plugin metadata imports while PyQt import is forbidden.

### Task 2 -- Bounded current-Host bridges and deterministic results

1. Replace top-level PyQt imports with lazy concrete bridge access for file dialogs, message boxes, and clipboard writes. Keep Qt values out of contribution, command, result, and Host-copied metadata.
2. Preserve direct compatibility methods but route canonical command handlers into the same behavior, not duplicated paths.
3. Return portable deterministic command envelopes for no active project/world, user cancel, success, validation/serialization failure, dependency results, Console publication availability, Player export, and unexpected errors.
4. Do not invent a universal dialog/clipboard Interface during this bounded Gate. The current Qt bridges remain explicit implementation seams for a future replacement Host.

### Task 3 -- Exact domain and lifecycle preservation

1. Preserve active-world fallback semantics, `.pond` summary JSON content, `PondSerializer(save_format="json")`, export extension behavior, and Cosmos replace-active/new-world activation semantics.
2. Preserve dependency scan source, summary/missing reporting, HTML escaping, `UI_CONSOLE_PANEL` logging fallback, and current warning/information details.
3. Preserve Player export through the existing `tools.export_player.export_project` authority and current project-path validation.
4. Remove only the obsolete language-time live menu rebuild subscription. Keep `on_load`/`on_unload` idempotent and do not add a second event/localization lifecycle.
5. Preserve `.pond`, Project World, AI Command/Inspector, SR2D, PackageManager, viewport/theme, package manifests, Player runtime closure, startup/shutdown, and all four Host authorities.

### Task 4 -- Protection and closure

1. Run dedicated red/green tests, `.pond`/serializer/Cosmos/dependency/Player protection, contribution/menu/command/Adapter/reload protection, and the complete non-signature suite.
2. Run modified-Module `compileall`, all four architecture guardrails, standard/eager real Editor smoke, and signature-only collection. Record exact blockers and do not install dependencies silently.
3. Update this plan to completed, convert its prompt to historical closure, update `docs/mainline_status.md`, `CONTEXT.md`, and `docs/INDEX.md`, and name exactly one next Gate.

## Completion boundary

E49 may complete only EditorWorkflow's five Qt-free menu-command shells, canonical execution, concrete file-dialog/message-box/clipboard bridge containment, obsolete live-localization rebuild removal, and exact preservation of `.pond`, dependency-scan, Console, and Player-export behavior. It does not migrate StandardUI; create portable file/dialog/clipboard/widget systems; rewrite Cosmos/serializer/Player/Project World authority; migrate concrete editor content; choose a replacement Host; make native/OpenGL default-ready; provision signatures; or complete the editor/engine.

## Implementation result

- `EditorWorkflowPlugin` now implements `IEditorPlugin + ICommandProvider`; it no longer implements `IMenuProvider`, publishes `get_menu_items()` / empty toolbar callbacks, or owns a language-time live-menu rebuild lifecycle.
- The plugin publishes exactly five immutable copied `menu_command` contributions: Edit / Copy Pond Summary plus File / Export Pond, Import Pond, Scan Dependencies, and Export Player. Every contribution contains only stable path/label/order/command facts, empty payload, no invented shortcut, and a canonical `plugin.editor_workflow.*` command ID.
- Exactly five GUI-required, mutating, non-undoable canonical commands are registered through the existing command Registry. `LegacyEditorPluginAdapter` canonicalizes ownership, projects actions, invokes the canonical Registry, and removes the exact actions/commands on unload and reload; stale actions fail instead of reaching a replaced plugin instance.
- Top-level PyQt imports were removed. `QFileDialog`, `QMessageBox`, `QInputDialog`, and `QApplication.clipboard()` are imported only inside bounded concrete current-Host bridge methods. No file-dialog, clipboard, widget, Console, Pond, or Player object enters Host-copied metadata or portable command results.
- Existing compatibility methods remain and canonical handlers call those same Implementations. Active-world fallback, summary shape and JSON formatting, `PondSerializer(save_format="json")`, export filter/extension behavior, replace-active identity preservation, imported-world naming/activation, dependency scan/report/Console escaping, and Player export authority remain unchanged.
- Command outcomes are JSON-safe and distinguish unavailable, cancelled, copied/exported/imported/scanned, failed, and partial presentation paths without moving domain policy into the Adapter.

## Verification evidence

- Stable executable E49 red line: `8 failed in 0.69s`. The first draft red fixture was corrected after proving that direct `QApplication.clipboard()` use without a `QApplication` can terminate the native process; the stable red line tests the intended Qt-free seam rather than relying on a crash.
- Final dedicated E49 lifecycle: `12 passed in 0.27s`.
- `.pond`/serializer/dependency/Player plus contribution/menu/command/Adapter/reload protection group: `76 passed in 7.77s`.
- First complete non-signature run: `1 failed, 1616 passed, 34 skipped, 34 subtests passed in 213.51s`; the sole unrelated failure was the fixed Asset Index cold wall-clock threshold (`11.03s` against `<10s`). The threshold and Asset Index implementation were not changed.
- Isolated Asset Index rerun: `1 passed in 9.09s`.
- Fresh second complete non-signature run: `1617 passed, 34 skipped, 34 subtests passed in 208.53s`.
- Modified Modules/tests pass `compileall` with `COMPILE_EXIT=0`.
- Guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Standard/eager real offscreen Editor smokes pass at `plugins=13/20` and `plugins=20/20`, with zero discovery/load errors, deterministic reverse shutdown, and no stale EditorWorkflow action/command state.
- Signature-only collection remains blocked by `ModuleNotFoundError: No module named 'cryptography'` (`1 error in 0.19s`, exit code `2`). No dependency was installed and signature verification is not claimed.

## Stable versus unfinished

Stable for E49: five portable EditorWorkflow menu shells, five canonical commands, exact copied/canonical ownership, bounded lazy Qt bridges, preserved `.pond`/Cosmos/dependency/Console/Player behavior, portable outcomes, and exact unload/reload cleanup.

One built-in legacy live menu provider remains: `StandardUIPlugin`. It also retains one legacy save toolbar action and separator, while its two simulation toolbar commands are already declarative. Concrete PyQt content, replacement-Host rendering/interaction parity, native/OpenGL default readiness, signatures, and whole-engine completion remain open.

## Next-Gate audit

`StandardUIPlugin` is the final built-in `IMenuProvider`. The current source exposes 16 live menu actions, two View separators, one legacy save-project toolbar action plus one toolbar separator, and two already-declarative simulation toolbar commands. Its behavior crosses Project World save/session authority, scene-save command/viewport snapshot collection, command-stack undo/redo, LayoutManager viewport/layout/Dock operations, PS experiment statusbar projection, project-opened presentation hints, application exit, localization refresh, and bounded current-Qt About/error/warning dialogs. The existing contribution contract has command-backed menu/toolbar facts but no structural separator fact; preserving the two menu separators and one toolbar separator therefore requires a narrowly closed contract decision rather than a general menu/UI DSL. The `Ctrl+Shift+P` shortcut collision between Save Project and Show PS Experiment Dock is existing behavior and must be recorded, not silently redesigned inside the migration.

## Unique next Gate

**Phase E50 -- Qt-Free Standard Editor Menu/Save Toolbar Commands and Exact Project/Layout/Dock/Status Bridge Lifecycle.** Migrate only StandardUI's remaining live menu and legacy save-toolbar slice through the existing Host-owned contribution Interface and canonical command Registry. Preserve Project World and scene-save authorities, command-stack behavior, LayoutManager viewport/layout/Dock behavior, PS experiment and project-opened statusbar lifecycles, current exit/About/error feedback, exact shortcuts and localization, the existing simulation toolbar contributions, and exact unload/reload cleanup. Add at most narrowly closed structural separator facts if executable parity requires them; do not add a general UI DSL, second Host/Registry/layout/Dock/project/session/status authority, replace the current Host, or claim the editor/engine complete.

