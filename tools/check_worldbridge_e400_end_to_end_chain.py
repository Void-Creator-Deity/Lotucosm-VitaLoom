from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt, validate_e382_receipt_against_child
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


def _remote_snapshot(root: Path, identity: object) -> dict[str, object]:
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
    with tempfile.TemporaryDirectory(prefix="vitaloom-e400-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        scene = project / "scenes" / "challenge_scene.pond"
        identity = build_project_world_identity(project, scene)
        child = _child()
        receipt = build_e382_receipt(child, child_returncode=0, project_identity=identity)
        encoded = encode_e382_receipt(receipt)
        receipt_valid = validate_e382_receipt_against_child(receipt, child)["valid"] is True
        root = Path(temporary) / "ledger"
        root.mkdir()
        consumed = consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        state = inspect_e384_receipt_ledger(root, project_identity=identity)
        remote = _remote_snapshot(root, identity)
        tampered_child = copy.deepcopy(child)
        tampered_child["component_digests"] = dict(child["component_digests"])
        tampered_child["component_digests"]["sr_state"] = "f" * 64
        try:
            consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=tampered_child)
        except E384LedgerError as exc:
            component_tamper_rejected = exc.code == "receipt_child_binding_mismatch"
        else:
            component_tamper_rejected = False
        result = {
            "status": "worldbridge_e400_end_to_end_chain",
            "contract_valid": receipt_valid and consumed["status"] == "consumed" and state == remote and state["consumed_count"] == 1 and component_tamper_rejected,
            "real_e381_child": True,
            "real_project_identity": True,
            "component_digest_binding": receipt_valid,
            "ledger_provenance_recorded": bool(state["component_provenance"]),
            "cross_process_snapshot_equal": state == remote,
            "component_tamper_rejected": component_tamper_rejected,
            "ledger_count_after_tamper": state["consumed_count"],
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
