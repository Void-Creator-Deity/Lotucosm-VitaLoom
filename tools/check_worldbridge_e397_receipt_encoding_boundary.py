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

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, canonical_bytes, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import E384LedgerError, build_project_world_identity, consume_e382_receipt_durable


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
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e397-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        identity = build_project_world_identity(project, "scenes/challenge_scene.pond")
        receipt = build_e382_receipt(child, child_returncode=0, project_identity=identity)
        root = Path(temporary) / "ledger"
        root.mkdir()
        cases: dict[str, bytes] = {}
        unknown = dict(receipt)
        unknown["unknown_receipt_field"] = True
        unknown["receipt_digest"] = __import__("core.Lotucosm.runtime.world_bridge_e382_restore_receipt", fromlist=["digest"]).digest({key: value for key, value in unknown.items() if key != "receipt_digest"})
        cases["unknown_field"] = canonical_bytes(unknown)
        cases["duplicate_key"] = canonical_bytes(receipt).replace(b'"status":', b'"status":"tampered","status":', 1)
        cases["noncanonical"] = json.dumps(receipt, ensure_ascii=False).encode("utf-8")
        rejected: dict[str, bool] = {}
        for name, encoded in cases.items():
            try:
                consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
            except (ValueError, E384LedgerError):
                rejected[name] = True
            else:
                rejected[name] = False
        result = {
            "status": "worldbridge_e397_receipt_encoding_boundary",
            "contract_valid": all(rejected.values()),
            "rejections": rejected,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
