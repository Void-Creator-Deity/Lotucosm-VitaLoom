# -*- coding: utf-8 -*-
"""Qt-free SR runtime identity snapshot authority contract."""
from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path

import pytest

from core.VitaLoom.simulation.sr_runtime_snapshot_authority import (
    SrRuntimeSnapshotAuthority,
)


def _identity(epoch: str, entity_id: str = "entity_1", scene_path: str = "scenes/demo.pond") -> dict[str, str]:
    return {
        "track": "sr_play",
        "runtime_epoch": epoch,
        "scene_path": scene_path,
        "entity_id": entity_id,
    }


def _snapshot(entity_id: str = "entity_1", **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "entity_id": entity_id,
        "entity_type": "organism",
        "serialized_scene_counterpart": True,
        "position": [12.5, 20.0],
    }
    value.update(extra)
    return value


def test_begin_creates_unique_opaque_runtime_epochs() -> None:
    authority = SrRuntimeSnapshotAuthority()

    first = authority.begin("scenes/demo.pond")
    second = authority.begin("scenes/demo.pond")

    assert isinstance(first, str) and first
    assert isinstance(second, str) and second
    assert first != second
    assert authority.current_epoch() == second


def test_query_before_begin_is_not_running() -> None:
    result = SrRuntimeSnapshotAuthority().query(_identity("old_epoch"))

    assert result["status"] == "not_running"
    assert result["scope"] == "selected_sr_runtime_entity"
    assert result["authority"] == "sr_runtime_snapshot_authority"
    assert result["identity_relation"] == "scene_correlated_not_unified"
    json.dumps(result, allow_nan=False)


def test_query_validates_identity_and_track() -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")

    missing_field = _identity(epoch)
    missing_field.pop("entity_id")
    assert authority.query(missing_field)["status"] == "invalid_identity"
    assert authority.query({**_identity(epoch), "track": "ps_batch"})["status"] == "unsupported_track"
    assert authority.query(_identity(epoch, scene_path="scenes/other.pond"))["status"] == "invalid_identity"


def test_publish_query_and_copy_isolation() -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")
    source = _snapshot(metadata={"tags": ["seed"]})

    revision = authority.publish(epoch, [source])
    source["position"][0] = 999.0  # type: ignore[index]
    source["metadata"]["tags"].append("mutated")  # type: ignore[index,union-attr]

    first = authority.query(_identity(epoch))
    assert revision == 1
    assert first["status"] == "ok"
    assert first["revision"] == 1
    assert first["snapshot"] == {
        "source": "read_only_json_snapshot",
        "entity_id": "entity_1",
        "entity_type": "organism",
        "serialized_scene_counterpart": True,
        "position": [12.5, 20.0],
        "metadata": {"tags": ["seed"]},
    }

    first["snapshot"]["position"][0] = -100.0
    first["snapshot"]["metadata"]["tags"].append("query_mutation")
    second = authority.query(_identity(epoch))
    assert second["snapshot"]["position"] == [12.5, 20.0]
    assert second["snapshot"]["metadata"] == {"tags": ["seed"]}


def test_publish_replaces_snapshot_set_and_increments_revision() -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")

    assert authority.publish(epoch, [_snapshot("entity_1"), _snapshot("entity_2")]) == 1
    assert authority.publish(epoch, [_snapshot("entity_2", serialized_scene_counterpart=False)]) == 2

    assert authority.query(_identity(epoch, "entity_1"))["status"] == "missing"
    current = authority.query(_identity(epoch, "entity_2"))
    assert current["status"] == "ok"
    assert current["snapshot"]["serialized_scene_counterpart"] is False


def test_stale_is_resolved_before_missing() -> None:
    authority = SrRuntimeSnapshotAuthority()
    old_epoch = authority.begin("scenes/demo.pond")
    authority.publish(old_epoch, [_snapshot("same_id")])
    new_epoch = authority.begin("scenes/demo.pond")
    authority.publish(new_epoch, [_snapshot("same_id")])

    assert authority.query(_identity(old_epoch, "does_not_exist"))["status"] == "stale"
    assert authority.query(_identity(new_epoch, "does_not_exist"))["status"] == "missing"


def test_end_transitions_and_does_not_end_newer_epoch() -> None:
    authority = SrRuntimeSnapshotAuthority()
    old_epoch = authority.begin("scenes/demo.pond")
    current_epoch = authority.begin("scenes/demo.pond")

    assert authority.end(old_epoch)["status"] == "stale"
    assert authority.current_epoch() == current_epoch
    assert authority.end(current_epoch)["status"] == "ended"
    assert authority.current_epoch() is None
    assert authority.query(_identity(current_epoch))["status"] == "not_running"
    assert authority.end(current_epoch)["status"] == "not_running"


@pytest.mark.parametrize(
    "bad_value",
    [
        object(),
        lambda: None,
        (1, 2),
        {"bad_key": {1: "value"}},
        float("nan"),
        float("inf"),
    ],
)
def test_publish_rejects_non_json_snapshot_values(bad_value: object) -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")

    with pytest.raises((TypeError, ValueError)):
        authority.publish(epoch, [_snapshot(extra=bad_value)])


def test_publish_rejects_duplicate_or_missing_entity_ids() -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")

    with pytest.raises(ValueError, match="duplicate"):
        authority.publish(epoch, [_snapshot("same"), _snapshot("same")])
    with pytest.raises(ValueError, match="entity_id"):
        authority.publish(epoch, [{"entity_type": "organism"}])


def test_publish_rejects_not_running_and_stale_epochs() -> None:
    authority = SrRuntimeSnapshotAuthority()
    with pytest.raises(RuntimeError, match="not_running"):
        authority.publish("unknown", [_snapshot()])

    old_epoch = authority.begin("scenes/demo.pond")
    authority.begin("scenes/demo.pond")
    with pytest.raises(RuntimeError, match="stale"):
        authority.publish(old_epoch, [_snapshot()])


def test_authority_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
        / "core"
        / "VitaLoom"
        / "simulation"
        / "sr_runtime_snapshot_authority.py"
    )
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_sr_runtime_snapshot_authority", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SrRuntimeSnapshotAuthority().current_epoch() is None
