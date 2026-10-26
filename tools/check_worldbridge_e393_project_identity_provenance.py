from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import E384LedgerError, build_project_world_identity, consume_e382_receipt_durable, inspect_e384_receipt_ledger


def _child() -> dict[str, object]:
    completed = subprocess.run([sys.executable, "-B", "tools/check_worldbridge_e381_tick_sequence.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("status") == "worldbridge_e381_tick_sequence" and completed.returncode == 0:
            return value
    raise AssertionError(completed.stderr[-2000:])


def verify() -> dict[str, object]:
    source_project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e393-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source_project, project)
        scene = project / "scenes" / "challenge_scene.pond"
        identity = build_project_world_identity(project, scene)
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        root = Path(temporary) / "ledger"
        root.mkdir()
        consumed = consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        local = inspect_e384_receipt_ledger(root, project_identity=identity)
        receipt_digest = consumed["receipt_digest"]
        snapshot = local["component_provenance"][receipt_digest]["project_identity"]
        snapshot_bound = snapshot == identity
        scene_bytes = scene.read_bytes()
        scene.write_bytes(scene_bytes + b"\n")
        changed_identity = build_project_world_identity(project, scene)
        try:
            consume_e382_receipt_durable(root, encoded, project_identity=changed_identity, expected_child_result=child)
        except E384LedgerError as exc:
            changed_world_rejected = exc.code == "receipt_project_identity_mismatch"
        else:
            changed_world_rejected = False
        scene.write_bytes(scene_bytes)
        result = {
            "status": "worldbridge_e393_project_identity_provenance",
            "contract_valid": snapshot_bound and changed_world_rejected and local["consumed_count"] == 1,
            "real_manifest_scene_snapshot_recorded": snapshot_bound,
            "changed_project_world_rejected": changed_world_rejected,
            "ledger_consumed_count_after_rejection": local["consumed_count"],
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
