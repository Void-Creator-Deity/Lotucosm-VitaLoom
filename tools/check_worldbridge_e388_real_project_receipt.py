from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import build_project_world_identity, consume_e382_receipt_durable


def _run_real_e381() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e381_tick_sequence.py"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("status") == "worldbridge_e381_tick_sequence":
            if completed.returncode != 0:
                raise AssertionError("real E381 child failed")
            return value
    raise AssertionError(completed.stderr[-2000:])


def verify() -> dict[str, object]:
    project = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    scene = project / "scenes" / "challenge_scene.pond"
    child = _run_real_e381()
    identity = build_project_world_identity(project, scene)
    encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
    with tempfile.TemporaryDirectory(prefix="vitaloom-e388-ledger-") as temporary:
        ledger_project = Path(temporary)
        consumed = consume_e382_receipt_durable(ledger_project, encoded, project_identity=identity)
    result = {
        "status": "worldbridge_e388_real_project_receipt",
        "contract_valid": consumed["status"] == "consumed",
        "real_e381_child": True,
        "real_project_manifest_scene_identity": True,
        "receipt_bound_to_real_project": True,
        "formal_ledger_write_isolated": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
