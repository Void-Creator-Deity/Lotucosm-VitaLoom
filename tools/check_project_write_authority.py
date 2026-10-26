#!/usr/bin/env python3
"""Verify the canonical Project World write interlock across public seams."""
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
    checkpoint_interlock_status,
    export_checkpoint_artifact,
    import_checkpoint_artifact,
)
from core.VitaLoom.commands.runtime_commands import _refresh_project_lock
from core.VitaLoom.project.asset_reference_transaction import (
    AssetReferenceTransactionError,
    resolve_asset_reference_transaction,
)
from core.VitaLoom.project.project_manager import ProjectManager
from core.VitaLoom.project.project_write_authority import (
    build_project_write_authority_witness,
    project_write_interlock,
    validate_project_write_authority_witness,
)
from tools.check_worldbridge_e548_rng_draw_order_authority import (
    _trusted_sample_project,
)
from tools.check_worldbridge_e562_script_checkpoint_authority import (
    _verify_script_checkpoint,
)


RUNTIME_CONTRACT_VERSION = "1.0.0"


def _write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True),
        encoding="utf-8",
    )


def _hold(project: Path, ready: Path, release: Path) -> int:
    with project_write_interlock(
        project,
        authority_action="e566_holder",
    ) as ticket:
        _write(ready, ticket)
        deadline = time.monotonic() + 30.0
        while not release.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("E566 release signal timed out")
            time.sleep(0.05)
    return 0


def _probe_checkpoint(
    project: Path,
    scene: Path,
    artifact: Path,
    output: Path,
) -> int:
    try:
        import_checkpoint_artifact(
            project_path=project,
            scene_path=scene,
            artifact_path=artifact,
            runtime_contract_version=RUNTIME_CONTRACT_VERSION,
        )
    except CheckpointTransactionError as exc:
        result = {
            "blocked": exc.code == "checkpoint_interlock_held",
            "code": exc.code,
        }
    else:
        result = {
            "blocked": False,
            "code": "checkpoint_import_succeeded",
        }
    _write(output, result)
    return 0 if result["blocked"] else 1


def _probe_lock_refresh(project: Path, output: Path) -> int:
    result = {
        "blocked": _refresh_project_lock(project) is False,
        "code": "project_lock_refresh_blocked",
    }
    _write(output, result)
    return 0 if result["blocked"] else 1


def _probe_asset(project: Path, output: Path) -> int:
    try:
        resolve_asset_reference_transaction(
            project,
            "missing",
            action="rollback",
        )
    except AssetReferenceTransactionError as exc:
        result = {
            "blocked": exc.code == "asset_transaction_interlock_held",
            "code": exc.code,
        }
    else:
        result = {
            "blocked": False,
            "code": "asset_transaction_not_blocked",
        }
    _write(output, result)
    return 0 if result["blocked"] else 1


def _probe_project_save(project: Path, output: Path) -> int:
    _application = QApplication.instance() or QApplication([])
    ProjectManager._instance = None
    manager = ProjectManager()
    saved = manager.save_project(str(project))
    report = dict(manager.last_project_save_report or {})
    result = {
        "blocked": saved is False
        and report.get("code") == "project_write_interlock_held",
        "saved": bool(saved),
        "code": report.get("code"),
    }
    _write(output, result)
    return 0 if result["blocked"] else 1


