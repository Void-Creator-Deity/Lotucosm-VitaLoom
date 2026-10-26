# E180 Inspector Scene-Entity Name Mutation Contract Discovery Gate

Date: 2026-07-31
Status: complete

## Previous gate

E179 proved that the remaining `script.set_property` and `entity.set_property` Inspector routes are broad compatibility surfaces, not complete stale-safe semantic-history contracts. No generic migration is permitted.

## Objective

Audit exactly one potential field-specific replacement: an active-scene entity's display `name`. Decide whether it can become a narrow semantic command without changing `.pond` semantics or broadening generic mutation authority. Implement at most one name-only migration only after every proof below is present.

## Required evidence before implementation

1. Active `.pond` owner and stable `entity_id`, distinct from editable `name`;
2. canonical JSON location and existing `name` serialization/default rules;
3. exact string-only schema, including allowed normalization, empty-value policy and deterministic error behavior;
4. a dedicated name command with an exact expected-current witness for both undo and redo;
5. same-process and fresh-registry durable stale undo/redo rejection that never writes;
6. Inspector `scene.open` rehydration after success and terminal rejection with no local fallback;
7. compatibility analysis for entities that omit `name`, legacy UI objects and existing generic command callers.

## Non-goals

- Do not add, extend or rebrand a generic Registry property setter.
- Do not change `script.set_property` selector grammar or value behavior.
- Do not migrate non-scene/ownerless local fallback.
- Do not claim unified undo/redo, WorldBridge, native acceleration or OpenGL default readiness.

## Completion rule

If any prerequisite is absent, record the precise blocker and retain current behavior. If all prerequisites are proven, migrate only `name`, add narrow schema and guarded-history tests, and update the audit/mainline evidence. Preserve `.pond`, Inspector binding, AI command flows and `unified_undo_redo_runtime=false` unless independently changed with proof.
## Decision and evidence

**Decision: zero runtime migration.** The proposed name-only command is not justified by the existing production surface.

1. `entity_id` is the stable entity identity and the canonical stored value is `entities[id].name`; `entity.create` defaults a missing `name` to `entity_id`.
2. The active `.pond` entity Inspector renders only position axes and script fields. It reads `name` only to form its status label; it creates no editable `prop_name="name"` control. The legacy node Inspector also exposes no name field. Therefore there is no real active-scene Inspector name write to migrate.
3. If an unproven future control were to call the current route, it would enter broad `entity.set_property`; the command accepts arbitrary dotted paths and JSON values, and its snapshot inverse has no expected-current witness. It cannot be treated as a name contract.
4. `.pond` validation checks duplicate IDs and dependencies but defines no `name` string policy. Existing sources provide no compatibility-safe empty-value, normalization, maximum-length, or non-string error contract. A new ASCII-only or trim-on-write rule would be an undocumented file-format change.
5. The Inspector's authority boundary itself is already correct: active-scene semantic success best-effort rehydrates with `scene.open`, while rejection is terminal and never falls through to a local command. E175/E177 non-scene and ownerless local fallback remains unchanged.

## Verification

- Focused offscreen Inspector/scene-history/audit suite: `46 passed, 9 subtests passed in 2.85s`.
- `py_compile` passed for the inspected Inspector, binding, runtime-command, and Registry modules.
- `check_ai_command_audit_status.py`, `check_core_boundaries.py`, and `check_gui_boundaries.py` passed. Audit remains schema v4 with `unified_undo_redo_runtime=false`.
- Repository-wide pytest was intentionally skipped: E180 is a no-runtime-change discovery gate, and its focused suite proves the preserved existing seam rather than an unimplemented name API.

## Fallback and unblock

Retain the current status-label-only name behavior and broad compatibility command unchanged. A future feature request to edit active-scene entity display names must first define a `.pond` string policy, introduce a visible Inspector field, add a dedicated guarded `entity.set_name` command with same-process and fresh-registry stale replay proofs, and verify the existing terminal-rejection/rehydration boundary. It must not retrofit generic `entity.set_property` or create a local fallback after rejection.