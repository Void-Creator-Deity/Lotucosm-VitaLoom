from __future__ import annotations

import copy
import json
import os
import random
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from _runtime_bootstrap import install_runtime_paths
except ModuleNotFoundError:  # Imported as tools.* by the focused test suite.
    from tools._runtime_bootstrap import install_runtime_paths


install_runtime_paths(Path(__file__).resolve().parents[1])

from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
    WorldBridgeLiveCheckpointError,
)
from core.Lotucosm.runtime import world_bridge_live_checkpoint_adapter as adapter_module
from core.VitaLoom.viewports.game_viewport import GameViewport
from core.Lotucosm.runtime.world_bridge_e366_live_checkpoint_admission import (
    build_worldbridge_e366_live_checkpoint_admission_contract,
)
from core.Lotucosm.runtime.world_bridge_e367_live_viewport_witness import (
    build_worldbridge_e367_live_viewport_witness_contract,
)
from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
    create_worldbridge_deterministic_randomness_context,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


_APP: QApplication | None = None


def _application() -> QApplication:
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def _prepare_viewport() -> GameViewport:
    viewport = GameViewport()
    viewport._using_scene_runtime = True
    viewport._sr_runtime_epoch = "e367-cli"
    viewport._sr_runtime_scene_path = "e367-cli.pond"
    viewport._unified_pond_mode = True
    viewport.scene_runtime_entities = []
    viewport.set_worldbridge_opt_in_deterministic_randomness_context(
        create_worldbridge_deterministic_randomness_context("e367-cli-context", "e367-fixed-seed")
    )
    viewport._unified_pond = viewport._ensure_unified_pond()
    return viewport


def build_e367_witness() -> dict[str, object]:
    import numpy as np

    python_state = random.getstate()
    numpy_state = np.random.get_state()
    random.seed("e367-process-seed")
    np.random.seed(367)
    try:
        return _build_e367_witness()
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)


def _build_e367_witness() -> dict[str, object]:
    app = _application()
    viewport = _prepare_viewport()
    checkpoint = GameViewport.capture_worldbridge_live_checkpoint(viewport, "e367-cli")
    before = copy.deepcopy(checkpoint)
    real_factory = adapter_module.create_game_viewport_live_checkpoint_adapters

    def fail_ps(_state: object) -> None:
        raise RuntimeError("e367 injected PS restore failure")

    adapter_module.create_game_viewport_live_checkpoint_adapters = lambda _viewport: replace(
        real_factory(_viewport), restore_ps=fail_ps
    )
    try:
        try:
            GameViewport.restore_worldbridge_live_checkpoint(viewport, checkpoint)
        except WorldBridgeLiveCheckpointError as error:
            report = error.report
        else:
            raise AssertionError("controlled PS restore failure was not observed")
    finally:
        adapter_module.create_game_viewport_live_checkpoint_adapters = real_factory

    after = GameViewport.capture_worldbridge_live_checkpoint(viewport, "e367-after")
    before_stable = copy.deepcopy(before)
    after_stable = copy.deepcopy(after)
    # Owner-gate hold/acquisition counters describe this process-local capture
    # attempt, not portable session state. E551 validates the locked boundary
    # separately while E508/E556 exclude these counters from parity digests.
    before_stable["lifecycle"].pop("owner_gate_snapshot", None)
    after_stable["lifecycle"].pop("owner_gate_snapshot", None)
    preserved = all(before_stable[field] == after_stable[field] for field in (
        "sr_state", "ps_state", "bridge_identity_links", "input_state",
        "randomness_state", "lifecycle",
    ))
    witness = GameViewport.build_worldbridge_live_checkpoint_admission_witness(
        viewport,
        after,
        rollback_evidence={
            "atomic": report.get("compensation_complete") is True,
            "target_preserved": preserved,
        },
    )
    aggregate = build_worldbridge_e366_live_checkpoint_admission_contract(witness)
    factory_restored = (
        adapter_module.create_game_viewport_live_checkpoint_adapters is real_factory
    )
    viewport.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    cleanup = {
        "factory_restored": factory_restored,
        "viewport_deleted": bool(sip.isdeleted(viewport)),
    }
    runtime_witness = build_worldbridge_e367_live_viewport_witness_contract(
        witness, cleanup
    )
    runtime_status = build_runtime_worldbridge_status(
        live_checkpoint_witness=witness,
        live_checkpoint_cleanup=cleanup,
    )
    return {
        "status": "worldbridge_e367_live_viewport_witness",
        "contract_valid": aggregate["contract_valid"],
        "checkpoint_identity": witness["checkpoint_identity"],
        "witness": witness,
        "aggregate": aggregate,
        "cleanup": cleanup,
        "runtime_witness": runtime_witness,
        "runtime_status_e367": runtime_status["e367_live_viewport_witness"],
        "failure_report": {
            "phase": report.get("phase"),
            "compensation_complete": report.get("compensation_complete"),
            "target_preserved": preserved,
        },
    }


if __name__ == "__main__":
    result = build_e367_witness()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    checks = {
        "contract_valid": result["contract_valid"],
        "aggregate_opt_in_live_adapter_admitted": result["aggregate"][
            "opt_in_live_adapter_admitted"
        ],
        "runtime_witness_contract_valid": result["runtime_witness"]["contract_valid"],
        "runtime_status_cleanup_complete": result["runtime_status_e367"][
            "cleanup_complete"
        ],
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        detail = {
            "failed": failed,
            "witness_evidence": result["witness"]["evidence"],
            "cleanup": result["cleanup"],
            "failure_report": result["failure_report"],
            "runtime_status_cleanup": result["runtime_status_e367"]["cleanup"],
        }
        print(
            "::error title=WorldBridge E367 witness failed::"
            + json.dumps(detail, ensure_ascii=True, sort_keys=True)
        )
        raise SystemExit(1)
    raise SystemExit(0)
