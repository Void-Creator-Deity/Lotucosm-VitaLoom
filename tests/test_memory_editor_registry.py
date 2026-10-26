# -*- coding: utf-8 -*-
"""E268 regression tests for MemoryEditor Registry authority."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.Lotucosm.memory import MemoryGene, MemorySystem
from core.VitaLoom.commands.registry import reset_command_registry
from core.VitaLoom.memory_editor import MemoryEditor


class _FailOnActionPatternMemory(MemoryGene):
    """Exercise the command's rollback contract with a failing second setter."""

    def __init__(self) -> None:
        super().__init__("old", {"move": 0.2}, 0.4)
        self._action_pattern = self.action_pattern

    @property
    def action_pattern(self):
        return self._action_pattern

    @action_pattern.setter
    def action_pattern(self, value):
        if value == {"fail": True}:
            raise RuntimeError("action pattern rejected")
        self._action_pattern = value


class _Organism:
    def __init__(self, memory_system: MemorySystem) -> None:
        self.memory_system = memory_system


class MemoryEditorRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = reset_command_registry()
        self.memory = MemoryGene("old", {"move": 0.2}, 0.4)
        self.system = MemorySystem()
        self.system.memories.append(self.memory)
        self.editor = MemoryEditor(_Organism(self.system))

    def tearDown(self) -> None:
        self.editor.close()

    def test_edit_routes_through_registry_and_supports_undo_redo(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", "new", {"move": 0.9}, 0.8))
        self.assertEqual(self.memory.situation, "new")
        self.assertEqual(self.memory.action_pattern, {"move": 0.9})
        self.assertEqual(self.memory.success_rate, 0.8)

        history = self.registry._undo_stack
        self.assertEqual(len(history), 1)
        encoded = json.dumps(history, ensure_ascii=False)
        self.assertNotIn("MemoryGene", encoded)
        self.assertIn("old", encoded)
        self.assertNotIn(str(id(self.memory)), encoded)
        self.assertNotIn(repr(self.memory), encoded)

        undone = self.registry.undo_last()
        self.assertTrue(undone["ok"], undone)
        self.assertEqual(self.memory.situation, "old")
        self.assertEqual(self.memory.action_pattern, {"move": 0.2})
        self.assertEqual(self.memory.success_rate, 0.4)

        redone = self.registry.redo_last()
        self.assertTrue(redone["ok"], redone)
        self.assertEqual(self.memory.situation, "new")

    def test_single_field_edit_preserves_other_fields(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", success_rate=0.9))
        self.assertEqual(self.memory.situation, "old")
        self.assertEqual(self.memory.action_pattern, {"move": 0.2})
        self.assertEqual(self.memory.success_rate, 0.9)

    def test_non_mapping_action_pattern_fails_without_mutation(self) -> None:
        before = (self.memory.situation, dict(self.memory.action_pattern), self.memory.success_rate)
        self.assertFalse(self.editor.edit_memory("old", action_pattern=["invalid"]))
        self.assertEqual(
            (self.memory.situation, self.memory.action_pattern, self.memory.success_rate),
            before,
        )
        self.assertFalse(self.registry._undo_stack)

    def test_second_setter_failure_rolls_back_the_complete_snapshot(self) -> None:
        failing = _FailOnActionPatternMemory()
        system = MemorySystem()
        system.memories.append(failing)
        editor = MemoryEditor(_Organism(system))
        try:
            self.assertFalse(editor.edit_memory("old", "new", {"fail": True}, 0.8))
        finally:
            editor.close()
        self.assertEqual(failing.situation, "old")
        self.assertEqual(failing.action_pattern, {"move": 0.2})
        self.assertEqual(failing.success_rate, 0.4)

    def test_duplicate_situation_keeps_first_match_compatibility(self) -> None:
        second = MemoryGene("old", {"wait": 0.1}, 0.3)
        self.system.memories.append(second)
        self.assertTrue(self.editor.edit_memory("old", "new"))
        self.assertEqual(self.memory.situation, "new")
        self.assertEqual(second.situation, "old")

    def test_stale_guard_does_not_mutate_and_failed_history_remains_available(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", "new"))
        self.memory.success_rate = 0.1
        result = self.registry.undo_last()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "stale_memory")
        self.assertEqual(self.memory.situation, "new")
        self.assertEqual(self.memory.success_rate, 0.1)
        self.assertTrue(self.registry._undo_stack)

    def test_failed_redo_remains_available_for_retry(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", "new"))
        self.assertTrue(self.registry.undo_last()["ok"])
        self.memory.success_rate = 0.1
        result = self.registry.redo_last()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "stale_memory")
        self.assertTrue(self.registry._redo_stack)
        self.assertEqual(self.memory.situation, "old")

    def test_import_routes_store_through_registry_and_supports_collection_undo_redo(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(
                {"situation": "imported", "action_pattern": {"turn": 0.7}, "success_rate": 0.6},
                handle,
            )
            path = handle.name
        try:
            self.assertTrue(self.editor.import_memory(path))
        finally:
            Path(path).unlink(missing_ok=True)
        self.assertEqual([memory.situation for memory in self.system.memories], ["old", "imported"])
        history_json = json.dumps(self.registry._undo_stack, ensure_ascii=False)
        self.assertNotIn("MemorySystem", history_json)
        self.assertNotIn(str(id(self.system)), history_json)
        self.assertTrue(self.registry.undo_last()["ok"])
        self.assertEqual([memory.situation for memory in self.system.memories], ["old"])
        self.assertTrue(self.registry.redo_last()["ok"])
        self.assertEqual([memory.situation for memory in self.system.memories], ["old", "imported"])

    def test_import_capacity_eviction_undo_redo_restores_exact_collection(self) -> None:
        self.system.max_memories = 2
        self.memory.strength = 0.2
        strong = MemoryGene("strong", {"wait": 1.0}, 0.8)
        strong.strength = 0.9
        self.system.memories.append(strong)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump({"situation": "imported", "action_pattern": {"turn": 0.7}, "success_rate": 0.6}, handle)
            path = handle.name
        try:
            self.assertTrue(self.editor.import_memory(path))
        finally:
            Path(path).unlink(missing_ok=True)
        self.assertEqual([memory.situation for memory in self.system.memories], ["strong", "imported"])
        self.assertTrue(self.registry.undo_last()["ok"])
        self.assertEqual([memory.situation for memory in self.system.memories], ["old", "strong"])
        self.assertTrue(self.registry.redo_last()["ok"])
        self.assertEqual([memory.situation for memory in self.system.memories], ["strong", "imported"])
        self.assertEqual([memory.strength for memory in self.system.memories], [0.9, 1.0])

    def test_import_missing_transient_memory_system_fails_without_history(self) -> None:
        token = self.editor._memory_system_binding()
        expected = self.editor._memory_collection_snapshot()
        self.editor.close()
        result = self.registry.run(
            "memory.store",
            {
                "target_token": token,
                "expected_memories": expected,
                "memory_entry": {"situation": "new", "action_pattern": {}, "success_rate": 0.5},
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "transient_memory_system_not_found")
        self.assertEqual([memory.situation for memory in self.system.memories], ["old"])
        self.assertFalse(self.registry._undo_stack)

    def test_restore_verification_failure_rolls_back_custom_memory_system(self) -> None:
        class CorruptingStore(MemorySystem):
            def store(self, memory_entry):
                self.memories.append(type("BrokenMemory", (), {"situation": "broken", "action_pattern": [], "success_rate": 0.1})())

        system = CorruptingStore()
        system.memories.append(MemoryGene("old", {"move": 0.2}, 0.4))
        editor = MemoryEditor(_Organism(system))
        token = editor._memory_system_binding()
        expected = editor._memory_collection_snapshot()
        try:
            result = self.registry.run(
                "memory.store",
                {
                    "target_token": token,
                    "expected_memories": expected,
                    "memory_entry": {"situation": "new", "action_pattern": {}, "success_rate": 0.5},
                },
            )
        finally:
            editor.close()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "memory_system_invalid")
        self.assertEqual([memory.situation for memory in system.memories], ["old"])

    def test_import_rejects_non_object_without_mutation_or_history(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(["invalid"], handle)
            path = handle.name
        try:
            self.assertFalse(self.editor.import_memory(path))
        finally:
            Path(path).unlink(missing_ok=True)
        self.assertEqual([memory.situation for memory in self.system.memories], ["old"])
        self.assertFalse(self.registry._undo_stack)

    def test_import_stale_collection_guard_does_not_mutate(self) -> None:
        token = self.editor._memory_system_binding()
        expected = self.editor._memory_collection_snapshot()
        self.system.memories.append(MemoryGene("external", {}, 0.2))
        result = self.registry.run(
            "memory.store",
            {
                "target_token": token,
                "expected_memories": expected,
                "memory_entry": {"situation": "new", "action_pattern": {}, "success_rate": 0.5},
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "stale_memory_system")
        self.assertEqual([memory.situation for memory in self.system.memories], ["old", "external"])
        self.assertFalse(self.registry._undo_stack)

    def test_import_store_failure_rolls_back_collection(self) -> None:
        class FailingStore(MemorySystem):
            def store(self, memory_entry):
                self.memories.append(MemoryGene("partial", {}, 0.1))
                raise RuntimeError("store failed")

        system = FailingStore()
        system.memories.append(MemoryGene("old", {}, 0.4))
        editor = MemoryEditor(_Organism(system))
        token = editor._memory_system_binding()
        expected = editor._memory_collection_snapshot()
        try:
            result = self.registry.run(
                "memory.store",
                {
                    "target_token": token,
                    "expected_memories": expected,
                    "memory_entry": {"situation": "new", "action_pattern": {}, "success_rate": 0.5},
                },
            )
        finally:
            editor.close()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "memory_store_failed")
        self.assertEqual([memory.situation for memory in system.memories], ["old"])

    def test_missing_transient_target_fails_without_mutation(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", "new"))
        token = next(iter(self.editor._memory_tokens.values()))
        self.editor.close()
        result = self.registry.undo_last()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "transient_memory_not_found")
        self.assertEqual(self.memory.situation, "new")

    def test_memory_command_is_not_durable_without_project_path(self) -> None:
        self.assertTrue(self.editor.edit_memory("old", "new"))
        self.assertFalse(any("audit_path" in item for item in self.registry._undo_stack))


if __name__ == "__main__":
    unittest.main()
