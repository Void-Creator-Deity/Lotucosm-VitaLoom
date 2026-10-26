# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import unittest
from types import SimpleNamespace
from pathlib import Path

from builtin.entity_types.organism import Organism
from core.Lotucosm.runtime.world_bridge_mapping_audit import (
    build_worldbridge_mapping_audit,
)


ROOT = Path(__file__).resolve().parents[1]
FIELD_MAPPER = ROOT / (
    "FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/"
    "core/Lotucosm/runtime/world_bridge_field_mapper.py"
)


class _UpdateProbe:
    def __init__(self) -> None:
        self.update_calls = 0

    def update(self, delta_time: float) -> None:
        self.update_calls += 1


class WorldBridgeActiveVisibleAuthorityDecisionTests(unittest.TestCase):
    def test_inactive_ps_organism_obeys_entity_activity_invariant(self) -> None:
        organism = Organism("inactive-organism", (0.0, 0.0), energy=10.0)
        organism.active = False
        probe = _UpdateProbe()
        organism.components = {"probe": probe}

        organism.update(1.0)

        self.assertEqual(probe.update_calls, 0)
        self.assertEqual(organism.energy, 10.0)

    def test_ledger_records_active_mapping_and_visible_presentation_gap(self) -> None:
        audit = build_worldbridge_mapping_audit()

        self.assertEqual(audit["fields"]["active_visible_state"]["state"], "partial")
        self.assertNotIn("active_visible_state", audit["known_losses"])
        self.assertFalse(audit["lossless"])
        self.assertFalse(audit["default_ready"])

    def test_bridge_has_no_unreviewed_active_or_visible_attribute_route(self) -> None:
        tree = ast.parse(FIELD_MAPPER.read_text(encoding="utf-8"))
        mapper = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "WorldBridgeFieldMapper"
        )
        references: list[tuple[int, str]] = []
        for node in ast.walk(mapper):
            if isinstance(node, ast.Attribute) and node.attr in {"active", "visible"}:
                references.append((node.lineno, node.attr))
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"getattr", "hasattr", "setattr"}
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in {"active", "visible"}
            ):
                references.append((node.lineno, str(node.args[1].value)))
        self.assertTrue(references)
        self.assertTrue(all(item[1] == "active" for item in references))

    def test_bridge_syncs_active_without_claiming_visible_equivalence(self) -> None:
        from core.Lotucosm.runtime.world_bridge import (
            sync_organism_to_sr_display,
            sync_sr_entity_to_organism,
        )

        entity = SimpleNamespace(
            position=(0.0, 0.0), velocity=(0.0, 0.0), acceleration=(0.0, 0.0),
            energy=10.0, health=5.0, size=10.0, radius=10.0, active=False,
            visible=False,
        )
        organism = Organism("active-bridge", (0.0, 0.0), energy=10.0)
        sync_sr_entity_to_organism(entity, organism)
        self.assertFalse(organism.active)
        organism.active = True
        sync_organism_to_sr_display(organism, entity)
        self.assertTrue(entity.active)
        self.assertFalse(entity.visible)

    def test_inactive_sr_entity_skips_whole_script_tick(self) -> None:
        from core.Lotucosm.scene_runtime.tick_phases import run_script_tick_batch

        class _ScriptProbe:
            def __init__(self) -> None:
                self.calls = 0

            def step_scripts(self, ctx: object) -> None:
                self.calls += 1

        class _InactiveEntity:
            def __init__(self) -> None:
                self.id = "inactive-sr"
                self.active = False
                self.position = [0.0, 0.0]
                self.scripts = [_ScriptProbe()]

        inactive = _InactiveEntity()
        # A fully populated call with an unusable host: the active gate must
        # short-circuit before any host or ambient-field access.
        run_script_tick_batch(
            None,
            entities_batch=[inactive],
            all_e=[inactive],
            dt=0.016,
            spawn_list=[],
            remove_ids=[],
            damage_list=[],
            fx_list=[],
            niche_p=0.0,
            deriv=0.0,
            load_before=0.0,
            peer_scale=1.0,
            min_horizon=0.0,
            sr_caps=None,
            w=100,
            h=100,
            input_snap=None,
            use_prev_inbound=False,
        )

        self.assertEqual(inactive.scripts[0].calls, 0)


if __name__ == "__main__":
    unittest.main()
