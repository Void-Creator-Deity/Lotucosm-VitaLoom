from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import E384LedgerError, consume_e382_receipt_durable, inspect_e384_receipt_ledger


def verify() -> dict[str, object]:
    child = {"status": "worldbridge_e381_tick_sequence", "contract_valid": True, "tick_count": 3, "fresh_sr_restore": True, "fresh_ps_restore": True, "canonical_parity": True, "component_digests": {field: "0" * 64 for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")}}
    identity = {"project_id": "e386-project", "project_manifest_digest": "manifest-a", "scene_digest": "scene-a"}
    encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
    with tempfile.TemporaryDirectory(prefix="vitaloom-e386-") as temporary:
        root = Path(temporary)
        try:
            consume_e382_receipt_durable(root, encoded, project_identity={**identity, "scene_digest": "scene-b"})
        except E384LedgerError as exc:
            receipt_identity_rejected = exc.code == "receipt_project_identity_mismatch"
        else:
            receipt_identity_rejected = False
        if (root / ".vitaloom" / "worldbridge_e382_receipt_ledger.json").exists():
            raise AssertionError("foreign receipt created a ledger")
        consume_e382_receipt_durable(root, encoded, project_identity=identity)
        ledger = inspect_e384_receipt_ledger(root, project_identity=identity)
        if ledger["consumed_count"] != 1:
            raise AssertionError(ledger)
        try:
            inspect_e384_receipt_ledger(root, project_identity={**identity, "scene_digest": "scene-b"})
        except E384LedgerError as exc:
            ledger_identity_rejected = exc.code == "ledger_project_identity_mismatch"
        else:
            ledger_identity_rejected = False
    result = {
        "status": "worldbridge_e386_project_identity",
        "contract_valid": receipt_identity_rejected and ledger_identity_rejected,
        "receipt_project_identity_rejected": receipt_identity_rejected,
        "ledger_project_identity_rejected": ledger_identity_rejected,
        "ledger_digest_bound": True,
        "schema_bound": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
