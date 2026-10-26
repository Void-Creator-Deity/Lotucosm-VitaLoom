from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import (
    build_e382_receipt, validate_e382_receipt_against_child,
)
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import build_project_world_identity


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
    child = _child()
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    identity = build_project_world_identity(project, "scenes/challenge_scene.pond")
    receipt = build_e382_receipt(child, child_returncode=0, project_identity=identity)
    if validate_e382_receipt_against_child(receipt, child)["valid"] is not True:
        raise AssertionError("real child receipt did not validate")
    tampered = dict(child)
    tampered["tick_count"] = 4
    tamper_rejected = validate_e382_receipt_against_child(receipt, tampered)["valid"] is False
    result = {
        "status": "worldbridge_e389_checkpoint_digest",
        "contract_valid": tamper_rejected,
        "real_e381_child": True,
        "complete_child_result_digest_bound": True,
        "tampered_checkpoint_rejected": tamper_rejected,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