def _run_probe(*args: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *args],
        cwd=ROOT,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "E566 probe failed: "
            + completed.stdout[-1000:]
            + completed.stderr[-3000:]
        )
    return json.loads(Path(args[-1]).read_text(encoding="utf-8"))


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
        with tempfile.TemporaryDirectory(prefix="vitaloom-e566-") as temp:
            temp_path = Path(temp)
            artifact = temp_path / "checkpoint.json"
            ready = temp_path / "holder.ready"
            release = temp_path / "holder.release"
            checkpoint_output = temp_path / "checkpoint-probe.json"
            lock_output = temp_path / "lock.json"
            asset_output = temp_path / "asset.json"
            project_output = temp_path / "project.json"
            export_checkpoint_artifact(
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
                    "--hold",
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
                            "E566 holder exited early: "
                            + stdout[-1000:]
                            + stderr[-2000:]
                        )
                    if time.monotonic() >= deadline:
                        raise TimeoutError("E566 holder ready signal timed out")
                    time.sleep(0.05)
                checkpoint = _run_probe(
                    "--probe-checkpoint",
                    str(project),
                    str(scene),
                    str(artifact),
                    str(checkpoint_output),
                )
                lock_refresh = _run_probe(
                    "--probe-lock-refresh",
                    str(project),
                    str(lock_output),
                )
                asset = _run_probe(
                    "--probe-asset",
                    str(project),
                    str(asset_output),
                )
                project_save = _run_probe(
                    "--probe-project-save",
                    str(project),
                    str(project_output),
                )
            finally:
                release.write_text("release", encoding="utf-8")
                holder_stdout, holder_stderr = holder.communicate(timeout=30)
                if holder.returncode != 0:
                    raise RuntimeError(
                        "E566 holder failed: "
                        + holder_stdout[-1000:]
                        + holder_stderr[-2000:]
                    )
            imported = import_checkpoint_artifact(
                project_path=project,
                scene_path=scene,
                artifact_path=artifact,
                runtime_contract_version=RUNTIME_CONTRACT_VERSION,
            )
            holder_pid = json.loads(
                ready.read_text(encoding="utf-8")
            )["owner_pid"]
            interlock_path = checkpoint_interlock_status(project)[
                "interlock_path"
            ]
            evidence = {
                "holder_pid": holder_pid,
                "importer_pid": os.getpid(),
                "canonical_interlock_path": interlock_path,
                "checkpoint_import_blocked": checkpoint["blocked"],
                "asset_transaction_blocked": asset["blocked"],
                "project_lock_refresh_blocked": lock_refresh["blocked"],
                "project_save_blocked": project_save["blocked"],
                "post_release_import_succeeded": (
                    imported["decision"] == "imported"
                ),
                "interlock_released": (
                    checkpoint_interlock_status(project)["held"] is False
                ),
            }
            witness = build_project_write_authority_witness(evidence)
            validation = validate_project_write_authority_witness(witness)
            if validation != {"valid": True, "errors": []}:
                raise AssertionError(
                    "E566 witness invalid: " + ",".join(validation["errors"])
                )
            return {
                "schema_version": 1,
                "status": "project_write_authority",
                "holder_pid": holder_pid,
                "importer_pid": os.getpid(),
                "canonical_interlock_path": interlock_path,
                "checkpoint_import_blocked": checkpoint,
                "asset_transaction_blocked": asset,
                "project_lock_refresh_blocked": lock_refresh,
                "project_save_blocked": project_save,
                "post_release_import_succeeded": (
                    imported["decision"] == "imported"
                ),
                "interlock_released": (
                    checkpoint_interlock_status(project)["held"] is False
                ),
                "witness_digest": witness["witness_digest"],
                "witness": witness,
                "errors": [],
                "ok": True,
            }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hold", nargs=3, metavar=("PROJECT", "READY", "RELEASE"))
    parser.add_argument(
        "--probe-checkpoint",
        nargs=4,
        metavar=("PROJECT", "SCENE", "ARTIFACT", "OUTPUT"),
    )
    parser.add_argument(
        "--probe-lock-refresh",
        nargs=2,
        metavar=("PROJECT", "OUTPUT"),
    )
    parser.add_argument(
        "--probe-asset",
        nargs=2,
        metavar=("PROJECT", "OUTPUT"),
    )
    parser.add_argument(
        "--probe-project-save",
        nargs=2,
        metavar=("PROJECT", "OUTPUT"),
    )
    args = parser.parse_args()
    if args.hold is not None:
        return _hold(
            Path(args.hold[0]),
            Path(args.hold[1]),
            Path(args.hold[2]),
        )
    if args.probe_checkpoint is not None:
        return _probe_checkpoint(
            Path(args.probe_checkpoint[0]),
            Path(args.probe_checkpoint[1]),
            Path(args.probe_checkpoint[2]),
            Path(args.probe_checkpoint[3]),
        )
    if args.probe_lock_refresh is not None:
        return _probe_lock_refresh(
            Path(args.probe_lock_refresh[0]),
            Path(args.probe_lock_refresh[1]),
        )
    if args.probe_asset is not None:
        return _probe_asset(
            Path(args.probe_asset[0]),
            Path(args.probe_asset[1]),
        )
    if args.probe_project_save is not None:
        return _probe_project_save(
            Path(args.probe_project_save[0]),
            Path(args.probe_project_save[1]),
        )
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
