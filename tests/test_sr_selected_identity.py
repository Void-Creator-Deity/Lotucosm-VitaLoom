# -*- coding: utf-8 -*-
"""Qt-free selected SR identity correlation contract for Phase 6L."""
from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path

from core.VitaLoom.simulation.sr_runtime_snapshot_authority import (
    SrRuntimeSnapshotAuthority,
)
from core.VitaLoom.simulation.sr_selected_identity import (
    SrSelectedIdentityCorrelation,
)


def _selection(
    entity_id: str = "entity_1",
    scene_path: str = "scenes/demo.pond",
) -> dict[str, object]:
    return {
        "selection_count": 1,
        "items": [
            {
                "kind": "scene_entity",
                "scene_path": scene_path,
                "entity_id": entity_id,
            }
        ],
    }


def _runtime(epoch: str | None, scene_path: str = "scenes/demo.pond") -> dict[str, object]:
    return {
        "track": "sr_play",
        "runtime_epoch": epoch,
        "scene_path": scene_path,
    }


def _snapshot(
    entity_id: str = "entity_1",
    *,
    counterpart: bool = True,
) -> dict[str, object]:
    return {
        "entity_id": entity_id,
        "entity_type": "organism",
        "serialized_scene_counterpart": counterpart,
        "position": [4.0, 8.0],
    }


def _active(
    *,
    entity_id: str = "entity_1",
    counterpart: bool = True,
    scene_path: str = "scenes/demo.pond",
) -> tuple[SrRuntimeSnapshotAuthority, str]:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin(scene_path)
    authority.publish(epoch, [_snapshot(entity_id, counterpart=counterpart)])
    return authority, epoch


def test_no_multi_and_non_entity_selection_are_unavailable() -> None:
    correlation = SrSelectedIdentityCorrelation()
    authority, epoch = _active()

    no_selection = correlation.resolve(
        {"selection_count": 0, "items": []},
        _runtime(epoch),
        authority.query,
    )
    multi_selection = correlation.resolve(
        {
            "selection_count": 2,
            "items": [
                {"kind": "scene_entity", "scene_path": "scenes/demo.pond", "entity_id": "entity_1"},
                {"kind": "scene_entity", "scene_path": "scenes/demo.pond", "entity_id": "entity_2"},
            ],
        },
        _runtime(epoch),
        authority.query,
    )
    non_entity = correlation.resolve(
        {"selection_count": 1, "items": [{"kind": "pond"}]},
        _runtime(epoch),
        authority.query,
    )

    assert no_selection["status"] == "unavailable"
    assert no_selection["reason"] == "no_selection"
    assert multi_selection["status"] == "unavailable"
    assert multi_selection["reason"] == "multiple_selection"
    assert non_entity["status"] == "unavailable"
    assert non_entity["reason"] == "non_entity_selection"


def test_malformed_selection_projection_is_invalid_identity() -> None:
    correlation = SrSelectedIdentityCorrelation()
    authority, epoch = _active()

    for malformed in (
        object(),
        {"selection_count": 1},
        {"selection_count": "1", "items": []},
        {"selection_count": 1, "items": [{"kind": "scene_entity", "entity_id": "entity_1"}]},
        {"selection_count": 1, "items": [{"kind": "scene_entity", "scene_path": "x", "entity_id": ""}]},
    ):
        assert correlation.resolve(malformed, _runtime(epoch), authority.query)["status"] == "invalid_identity"


def test_valid_selection_without_active_runtime_is_not_running() -> None:
    result = SrSelectedIdentityCorrelation().resolve(
        _selection(),
        _runtime(None),
        SrRuntimeSnapshotAuthority().query,
    )

    assert result["status"] == "not_running"
    assert result["identity"] is None


def test_scene_paths_are_correlated_before_authority_query(tmp_path: Path) -> None:
    scene = tmp_path / "scenes" / "demo.pond"
    authority, epoch = _active(scene_path=str(scene))
    selection_path = str(scene.parent / "." / "demo.pond")

    result = SrSelectedIdentityCorrelation().resolve(
        _selection(scene_path=selection_path),
        _runtime(epoch, str(scene)),
        authority.query,
    )

    assert result["status"] == "ok"
    assert result["identity"]["scene_path"] == str(scene)


