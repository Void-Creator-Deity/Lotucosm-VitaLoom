# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

from core.Lotucosm.runtime import world_bridge_mapping_audit
from core.Lotucosm.runtime.world_bridge_ledger_closure import (
    build_worldbridge_ledger_closure,
)
from core.VitaLoom.simulation.runtime_worldbridge_status import (
    build_runtime_worldbridge_status,
)


class WorldBridgeMappingLedgerClosureTests(unittest.TestCase):
    def test_closure_has_all_reviewed_fields_and_required_decision_payloads(self) -> None:
        closure = build_worldbridge_ledger_closure()
        self.assertEqual(closure["field_count"], 15)
        self.assertEqual(closure["expected_field_count"], 15)
        self.assertTrue(closure["fields_consistent"])
        self.assertTrue(closure["mutation_owner_contract_valid"])
        self.assertTrue(closure["decision_payloads_present"])
        self.assertTrue(closure["ledger_closed_for_review"])
        self.assertEqual(
            closure["known_losses"],
            [
                "hierarchy",
                "membrane_component_graph",
                "render_identity",
                "scripts",
            ],
        )

    def test_closure_stays_open_when_owner_contract_metadata_is_tampered(self) -> None:
        original_builder = world_bridge_mapping_audit.build_worldbridge_mutation_owner_contract

        def build_tampered_contract():
            contract = original_builder()
            contract["fields"]["position"]["mutation_api"] = "unverified_writer"
            return contract

        world_bridge_mapping_audit.build_worldbridge_mutation_owner_contract = build_tampered_contract
        try:
            closure = build_worldbridge_ledger_closure()
        finally:
            world_bridge_mapping_audit.build_worldbridge_mutation_owner_contract = original_builder

        self.assertFalse(closure["mutation_owner_contract_valid"])
        self.assertFalse(closure["fields_consistent"])
        self.assertFalse(closure["ledger_closed_for_review"])
        self.assertFalse(closure["no_admission_claim"])

    def test_closure_cannot_admit_unified_runtime_or_lossless_replay(self) -> None:
        closure = build_worldbridge_ledger_closure()
        self.assertTrue(closure["no_admission_claim"])
        self.assertFalse(closure["unified_runtime_admitted"])
        self.assertFalse(closure["default_ready"])
        self.assertIn("full_unified_runtime_replay", closure["do_not_claim"])

        status = build_runtime_worldbridge_status()
        self.assertEqual(status["runtime_mode"], "dual")
        self.assertFalse(status["default_ready"])
        self.assertIn("full_unified_runtime_replay", status["do_not_claim"])


if __name__ == "__main__":
    unittest.main()

