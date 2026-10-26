# E190 Mutating Command Undoability Classification Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E189 completed exact guarded history for `asset.apply_to_scene`. The representative undoable mutation set has deterministic records or transaction-owned replay paths, but commands declared `mutates=True, undoable=False` had not been reclassified as a complete set.

## Inventory result

The registry contains exactly 31 mutating, non-undoable CommandSpecs. `tests/test_ai_command_non_undoable_mutation_inventory.py` freezes the exact set and enforces one, and only one, category for each entry.

| Category | Commands | Classification and history decision |
| --- | --- | --- |
| History control / internal inverse (6) | `command.undo`, `command.redo`, `command.undo_project`, `command.redo_project`, `entity.restore_snapshot`, `entity.restore_deleted_snapshot` | Must remain non-undoable. These are the history controller or inverse primitives; tracking them as user operations would recursively create history records. |
| Derived maintenance (1) | `asset.refresh` | Must remain non-undoable. It refreshes derived asset-registry projection data rather than changing a user-owned canonical scene/project intent. |
| Transaction or recovery authority (6) | `asset.transaction.undo`, `asset.transaction.redo`, `asset.transaction.prune.apply`, `asset.transaction.recovery.resolve`, `package.transaction.recovery.resolve`, `plugin.host.recovery.resolve` | Must remain non-undoable. Each has an explicit transaction/recovery owner, provenance or irreversible-prune semantics; generic Registry history would obscure that authority. |
| Filesystem/package lifecycle (7) | `asset.create`, `asset.import`, `project.create`, `plugin.enable`, `plugin.disable`, `plugin.install`, `plugin.uninstall` | Explicitly deferred. They materialize files/directories, copy external bytes, or alter package/plugin/lock state with potential host and dependency effects. Any later inverse requires source/provenance, multi-file witnesses, and lifecycle-specific failure/recovery design. |
| Persistent project/scene state (4) | `project.set_active_scene`, `project.set_ps_experiment_preset`, `project.set_evolution_defaults`, `scene.save` | Requires individual decisions, not a bulk metadata flip. `scene.save` can replace arbitrary scene content; `project.set_active_scene` can additionally invoke optional scene loading; `project.set_evolution_defaults` owns an arbitrary mapping. `project.set_ps_experiment_preset` is the narrowest candidate. |
| Host/runtime transient state (7) | `project.open`, `scene.open`, `selection.set`, `simulation.play`, `simulation.toggle`, `simulation.pause`, `simulation.stop` | Must remain non-undoable. These affect host adapter/runtime/selection/simulation state rather than a canonical replayable project edit. |

## Durable audit and caller result

- `CommandRegistry.run()` may still append durable audit entries for project-scoped mutating commands; audit retention is not a declaration that every command is project-undo replayable.
- The latest replayable audit selector intentionally excludes these non-undoable operations. The history-control commands are excluded from audit append entirely, and restore/transaction primitives are invoked as owned inverses rather than standalone replay candidates.
- The `PSExperimentPanel` invokes `project.set_ps_experiment_preset` through the Registry and refreshes only its presentation after command success. The handler itself normalizes the supplied string and replaces exactly one `project.json` field; it neither reads a preset resource nor invokes a host adapter. This makes it the selected next inventory candidate.

## Proof

- Added `tests/test_ai_command_non_undoable_mutation_inventory.py`, which proves the registered non-undoable mutation set equals the 31-command classification and that every listed spec is mutating but non-undoable.
- Focused inventory/audit/isomorphic command suite passed `14 passed in 0.74s`.
- E189 command-history evidence remains `43 passed, 10 subtests passed in 3.91s`; audit schema remains version 4 with `unified_undo_redo_runtime=false`. Repository-wide pytest was intentionally not run.

## Non-goals retained

- No command metadata was changed merely to increase undo coverage.
- No generic project-manifest inverse, asset lifecycle inverse, plugin/package lifecycle inverse, global unified undo/redo, native acceleration, or OpenGL-default claim was introduced.

## Next gate

Exactly one next gate: **E191 -- Project PS Experiment Preset Deterministic Guarded-History Contract Inventory Gate**.
