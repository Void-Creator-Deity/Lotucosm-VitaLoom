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


def _remote_inspect(root: Path, identity: object) -> dict[str, object]:
    code = """
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'tools'))
from _runtime_bootstrap import install_runtime_paths
install_runtime_paths(Path(sys.argv[1]))
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import inspect_e384_receipt_ledger
print(json.dumps(inspect_e384_receipt_ledger(Path(sys.argv[2]), project_identity=json.loads(sys.argv[3])), sort_keys=True))
"""
    completed = subprocess.run([sys.executable, "-B", "-c", code, str(ROOT), str(root), json.dumps(identity, ensure_ascii=False)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(completed.stdout)


def verify() -> dict[str, object]:
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e395-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        scene = project / "scenes" / "challenge_scene.pond"
        normalized = build_project_world_identity(project, scene)
        equivalent = build_project_world_identity(project, project / "scenes" / ".." / "scenes" / "challenge_scene.pond")
        path_normalization_stable = normalized == equivalent
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=normalized))
        ledger = Path(temporary) / "ledger"
        ledger.mkdir()
        first = consume_e382_receipt_durable(ledger, encoded, project_identity=equivalent, expected_child_result=child)
        local = inspect_e384_receipt_ledger(ledger, project_identity=normalized)
        remote = _remote_inspect(ledger, normalized)
        try:
            consume_e382_receipt_durable(ledger, encoded, project_identity=normalized, expected_child_result=child)
        except E384LedgerError as exc:
            duplicate_rejected = exc.code == "receipt_replay_rejected"
        else:
            duplicate_rejected = False
        result = {
            "status": "worldbridge_e395_identity_cross_process",
            "contract_valid": path_normalization_stable and local == remote and first["ledger_digest"] == local["ledger_digest"] and duplicate_rejected,
            "path_normalization_stable": path_normalization_stable,
            "cross_process_snapshot_equal": local == remote,
            "duplicate_consumption_rejected": duplicate_rejected,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
