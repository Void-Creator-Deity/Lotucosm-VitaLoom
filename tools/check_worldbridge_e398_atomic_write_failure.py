from __future__ import annotations

import json
import copy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime import world_bridge_e384_receipt_ledger as ledger_module
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
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e398-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        identity = build_project_world_identity(project, "scenes/challenge_scene.pond")
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        root = Path(temporary) / "ledger"
        root.mkdir()
        first = consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        child_two = copy.deepcopy(child)
        child_two["tick_count"] = 4
        encoded_two = encode_e382_receipt(build_e382_receipt(child_two, child_returncode=0, project_identity=identity))
        ledger_path = root / ".vitaloom" / "worldbridge_e382_receipt_ledger.json"
        before = ledger_path.read_bytes()
        failures: dict[str, bool] = {}
        for name, target in (("replace", "replace"), ("fsync", "fsync")):
            calls = {"count": 0}
            def replacement(*args):
                calls["count"] += 1
                if name == "fsync" and calls["count"] == 1:
                    return None
                raise OSError(f"injected {name} failure")
            with patch.object(ledger_module.os, target, side_effect=replacement):
                try:
                    consume_e382_receipt_durable(root, encoded_two, project_identity=identity, expected_child_result=child_two)
                except E384LedgerError as exc:
                    failures[name] = exc.code == "ledger_write_failed"
                else:
                    failures[name] = False
            failures[name] = failures[name] and ledger_path.read_bytes() == before and not (root / ".vitaloom" / "worldbridge_e382_receipt_ledger.lock").exists()
        state = inspect_e384_receipt_ledger(root, project_identity=identity)
        temporary_files = list((root / ".vitaloom").glob(".*.tmp"))
        result = {
            "status": "worldbridge_e398_atomic_write_failure",
            "contract_valid": all(failures.values()) and state["consumed_count"] == 1 and not temporary_files and first["status"] == "consumed",
            "replace_failure_rejected": failures["replace"],
            "fsync_failure_rejected": failures["fsync"],
            "ledger_preserved": state["consumed_count"] == 1,
            "temporary_files_cleaned": not temporary_files,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
