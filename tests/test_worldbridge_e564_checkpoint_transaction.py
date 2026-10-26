from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_e563_cross_session_script_rehydration import (
    build_cross_session_source_bundle,
)
from core.Lotucosm.runtime.world_bridge_e564_checkpoint_transaction import (
    CheckpointTransactionError,
    checkpoint_interlock,
    checkpoint_interlock_status,
    export_checkpoint_artifact,
    import_checkpoint_artifact,
    restore_checkpoint_artifact,
    validate_checkpoint_artifact,
)
from core.Lotucosm.runtime.world_bridge_script_checkpoint import (
    capture_sr_script_checkpoint,
)


RUNTIME_CONTRACT_VERSION = "1.0.0"


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


def _project(root: Path) -> Path:
    project = root / "project"
    (project / "scripts").mkdir(parents=True)
    (project / "scenes").mkdir()
    source = project / "scripts" / "probe.py"
    source.write_text("class ProbeScript:\n    pass\n", encoding="utf-8")
    scene = project / "scenes" / "main.pond"
    scene.write_text(
        json.dumps({"entities": []}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = {
        "name": "E564 Probe",
        "version": "1.0.0",
        "loom_editor_version": "1.0.0",
        "required_packages": ["vitalloom.core.platform"],
        "capabilities": ["sr2d"],
        "script_trust": {
            "sha256_allowlist": [
                {
                    "path": "scripts/probe.py",
                    "sha256": source_digest,
                }
            ]
        },
    }
    (project / "project.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (project / "project.lock.json").write_text(
        json.dumps(
            {"schema_version": 1, "fixture": "e564"},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return project


def _probe_entity(project: Path) -> SimpleNamespace:
    script = _ProbeScript()
    script._scene_script_path = str(project / "scripts" / "probe.py")
    script._scene_script_properties = {"level": 2}
    script._runtime_value = 4.5
    return _entity("sr:probe", [script])


def _instantiate(data: dict[str, object]) -> _ProbeScript:
    script = _ProbeScript()
    script._scene_script_path = str(data["path"])
    script._scene_script_properties = copy.deepcopy(data["properties"])
    return script


@pytest.fixture()
def payload(tmp_path: Path) -> dict[str, object]:
    project = _project(tmp_path)
    entity = _probe_entity(project)
    graph = capture_sr_script_checkpoint(
        runtime_epoch="epoch-source",
        project_path=project,
        entities=[entity],
    )
    bundle = build_cross_session_source_bundle(
        checkpoint_graph=graph,
        project_path=project,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
    )
    return {"project": project, "graph": graph, "bundle": bundle}


def test_export_import_and_restore_are_interlocked_and_deterministic(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    project = payload["project"]
    graph = payload["graph"]
    bundle = payload["bundle"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    artifact = tmp_path / "export" / "checkpoint.json"

    first = export_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        artifact_path=artifact,
    )
    first_bytes = artifact.read_bytes()
    second = export_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        artifact_path=artifact,
    )
    assert artifact.read_bytes() == first_bytes
    assert first["artifact_digest"] == second["artifact_digest"]
    assert checkpoint_interlock_status(project)["held"] is False

    imported = import_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        artifact_path=artifact,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
    )
    assert imported["decision"] == "imported"
    assert imported["checkpoint_graph"] == graph
    assert imported["source_bundle"] == bundle
    assert imported["interlock"]["owner_pid"] > 0

    fresh_entity = _probe_entity(project)
    fresh_entity.replace_scripts([])
    restored = restore_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        artifact_path=artifact,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        target_runtime_epoch="epoch-target",
        entities=[fresh_entity],
        instantiate_script=_instantiate,
    )
    assert restored["decision"] == "rehydrated"
    assert restored["restore_result"]["admitted"] is True
    assert restored["restore_result"]["restore_result"]["restored_scripts"] == 1
    assert fresh_entity.scripts[0]._runtime_value == 4.5


def test_artifact_tamper_and_project_lock_drift_are_rejected(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    project = payload["project"]
    graph = payload["graph"]
    bundle = payload["bundle"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    artifact = tmp_path / "checkpoint.json"
    export_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        artifact_path=artifact,
    )
    value = json.loads(artifact.read_text(encoding="utf-8"))
    value["checkpoint_graph"]["entities"][0]["scripts"][0][
        "source_sha256"
    ] = "0" * 64
    artifact.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    with pytest.raises(CheckpointTransactionError) as tampered:
        import_checkpoint_artifact(
            project_path=project,
            scene_path="scenes/main.pond",
            artifact_path=artifact,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
    assert tampered.value.code == "checkpoint_artifact_invalid"

    export_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        artifact_path=artifact,
    )
    (project / "project.lock.json").write_text(
        json.dumps({"schema_version": 1, "fixture": "changed"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(CheckpointTransactionError) as stale:
        import_checkpoint_artifact(
            project_path=project,
            scene_path="scenes/main.pond",
            artifact_path=artifact,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
    assert stale.value.code == "checkpoint_artifact_invalid"


def test_interlock_is_exclusive_and_released_after_errors(
    payload: dict[str, object],
) -> None:
    project = payload["project"]
    assert isinstance(project, Path)
    with checkpoint_interlock(project) as held:
        assert held["owner_pid"] > 0
        assert checkpoint_interlock_status(project)["held"] is True
        with checkpoint_interlock(project) as reentrant:
            assert reentrant["status"] == "held_reentrant"
            assert reentrant["owner_nonce"] == held["owner_nonce"]
    assert checkpoint_interlock_status(project)["held"] is False

    with pytest.raises(RuntimeError):
        with checkpoint_interlock(project):
            raise RuntimeError("probe failure")
    assert checkpoint_interlock_status(project)["held"] is False


def test_atomic_write_failure_preserves_previous_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    project = payload["project"]
    graph = payload["graph"]
    bundle = payload["bundle"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    artifact = tmp_path / "checkpoint.json"
    artifact.write_bytes(b"previous-artifact")

    from core.Lotucosm.runtime import (
        world_bridge_e564_checkpoint_transaction as transaction,
    )

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(transaction.os, "replace", fail_replace)
    with pytest.raises(CheckpointTransactionError) as failure:
        export_checkpoint_artifact(
            project_path=project,
            scene_path="scenes/main.pond",
            checkpoint_graph=graph,
            source_bundle=bundle,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
            artifact_path=artifact,
        )
    assert failure.value.code == "checkpoint_artifact_write_failed"
    assert artifact.read_bytes() == b"previous-artifact"
    assert list(tmp_path.glob(".checkpoint.json.*.tmp")) == []
    assert checkpoint_interlock_status(project)["held"] is False


def test_artifact_contract_rejects_identity_and_source_drift(
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    project = payload["project"]
    graph = payload["graph"]
    bundle = payload["bundle"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    artifact_path = tmp_path / "checkpoint.json"
    export_checkpoint_artifact(
        project_path=project,
        scene_path="scenes/main.pond",
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        artifact_path=artifact_path,
    )
    value = json.loads(artifact_path.read_text(encoding="utf-8"))
    value["project_world_identity"]["scene_digest"] = "0" * 64
    value["artifact_digest"] = hashlib.sha256(
        json.dumps(
            {**value, "artifact_digest": ""},
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    validation = validate_checkpoint_artifact(
        value,
        project_path=project,
        scene_path="scenes/main.pond",
        expected_runtime_contract_version=RUNTIME_CONTRACT_VERSION,
    )
    assert validation["valid"] is False
    assert "artifact_project_world_identity_mismatch" in validation["errors"]
