# E189 Fresh-Session Completion Prompt -- Scene Asset Application Deterministic Guarded-History Contract Inventory Gate

E189 is complete. `asset.apply_to_scene` validates an existing project asset path but does not read its content; it creates one payload-derived entity, appends it to `entities`, and does not mutate `connections`, `components`, or other scene collections. The command now returns the exact serialized entity, append slot, and full entity/connection witnesses.

Its history recipe is source-independent: guarded `entity.delete` undoes the placement, and guarded `entity.create(..., preserve_entity_snapshot=True)` redoes the captured entity without resolving or rereading the asset. Both in-memory and fresh-registry durable replay reject stale entity/connection state before writes and do not append rejected replay audit entries. The command is a representative durable-project replay candidate; audit remains schema v4 with `unified_undo_redo_runtime=false`.

Evidence: `tests/test_ai_command_asset_apply_guarded_history.py` plus related command history tests passed `43 passed, 10 subtests passed in 3.91s`; compilation, audit-status, core-boundary, and GUI-boundary guards passed. No whole-repository pytest, global unified-history, native acceleration, or OpenGL-default claim is valid.

The next and only gate is E190: inventory every `mutates=True, undoable=False` command and classify whether it is intentionally UI/transient or a persisted project/scene mutation needing an explicit history decision. Do not mark commands undoable merely to improve a count.
