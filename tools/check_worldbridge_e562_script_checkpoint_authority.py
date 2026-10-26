#!/usr/bin/env python3
"""Verify same-host project-source-bound SR script checkpoint rehydration."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.world_bridge_e562_script_checkpoint_authority import (
    PROOF_FIELDS,
    build_worldbridge_e562_script_checkpoint_authority,
    validate_worldbridge_e562_script_checkpoint_authority,
)
from tools.check_worldbridge_e554_shared_randomness_authority import (
    _trusted_sample_project,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def _verify_script_checkpoint(project: Path) -> dict[str, object]:
    _application = QApplication.instance() or QApplication([])
    scene = project / "scenes" / "challenge_scene.pond"
    get_editor_context().current_project_path = str(project)
    _require(
        scene_manager.get_scene_manager().load_scene(str(scene)),
        "E562 scene load failed",
    )
    viewport = GameViewport()
    viewport._using_scene_runtime = True
    viewport._sr_runtime_epoch = "e562-script-checkpoint"
    viewport._sr_runtime_scene_path = str(scene)
    _require(
        viewport._load_scene_runtime_entities(),
        "E562 SR runtime load failed",
    )
    viewport._unified_pond_mode = True
    viewport.is_playing = True
    viewport.is_paused = False
    viewport._ensure_unified_pond()

    target = next(
        (
            entity
            for entity in viewport.scene_runtime_entities
            if getattr(entity, "scripts", None)
        ),
        None,
    )
    _require(target is not None, "E562 requires a file-backed scene script")
    checkpoint = viewport.capture_worldbridge_live_checkpoint("e562-before")
    source_graph = checkpoint.get("lifecycle", {}).get("script_graph")
    _require(
        isinstance(source_graph, dict),
        "E562 checkpoint did not carry a script graph",
    )
    source_row = next(
        (
            row
            for row in source_graph["entities"]
            if row["entity_id"] == target.id
        ),
        None,
    )
    _require(source_row is not None, "E562 target script graph row missing")
    original_count = len(target.scripts)
    target.replace_scripts([])
    restore_result = viewport.restore_worldbridge_live_checkpoint(checkpoint)
    _require(
        restore_result.get("restored") is True,
        "E562 script checkpoint restore failed",
    )
    script_restore_result = getattr(
        viewport,
        "_worldbridge_script_checkpoint_restore_result",
        None,
    )
    _require(
        isinstance(script_restore_result, dict),
        "E562 script-specific restore result missing",
    )
    _require(
        len(target.scripts) == original_count,
        "E562 script count drifted",
    )

    recaptured = viewport.capture_worldbridge_live_checkpoint("e562-after")
    recaptured_graph = recaptured.get("lifecycle", {}).get("script_graph")
    _require(
        isinstance(recaptured_graph, dict),
        "E562 recapture did not carry a script graph",
    )
    witness = build_worldbridge_e562_script_checkpoint_authority(
        runtime_epoch=str(viewport._sr_runtime_epoch),
        source_script_graph=source_graph,
        restore_result=script_restore_result,
        recaptured_script_graph=recaptured_graph,
    )
    validation = validate_worldbridge_e562_script_checkpoint_authority(witness)
    _require(
        validation == {"valid": True, "errors": []},
        "E562 witness invalid",
    )
    _require(
        all(witness[field] is True for field in PROOF_FIELDS),
        "E562 did not prove every script descriptor boundary",
    )

    tampered = copy.deepcopy(witness)
    tampered["recaptured_script_graph"]["entities"][0]["scripts"][0][
        "source_sha256"
    ] = "0" * 64
    tampered = _reseal(tampered)
    tampered_validation = (
        validate_worldbridge_e562_script_checkpoint_authority(tampered)
    )
    _require(
        tampered_validation["valid"] is False,
        "tampered E562 witness accepted",
    )
    _require(
        any(
            error in {
                "source_script_digest_invalid",
                "script_descriptors_mismatch",
                "graph_digest_mismatch",
            }
            or "source_digest" in error
            for error in tampered_validation["errors"]
        ),
        "E562 did not diagnose script source tamper",
    )

    return {
        "schema_version": 1,
        "status": "worldbridge_e562_script_checkpoint_authority",
        "real_game_viewport": True,
        "read_only": True,
        "scope": witness["scope"],
        "policy": witness["policy"],
        "runtime_epoch": witness["runtime_epoch"],
        "source_graph_digest": witness["source_graph_digest"],
        "recaptured_graph_digest": witness["recaptured_graph_digest"],
        "restored_entities": script_restore_result["restored_entities"],
        "restored_scripts": script_restore_result["restored_scripts"],
        "proof": {field: witness[field] for field in PROOF_FIELDS},
        "remaining_script_blockers": witness["remaining_script_blockers"],
        "witness_validated": True,
        "witness_digest": witness["witness_digest"],
        "tampered_source_rejected": True,
        "tampered_errors": tampered_validation["errors"],
        "witness": witness,
        "contract_valid": True,
        "errors": [],
        "ok": True,
    }


def verify() -> dict[str, object]:
    with _trusted_sample_project(ROOT) as project:
        return _verify_script_checkpoint(project)


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
