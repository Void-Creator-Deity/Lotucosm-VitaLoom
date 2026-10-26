# -*- coding: utf-8 -*-
"""Keep the non-undoable mutation classification explicit and reviewable."""
from __future__ import annotations

import unittest

from core.VitaLoom.commands.registry import reset_command_registry


# This is an inventory assertion, not a claim that these commands are all safe
# to invert.  E190 keeps future mutating CommandSpecs from silently falling out
# of the documented classification gate.
CLASSIFIED_NON_UNDOABLE_MUTATIONS = {
    "history_control": {
        "command.redo",
        "command.redo_project",
        "command.undo",
        "command.undo_project",
        "entity.restore_deleted_snapshot",
        "entity.restore_snapshot",
        "scene.restore_snapshot",
        "project.restore_active_scene_snapshot",
        "project.restore_ps_experiment_preset_snapshot",
        "project.restore_evolution_defaults_snapshot",
        "memory.restore",
    },
    "derived_maintenance": {
        "asset.refresh",
    },
    "transaction_or_recovery_authority": {
        "asset.transaction.prune.apply",
        "asset.transaction.recovery.resolve",
        "asset.transaction.redo",
        "asset.transaction.undo",
        "package.transaction.recovery.resolve",
        "plugin.host.recovery.resolve",
    },
    "filesystem_or_package_side_effect": {
        "asset.create",
        "asset.import",
        "plugin.disable",
        "plugin.enable",
        "plugin.install",
        "plugin.uninstall",
        "project.create",
    },
    "persistent_project_or_scene_deferral": set(),
    "host_or_runtime_transient": {
        "project.open",
        "scene.open",
        "selection.set",
        "simulation.pause",
        "simulation.play",
        "simulation.stop",
        "simulation.toggle",
    },
}


class NonUndoableMutationInventoryTests(unittest.TestCase):
    def test_every_non_undoable_mutation_has_exactly_one_e190_classification(self) -> None:
        registry = reset_command_registry()
        actual = {
            command["id"]
            for command in registry.list()
            if command["mutates"] and not command["undoable"]
        }
        classified = set().union(*CLASSIFIED_NON_UNDOABLE_MUTATIONS.values())

        self.assertEqual(actual, classified)
        self.assertEqual(sum(len(group) for group in CLASSIFIED_NON_UNDOABLE_MUTATIONS.values()), len(classified))

        for command_id in sorted(classified):
            spec = registry.describe(command_id)
            self.assertTrue(spec["mutates"], command_id)
            self.assertFalse(spec["undoable"], command_id)


if __name__ == "__main__":
    unittest.main()
