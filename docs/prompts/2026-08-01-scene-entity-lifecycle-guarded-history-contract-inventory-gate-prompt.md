# E181 Fresh-Session Prompt — Scene Entity Lifecycle Guarded-History Contract Inventory Gate

E180 is complete with zero migration: no active-scene Inspector name control exists, and no safe existing `.pond` name-string schema was found.

## Read first

- `docs/superpowers/plans/2026-07-31-inspector-scene-entity-name-mutation-contract-discovery-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/scene_viewport.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/ui/command_actions.py`

## Rules

- Audit `entity.create`, `entity.delete`, restore paths and their durable inverse recipes before changing runtime behavior.
- Preserve `entity_id` as stable identity; preserve `.pond` entity and connection ordering exactly unless the current command contract explicitly changes it.
- A snapshot is not automatically a stale-safe inverse. Prove expected-current behavior for both undo and redo, in-memory and fresh Registry project replay, before calling it guarded.
- Successful semantic history may rehydrate via `scene.open`; a failed semantic history call must not fall back to legacy `CommandStack` or emit success effects.
- Keep `unified_undo_redo_runtime=false` authoritative. Do not touch `CONTEXT.md` or unrelated dirty work.

## Recorded outcome

E181 completed a narrow guarded-history migration for `entity.create -> undo entity.delete -> redo entity.create` only. Guarded create undo verifies the created entity's complete snapshot, its original ordered index, and its incident connection rows; guarded redo verifies the complete canonical post-undo entity and connection lists. Mismatches reject before write for both same-process history and fresh-Registry durable replay. Focused proof passed `17 passed, 3 subtests passed`, and the expanded scoped suite passed `51 passed, 9 subtests passed`.

Do not extend this result to `entity.delete -> entity.restore_deleted_snapshot`: that restoration inverse still lacks an expected-current full-scene witness, so it remains non-stale-safe. Full-suite pytest was not run, and the audit status remains schema v4 with `unified_undo_redo_runtime=false`.

## Follow-up

Continue only through **E182 -- Scene Entity Delete-Restore Guarded-History Contract Design Gate**. First design and prove a full post-delete witness for restore/redo; do not implement a migration if the existing `.pond` semantics cannot support safe stale rejection.