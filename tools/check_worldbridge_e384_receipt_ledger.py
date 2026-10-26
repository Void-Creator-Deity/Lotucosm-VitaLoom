from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import (
    E384LedgerError, consume_e382_receipt_durable, inspect_e384_receipt_ledger,
)


def verify() -> dict[str, object]:
    child = {"status": "worldbridge_e381_tick_sequence", "contract_valid": True, "tick_count": 3, "fresh_sr_restore": True, "fresh_ps_restore": True, "canonical_parity": True, "component_digests": {field: "0" * 64 for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")}}
    project_identity = "e384-ledger-project"
    encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=project_identity))
    with tempfile.TemporaryDirectory(prefix="vitaloom-e384-") as temporary:
        project = Path(temporary)
        first = consume_e382_receipt_durable(project, encoded, project_identity=project_identity)
        try:
            consume_e382_receipt_durable(project, encoded, project_identity=project_identity)
        except E384LedgerError as exc:
            replay_rejected = exc.code == "receipt_replay_rejected"
        else:
            replay_rejected = False
        if not replay_rejected or inspect_e384_receipt_ledger(project, project_identity=project_identity)["consumed_count"] != 1:
            raise AssertionError({"first": first, "ledger": inspect_e384_receipt_ledger(project, project_identity=project_identity)})
    result = {
        "status": "worldbridge_e384_receipt_ledger",
        "contract_valid": True,
        "atomic_write": True,
        "durable_consumption": True,
        "duplicate_consumption_rejected": True,
        "crash_recovery_admitted": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