def test_scene_mismatch_is_invalid_identity_not_missing(tmp_path: Path) -> None:
    active_scene = tmp_path / "active.pond"
    authority, epoch = _active(scene_path=str(active_scene))

    result = SrSelectedIdentityCorrelation().resolve(
        _selection(scene_path=str(tmp_path / "other.pond")),
        _runtime(epoch, str(active_scene)),
        authority.query,
    )

    assert result["status"] == "invalid_identity"
    assert result["reason"] == "scene_mismatch"


def test_current_selection_resolves_opaque_epoch_and_snapshot() -> None:
    authority, epoch = _active()

    result = SrSelectedIdentityCorrelation().resolve(
        _selection(),
        _runtime(epoch),
        authority.query,
    )

    assert result["status"] == "ok"
    assert result["identity"] == {
        "track": "sr_play",
        "runtime_epoch": epoch,
        "scene_path": "scenes/demo.pond",
        "entity_id": "entity_1",
    }
    assert result["snapshot"]["serialized_scene_counterpart"] is True
    assert result["selection_relation"] == "scene_correlated_not_unified"
    json.dumps(result, ensure_ascii=False, allow_nan=False)


def test_old_explicit_identity_is_stale_before_missing() -> None:
    correlation = SrSelectedIdentityCorrelation()
    authority = SrRuntimeSnapshotAuthority()
    old_epoch = authority.begin("scenes/demo.pond")
    authority.publish(old_epoch, [_snapshot("same_id")])
    new_epoch = authority.begin("scenes/demo.pond")
    authority.publish(new_epoch, [_snapshot("same_id")])

    result = correlation.resolve(
        _selection("same_id"),
        _runtime(new_epoch),
        authority.query,
        explicit_identity={
            "track": "sr_play",
            "runtime_epoch": old_epoch,
            "scene_path": "scenes/demo.pond",
            "entity_id": "same_id",
        },
    )

    assert result["status"] == "stale"


def test_missing_serialized_entity_remains_missing() -> None:
    authority = SrRuntimeSnapshotAuthority()
    epoch = authority.begin("scenes/demo.pond")
    authority.publish(epoch, [])

    result = SrSelectedIdentityCorrelation().resolve(
        _selection(),
        _runtime(epoch),
        authority.query,
    )

    assert result["status"] == "missing"


def test_runtime_created_entity_cannot_claim_edit_identity() -> None:
    authority, epoch = _active(entity_id="generated_1", counterpart=False)

    result = SrSelectedIdentityCorrelation().resolve(
        _selection("generated_1"),
        _runtime(epoch),
        authority.query,
    )

    assert result["status"] == "invalid_identity"
    assert result["reason"] == "not_serialized_scene_counterpart"
    assert "snapshot" not in result


def test_unsupported_explicit_track_is_preserved() -> None:
    authority, epoch = _active()
    result = SrSelectedIdentityCorrelation().resolve(
        _selection(),
        _runtime(epoch),
        authority.query,
        explicit_identity={
            "track": "ps_batch",
            "runtime_epoch": epoch,
            "scene_path": "scenes/demo.pond",
            "entity_id": "entity_1",
        },
    )
    assert result["status"] == "unsupported_track"


def test_result_is_copy_isolated() -> None:
    authority, epoch = _active()
    correlation = SrSelectedIdentityCorrelation()

    first = correlation.resolve(_selection(), _runtime(epoch), authority.query)
    first["snapshot"]["position"][0] = 999.0
    first["identity"]["entity_id"] = "changed"
    second = correlation.resolve(_selection(), _runtime(epoch), authority.query)

    assert second["snapshot"]["position"] == [4.0, 8.0]
    assert second["identity"]["entity_id"] == "entity_1"


def test_module_imports_when_pyqt6_is_blocked(monkeypatch) -> None:
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
        / "sr_selected_identity.py"
    )
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError("Qt-free selected identity Module imported PyQt6")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_sr_selected_identity_headless", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "SrSelectedIdentityCorrelation")

