# E191 Project PS Experiment Preset Deterministic Guarded-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E190 classified all 31 non-undoable mutating CommandSpecs and selected `project.set_ps_experiment_preset` as the narrowest persistent-project candidate. Its direct handler normalized a supplied string and wrote one `project.json` field, but it had no semantic history record.

## Inventory result

- The direct handler resolves only the project contract, validates a non-empty supplied `preset_path`, normalizes backslashes to `/`, and replaces exactly `project.json["ps_experiment_preset"]`. It does not read a preset resource, inspect preset metadata, or invoke a host adapter.
- The previous field can be absent or present. A present legacy value is restored as its exact JSON-safe value, including a mapping rather than coercing it to a string; an absent previous field is restored by removing the key.
- A full canonical project-manifest witness is required for inverse replay. Independent changes anywhere in `project.json`, including unrelated fields, reject replay before `_write_json()` and before a durable replay audit is appended.
- `PSExperimentPanel` retains its direct Registry route and success-only presentation refresh. Existing direct callers remain compatible because `expected_project` is optional on `project.set_ps_experiment_preset`; it is required only by the owned history inverse.

## Implemented contract

- `project.set_ps_experiment_preset` is now `undoable=True`. Successful execution captures the prior field presence/value and full post-execute project witness in its result.
- Added the internal non-undoable inverse `project.restore_ps_experiment_preset_snapshot`. It requires the full expected manifest, restores the exact previous value or key absence, and returns the exact post-undo manifest for redo guarding.
- The Registry builds a narrow project history record: guarded inverse for undo and the original normalized `project.set_ps_experiment_preset` payload for redo. Both in-memory and fresh-registry durable replay attach the inverse post-state as redo's `expected_project` guard.
- The durable replay selector and audit-status representative inventory now include `project.set_ps_experiment_preset`. The E190 non-undoable inventory remains 31 entries: the direct command leaves that set while its internal inverse takes its explicit history-control classification.

## Proof

- Added `tests/test_ai_command_project_ps_preset_guarded_history.py`, covering normalized direct execution, in-memory undo/redo, fresh-registry durable undo/redo without any preset source, stale undo and redo rejection before write/audit, retry after canonical restoration, exact restoration of a legacy non-string field value, and direct compatibility without `expected_project`.
- Focused cross-history suite passed: `50 passed, 10 subtests passed in 3.64s`.
- `py_compile` passed for the changed production/test/audit files. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. Audit stays schema version 4 with `unified_undo_redo_runtime=false`.
- Repository-wide pytest was intentionally not run.

## Non-goals retained

- No generic project-manifest setter, adjacent project-setting migration, project lifecycle inverse, scene-save migration, global unified undo/redo, native acceleration completion, or OpenGL-default claim was introduced.

## Next gate

Exactly one next gate: **E192 -- Project Evolution Defaults Deterministic Guarded-History Contract Inventory Gate**.