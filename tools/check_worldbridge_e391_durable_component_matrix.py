from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import (
    build_e382_receipt,
    canonical_bytes,
    digest,
    encode_e382_receipt,
)
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import (
    E384LedgerError,
    consume_e382_receipt_durable,
    inspect_e384_receipt_ledger,
)

COMPONENTS = ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")


def _child() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_e381_tick_sequence.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
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
    receipt = build_e382_receipt(child, child_returncode=0, project_identity="e391-project")
    encoded = encode_e382_receipt(receipt)
    with tempfile.TemporaryDirectory(prefix="vitaloom-e391-") as temporary:
        root = Path(temporary)
        baseline = consume_e382_receipt_durable(
            root, encoded, project_identity="e391-project", expected_child_result=child
        )
        if baseline["status"] != "consumed":
            raise AssertionError("baseline receipt was not consumed")
        rejected: dict[str, bool] = {}
        for component in COMPONENTS:
            tampered_child = dict(child)
            tampered_child["component_digests"] = dict(child["component_digests"])
            tampered_child["component_digests"][component] = "f" * 64
            try:
                consume_e382_receipt_durable(
                    root, encoded, project_identity="e391-project", expected_child_result=tampered_child
                )
            except E384LedgerError as exc:
                rejected[component] = exc.code == "receipt_child_binding_mismatch"
            else:
                rejected[component] = False
        incomplete = dict(receipt)
        incomplete["component_digests"] = dict(receipt["component_digests"])
        del incomplete["component_digests"]["lifecycle"]
        incomplete["receipt_digest"] = digest({key: value for key, value in incomplete.items() if key != "receipt_digest"})
        try:
            consume_e382_receipt_durable(
                root, canonical_bytes(incomplete), project_identity="e391-project", expected_child_result=child
            )
        except (E384LedgerError, ValueError):
            incomplete_rejected = True
        else:
            incomplete_rejected = False
        ledger = inspect_e384_receipt_ledger(root, project_identity="e391-project")
        result = {
            "status": "worldbridge_e391_durable_component_matrix",
            "contract_valid": all(rejected.values()) and incomplete_rejected and ledger["consumed_count"] == 1,
            "baseline_consumed": True,
            "component_rejections": rejected,
            "incomplete_component_rejected": incomplete_rejected,
            "ledger_consumed_count_after_rejections": ledger["consumed_count"],
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
