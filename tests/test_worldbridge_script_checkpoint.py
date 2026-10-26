from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

from core.Lotucosm.runtime.world_bridge_script_checkpoint import (
    capture_sr_script_checkpoint,
    restore_sr_script_checkpoint,
    validate_sr_script_checkpoint,
)


class _ProbeScript:
    def __init__(self) -> None:
        self._scene_script_path = ""
        self._scene_script_properties: dict[str, object] = {}
        self._runtime_value = 0.0
        self._owner = object()


def _entity(entity_id: str, scripts: list[object]) -> SimpleNamespace:
    entity = SimpleNamespace(id=entity_id, scripts=scripts)

    def replace_scripts(replacement: list[object]) -> None:
        entity.scripts = list(replacement)

    entity.replace_scripts = replace_scripts
    return entity


def _source(project: Path) -> Path:
    source = project / "scripts" / "probe.py"
    source.parent.mkdir(parents=True)
    source.write_text("class ProbeScript:\n    pass\n", encoding="utf-8")
    return source


def test_script_checkpoint_roundtrip_rebuilds_source_bound_state(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = _source(project)
    script = _ProbeScript()
    script._scene_script_path = str(source)
    script._scene_script_properties = {"mind": {"level": 2}}
    script._runtime_value = 3.5
    updated: list[float] = []
    entity = _entity("sr:probe", [script])

    checkpoint = capture_sr_script_checkpoint(
        runtime_epoch="epoch-1",
        project_path=project,
        entities=[entity],
    )

    assert validate_sr_script_checkpoint(
        checkpoint,
        runtime_epoch="epoch-1",
    ) == {"valid": True, "errors": []}
    descriptor = checkpoint["entities"][0]["scripts"][0]
    assert descriptor["source_path"] == "scripts/probe.py"
    assert descriptor["runtime_state"]["_runtime_value"] == 3.5
    assert "_owner" not in descriptor["runtime_state"]
    assert descriptor["rebound_state_fields"] == ["_owner"]

    def instantiate(data: dict[str, object]) -> _ProbeScript:
        updated.append(1.0)
        replacement = _ProbeScript()
        replacement._scene_script_path = str(data["path"])
        replacement._scene_script_properties = copy.deepcopy(
            data["properties"]
        )
        return replacement

    result = restore_sr_script_checkpoint(
        checkpoint,
        runtime_epoch="epoch-1",
        project_path=project,
        entities=[entity],
        instantiate_script=instantiate,
    )

    assert result["restored_entities"] == 1
    assert result["restored_scripts"] == 1
    assert updated == [1.0]
    assert entity.scripts[0] is not script
    assert entity.scripts[0]._runtime_value == 3.5
    assert entity.scripts[0]._scene_script_properties == {
        "mind": {"level": 2}
    }
    assert entity.scripts[0]._owner is not None


def test_script_checkpoint_rejects_digest_tamper(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = _source(project)
    script = _ProbeScript()
    script._scene_script_path = str(source)
    entity = _entity("sr:probe", [script])
    checkpoint = capture_sr_script_checkpoint(
        runtime_epoch="epoch-1",
        project_path=project,
        entities=[entity],
    )
    checkpoint["graph_digest"] = "0" * 64

    validation = validate_sr_script_checkpoint(
        checkpoint,
        runtime_epoch="epoch-1",
    )

    assert validation["valid"] is False
    assert "graph_digest_mismatch" in validation["errors"]


def test_script_checkpoint_rejects_source_drift_before_replacing_owner(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = _source(project)
    script = _ProbeScript()
    script._scene_script_path = str(source)
    original = [script]
    entity = _entity("sr:probe", original)
    checkpoint = capture_sr_script_checkpoint(
        runtime_epoch="epoch-1",
        project_path=project,
        entities=[entity],
    )
    source.write_text("class Changed:\n    pass\n", encoding="utf-8")

    try:
        restore_sr_script_checkpoint(
            checkpoint,
            runtime_epoch="epoch-1",
            project_path=project,
            entities=[entity],
            instantiate_script=lambda _data: _ProbeScript(),
        )
    except ValueError as exc:
        assert "source digest mismatch" in str(exc)
    else:
        raise AssertionError("source drift was accepted")
    assert entity.scripts == original
