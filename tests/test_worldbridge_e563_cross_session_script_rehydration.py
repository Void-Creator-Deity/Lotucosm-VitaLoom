from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.Lotucosm.runtime.world_bridge_e538_shared_contracts import (
    build_worldbridge_e538_shared_contracts,
)
from core.Lotucosm.runtime.world_bridge_e562_script_checkpoint_authority import (
    build_worldbridge_e562_script_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_e563_cross_session_script_rehydration import (
    CLOSED_ADMISSION_FIELDS,
    POLICY,
    PROOF_FIELDS,
    SCOPE,
    build_cross_session_source_bundle,
    build_worldbridge_e563_cross_session_script_rehydration_authority,
    restore_cross_session_script_checkpoint,
    validate_cross_session_source_bundle,
    validate_worldbridge_e563_cross_session_script_rehydration_authority,
)
from core.Lotucosm.runtime.world_bridge_script_checkpoint import (
    capture_sr_script_checkpoint,
    retarget_sr_script_checkpoint,
)
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
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


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _reseal_bundle(bundle: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(bundle)
    sealed["bundle_digest"] = ""
    sealed["bundle_digest"] = _digest(sealed)
    return sealed


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _project(root: Path, *, name: str = "E563 Probe") -> Path:
    project = root / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    source = scripts / "probe.py"
    source.write_text(
        "class ProbeScript:\n"
        "    pass\n",
        encoding="utf-8",
    )
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = {
        "name": name,
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
    return project


def _probe_entity(project: Path) -> SimpleNamespace:
    script = _ProbeScript()
    script._scene_script_path = str(project / "scripts" / "probe.py")
    script._scene_script_properties = {"value": 3}
    script._runtime_value = 8.5
    return _entity("sr:probe", [script])


def _instantiate(data: dict[str, object]) -> _ProbeScript:
    script = _ProbeScript()
    script._scene_script_path = str(data["path"])
    script._scene_script_properties = copy.deepcopy(data["properties"])
    return script


def _base_witness(graph: dict[str, object]) -> dict[str, object]:
    return build_worldbridge_e562_script_checkpoint_authority(
        runtime_epoch="epoch-source",
        source_script_graph=graph,
        restore_result={
            "status": "worldbridge_sr_script_checkpoint_restore",
            "runtime_epoch": "epoch-source",
            "restored_entities": 1,
            "restored_scripts": 1,
        },
        recaptured_script_graph=copy.deepcopy(graph),
    )


def _quarantine(
    *,
    graph: dict[str, object],
    bundle: dict[str, object],
    project: Path,
    runtime_contract_version: str = "1.0.0",
) -> tuple[dict[str, object], SimpleNamespace, object]:
    entity = _probe_entity(project)
    original_script = entity.scripts[0]
    result = restore_cross_session_script_checkpoint(
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=runtime_contract_version,
        target_runtime_epoch="epoch-fresh",
        project_path=project,
        entities=[entity],
        instantiate_script=_instantiate,
    )
    return result, entity, original_script


def _build_e563_witness(
    tmp_path: Path,
    payload: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    project = payload["project"]
    graph = payload["graph"]
    bundle = payload["bundle"]
    base = payload["base"]
    fresh_result = payload["fresh_result"]
    recaptured = payload["recaptured"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    assert isinstance(base, dict)
    assert isinstance(fresh_result, dict)
    assert isinstance(recaptured, dict)

    missing_project = _project(tmp_path / "missing", name="E563 Probe")
    (missing_project / "scripts" / "probe.py").unlink()
    missing = _quarantine(
        graph=graph,
        bundle=bundle,
        project=missing_project,
    )
    version = _quarantine(
        graph=graph,
        bundle=bundle,
        project=project,
        runtime_contract_version="2.0.0",
    )
    tampered_bundle = copy.deepcopy(bundle)
    tampered_bundle["sources"][0]["sha256"] = "0" * 64
    tampered_bundle = _reseal_bundle(tampered_bundle)
    tamper = _quarantine(
        graph=graph,
        bundle=tampered_bundle,
        project=project,
    )
    witness = (
        build_worldbridge_e563_cross_session_script_rehydration_authority(
            runtime_contract_version="1.0.0",
            base_script_checkpoint_witness=base,
            source_bundle=bundle,
            fresh_restore_result=fresh_result,
            fresh_recaptured_script_graph=recaptured,
            quarantine_results=[missing[0], version[0], tamper[0]],
        )
    )
    return witness, bundle


@pytest.fixture()
def e563_payload(tmp_path: Path) -> dict[str, object]:
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
        runtime_contract_version="1.0.0",
    )
    base = _base_witness(graph)
    fresh_entity = _probe_entity(project)
    fresh_entity.replace_scripts([])
    fresh_result = restore_cross_session_script_checkpoint(
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version="1.0.0",
        target_runtime_epoch="epoch-fresh",
        project_path=project,
        entities=[fresh_entity],
        instantiate_script=_instantiate,
    )
    recaptured = capture_sr_script_checkpoint(
        runtime_epoch="epoch-fresh",
        project_path=project,
        entities=[fresh_entity],
    )
    return {
        "project": project,
        "graph": graph,
        "bundle": bundle,
        "base": base,
        "fresh_result": fresh_result,
        "recaptured": recaptured,
    }


def test_source_bundle_binds_checkpoint_identity_and_trust(
    e563_payload: dict[str, object],
) -> None:
    project = e563_payload["project"]
    graph = e563_payload["graph"]
    bundle = e563_payload["bundle"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)

    assert validate_cross_session_source_bundle(
        bundle,
        checkpoint_graph=graph,
        project_path=project,
        expected_runtime_contract_version="1.0.0",
    ) == {"valid": True, "errors": []}

    tampered = copy.deepcopy(bundle)
    tampered["sources"][0]["path"] = "scripts/other.py"
    tampered = _reseal_bundle(tampered)
    validation = validate_cross_session_source_bundle(
        tampered,
        checkpoint_graph=graph,
        project_path=project,
        expected_runtime_contract_version="1.0.0",
    )
    assert validation["valid"] is False
    assert "source_bundle_source_set_mismatch" in validation["errors"]


def test_cross_session_restore_retargets_epoch_and_rebuilds_sources(
    e563_payload: dict[str, object],
) -> None:
    project = e563_payload["project"]
    graph = e563_payload["graph"]
    bundle = e563_payload["bundle"]
    fresh_result = e563_payload["fresh_result"]
    recaptured = e563_payload["recaptured"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    assert isinstance(fresh_result, dict)
    assert isinstance(recaptured, dict)

    retargeted = retarget_sr_script_checkpoint(
        graph,
        target_runtime_epoch="epoch-fresh",
    )
    assert retargeted["entities"] == graph["entities"]
    assert retargeted["graph_digest"] != graph["graph_digest"]
    assert fresh_result["decision"] == "rehydrated"
    assert fresh_result["admitted"] is True
    assert fresh_result["restore_result"]["restored_entities"] == 1
    assert fresh_result["restore_result"]["restored_scripts"] == 1
    assert recaptured["runtime_epoch"] == "epoch-fresh"
    assert recaptured["entities"] == graph["entities"]


def test_e563_proves_fresh_rehydration_and_three_quarantine_cases(
    tmp_path: Path,
    e563_payload: dict[str, object],
) -> None:
    project = e563_payload["project"]
    graph = e563_payload["graph"]
    bundle = e563_payload["bundle"]
    base = e563_payload["base"]
    fresh_result = e563_payload["fresh_result"]
    recaptured = e563_payload["recaptured"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    assert isinstance(base, dict)
    assert isinstance(fresh_result, dict)
    assert isinstance(recaptured, dict)

    missing_project = _project(tmp_path / "missing", name="E563 Probe")
    (missing_project / "scripts" / "probe.py").unlink()
    missing = _quarantine(
        graph=graph,
        bundle=bundle,
        project=missing_project,
    )

    version = _quarantine(
        graph=graph,
        bundle=bundle,
        project=project,
        runtime_contract_version="2.0.0",
    )

    tampered_bundle = copy.deepcopy(bundle)
    tampered_bundle["sources"][0]["sha256"] = "0" * 64
    tampered_bundle = _reseal_bundle(tampered_bundle)
    tamper = _quarantine(
        graph=graph,
        bundle=tampered_bundle,
        project=project,
    )

    quarantine_results = [missing[0], version[0], tamper[0]]
    for result, _entity_value, original_script in (
        missing,
        version,
        tamper,
    ):
        assert result["decision"] == "quarantined"
        assert result["admitted"] is False
        assert result["live_owner_preserved"] is True
        assert _entity_value.scripts == [original_script]
    assert any(
        "source_bundle_source_missing:" in error
        for error in missing[0]["errors"]
    )
    assert any(
        "source_bundle_runtime_contract_mismatch" in error
        for error in version[0]["errors"]
    )
    assert any(
        "source_bundle_source_digest_mismatch:" in error
        for error in tamper[0]["errors"]
    )

    witness = (
        build_worldbridge_e563_cross_session_script_rehydration_authority(
            runtime_contract_version="1.0.0",
            base_script_checkpoint_witness=base,
            source_bundle=bundle,
            fresh_restore_result=fresh_result,
            fresh_recaptured_script_graph=recaptured,
            quarantine_results=quarantine_results,
        )
    )
    assert validate_worldbridge_e563_cross_session_script_rehydration_authority(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["scope"] == SCOPE
    assert witness["policy"] == POLICY
    assert witness["cross_session_script_rehydration_admitted"] is True
    assert witness["grants_admission"] is True
    assert all(
        witness[field] is False for field in CLOSED_ADMISSION_FIELDS
    )

    tampered_witness = copy.deepcopy(witness)
    tampered_witness["fresh_restore_result"]["restore_result"][
        "restored_scripts"
    ] = 2
    tampered_witness = _reseal_witness(tampered_witness)
    assert (
        validate_worldbridge_e563_cross_session_script_rehydration_authority(
            tampered_witness
        )["valid"]
        is False
    )


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e563_rejects_out_of_scope_admission_overclaim(
    tmp_path: Path,
    e563_payload: dict[str, object],
    field: str,
) -> None:
    project = e563_payload["project"]
    graph = e563_payload["graph"]
    bundle = e563_payload["bundle"]
    base = e563_payload["base"]
    fresh_result = e563_payload["fresh_result"]
    recaptured = e563_payload["recaptured"]
    assert isinstance(project, Path)
    assert isinstance(graph, dict)
    assert isinstance(bundle, dict)
    assert isinstance(base, dict)
    assert isinstance(fresh_result, dict)
    assert isinstance(recaptured, dict)

    missing_project = _project(tmp_path / "missing", name="E563 Probe")
    (missing_project / "scripts" / "probe.py").unlink()
    missing = _quarantine(
        graph=graph,
        bundle=bundle,
        project=missing_project,
    )
    version = _quarantine(
        graph=graph,
        bundle=bundle,
        project=project,
        runtime_contract_version="2.0.0",
    )
    tampered_bundle = copy.deepcopy(bundle)
    tampered_bundle["sources"][0]["sha256"] = "f" * 64
    tampered_bundle = _reseal_bundle(tampered_bundle)
    tamper = _quarantine(
        graph=graph,
        bundle=tampered_bundle,
        project=project,
    )
    witness = (
        build_worldbridge_e563_cross_session_script_rehydration_authority(
            runtime_contract_version="1.0.0",
            base_script_checkpoint_witness=base,
            source_bundle=bundle,
            fresh_restore_result=fresh_result,
            fresh_recaptured_script_graph=recaptured,
            quarantine_results=[missing[0], version[0], tamper[0]],
        )
    )
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = (
        validate_worldbridge_e563_cross_session_script_rehydration_authority(
            candidate
        )
    )
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e563_admission_reaches_contracts_audit_and_status(
    tmp_path: Path,
    e563_payload: dict[str, object],
) -> None:
    witness, _bundle = _build_e563_witness(tmp_path, e563_payload)
    assert validate_worldbridge_e563_cross_session_script_rehydration_authority(
        witness
    ) == {"valid": True, "errors": []}

    contract = build_worldbridge_e538_shared_contracts(
        cross_session_script_witness=witness,
    )
    assert contract["contract_valid"] is True
    assert contract["admissions"][
        "cross_session_script_rehydration_admitted"
    ] is True
    assert "cross_session_script_rehydration" not in contract["do_not_claim"]
    assert (
        "portable_sr_executable_script_checkpoint"
        in contract["do_not_claim"]
    )

    admission = build_worldbridge_tick_replay_admission(
        cross_session_script_witness=witness,
    )
    assert (
        admission["cross_session_script_rehydration_admitted"] is True
    )
    assert (
        admission["cross_session_script_evidence"]["witness_digest"]
        == witness["witness_digest"]
    )
    assert admission["lossless"] is False
    assert admission["default_ready"] is False

    audit = build_worldbridge_mapping_audit(
        cross_session_script_witness=witness,
    )
    assert audit["cross_session_script_rehydration_admitted"] is True
    assert "cross_session_script_rehydration" not in audit["do_not_claim"]
    assert "portable_sr_executable_script_checkpoint" in audit["do_not_claim"]

    status = build_runtime_worldbridge_status(
        cross_session_script_witness=witness,
    )
    assert status["cross_session_script_rehydration_admitted"] is True
    assert (
        status["cross_session_script_evidence"]["witness_digest"]
        == witness["witness_digest"]
    )
    assert status["default_ready"] is False
