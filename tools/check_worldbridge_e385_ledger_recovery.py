from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import E384LedgerError, consume_e382_receipt_durable, inspect_e384_receipt_ledger


def _encoded() -> bytes:
    child = {"status": "worldbridge_e381_tick_sequence", "contract_valid": True, "tick_count": 3, "fresh_sr_restore": True, "fresh_ps_restore": True, "canonical_parity": True, "component_digests": {field: "0" * 64 for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")}}
    return encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity="e385-recovery-project"))


def verify() -> dict[str, object]:
    encoded = _encoded()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e385-") as temporary:
        root = Path(temporary)
        metadata = root / ".vitaloom"
        metadata.mkdir()
        lock = metadata / "worldbridge_e382_receipt_ledger.lock"
        lock.write_text("crashed-owner", encoding="ascii")
        try:
            consume_e382_receipt_durable(root, encoded, project_identity="e385-recovery-project")
        except E384LedgerError as exc:
            stale_lock_rejected = exc.code == "ledger_interlock_held"
        else:
            stale_lock_rejected = False
        if lock.exists() is not True:
            raise AssertionError("stale lock was auto-cleaned")
        lock.unlink()
        (metadata / "worldbridge_e382_receipt_ledger.json").write_text(json.dumps({"schema_version": 999, "consumed": []}), encoding="utf-8")
        try:
            inspect_e384_receipt_ledger(root, project_identity="e385-recovery-project")
        except E384LedgerError as exc:
            schema_rejected = exc.code == "ledger_schema_invalid"
        else:
            schema_rejected = False
        (metadata / "worldbridge_e382_receipt_ledger.json").unlink()
        (metadata / "worldbridge_e382_receipt_ledger.lock").write_text("held", encoding="ascii")
        try:
            consume_e382_receipt_durable(root, b'{"status":', project_identity="e385-recovery-project")
        except ValueError:
            malformed_receipt_rejected = True
        else:
            malformed_receipt_rejected = False
        result = {
            "status": "worldbridge_e385_ledger_recovery",
            "contract_valid": stale_lock_rejected and schema_rejected and malformed_receipt_rejected,
            "stale_lock_rejected": stale_lock_rejected,
            "stale_lock_not_auto_cleaned": lock.exists(),
            "schema_migration_rejected": schema_rejected,
            "malformed_receipt_rejected": malformed_receipt_rejected,
            "crash_recovery_admitted": False,
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
