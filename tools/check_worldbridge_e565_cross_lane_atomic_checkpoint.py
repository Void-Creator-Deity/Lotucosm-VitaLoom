#!/usr/bin/env python3
"""Probe E565 cross-process SR/PS checkpoint restore."""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
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

from core.Lotucosm.runtime.world_bridge_e551_scene_pond_checkpoint_authority import (
    build_worldbridge_e551_scene_pond_checkpoint_authority,
    validate_worldbridge_e551_scene_pond_checkpoint_authority,
)
from core.Lotucosm.runtime.world_bridge_e565_cross_lane_atomic_checkpoint import (
    PROOF_FIELDS,
    apply_checkpoint_to_fresh_viewport,
    build_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
    validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import _new_viewport
from tools.check_worldbridge_e551_scene_pond_checkpoint_authority import (
    _atomic_capture_probe,
)
from tools.check_worldbridge_e505_fresh_host_reconstruction import (
    verify as verify_e505,
)
from tools.check_worldbridge_e564_checkpoint_transaction import (
    verify as verify_e564,
)


def _child_restore(input_path: Path, output_path: Path) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    project = Path(payload["project_path"]).resolve()
    scene = Path(payload["scene_path"]).resolve()
    checkpoint = payload["checkpoint"]
    app = QApplication.instance() or QApplication([])
    viewport = _new_viewport(project, scene, "e505-root-seed")
    viewport._begin_sr_snapshot_lifetime()
    try:
        applied = apply_checkpoint_to_fresh_viewport(
            viewport=viewport,
            source_checkpoint=checkpoint,
            source_structure=payload["source_structure"],
            source_next_rng_snapshot=payload["source_next_rng_snapshot"],
        )
        output = {
            "parent_pid": int(payload["parent_pid"]),
            "child_pid": os.getpid(),
            "source_checkpoint_digest": checkpoint["digest"],
            "fresh_checkpoint": applied["fresh_checkpoint"],
            "structure_comparison": applied["structure_comparison"],
            "e504_witness": applied["e504_witness"],
            "fresh_host_quarantinable": applied["host_quarantinable"],
            "errors": [],
            "ok": True,
        }
    except Exception as exc:
        output = {
            "child_pid": os.getpid(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "report": getattr(exc, "report", None),
            "ok": False,
        }
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, allow_nan=False, sort_keys=True),
        encoding="utf-8",
    )
    return 0 if output["ok"] else 1


def verify() -> dict[str, Any]:
    e505 = verify_e505()
    checkpoint = e505["source_checkpoint"]
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    atomic = _atomic_capture_probe(project, scene)
    e551_witness = build_worldbridge_e551_scene_pond_checkpoint_authority(
        checkpoint=checkpoint,
        fresh_dual_lane_witness=e505["witness"],
        atomic_capture_evidence=atomic,
    )
    if (
        validate_worldbridge_e551_scene_pond_checkpoint_authority(e551_witness)
        != {"valid": True, "errors": []}
    ):
        raise AssertionError("E565 E551 prerequisite invalid")
    e564 = verify_e564()
    transaction_evidence = {
        "artifact_digest": e564["artifact_digest"],
        "imported_artifact_digest": e564["artifact_digest"],
        "project_lock_digest": e564["project_lock_digest"],
        "contention_code": e564["cross_process_contention"]["code"],
        "holder_pid": e564["holder_pid"],
        "importer_pid": e564["importer_pid"],
        "interlock_released": e564["interlock_released"],
        "canonical_artifact": e564["artifact_canonical"],
        "atomic_write_failure_preserved_previous": e564[
            "atomic_replace_verified_by_unit_failure_injection"
        ],
        "errors": [],
    }
    with tempfile.TemporaryDirectory(prefix="vitaloom-e565-") as temp:
        temp_path = Path(temp)
        input_path = temp_path / "input.json"
        output_path = temp_path / "output.json"
        input_path.write_text(
            json.dumps(
                {
                    "project_path": str(project),
                    "scene_path": str(scene),
                    "checkpoint": checkpoint,
                    "source_structure": e505["source_structure"],
                    "source_next_rng_snapshot": e505[
                        "source_next_rng_snapshot"
                    ],
                    "parent_pid": os.getpid(),
                },
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        child = subprocess.run(
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
        output = (
            json.loads(output_path.read_text(encoding="utf-8"))
            if output_path.is_file()
            else None
        )
        if child.returncode != 0 or not output or output.get("ok") is not True:
            return {
                "status": "worldbridge_e565_probe",
                "child_returncode": child.returncode,
                "child_stdout": child.stdout[-2000:],
                "child_stderr": child.stderr[-4000:],
                "child_output": output,
                "e551_witness_digest": e551_witness["witness_digest"],
                "ok": False,
            }
        try:
            witness = (
                build_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
                    e551_witness=e551_witness,
                    transaction_evidence=transaction_evidence,
                    source_checkpoint=checkpoint,
                    child_result=output,
                )
            )
        except ValueError as exc:
            return {
                "status": "worldbridge_e565_probe",
                "child_returncode": child.returncode,
                "child_output": output,
                "e551_witness_digest": e551_witness["witness_digest"],
                "authority_errors": str(exc),
                "ok": False,
            }
        validation = (
            validate_worldbridge_e565_cross_lane_atomic_checkpoint_authority(
                witness
            )
        )
        if validation != {"valid": True, "errors": []}:
            raise AssertionError(
                "E565 witness invalid: " + ",".join(validation["errors"])
            )
        return {
            "schema_version": 1,
            "status": "worldbridge_e565_cross_lane_atomic_checkpoint",
            "real_child_process": True,
            "child_returncode": child.returncode,
            "parent_pid": os.getpid(),
            "child_pid": output["child_pid"],
            "source_checkpoint_digest": witness["source_checkpoint_digest"],
            "fresh_checkpoint_digest": witness["fresh_checkpoint_digest"],
            "e551_witness_digest": witness["e551_witness_digest"],
            "e564_transaction_digest": witness[
                "transaction_artifact_digest"
            ],
            "fresh_dual_lane_parity": witness["fresh_dual_lane_parity"],
            "structure_equal": witness["structure_equal"],
            "proof": {field: witness[field] for field in PROOF_FIELDS},
            "atomic_sr_ps_checkpoint": witness[
                "atomic_sr_ps_checkpoint"
            ],
            "cross_lane_restore_admitted": witness[
                "cross_lane_restore_admitted"
            ],
            "witness_digest": witness["witness_digest"],
            "witness": witness,
            "errors": [],
            "ok": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore-child", nargs=2, metavar=("INPUT", "OUTPUT"))
    args = parser.parse_args()
    if args.restore_child is not None:
        return _child_restore(
            Path(args.restore_child[0]),
            Path(args.restore_child[1]),
        )
    result = verify()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
