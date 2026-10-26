"""Qt-free Registry contract for Inspector transient property edits."""

from __future__ import annotations

import json
from dataclasses import dataclass


from core.VitaLoom.commands.registry import CommandRegistry
from core.VitaLoom.commands.runtime_commands import register_runtime_commands


@dataclass
class _Node:
    x: float = 1.0
    y: float = 2.0
    name: str = "old"


class _OwnerManagedNode:
    def __init__(self) -> None:
        self.position = [1.0, 2.0]
        self.energy = 3.0
        self.calls: list[tuple[str, object]] = []

    def set_position(self, value) -> None:
        self.calls.append(("position", value))
        self.position = list(value)

    def set_energy(self, value) -> None:
        self.calls.append(("energy", value))
        self.energy = float(value)


def _registry() -> CommandRegistry:
    registry = CommandRegistry()
    register_runtime_commands(registry)
    return registry


def _set(registry: CommandRegistry, target, path: str, value, **extra):
    token = registry.bind_transient_target(target)
    payload = {
        "target_token": token,
        "property_path": path,
        "value": value,
        **extra,
    }
    return token, registry.run("inspector.set_property", payload)


def test_dict_field_execute_undo_redo_and_serializable_history():
    registry = _registry()
    target = {"enabled": False}
    token, result = _set(registry, target, "enabled", True, expected_present=True, expected_value=False)

    assert result["ok"] is True
    assert target["enabled"] is True
    assert json.dumps(registry._undo_stack)
    history = registry._undo_stack[-1]
    assert all(value is not target for value in history.values())
    assert token in json.dumps(history)

    assert registry.undo_last()["ok"] is True
    assert target["enabled"] is False
    assert registry.redo_last()["ok"] is True
    assert target["enabled"] is True


def test_object_field_and_position_axes_use_same_registry_command():
    registry = _registry()
    node = _Node()

    _, result = _set(registry, node, "name", "new", expected_present=True, expected_value="old")
    assert result["ok"] is True
    assert node.name == "new"
    assert registry.undo_last()["ok"] is True
    assert node.name == "old"
    assert registry.redo_last()["ok"] is True
    assert node.name == "new"

    _, result = _set(registry, node, "position_x", 8.5, expected_present=True, expected_value=1.0)
    assert result["ok"] is True
    assert node.x == 8.5
    assert registry.undo_last()["ok"] is True
    assert node.x == 1.0
    assert registry.redo_last()["ok"] is True
    assert node.x == 8.5


def test_script_nested_property_execute_undo_redo():
    registry = _registry()
    target = {"scripts": [{"name": "brain", "properties": {"mind": {"level": 1}}}]}

    _, result = _set(
        registry,
        target,
        "script_brain_mind.level",
        3,
        expected_present=True,
        expected_value=1,
    )
    assert result["ok"] is True
    assert target["scripts"][0]["properties"]["mind"]["level"] == 3
    assert registry.undo_last()["ok"] is True
    assert target["scripts"][0]["properties"]["mind"]["level"] == 1
    assert registry.redo_last()["ok"] is True
    assert target["scripts"][0]["properties"]["mind"]["level"] == 3


def test_stale_expected_value_does_not_mutate_or_create_history():
    registry = _registry()
    target = {"value": 2}
    token = registry.bind_transient_target(target)
    result = registry.run(
        "inspector.set_property",
        {
            "target_token": token,
            "property_path": "value",
            "value": 9,
            "expected_present": True,
            "expected_value": 1,
        },
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "stale_inspector_property"
    assert target == {"value": 2}
    assert registry._undo_stack == []


def test_missing_token_and_invalid_nested_write_are_atomic():
    registry = _registry()
    missing = registry.run(
        "inspector.set_property",
        {"target_token": "missing", "property_path": "value", "value": 1},
    )
    assert missing["ok"] is False
    assert missing["error"]["code"] == "transient_target_not_found"

    target = {
        "scripts": [{"name": "brain", "properties": {"root": "not-a-dict"}}],
        "stable": 4,
    }
    token = registry.bind_transient_target(target)
    result = registry.run(
        "inspector.set_property",
        {
            "target_token": token,
            "property_path": "script_brain_root.child",
            "value": 9,
            "expected_present": False,
            "present": False,
        },
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "inspector_property_write_failed"
    assert target == {
        "scripts": [{"name": "brain", "properties": {"root": "not-a-dict"}}],
        "stable": 4,
    }
    assert registry._undo_stack == []


def test_missing_nested_leaf_delete_is_a_noop_without_partial_mutation():
    registry = _registry()
    target = {"scripts": [{"name": "brain", "properties": {"mind": {"level": 1}}}]}
    token = registry.bind_transient_target(target)
    result = registry.run(
        "inspector.set_property",
        {
            "target_token": token,
            "property_path": "script_brain_mind.missing",
            "value": None,
            "expected_present": False,
            "present": False,
        },
    )
    assert result["ok"] is True
    assert target["scripts"][0]["properties"]["mind"] == {"level": 1}
    assert registry._undo_stack == []


def test_owner_managed_transient_properties_use_owner_apis_through_registry_history():
    registry = _registry()
    node = _OwnerManagedNode()

    _, position_result = _set(
        registry, node, "position_x", 8.5, expected_present=True, expected_value=1.0
    )
    assert position_result["ok"] is True
    assert node.position == [8.5, 2.0]
    assert [name for name, _value in node.calls] == ["position"]
    assert registry.undo_last()["ok"] is True
    assert node.position == [1.0, 2.0]
    assert registry.redo_last()["ok"] is True
    assert node.position == [8.5, 2.0]

    _, energy_result = _set(
        registry, node, "energy", 9.0, expected_present=True, expected_value=3.0
    )
    assert energy_result["ok"] is True
    assert node.energy == 9.0
    assert [name for name, _value in node.calls] == ["position", "position", "position", "energy"]
    assert registry.undo_last()["ok"] is True
    assert node.energy == 3.0
    assert registry.redo_last()["ok"] is True
    assert node.energy == 9.0
