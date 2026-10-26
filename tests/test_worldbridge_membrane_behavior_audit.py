# -*- coding: utf-8 -*-
"""E538: PS membrane behavior stays lane-local under the WorldBridge."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_membrane_behavior_audit import (
    build_worldbridge_membrane_behavior_audit,
    scan_membrane_behavior_calls,
)
from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)
from core.Lotucosm.runtime.world_bridge_component_projection import (
    project_worldbridge_component,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime"
MEMBRANE = RUNTIME / "builtin/components/membrane.py"


class _FakeMembrane:
    component_id = "membrane_probe"
    component_type = "membrane"
    location = "external"
    acquired = False
    congenital = True
    attach_point = "cell_wall"
    radius = 42.0
    ingest_threshold = 0.35
    efficiency = 1.25

    def get_inspectable_properties(self) -> dict:
        return {
            "radius": {"value": self.radius, "type": float, "attributes": {}},
            "ingest_threshold": {"value": self.ingest_threshold, "type": float, "attributes": {}},
            "efficiency": {"value": self.efficiency, "type": float, "attributes": {}},
        }

    def auto_ingest(self, *_args, **_kwargs) -> None:
        raise AssertionError("auto_ingest is a live PS behavior and must not be projected")

    def is_inside(self, *_args, **_kwargs) -> None:
        raise AssertionError("is_inside is a live PS behavior and must not be projected")


class WorldBridgeMembraneBehaviorAuditTests(unittest.TestCase):
    def test_audit_binds_declared_fields_to_the_real_ps_producer(self) -> None:
        audit = build_worldbridge_membrane_behavior_audit()
        decision = build_worldbridge_component_decision()
        membrane_kind = decision["component_kinds"]["Membrane"]

        self.assertEqual(audit["status"], "worldbridge_membrane_behavior_audit")
        self.assertTrue(audit["read_only"])
        self.assertTrue(audit["audit_only"])
        self.assertEqual(audit["mapping_state"], "decision_only")

        self.assertTrue(audit["producer"]["membrane_class_importable"])
        self.assertEqual(audit["producer"]["error"], None)
        self.assertEqual(
            audit["declared_safe_projection_fields"],
            list(membrane_kind["safe_projection_fields"]),
        )
        self.assertEqual(
            audit["declared_forbidden_behavior"],
            list(membrane_kind["forbidden_behavior"]),
        )
        self.assertEqual(audit["missing_projection_fields"], [])
        self.assertEqual(audit["missing_forbidden_behavior"], [])
        self.assertTrue(audit["producer_projection_bound"])
        # Declared projection fields must come from the real registered properties.
        self.assertTrue(
            set(audit["declared_safe_projection_fields"])
            <= set(audit["producer"]["registered_projection_fields"])
        )
        for name in audit["declared_forbidden_behavior"]:
            self.assertIn(name, audit["producer"]["behavior_methods"])

    def test_behavior_is_proven_live_in_ps_lane_and_absent_from_cross_lane_surfaces(self) -> None:
        audit = build_worldbridge_membrane_behavior_audit()

        # Non-vacuous: the PS lane really calls the behavior, so the isolation
        # claim is not satisfied by an empty scan.
        self.assertGreater(audit["ps_lane_usage"]["scanned_files"], 0)
        self.assertTrue(audit["ps_lane_usage"]["calls"])
        self.assertTrue(
            any(call["file"].endswith("builtin/entity_types/organism.py") for call in audit["ps_lane_usage"]["calls"])
        )

        self.assertGreater(audit["cross_lane_scan"]["scanned_files"], 0)
        self.assertTrue(audit["cross_lane_scan"]["scan_roots"])
        self.assertEqual(audit["cross_lane_scan"]["calls"], [])
        self.assertTrue(audit["behavior_is_lane_local"])
        self.assertTrue(audit["cross_lane_behavior_isolated"])

    def test_cross_lane_behavior_authority_stays_unadmitted(self) -> None:
        audit = build_worldbridge_membrane_behavior_audit()
        self.assertFalse(audit["cross_lane_behavior_admitted"])
        self.assertFalse(audit["lossless"])
        self.assertFalse(audit["replay_admitted"])
        self.assertFalse(audit["default_ready"])
        self.assertIn("cross_lane_behavior_authority", audit["blockers"])
        self.assertIn("worldbridge_live_membrane_mapping", audit["do_not_claim"])
        json.dumps(audit, ensure_ascii=False)

    def test_behavior_scanner_is_not_vacuous(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            planted = Path(tmp) / "planted_cross_lane.py"
            planted.write_text(
                "def leak(membrane):\n    return membrane.auto_ingest(None)\n",
                encoding="utf-8",
            )
            scan = scan_membrane_behavior_calls((Path(tmp),))
            self.assertEqual(scan["scanned_files"], 1)
            self.assertEqual(len(scan["calls"]), 1)
            self.assertEqual(scan["calls"][0]["call"], "auto_ingest")

    def test_projection_never_calls_live_membrane_behavior(self) -> None:
        projected = project_worldbridge_component(_FakeMembrane())
        self.assertFalse(projected["maps_live_components"])
        self.assertEqual(projected["component_fields"]["radius"], 42.0)
        self.assertEqual(projected["component_fields"]["ingest_threshold"], 0.35)
        self.assertEqual(projected["component_fields"]["efficiency"], 1.25)

    def test_runtime_status_exposes_membrane_behavior_audit(self) -> None:
        from core.VitaLoom.simulation.runtime_worldbridge_status import (
            build_runtime_worldbridge_status,
        )

        status = build_runtime_worldbridge_status()
        self.assertEqual(
            status["membrane_behavior_audit"],
            build_worldbridge_membrane_behavior_audit(),
        )


if __name__ == "__main__":
    unittest.main()