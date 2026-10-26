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


def _reject(root: Path, identity: object, code: str) -> bool:
    try:
        inspect_e384_receipt_ledger(root, project_identity=identity)
    except E384LedgerError as exc:
        return exc.code == code
    return False


def verify() -> dict[str, object]:
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e396-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        identity = build_project_world_identity(project, "scenes/challenge_scene.pond")
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        root = Path(temporary) / "ledger"
        root.mkdir()
        consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        path = root / ".vitaloom" / "worldbridge_e382_receipt_ledger.json"
        valid = json.loads(path.read_text(encoding="utf-8"))
        valid["unknown_top_level"] = True
        path.write_text(json.dumps(valid, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        unknown_top_level_rejected = _reject(root, identity, "ledger_schema_invalid")
        valid.pop("unknown_top_level")
        valid["schema_version"] = 999
        path.write_text(json.dumps(valid, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        old_version_rejected = _reject(root, identity, "ledger_schema_invalid")
        result = {
            "status": "worldbridge_e396_ledger_schema_boundary",
            "contract_valid": unknown_top_level_rejected and old_version_rejected,
            "unknown_top_level_rejected": unknown_top_level_rejected,
            "old_schema_version_rejected": old_version_rejected,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
