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
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import E384LedgerError, consume_e382_receipt_durable, inspect_e384_receipt_ledger


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


def _cross_process_inspect(root: Path, identity: str) -> dict[str, object]:
    code = """
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'tools'))
from _runtime_bootstrap import install_runtime_paths
install_runtime_paths(Path(sys.argv[1]))
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import inspect_e384_receipt_ledger
print(json.dumps(inspect_e384_receipt_ledger(Path(sys.argv[2]), project_identity=sys.argv[3]), sort_keys=True))
"""
    completed = subprocess.run([sys.executable, "-B", "-c", code, str(ROOT), str(root), identity], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(completed.stdout)


def verify() -> dict[str, object]:
    child = _child()
    identity = "e392-project"
    encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
    with tempfile.TemporaryDirectory(prefix="vitaloom-e392-") as temporary:
        root = Path(temporary)
        consumed = consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        local = inspect_e384_receipt_ledger(root, project_identity=identity)
        remote = _cross_process_inspect(root, identity)
        cross_process_equal = local == remote and local["ledger_digest"] == consumed["ledger_digest"]
        ledger_path = root / ".vitaloom" / "worldbridge_e382_receipt_ledger.json"
        tampered = json.loads(ledger_path.read_text(encoding="utf-8"))
        tampered["component_provenance"][consumed["receipt_digest"]]["component_digests"]["sr_state"] = "f" * 64
        ledger_path.write_text(json.dumps(tampered, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        try:
            inspect_e384_receipt_ledger(root, project_identity=identity)
        except E384LedgerError as exc:
            tampered_rejected = exc.code == "ledger_digest_mismatch"
        else:
            tampered_rejected = False
        result = {
            "status": "worldbridge_e392_ledger_provenance",
            "contract_valid": cross_process_equal and tampered_rejected,
            "component_provenance_recorded": bool(local["component_provenance"]),
            "cross_process_reread_equal": cross_process_equal,
            "tampered_ledger_rejected": tampered_rejected,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
