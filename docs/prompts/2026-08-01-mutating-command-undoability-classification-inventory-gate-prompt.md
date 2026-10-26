# E190 Fresh-Session Completion Prompt -- Mutating Command Undoability Classification Inventory Gate

E190 is complete. The Runtime registry has exactly 31 `mutates=True, undoable=False` CommandSpecs, frozen by `tests/test_ai_command_non_undoable_mutation_inventory.py`. They are deliberately partitioned into history/internal inverse, derived maintenance, transaction/recovery, filesystem/package lifecycle, persistent project/scene, and host/runtime transient groups.

Do not bulk-mark any group undoable. History controls and inverse primitives must not recurse; transaction/recovery and lifecycle commands have their own authority/provenance/external-side-effect contracts; host/simulation/selection actions are transient. The only selected next candidate is `project.set_ps_experiment_preset`: it directly normalizes and replaces one `project.json` string field, has no preset-source read and no host adapter side effect. `project.set_active_scene`, `project.set_evolution_defaults`, and `scene.save` remain separately deferred for their broader contracts.

Evidence: focused inventory/audit/isomorphic suite passed `14 passed in 0.74s`; E189 command-history suite passed `43 passed, 10 subtests passed in 3.91s`. Audit remains schema v4 with `unified_undo_redo_runtime=false`. No global unified-history, full-suite pytest, native acceleration, or OpenGL-default claim is valid.

The next and only gate is E191: inventory `project.set_ps_experiment_preset` for an exact, guarded, durable history contract. Preserve direct handler behavior and panel success-only presentation refresh; do not infer safety from it being a single field.
