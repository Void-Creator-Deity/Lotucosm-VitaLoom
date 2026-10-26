#!/usr/bin/env python3
"""Verify E563 cross-process source-bundle rehydration and quarantine."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6.QtWidgets import QApplication

from core.Lotucosm.runtime.world_bridge_e562_script_checkpoint_authority import (
    build_worldbridge_e562_script_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_e563_cross_session_script_rehydration import (
    PROOF_FIELDS,
    build_cross_session_source_bundle,
    build_worldbridge_e563_cross_session_script_rehydration_authority,
    restore_cross_session_script_checkpoint,
    validate_worldbridge_e563_cross_session_script_rehydration_authority,
)
from core.Lotucosm.runtime.world_bridge_script_checkpoint import (
    capture_sr_script_checkpoint,
)
from core.VitaLoom.core.editor_context import get_editor_context
from core.VitaLoom.scene import scene_manager
from core.VitaLoom.viewports.game_viewport import GameViewport
from tools.check_worldbridge_e548_rng_draw_order_authority import (
    _trusted_sample_project,
)
from tools.check_worldbridge_e562_script_checkpoint_authority import (
    _verify_script_checkpoint,
)


RUNTIME_CONTRACT_VERSION = "1.0.0"
TARGET_RUNTIME_EPOCH = "e563-fresh-process"


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


def _reseal_bundle(bundle: dict[str, object]) -> dict[str, object]:
    sealed = copy.deepcopy(bundle)
    sealed["bundle_digest"] = ""
    sealed["bundle_digest"] = _digest(sealed)
    return sealed


def _placeholder_entities(graph: dict[str, object]) -> list[SimpleNamespace]:
    entities: list[SimpleNamespace] = []
    for row in graph.get("entities", []):
        if not isinstance(row, dict):
            continue
        entity = SimpleNamespace(id=str(row["entity_id"]), scripts=[object()])

        def replace_scripts(
            replacement: list[object],
            *,
            owner: SimpleNamespace = entity,
        ) -> None:
            owner.scripts = list(replacement)

        entity.replace_scripts = replace_scripts
        entities.append(entity)
    return entities


def _quarantine(
    *,
    graph: dict[str, object],
    bundle: dict[str, object],
    project: Path,
    runtime_contract_version: str = RUNTIME_CONTRACT_VERSION,
) -> dict[str, object]:
    entities = _placeholder_entities(graph)
    before = [list(entity.scripts) for entity in entities]
    result = restore_cross_session_script_checkpoint(
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=runtime_contract_version,
        target_runtime_epoch=TARGET_RUNTIME_EPOCH,
        project_path=project,
        entities=entities,
        instantiate_script=lambda _data: object(),
    )
    _require(result["decision"] == "quarantined", "E563 case did not quarantine")
    _require(result["admitted"] is False, "E563 quarantined case was admitted")
    _require(
        result["live_owner_preserved"] is True,
        "E563 quarantined case mutated the live owner",
    )
    _require(
        [list(entity.scripts) for entity in entities] == before,
        "E563 quarantined case changed script identity",
    )
    return result


def _child_restore(input_path: Path, output_path: Path) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    project = Path(payload["project_path"]).resolve()
    scene = Path(payload["scene_path"]).resolve()
    graph = payload["checkpoint_graph"]
    bundle = payload["source_bundle"]
    target_epoch = str(payload["target_runtime_epoch"])

    _application = QApplication.instance() or QApplication([])
    get_editor_context().current_project_path = str(project)
    _require(
        scene_manager.get_scene_manager().load_scene(str(scene)),
        "E563 child scene load failed",
    )
    viewport = GameViewport()
    viewport._using_scene_runtime = True
    viewport._sr_runtime_epoch = target_epoch
    viewport._sr_runtime_scene_path = str(scene)
    viewport._sr_runtime_project_path = str(project)
    _require(
        viewport._load_scene_runtime_entities(),
        "E563 child SR runtime load failed",
    )
    _require(
        not viewport._sr_script_failure_receipts,
        "E563 child trusted scripts failed to load",
    )
    entities = list(viewport.scene_runtime_entities)
    for entity in entities:
        entity.replace_scripts([])

    restore_result = restore_cross_session_script_checkpoint(
        checkpoint_graph=graph,
        source_bundle=bundle,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        target_runtime_epoch=target_epoch,
        project_path=project,
        entities=entities,
        instantiate_script=lambda descriptor: viewport._instantiate_scene_script(
            descriptor,
            str(project),
        ),
    )
    recaptured = capture_sr_script_checkpoint(
        runtime_epoch=target_epoch,
        project_path=project,
        entities=entities,
    )
    result = {
        "child_pid": os.getpid(),
        "project_path": str(project),
        "scene_path": str(scene),
        "restore_result": restore_result,
        "recaptured_graph": recaptured,
        "script_failure_receipts": list(viewport._sr_script_failure_receipts),
        "ok": restore_result.get("decision") == "rehydrated",
    }
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True),
        encoding="utf-8",
    )
    return 0 if result["ok"] else 1


def _run_child(
    *,
    project: Path,
    scene: Path,
    graph: dict[str, object],
    bundle: dict[str, object],
) -> tuple[dict[str, Any], int]:
    with tempfile.TemporaryDirectory(prefix="vitaloom-e563-child-") as temp:
        temp_path = Path(temp)
        input_path = temp_path / "input.json"
        output_path = temp_path / "output.json"
        input_path.write_text(
            json.dumps(
                {
                    "project_path": str(project),
                    "scene_path": str(scene),
                    "checkpoint_graph": graph,
                    "source_bundle": bundle,
                    "target_runtime_epoch": TARGET_RUNTIME_EPOCH,
                },
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--restore-child",
                str(input_path),
                str(output_path),
            ],
            cwd=ROOT,
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            child_output = (
                output_path.read_text(encoding="utf-8")
                if output_path.is_file()
                else "<missing child output>"
            )
            raise RuntimeError(
                f"E563 child restore failed ({result.returncode}): "
                + result.stdout[-2000:]
                + result.stderr[-4000:]
                + child_output[-4000:]
            )
        return (
            json.loads(output_path.read_text(encoding="utf-8")),
            result.returncode,
        )


def verify() -> dict[str, object]:
    with _trusted_sample_project(ROOT) as source_project:
        e562 = _verify_script_checkpoint(source_project)
        base_witness = e562["witness"]
        graph = base_witness["source_script_graph"]
        bundle = build_cross_session_source_bundle(
            checkpoint_graph=graph,
            project_path=source_project,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
        scene = source_project / "scenes" / "challenge_scene.pond"

        with tempfile.TemporaryDirectory(
            prefix="vitaloom-e563-fresh-project-"
        ) as fresh_temp:
            fresh_project = Path(fresh_temp) / source_project.name
            shutil.copytree(source_project, fresh_project)
            fresh_scene = fresh_project / scene.relative_to(source_project)
            child_result, child_returncode = _run_child(
                project=fresh_project,
                scene=fresh_scene,
                graph=graph,
                bundle=bundle,
            )
            _require(
                child_result["child_pid"] != os.getpid(),
                "E563 restore did not cross a process boundary",
            )
            _require(
                child_result["restore_result"]["decision"] == "rehydrated",
                "E563 child did not rehydrate scripts",
            )
            _require(
                not child_result["script_failure_receipts"],
                "E563 child rehydration recorded script failures",
            )

        with tempfile.TemporaryDirectory(
            prefix="vitaloom-e563-missing-source-"
        ) as missing_temp:
            missing_project = Path(missing_temp) / source_project.name
            shutil.copytree(source_project, missing_project)
            (missing_project / "scripts" / "evo_central_brain_pvaec.py").unlink()
            missing_result = _quarantine(
                graph=graph,
                bundle=bundle,
                project=missing_project,
            )

        version_result = _quarantine(
            graph=graph,
            bundle=bundle,
            project=source_project,
            runtime_contract_version="2.0.0",
        )
        tampered_bundle = copy.deepcopy(bundle)
        tampered_bundle["sources"][0]["sha256"] = "0" * 64
        tampered_bundle = _reseal_bundle(tampered_bundle)
        tamper_result = _quarantine(
            graph=graph,
            bundle=tampered_bundle,
            project=source_project,
        )

        witness = (
            build_worldbridge_e563_cross_session_script_rehydration_authority(
                runtime_contract_version=RUNTIME_CONTRACT_VERSION,
                base_script_checkpoint_witness=base_witness,
                source_bundle=bundle,
                fresh_restore_result=child_result["restore_result"],
                fresh_recaptured_script_graph=child_result["recaptured_graph"],
                quarantine_results=[
                    missing_result,
                    version_result,
                    tamper_result,
                ],
            )
        )
        validation = (
            validate_worldbridge_e563_cross_session_script_rehydration_authority(
                witness
            )
        )
        _require(
            validation == {"valid": True, "errors": []},
            "E563 witness invalid: " + ",".join(validation["errors"]),
        )
        _require(
            all(witness[field] is True for field in PROOF_FIELDS),
            "E563 did not prove every required boundary",
        )
        return {
            "schema_version": 1,
            "status": "worldbridge_e563_cross_session_script_rehydration",
            "real_child_process": True,
            "child_returncode": child_returncode,
            "child_pid": child_result["child_pid"],
            "parent_pid": os.getpid(),
            "source_graph_digest": witness["source_graph_digest"],
            "fresh_graph_digest": witness["fresh_graph_digest"],
            "source_bundle_digest": witness["source_bundle_digest"],
            "restored_entities": child_result["restore_result"][
                "restore_result"
            ]["restored_entities"],
            "restored_scripts": child_result["restore_result"][
                "restore_result"
            ]["restored_scripts"],
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "quarantine_reasons": [
                missing_result["quarantine_reason"],
                version_result["quarantine_reason"],
                tamper_result["quarantine_reason"],
            ],
            "remaining_script_blockers": witness[
                "remaining_script_blockers"
            ],
            "witness_validated": True,
            "witness_digest": witness["witness_digest"],
            "witness": witness,
            "contract_valid": True,
            "errors": [],
            "ok": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore-child", nargs=2, metavar=("INPUT", "OUTPUT"))
    args = parser.parse_args()
    if args.restore_child is not None:
        return _child_restore(Path(args.restore_child[0]), Path(args.restore_child[1]))
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
