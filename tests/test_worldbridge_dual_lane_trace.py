# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import unittest

from core.Lotucosm.runtime.world_bridge_dual_lane_trace import (
    build_worldbridge_dual_lane_trace,
    build_worldbridge_dual_lane_trace_contract,
    validate_worldbridge_dual_lane_trace,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


class WorldBridgeDualLaneTraceTests(unittest.TestCase):
    def test_trace_is_deterministic_copy_isolated_and_sorts_links(self) -> None:
        sr = {"sim_time": 1.25, "tick": 25, "population": 2, "nested": {"value": 1}}
        ps = {"tick": 3, "population": 2, "nested": {"value": 2}}
        links = [
            {"sr_entity_id": "sr:b", "ps_organism_id": "ps:b"},
            {"sr_entity_id": "sr:a", "ps_organism_id": "ps:a"},
        ]
        first = build_worldbridge_dual_lane_trace(sr, ps, entity_links=links)
        second = build_worldbridge_dual_lane_trace(sr, ps, entity_links=reversed(links))

        self.assertEqual(first, second)
        self.assertEqual(
            [item["sr_entity_id"] for item in first["entity_links"]],
            ["sr:a", "sr:b"],
        )
        self.assertEqual(first["lanes"]["sr"]["clock_domain"], "sr_scaled_scene_seconds")
        self.assertEqual(first["lanes"]["ps"]["clock_domain"], "ps_pond_unit_ticks")
        self.assertNotEqual(
            first["lanes"]["sr"]["clock_domain"],
            first["lanes"]["ps"]["clock_domain"],
        )
        self.assertTrue(validate_worldbridge_dual_lane_trace(first)["valid"])

        sr["nested"]["value"] = 99
        ps["nested"]["value"] = 99
        self.assertEqual(first["lanes"]["sr"]["checkpoint"]["nested"]["value"], 1)
        self.assertEqual(first["lanes"]["ps"]["checkpoint"]["nested"]["value"], 2)

    def test_trace_preserves_mapping_losses_and_non_admission_claims(self) -> None:
        trace = build_worldbridge_dual_lane_trace(
            {"sim_time": 0.05, "tick": 1},
            {"tick": 1},
        )
        self.assertEqual(
            trace["declared_mapping_losses"],
            [
                "hierarchy",
                "membrane_component_graph",
                "memory_genes",
                "render_identity",
                "scripts",
            ],
        )
        self.assertFalse(trace["shared_clock"])
        self.assertFalse(trace["lossless"])
        self.assertFalse(trace["replay_admitted"])
        self.assertFalse(trace["default_ready"])
        self.assertEqual(trace["determinism_scope"], "snapshot_packaging_only")
        self.assertEqual(
            trace["existing_runner_scope"],
            "ps_batch_vs_ps_unified_bridge_adapter_not_live_sr_ps_trace",
        )

    def test_validator_rejects_shared_clock_lossless_replay_and_identity_overclaims(self) -> None:
        trace = build_worldbridge_dual_lane_trace(
            {"sim_time": 0.1},
            {"tick": 1},
            entity_links=[{"sr_entity_id": "sr:1", "ps_organism_id": "ps:1"}],
        )
        cases = {
            "shared_clock_not_admitted": {"shared_clock": True},
            "lossless_mapping_not_admitted": {"lossless": True},
            "unified_replay_not_admitted": {"replay_admitted": True},
            "default_ready_not_admitted": {"default_ready": True},
            "cross_track_identity_not_admitted": {"identity_relation": "same_identity"},
        }
        for expected_error, changes in cases.items():
            with self.subTest(expected_error=expected_error):
                tampered = copy.deepcopy(trace)
                tampered.update(changes)
                result = validate_worldbridge_dual_lane_trace(tampered)
                self.assertFalse(result["valid"])
                self.assertIn(expected_error, result["errors"])
                self.assertIn("trace_digest_mismatch", result["errors"])

    def test_builder_rejects_duplicate_or_invalid_cross_lane_links(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate sr_entity_id"):
            build_worldbridge_dual_lane_trace(
                {"sim_time": 0.0},
                {"tick": 0},
                entity_links=[
                    {"sr_entity_id": "sr:1", "ps_organism_id": "ps:1"},
                    {"sr_entity_id": "sr:1", "ps_organism_id": "ps:2"},
                ],
            )
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            build_worldbridge_dual_lane_trace(
                {"sim_time": 0.0},
                {"tick": 0},
                entity_links=[{"sr_entity_id": "", "ps_organism_id": "ps:1"}],
            )

    def test_contract_is_nested_in_runtime_status_without_admission(self) -> None:
        contract = build_worldbridge_dual_lane_trace_contract()
        self.assertTrue(contract["contract_valid"])
        self.assertFalse(contract["tick_merge_admitted"])
        self.assertFalse(contract["replay_admitted"])
        self.assertFalse(contract["default_ready"])

        status = build_runtime_worldbridge_status()
        self.assertEqual(status["runtime_mode"], "dual")
        self.assertFalse(status["default_ready"])
        self.assertEqual(status["dual_lane_trace_contract"], contract)


if __name__ == "__main__":
    unittest.main()
