# -*- coding: utf-8 -*-
"""AI-native command registry: schema, execution, and lifecycle basics."""
from __future__ import annotations

import unittest

from core.VitaLoom.commands.registry import (
    CommandRegistry,
    CommandSpec,
    command_error,
    command_ok,
)


class CommandRegistryTests(unittest.TestCase):
    def test_register_describe_and_run(self) -> None:
        registry = CommandRegistry()

        def _handler(payload, context):
            return command_ok({"echo": payload["text"]}, events=["echoed"])

        registry.register(
            CommandSpec(
                id="test.echo",
                title="Echo",
                input_schema={
                    "type": "object",
                    "required": ["text"],
                    "properties": {"text": {"type": "string"}},
                },
                handler=_handler,
                capability="test",
            )
        )

        self.assertEqual(registry.describe("test.echo")["id"], "test.echo")
        result = registry.run("test.echo", {"text": "hello"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["echo"], "hello")
        self.assertEqual(result["events"], ["echoed"])

    def test_duplicate_id_is_rejected(self) -> None:
        registry = CommandRegistry()
        spec = CommandSpec(id="test.same", title="Same", handler=lambda payload, context: command_ok())
        registry.register(spec)
        with self.assertRaises(ValueError):
            registry.register(spec)

    def test_schema_validation_failure(self) -> None:
        registry = CommandRegistry()
        registry.register(
            CommandSpec(
                id="test.need_int",
                title="Need Int",
                input_schema={
                    "type": "object",
                    "required": ["count"],
                    "properties": {"count": {"type": "integer"}},
                },
                handler=lambda payload, context: command_ok(),
            )
        )

        result = registry.run("test.need_int", {"count": "nope"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "schema_validation_failed")

    def test_unregister_by_owner(self) -> None:
        registry = CommandRegistry()
        registry.register(
            CommandSpec(
                id="test.owned",
                title="Owned",
                owner="PluginA",
                handler=lambda payload, context: command_ok(),
            )
        )
        self.assertIn("test.owned", [row["id"] for row in registry.list()])
        registry.unregister_owner("PluginA")
        self.assertEqual(registry.list(), [])

    def test_command_error_shape(self) -> None:
        result = command_error("boom", "Something failed", warnings=["careful"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["warnings"], ["careful"])
        self.assertEqual(result["error"]["code"], "boom")


if __name__ == "__main__":
    unittest.main()
