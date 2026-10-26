from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
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


def _rejected(root: Path, encoded: bytes, identity: object, child: dict[str, object]) -> bool:
    try:
        consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
    except E384LedgerError as exc:
        return exc.code == "receipt_project_identity_mismatch"
    return False


def verify() -> dict[str, object]:
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e394-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        scene = project / "scenes" / "challenge_scene.pond"
        identity = build_project_world_identity(project, scene)
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        ledger = Path(temporary) / "ledger"
        ledger.mkdir()
        consume_e382_receipt_durable(ledger, encoded, project_identity=identity, expected_child_result=child)

        manifest = project / "project.json"
        manifest.write_bytes(manifest.read_bytes() + b"\n")
        manifest_rejected = _rejected(ledger, encoded, build_project_world_identity(project, scene), child)
        manifest.write_bytes(manifest.read_bytes().rstrip(b"\n"))

        scene.write_bytes(scene.read_bytes() + b"\n")
        scene_rejected = _rejected(ledger, encoded, build_project_world_identity(project, scene), child)
        scene.write_bytes(scene.read_bytes().rstrip(b"\n"))

        alternate = project / "scenes" / "challenge_scene_alias.pond"
        shutil.copyfile(scene, alternate)
        path_rejected = _rejected(ledger, encoded, build_project_world_identity(project, alternate), child)
        count_unchanged = inspect_e384_receipt_ledger(ledger, project_identity=identity)["consumed_count"] == 1
        result = {
            "status": "worldbridge_e394_identity_change_matrix",
            "contract_valid": manifest_rejected and scene_rejected and path_rejected and count_unchanged,
            "manifest_change_rejected": manifest_rejected,
            "scene_change_rejected": scene_rejected,
            "scene_path_change_rejected": path_rejected,
            "ledger_consumed_count_after_rejections": 1 if count_unchanged else 0,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
