# E182 Fresh-Session Prompt — Scene Entity Delete-Restore Guarded-History Contract Design Gate

## Recorded outcome

E182 completed `entity.delete -> undo entity.restore_deleted_snapshot -> redo entity.delete`. Delete records complete ordered post-delete entity/connection lists; restore validates those optional witnesses before write and returns complete ordered post-restore lists; Registry uses the latter as the guarded delete-redo witness for same-process and fresh-Registry durable replay.

Same-ID recreation, survivor edits, connection reorders, and endpoint removal reject before `_write_json()`. Failed in-memory and durable replay operations retain retry eligibility after the exact canonical state is restored. Focused proof passed `21 passed, 10 subtests passed`; expanded scoped proof passed `55 passed, 16 subtests passed`.

The full test suite was not run. Audit remains schema v4 with `unified_undo_redo_runtime=false`. This result does not apply to the broad `entity.set_property -> entity.restore_snapshot` route.

## Follow-up

Continue only through **E183 -- Scene Entity Generic-Property Guarded-History Contract Decision Gate**. Audit the arbitrary dotted-path generic setter and its snapshot inverse before any migration; do not equate the existing generic API with a safe field-level contract.