from __future__ import annotations

import json
import multiprocessing
import shutil
import subprocess
import sys
import tempfile
import time
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


def _consume(args: tuple[str, bytes, object, dict[str, object], str]) -> dict[str, object]:
    root, encoded, identity, child, label = args
    for attempt in range(20):
        try:
            value = consume_e382_receipt_durable(root, encoded, project_identity=identity, expected_child_result=child)
        except E384LedgerError as exc:
            if exc.code == "ledger_interlock_held" and attempt < 19:
                time.sleep(0.01)
                continue
            return {"label": label, "status": "rejected", "code": exc.code}
        except ValueError as exc:
            return {"label": label, "status": "rejected", "code": type(exc).__name__}
        return {"label": label, "status": value["status"], "receipt_digest": value["receipt_digest"]}
    return {"label": label, "status": "rejected", "code": "retry_exhausted"}


def verify() -> dict[str, object]:
    source = ROOT / "workspace" / "projects" / "samples" / "pvaec-细胞演化"
    child = _child()
    with tempfile.TemporaryDirectory(prefix="vitaloom-e399-") as temporary:
        project = Path(temporary) / "project"
        shutil.copytree(source, project)
        identity = build_project_world_identity(project, "scenes/challenge_scene.pond")
        child_two = dict(child)
        child_two["tick_count"] = int(child["tick_count"]) + 1
        first = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        second = encode_e382_receipt(build_e382_receipt(child_two, child_returncode=0, project_identity=identity))
        root = Path(temporary) / "ledger"
        root.mkdir()
        context = multiprocessing.get_context("spawn")
        with context.Pool(2) as pool:
            different = pool.map(_consume, [(str(root), first, identity, child, "first"), (str(root), second, identity, child_two, "second")])
        with context.Pool(2) as pool:
            duplicate = pool.map(_consume, [(str(root), first, identity, child, "duplicate-a"), (str(root), first, identity, child, "duplicate-b")])
        state = inspect_e384_receipt_ledger(root, project_identity=identity)
        different_successes = sum(item["status"] == "consumed" for item in different)
        duplicate_successes = sum(item["status"] == "consumed" for item in duplicate)
        result = {
            "status": "worldbridge_e399_concurrent_consumption",
            "contract_valid": different_successes == 2 and duplicate_successes == 0 and state["consumed_count"] == 2,
            "different_receipts_both_consumed": different_successes == 2,
            "different_results": different,
            "same_receipt_second_attempt_rejected": duplicate_successes == 0,
            "ledger_consumed_count": state["consumed_count"],
            "provenance_count": len(state["component_provenance"]),
            "replay_admitted": False,
            "default_ready": False,
            "lossless": False,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
