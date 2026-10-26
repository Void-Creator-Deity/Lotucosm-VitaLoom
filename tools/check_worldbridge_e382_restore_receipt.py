from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"))

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import (
    build_e382_receipt, consume_e382_receipt, encode_e382_receipt,
    run_compensated_restore, validate_e382_receipt,
)
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import (
    E384LedgerError, consume_e382_receipt_durable,
)


def _child_result() -> tuple[dict, int]:
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
            return value, completed.returncode
    raise AssertionError({"child_returncode": completed.returncode, "stdout_tail": completed.stdout[-2000:], "stderr_tail": completed.stderr[-2000:]})


def verify() -> dict[str, object]:
    child, returncode = _child_result()
    project_identity = "e382-cross-process-project"
    receipt = build_e382_receipt(child, child_returncode=returncode, project_identity=project_identity)
    validation = validate_e382_receipt(receipt)
    if validation["valid"] is not True:
        raise AssertionError(validation)
    encoded = encode_e382_receipt(receipt)
    consumed: set[str] = set()
    consume_e382_receipt(encoded, consumed)
    try:
        consume_e382_receipt(encoded, consumed)
    except ValueError:
        replay_rejected = True
    else:
        replay_rejected = False
    if not replay_rejected:
        raise AssertionError("receipt replay accepted")
    with tempfile.TemporaryDirectory(prefix="vitaloom-e384-") as temporary:
        project = Path(temporary)
        child_code = (
            "import os, pathlib, sys, time; "
            "p=pathlib.Path(sys.argv[1]) / '.vitaloom'; p.mkdir(parents=True); "
            "f=os.open(str(p / 'worldbridge_e382_receipt_ledger.lock'), os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600); "
            "os.write(f, str(os.getpid()).encode()); os.close(f); "
            "pathlib.Path(sys.argv[1], 'ready').write_text('1'); time.sleep(1.5)"
        )
        holder = subprocess.Popen([sys.executable, "-c", child_code, str(project)], cwd=ROOT)
        ready = project / "ready"
        deadline = time.monotonic() + 5.0
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not ready.exists():
            holder.kill()
            raise AssertionError("E384 lock holder did not start")
        try:
            try:
                consume_e382_receipt_durable(project, encoded, project_identity=project_identity)
            except E384LedgerError as exc:
                cross_process_lock_rejected = exc.code == "ledger_interlock_held"
            else:
                cross_process_lock_rejected = False
        finally:
            holder.wait(timeout=5)
        if not cross_process_lock_rejected:
            raise AssertionError("cross-process ledger lock was not enforced")
    target = {"sr": {"tick": 3}, "ps": {"time": 3}, "bridge": {"identity": "e382"}}
    before = dict(target)

    def restore(value: dict) -> None:
        value["ps"] = {"time": 999}
        raise RuntimeError("injected_restore_failure")

    def rollback(value: dict) -> None:
        value.clear()
        value.update(before)

    compensation = run_compensated_restore(target, restore, rollback)
    if compensation["failure_abort_observed"] is not True or compensation["compensation_preserved_target"] is not True:
        raise AssertionError(compensation)
    tampered = dict(receipt)
    tampered["tick_count"] = 99
    if validate_e382_receipt(tampered)["valid"] is not False:
        raise AssertionError("tampered receipt accepted")
    result = {
        "status": "worldbridge_e382_restore_receipt",
        "contract_valid": True,
        "child_returncode": returncode,
        "receipt_schema_valid": True,
        "fresh_sequence_restore": True,
        "failure_abort_observed": True,
        "compensation_preserved_target": True,
        "cross_process_receipt_revalidated": True,
        "canonical_bytes_roundtrip": True,
        "duplicate_consumption_rejected": True,
        "cross_process_lock_rejected": True,
        "tamper_rejected": True,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
