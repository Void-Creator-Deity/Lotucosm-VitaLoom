from __future__ import annotations

import copy
import hashlib
import json

import pytest

from core.Lotucosm.runtime.world_bridge_e567_script_portability_boundary import (
    CLOSED_CAPABILITY_FIELDS,
    PROOF_FIELDS,
    validate_digest_only_artifact,
    validate_worldbridge_e567_script_portability_boundary,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)
from tools.check_worldbridge_e567_script_portability_boundary import (
    verify,
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


def _reseal(witness: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(witness)
    sealed["witness_digest"] = ""
    sealed["witness_digest"] = _digest(sealed)
    return sealed


def test_digest_only_artifact_rejects_executable_payloads() -> None:
    valid = {
        "artifact_digest": "a" * 64,
        "source_bundle": {
            "sources": [
                {
                    "path": "scripts/probe.py",
                    "sha256": "b" * 64,
                }
            ]
        },
    }
    assert validate_digest_only_artifact(valid) == {
        "valid": True,
        "errors": [],
    }

    for key, value in (
        ("source_code", "class Probe: pass"),
        ("bytecode", "base64"),
        ("pickle", "gASV"),
        ("executable_blob", "payload"),
    ):
        candidate = copy.deepcopy(valid)
        candidate["checkpoint_graph"] = {"script": {key: value}}
        validation = validate_digest_only_artifact(candidate)
        assert validation["valid"] is False
        assert any(key in error for error in validation["errors"])


@pytest.fixture(scope="module")
def evidence() -> dict[str, object]:
    result = verify()
    assert result["ok"] is True
    return result


def test_e567_closes_executable_source_portability_boundary(
    evidence: dict[str, object],
) -> None:
    witness = evidence["witness"]
    assert isinstance(witness, dict)
    assert validate_worldbridge_e567_script_portability_boundary(
        witness
    ) == {"valid": True, "errors": []}
    assert all(witness[field] is True for field in PROOF_FIELDS)
    assert witness["portable_sr_executable_script_checkpoint"] is False
    assert witness["digest_only_source_transport"] is True
    assert witness["executable_source_portability_closed"] is True
    assert all(
        witness[field] is False for field in CLOSED_CAPABILITY_FIELDS
    )
    status = build_runtime_worldbridge_status(
        script_portability_boundary_witness=witness,
    )
    assert status["executable_source_portability_boundary_closed"] is True
    assert (
        status["script_portability_boundary_evidence"]["witness_digest"]
        == witness["witness_digest"]
    )
    assert (
        "portable_sr_executable_script_checkpoint"
        in status["do_not_claim"]
    )


def test_e567_rejects_embedded_python_overclaim(
    evidence: dict[str, object],
) -> None:
    witness = evidence["witness"]
    assert isinstance(witness, dict)
    candidate = copy.deepcopy(witness)
    candidate["artifact"]["checkpoint_graph"]["entities"][0]["scripts"][0][
        "source_code"
    ] = "class Executable: pass"
    candidate = _reseal(candidate)
    validation = validate_worldbridge_e567_script_portability_boundary(
        candidate
    )
    assert validation["valid"] is False
    assert any("forbidden_executable_key" in item for item in validation["errors"])

    overclaim = copy.deepcopy(witness)
    overclaim["portable_sr_executable_script_checkpoint"] = True
    overclaim = _reseal(overclaim)
    validation = validate_worldbridge_e567_script_portability_boundary(
        overclaim
    )
    assert "portable_sr_executable_script_checkpoint_overclaim" in validation[
        "errors"
    ]
