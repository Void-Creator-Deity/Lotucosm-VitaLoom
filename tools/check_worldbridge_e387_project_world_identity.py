from __future__ import annotations

import json
import tempfile
from pathlib import Path

from _runtime_bootstrap import install_runtime_paths

ROOT = Path(__file__).resolve().parents[1]
install_runtime_paths(ROOT)

from core.Lotucosm.runtime.world_bridge_e382_restore_receipt import build_e382_receipt, encode_e382_receipt
from core.Lotucosm.runtime.world_bridge_e384_receipt_ledger import (
    E384LedgerError, build_project_world_identity, consume_e382_receipt_durable,
)


def verify() -> dict[str, object]:
    child = {"status": "worldbridge_e381_tick_sequence", "contract_valid": True, "tick_count": 3, "fresh_sr_restore": True, "fresh_ps_restore": True, "canonical_parity": True, "component_digests": {field: "0" * 64 for field in ("sr_state", "ps_state", "randomness_state", "input_state", "lifecycle")}}
    with tempfile.TemporaryDirectory(prefix="vitaloom-e387-") as temporary:
        root = Path(temporary) / "project"
        (root / "scenes").mkdir(parents=True)
        (root / "project.json").write_text('{"name":"e387"}', encoding="utf-8")
        scene = root / "scenes" / "main.pond"
        scene.write_bytes(b"scene-a")
        identity = build_project_world_identity(root, "scenes/main.pond")
        encoded = encode_e382_receipt(build_e382_receipt(child, child_returncode=0, project_identity=identity))
        consumed = consume_e382_receipt_durable(root, encoded, project_identity=identity)
        if consumed["status"] != "consumed":
            raise AssertionError(consumed)
        scene.write_bytes(b"scene-b")
        changed_identity = build_project_world_identity(root, "scenes/main.pond")
        try:
            consume_e382_receipt_durable(root, encoded, project_identity=changed_identity)
        except E384LedgerError as exc:
            changed_scene_rejected = exc.code == "receipt_project_identity_mismatch"
        else:
            changed_scene_rejected = False
    result = {
        "status": "worldbridge_e387_project_world_identity",
        "contract_valid": changed_scene_rejected,
        "manifest_scene_identity_derived": True,
        "changed_scene_rejected": changed_scene_rejected,
        "arbitrary_identity_only": False,
        "replay_admitted": False,
        "default_ready": False,
        "lossless": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if verify()["contract_valid"] else 1)
