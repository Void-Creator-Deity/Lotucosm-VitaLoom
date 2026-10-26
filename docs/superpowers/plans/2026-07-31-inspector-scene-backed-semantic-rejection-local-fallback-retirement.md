# E174 Inspector Scene-Backed Semantic-Rejection Local-Fallback Retirement

Date: 2026-07-31
Status: complete

## Previous gate

E173 completed the exact Inspector fallback inventory. It proved the legacy stack is still necessary for non-scene canvas node/connection/object/dictionary compatibility because the Registry has no identity-safe, persistence-safe generic property command. It also found a smaller correctness fault: `_apply_scene_entity_property_command()` returns only a boolean. When a known scene entity's Registry mutation returns a failure envelope, `_on_property_changed()` treats that failure as "not applicable", executes a local legacy command, and then calls legacy sync which may attempt the Registry mutation again.

This violates the single-authority rule for the scene-backed route even though successful scene mutations already use semantic history. It is independent from designing future non-scene contracts.

## Objective

Retire the Inspector local fallback only for a **known scene-backed entity after a semantic Registry rejection**. Introduce an explicit three-way result that distinguishes:

1. no applicable scene-backed semantic route;
2. semantic mutation applied (followed by best-effort canonical `scene.open` rehydration);
3. semantic mutation rejected/failed after a scene identity and current scene path were established.

The caller must use the legacy `CommandStack` only for case 1. Case 3 must not locally mutate, must not retry Registry through `_sync_scene_entity_data`, and must not emit modified/command-executed side effects for the rejected edit.

## Protected contracts and non-goals

- Preserve existing scene-success behavior: Registry mutation first, then best-effort `scene.open`, then normal Inspector signals.
- Preserve every non-scene local fallback branch exactly: legacy node/connection/object/dictionary mutation still uses the local stack.
- Preserve Registry failure envelopes as authority outcomes; do not fabricate a local success.
- Do not remove `InspectorPanel.command_stack`, `_PropertyWriteCommand`, `ModifyNodePropertyCommand`, or `ModifyConnectionPropertyCommand` in this phase.
- Do not alter `.pond`, Registry command IDs, audit schema, CommandStack implementation, SR2D seams, manifests, or L0-L4 Qt-free boundaries.
- Do not touch `CONTEXT.md` or unrelated dirty worktree files.

## Implementation plan

1. Record this plan and an E174 fresh-session prompt before Runtime code changes.
2. Make `_apply_scene_entity_property_command()` return a named internal outcome (not applicable/applied/rejected) while retaining its existing payload construction and success rehydrate behavior.
3. Change `_on_property_changed()` so only `not applicable` reaches `_build_property_command()` and `command_stack.execute()`; a rejected scene mutation is a no-op for that object.
4. Add regression coverage proving a rejected scene entity edit makes exactly one Registry attempt, leaves local field values and local stack untouched, emits no Inspector success signals, and does not issue `scene.open`.
5. Retain and run legacy node fallback coverage to prove the local compatibility stack remains available for an object with no scene identity.
6. Run focused tests, audit/boundary checks, static outcome/stack search, and a scoped whitespace check. Update plan/prompt/status/index with exactly one next gate.

## Acceptance evidence

- A scene-backed Registry failure cannot invoke `command_stack.execute()`.
- It does not cause a second semantic command attempt through legacy sync.
- It does not mutate the in-memory entity or emit Inspector success signals.
- A non-scene node edit still invokes exactly one legacy stack execution and changes the node.
- Successful scene entity mutation still dispatches its semantic command and canonical rehydrate.
- E173's truth remains: `unified_undo_redo_runtime=false`, because all non-scene Inspector fallbacks remain legacy-local.

## Verification commands

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_inspector_command_binding.py `
  tests\test_inspector_property_mapping.py `
  tests\test_script_property_edit.py `
  tests\test_command_stack_behavior.py `
  tests\test_ai_command_audit_status_tool.py `
  tests\test_ai_command_undo_redo_command_path.py
& '.\.venv\python.exe' -B tools\check_ai_command_audit_status.py
& '.\.venv\python.exe' -B tools\check_core_boundaries.py
& '.\.venv\python.exe' -B tools\check_gui_boundaries.py
rg -n '_SCENE_ENTITY_(NOT_APPLICABLE|APPLIED|REJECTED)|command_stack\.execute' FrameCore\plugins\lotucosm-vitaloom\versions\1.0.0\runtime\core\VitaLoom\docks\inspector.py
git diff --check -- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py tests/test_inspector_property_mapping.py docs/superpowers/plans/2026-07-31-inspector-scene-backed-semantic-rejection-local-fallback-retirement.md docs/prompts/2026-07-31-inspector-scene-backed-semantic-rejection-local-fallback-retirement-prompt.md docs/mainline_status.md
```

## Completion record

Completed 2026-07-31.

- `InspectorPanel._apply_scene_entity_property_command()` now returns the named internal outcomes `_SCENE_ENTITY_NOT_APPLICABLE`, `_SCENE_ENTITY_APPLIED`, and `_SCENE_ENTITY_REJECTED`.
- The semantic route is applicable only when the active scene data proves it owns the entity ID. This preserves legacy canvas objects that happen to expose an `id`, while a known current-scene entity with a Registry failure is rejected rather than sent to the local stack.
- `_on_property_changed()` permits `_build_property_command()` / `command_stack.execute()` only after `not_applicable`; a rejected semantic write performs no local mutation, no legacy sync retry, and no Inspector success side effects.
- A successful semantic write still performs best-effort `scene.open` rehydration. A refresh exception/failure is logged after mutation success and does not reclassify that committed edit as a local-fallback candidate.
- Regression evidence: a rejected `entity.set_property` produces exactly one Registry call, no `scene.open`, no local-stack execution, no entity mutation, and no `projectModified` / `commandExecuted` signal. A non-scene legacy node with an `id` still executes one local command and changes position.
- Verification passed: focused offscreen suite `29 passed in 1.77s`; `check_ai_command_audit_status.py`, `check_core_boundaries.py`, and `check_gui_boundaries.py` all exited 0; static outcome/stack search and scoped `git diff --check` passed. Audit schema v4 still truthfully reports `unified_undo_redo_runtime=false`; full suite was intentionally skipped.

Exactly one next gate: **E175 -- Inspector Non-Scene Semantic Mutation-Contract Decision and Migration Gate**.