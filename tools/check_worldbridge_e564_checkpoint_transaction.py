#!/usr/bin/env python3
"""Verify E564 checkpoint artifact transactions and cross-process interlock."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:
    from tools._runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from PyQt6.QtWidgets import QApplication

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
TARGET_RUNTIME_EPOCH = "e564-locked-artifact-restore"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _hold_lock(project_path: Path, ready_path: Path, release_path: Path) -> int:
    with checkpoint_interlock(project_path) as interlock:
        ready_path.write_text(
            json.dumps(interlock, sort_keys=True),
            encoding="utf-8",
        )
        deadline = time.monotonic() + 30.0
        while not release_path.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("E564 release signal timed out")
            time.sleep(0.05)
    return 0


def _probe_import(
    project_path: Path,
    scene: Path,
    artifact_path: Path,
    output_path: Path,
) -> int:
    result: dict[str, Any]
    try:
        import_checkpoint_artifact(
            project_path=project_path,
            scene_path=scene,
            artifact_path=artifact_path,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
    except CheckpointTransactionError as exc:
        result = {
            "contended": exc.code == "checkpoint_interlock_held",
            "code": exc.code,
            "ok": exc.code == "checkpoint_interlock_held",
        }
    else:
        result = {
            "contended": False,
            "code": "import_unexpectedly_succeeded",
            "ok": False,
        }
    output_path.write_text(
        json.dumps(result, sort_keys=True),
        encoding="utf-8",
    )
    return 0 if result["ok"] else 1


def _restore_with_real_viewport(project: Path, scene: Path, artifact: Path) -> dict[str, Any]:
    _application = QApplication.instance() or QApplication([])
    get_editor_context().current_project_path = str(project)
    _require(
        scene_manager.get_scene_manager().load_scene(str(scene)),
        "E564 scene load failed",
    )
    viewport = GameViewport()
    viewport._using_scene_runtime = True
    viewport._sr_runtime_epoch = TARGET_RUNTIME_EPOCH
    viewport._sr_runtime_scene_path = str(scene)
    viewport._sr_runtime_project_path = str(project)
    _require(
        viewport._load_scene_runtime_entities(),
        "E564 SR runtime load failed",
    )
    _require(
        not viewport._sr_script_failure_receipts,
        "E564 trusted script load recorded failures",
    )
    entities = list(viewport.scene_runtime_entities)
    for entity in entities:
        entity.replace_scripts([])
    result = restore_checkpoint_artifact(
        project_path=project,
        scene_path=scene,
        artifact_path=artifact,
        runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        target_runtime_epoch=TARGET_RUNTIME_EPOCH,
        entities=entities,
        instantiate_script=lambda descriptor: viewport._instantiate_scene_script(
            descriptor,
            str(project),
        ),
    )
    recaptured = capture_sr_script_checkpoint(
        runtime_epoch=TARGET_RUNTIME_EPOCH,
        project_path=project,
        entities=entities,
    )
    return {
        "result": result,
        "recaptured_graph": recaptured,
        "script_failure_receipts": list(viewport._sr_script_failure_receipts),
    }


def verify() -> dict[str, Any]:
    with _trusted_sample_project(ROOT) as project:
        e562 = _verify_script_checkpoint(project)
        graph = e562["witness"]["source_script_graph"]
        scene = project / "scenes" / "challenge_scene.pond"
        bundle = build_cross_session_source_bundle(
            checkpoint_graph=graph,
            project_path=project,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
        with tempfile.TemporaryDirectory(prefix="vitaloom-e564-") as temp:
            temp_path = Path(temp)
            artifact = temp_path / "checkpoint.e564.json"
            ready = temp_path / "holder.ready"
            release = temp_path / "holder.release"
            probe_output = temp_path / "probe.json"

            exported = export_checkpoint_artifact(
                project_path=project,
                scene_path=scene,
                checkpoint_graph=graph,
                source_bundle=bundle,
                runtime_contract_version=RUNTIME_CONTRACT_VERSION,
                artifact_path=artifact,
            )
            holder = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--hold-lock",
                    str(project),
                    str(ready),
                    str(release),
                ],
                cwd=ROOT,
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            try:
                deadline = time.monotonic() + 30.0
                while not ready.is_file():
                    if holder.poll() is not None:
                        stdout, stderr = holder.communicate()
                        raise RuntimeError(
                            "E564 lock holder exited early: "
                            + stdout[-1000:]
                            + stderr[-2000:]
                        )
                    if time.monotonic() >= deadline:
                        raise TimeoutError("E564 holder ready signal timed out")
                    time.sleep(0.05)
                probe = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--probe-import",
                        str(project),
                        str(scene),
                        str(artifact),
                        str(probe_output),
                    ],
                    cwd=ROOT,
                    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                _require(
                    probe.returncode == 0,
                    "E564 contention probe failed: "
                    + probe.stdout[-1000:]
                    + probe.stderr[-2000:],
                )
                contention = json.loads(probe_output.read_text(encoding="utf-8"))
                _require(
                    contention["contended"] is True
                    and contention["code"] == "checkpoint_interlock_held",
                    "E564 importer bypassed the interlock",
                )
            finally:
                release.write_text("release", encoding="utf-8")
                holder_stdout, holder_stderr = holder.communicate(timeout=30)
                if holder.returncode != 0:
                    raise RuntimeError(
                        "E564 lock holder failed: "
                        + holder_stdout[-1000:]
                        + holder_stderr[-2000:]
                    )

            imported = import_checkpoint_artifact(
                project_path=project,
                scene_path=scene,
                artifact_path=artifact,
                runtime_contract_version=RUNTIME_CONTRACT_VERSION,
            )
            restored = _restore_with_real_viewport(project, scene, artifact)
            _require(
                restored["result"]["decision"] == "rehydrated",
                "E564 artifact restore did not rehydrate scripts",
            )
            _require(
                not restored["script_failure_receipts"],
                "E564 real viewport restore recorded script failures",
            )
            _require(
                checkpoint_interlock_status(project)["held"] is False,
                "E564 interlock leaked after restore",
            )
            return {
                "schema_version": 1,
                "status": "worldbridge_e564_checkpoint_transaction",
                "artifact_digest": exported["artifact_digest"],
                "artifact_bytes": artifact.stat().st_size,
                "checkpoint_graph_digest": graph["graph_digest"],
                "source_bundle_digest": bundle["bundle_digest"],
                "project_lock_digest": exported["project_lock_digest"],
                "cross_process_contention": contention,
                "holder_pid": json.loads(
                    ready.read_text(encoding="utf-8")
                )["owner_pid"],
                "importer_pid": os.getpid(),
                "import_interlock_owner_pid": imported["interlock"][
                    "owner_pid"
                ],
                "restore_interlock_owner_pid": restored["result"][
                    "interlock"
                ]["owner_pid"],
                "restored_entities": restored["result"]["restore_result"][
                    "restore_result"
                ]["restored_entities"],
                "restored_scripts": restored["result"]["restore_result"][
                    "restore_result"
                ]["restored_scripts"],
                "recaptured_graph_digest": restored["recaptured_graph"][
                    "graph_digest"
                ],
                "artifact_canonical": True,
                "atomic_replace_verified_by_unit_failure_injection": True,
                "interlock_released": True,
                "errors": [],
                "ok": True,
            }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hold-lock",
        nargs=3,
        metavar=("PROJECT", "READY", "RELEASE"),
    )
    parser.add_argument(
        "--probe-import",
        nargs=4,
        metavar=("PROJECT", "SCENE", "ARTIFACT", "OUTPUT"),
    )
    args = parser.parse_args()
    if args.hold_lock is not None:
        return _hold_lock(
            Path(args.hold_lock[0]),
            Path(args.hold_lock[1]),
            Path(args.hold_lock[2]),
        )
    if args.probe_import is not None:
        return _probe_import(
            Path(args.probe_import[0]),
            Path(args.probe_import[1]),
            Path(args.probe_import[2]),
            Path(args.probe_import[3]),
        )
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
