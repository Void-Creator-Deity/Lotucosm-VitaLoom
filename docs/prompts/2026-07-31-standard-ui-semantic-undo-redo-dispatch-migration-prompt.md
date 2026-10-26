# Fresh-session prompt -- E172 Standard UI Semantic Undo/Redo Dispatch Migration

Date: 2026-07-31
Status: complete

Continue only the bounded E172 migration. E171 proved that `InspectorPanel` is the sole production legacy `CommandStack` owner. Standard UI Ctrl+Z/Ctrl+Y is a runtime-reachable menu contribution path, but its handlers still inspect a `context.command_stack` that no versioned Runtime production source injects; it is a stale dispatcher, not a second owner.

## Required implementation

1. In `runtime/builtin/editor_extensions/standard_ui_plugin.py`, route `StandardUIPlugin.undo()` to Registry `command.undo` and `.redo()` to `command.redo`.
2. Preserve the returned semantic Registry envelope. Do not translate failures such as empty history into a synthetic local success.
3. After a successful result with `result.scene_path`, run canonical `scene.open` with that path. Do not rehydrate on a failed operation or blank path.
4. Replace Standard UI lifecycle tests that inject `context.command_stack` with recording-registry proof. Exercise direct handler behavior and a real registered menu contribution action.
5. Update the AI command audit schema/status for the Standard UI semantic dispatch proof, but leave `unified_undo_redo_runtime` false.

## Required safety constraints

- Do not touch Inspector local-stack retirement in E172. Its remaining non-scene fallback needs a separate mutation-contract inventory.
- Preserve `.pond`, Command Registry, Inspector bindings, SR2D seams, package/project manifests, and Qt-free L0-L4 contracts.
- Do not claim whole-editor unified undo/redo, overall refactor completion, native/OpenGL readiness, WorldBridge readiness, or default unified Pond/replay.
- `CONTEXT.md` is accidentally truncated and may only be restored from external history; do not write or reconstruct it.
- Preserve unrelated dirty work. Never stage, commit, reset, restore, clean, or delete it.

## Required proof

Run targeted Standard UI/audit/semantic undo-redo/durable project tests, the audit and core/gui boundary tools, a static no-`context.command_stack` search in Standard UI, and `git diff --check`. Then mark the plan and this prompt complete, update `docs/mainline_status.md` and `docs/INDEX.md`, record skips, and name exactly one next gate.

## Completion record

E172 is complete. Standard UI no longer reads `context.command_stack`: its undo/redo handlers run semantic `command.undo` / `command.redo`, preserve Registry error envelopes, and rehydrate successful scene history through `scene.open`. Tests cover direct dispatch, an empty-history failure without rehydrate, and a real Ctrl+Z menu contribution action. The audit schema is v4 with `standard_ui_semantic_history_dispatch=true`; `unified_undo_redo_runtime=false` remains required. Targeted proof passed `17 passed, 3 subtests passed in 1.28s`; audit and core/gui boundary tools passed; whole-worktree whitespace check is still blocked by unrelated pre-existing `docs/INDEX.md` trailing whitespace.

## Exactly one next gate

E173 -- Inspector Non-Scene Local-Fallback Mutation-Contract Inventory. Do not remove Inspector's local stack until every non-scene-backed mutation entry point has a precise authority/contract inventory and one bounded, proven retirement slice is selected.