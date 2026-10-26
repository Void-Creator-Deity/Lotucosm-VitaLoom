from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.world_bridge_e554_shared_randomness_authority import (
    CLOSED_ADMISSION_FIELDS,
    PROOF_FIELDS,
    build_worldbridge_e554_shared_randomness_authority,
    validate_worldbridge_e554_shared_randomness_authority,
)
from core.Lotucosm.runtime.world_bridge_native_entropy_audit import (
    build_native_entropy_boundary_receipt,
)
from core.Lotucosm.runtime.world_bridge_randomness_authority import (
    build_caller_owned_stream_registry_digest,
    build_script_evidence_digest,
)
from core.Lotucosm.runtime.world_bridge_tick_replay_admission import (
    build_worldbridge_tick_replay_admission,
)
from core.Lotucosm.script_entropy_audit import (
    audit_script_file,
    build_dynamic_script_boundary_receipt,
    build_project_script_inventory,
    build_script_entropy_receipt,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)

from test_worldbridge_e548_rng_draw_order_authority import (
    _build as _build_e548_witness,
    _fixture as _e548_fixture,
)


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


def _reseal_witness(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def _script_evidence(
    tmp_path: Path,
    fixture: dict[str, object],
) -> dict[str, object]:
    source = tmp_path / "shared_randomness_script.py"
    source.write_text(
        "from core.Lotucosm.scripts import ScriptBase\n"
        "\n"
        "class SharedRandomnessScript(ScriptBase):\n"
        "    def on_tick(self, delta_time):\n"
        "        return self.random_uniform(0.0, 1.0)\n",
        encoding="utf-8",
    )
    audit = audit_script_file(source)
    receipt = fixture["receipt"]
    runtime_epoch = receipt["clock_decision"]["runtime_epoch"]
    owner = fixture["context"].get_stream("sr.runtime")
    owner_digest = build_caller_owned_stream_registry_digest(
        {"sr.runtime": owner}
    )
    script_receipt = build_script_entropy_receipt(
        audit,
        owner_family=type(owner).__name__,
        runtime_epoch=runtime_epoch,
        owner_stream_name="sr.runtime",
        owner_registry_digest=owner_digest,
    )
    declared_paths = [audit["path"]]
    inventory = build_project_script_inventory(
        {},
        scene_script_paths=declared_paths,
        loaded_receipts=[script_receipt],
    )
    execution_receipts = [
        {
            "execution_path": "scene_runtime_entities[0].scripts[0]",
            "owner_stream_name": "sr.runtime",
            "owner_family": type(owner).__name__,
            "owner_mode": "runtime",
            "lifecycle": "active",
            "execution_ticks": 2,
            "consumption_count": 1,
        }
    ]
    boundary = build_dynamic_script_boundary_receipt(
        [audit],
        [script_receipt],
        [],
        [],
    )
    evidence_digest = build_script_evidence_digest(
        [audit],
        [script_receipt],
        [],
        [],
        declared_paths,
        inventory,
        execution_receipts,
        boundary,
    )
    return {
        "schema_version": 1,
        "runtime_epoch": runtime_epoch,
        "audits": [audit],
        "receipts": [script_receipt],
        "trust_denials": [],
        "failure_receipts": [],
        "declared_paths": declared_paths,
        "inventory": inventory,
        "owner_stream_name": "sr.runtime",
        "owner_registry_digest": owner_digest,
        "owner_graph_digest": _digest(execution_receipts),
        "execution_receipts": execution_receipts,
        "boundary_receipt": boundary,
        "evidence_digest": evidence_digest,
    }


def _build_witness(monkeypatch, tmp_path) -> dict[str, object]:
    from core.Lotucosm.runtime import world_bridge_e554_shared_randomness_authority as module

    monkeypatch.setattr(module, "_native_runtime_available", lambda: False)
    fixture = _e548_fixture()
    draw = _build_e548_witness(fixture)
    return build_worldbridge_e554_shared_randomness_authority(
        rng_draw_order_witness=draw,
        script_evidence=_script_evidence(tmp_path, fixture),
        native_boundary_receipt=build_native_entropy_boundary_receipt(),
        native_backend_capability={"backend_id": "python"},
        requested_native_backend="auto",
    )


@pytest.fixture
def witness(monkeypatch, tmp_path) -> dict[str, object]:
    return _build_witness(monkeypatch, tmp_path)


def test_e554_binds_root_seed_dynamic_scripts_and_native_exclusion(
    witness: dict[str, object],
) -> None:
    assert validate_worldbridge_e554_shared_randomness_authority(witness) == {
        "valid": True,
        "errors": [],
    }
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["native_closure_mode"] == "excluded_from_selected_runtime"
    assert witness["native_runtime_adapter_available"] is False
    assert witness["rng_context_id"] == witness["rng_draw_order_witness"][
        "rng_context_id"
    ]
    assert witness["shared_root_seed_digest"] == witness[
        "rng_draw_order_witness"
    ]["rng_context_snapshot"]["root_seed_digest"]
    assert witness["grants_admission"] is False
    assert witness["admission_effect"] == "none"
    assert all(witness[field] is False for field in CLOSED_ADMISSION_FIELDS)


def test_e554_rejects_script_owner_registry_drift_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["script_evidence"]["owner_registry_digest"] = "0" * 64
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert "dynamic_script_owner_binding_mismatch" in validation["errors"]


def test_e554_rejects_script_corpus_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["script_evidence"]["audits"][0]["findings"] = [
        {"kind": "global_entropy_call", "authority": "os_entropy", "line": 1}
    ]
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert "dynamic_script_corpus_incomplete" in validation["errors"]
    assert "dynamic_entropy_boundary_not_closed" in validation["errors"]


def test_e554_rejects_native_receipt_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["native_boundary_receipt"]["status"] = "admitted"
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert (
        "native_receipt_native_boundary_receipt_overclaims_admission"
        in validation["errors"]
    )
    assert "native_receipt_source_bound_mismatch" in validation["errors"]
    assert "native_entropy_boundary_not_closed" in validation["errors"]


def test_e554_rejects_snapshot_context_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    snapshot = candidate["rng_draw_order_witness"]["rng_context_snapshot"]
    snapshot["root_seed_digest"] = "0" * 64
    snapshot["snapshot_digest"] = ""
    snapshot["snapshot_digest"] = _digest(snapshot)
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert "draw_draw_end_snapshot_mismatch" in validation["errors"]


@pytest.mark.parametrize("field", CLOSED_ADMISSION_FIELDS)
def test_e554_rejects_each_admission_overclaim(
    witness: dict[str, object],
    field: str,
) -> None:
    candidate = copy.deepcopy(witness)
    candidate[field] = True
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert f"{field}_overclaim" in validation["errors"]


def test_e554_rejects_extra_keys_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = _reseal_witness({**witness, "unexpected": True})

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert "witness_keys_invalid" in validation["errors"]


def test_e554_rejects_proof_boolean_tamper_after_reseal(
    witness: dict[str, object],
) -> None:
    candidate = copy.deepcopy(witness)
    candidate["native_entropy_boundary_closed"] = False
    candidate = _reseal_witness(candidate)

    validation = validate_worldbridge_e554_shared_randomness_authority(candidate)
    assert validation["valid"] is False
    assert "native_entropy_boundary_closed_mismatch" in validation["errors"]
    assert "native_entropy_boundary_closed_not_true" in validation["errors"]


def test_e554_admission_removes_only_the_randomness_blocker(
    witness: dict[str, object],
) -> None:
    baseline = build_worldbridge_tick_replay_admission()
    admission = build_worldbridge_tick_replay_admission(
        shared_randomness_authority_witness=witness
    )

    evidence = admission["shared_randomness_authority_evidence"]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    assert evidence["grants_admission"] is False
    assert admission["remaining_admission_blockers"] == [
        blocker
        for blocker in baseline["remaining_admission_blockers"]
        if blocker != "shared_random_seed_contract_missing"
    ]
    assert admission["tick_merge_admitted"] is False
    assert admission["full_unified_replay_admitted"] is False
    assert admission["default_ready"] is False


def test_e554_runtime_status_retains_shared_randomness_evidence(
    witness: dict[str, object],
) -> None:
    status = build_runtime_worldbridge_status(
        shared_randomness_authority_witness=witness
    )

    evidence = status["tick_replay_admission"][
        "shared_randomness_authority_evidence"
    ]
    assert evidence["validated"] is True
    assert evidence["witness_digest"] == witness["witness_digest"]
    shared = status["e538_shared_contracts"]
    assert shared["admissions"]["shared_random_seed_contract"] is True
    assert "shared_random_seed_contract_missing" not in shared[
        "remaining_admission_blockers"
    ]
    assert status["tick_replay_admission"]["default_ready"] is False
