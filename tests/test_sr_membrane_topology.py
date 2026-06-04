# -*- coding: utf-8 -*-
"""
SR 膜拓扑单测：附着、expand/dedupe、inherit→mutate 顺序、无中枢营养 GPS。

契约与实现注释见 core/Lotucosm/sr_membrane_topology.py；
宿主 tick 顺序见 tests/test_game_viewport_scene_reload.py。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""
from __future__ import annotations

import importlib.util
import math
import os
import unittest
from pathlib import Path
from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication

from core.Lotucosm.scene_runtime_context import SceneRuntimeTickContext
from core.Lotucosm.sr_membrane_topology import (
    aggregate_channel_signals,
    apply_explicit_signal_edges,
    build_membrane_attachments,
    dedupe_signal_edges,
    expand_signal_edges,
    inherit_chemo_edge_weights,
    mutate_signal_edges,
    resolve_membrane_template,
)

_ROOT = Path(__file__).resolve().parents[1]
_EVO = _ROOT / "projects" / "pvaec-细胞演化" / "scripts" / "evo_central_brain_pvaec.py"


def _load_evo():
    spec = importlib.util.spec_from_file_location("evo_brain", _EVO)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.EvoCentralBrainPvaec


class MembraneAttachTests(unittest.TestCase):
    def test_build_attachments_offsets(self) -> None:
        org = SimpleNamespace(
            id="hub",
            entity_type="organism",
            position=[100.0, 100.0],
            velocity=[0.0, 0.0],
            pinned=False,
            membrane_locked=False,
        )
        sen = SimpleNamespace(
            id="s1",
            entity_type="sensor",
            position=[130.0, 90.0],
            velocity=[0.0, 0.0],
            pinned=True,
            membrane_locked=False,
        )
        edges = [{"start": "hub", "end": "s1", "channel": "struct", "weight": 1.0}]
        attach = build_membrane_attachments([org, sen], edges)
        self.assertEqual(attach["s1"][0], "hub")
        self.assertAlmostEqual(attach["s1"][1], 30.0)
        self.assertAlmostEqual(attach["s1"][2], -10.0)
        self.assertFalse(sen.pinned)
        self.assertTrue(sen.membrane_locked)


class SignalAggregateTests(unittest.TestCase):
    def test_weighted_chemo_reaches_actuator(self) -> None:
        sensor = SimpleNamespace(
            id="s1",
            entity_type="sensor",
            sr_channel_out={"chemo": 0.8, "chemo_dir_x": 1.0, "chemo_dir_y": 0.0},
            sr_channel_out_prev={},
        )
        actuator = SimpleNamespace(id="a1", entity_type="actuator", sr_channel_out={}, sr_channel_out_prev={})
        edges = [{"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.5}]
        inbound = aggregate_channel_signals(edges, [sensor, actuator], use_prev=False)
        self.assertAlmostEqual(inbound["a1"]["chemo"], 1.2)
        self.assertAlmostEqual(inbound["a1"]["chemo_dir_x"], 1.2)


class GameViewportMembraneFollowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_sync_membrane_moves_child(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        gv = GameViewport()
        ent = gv._SceneRuntimeEntity("hub", "organism", (50.0, 50.0), 30.0)
        child = gv._SceneRuntimeEntity("s1", "sensor", (80.0, 50.0), 10.0)
        child.membrane_locked = True
        gv.scene_runtime_entities = [ent, child]
        gv._sr_membrane_attach = {"s1": ("hub", 30.0, 0.0)}
        ent.position[0] = 100.0
        ent.velocity[0] = 5.0
        gv._sync_membrane_positions()
        self.assertAlmostEqual(child.position[0], 130.0)
        self.assertAlmostEqual(child.velocity[0], 5.0)


class EvoNoGpsChemoTests(unittest.TestCase):
    def test_think_does_not_add_food_vector(self) -> None:
        Evo = _load_evo()
        brain = Evo()
        obs = {
            "nutrient_grad_x": 1.0,
            "nutrient_grad_y": 0.0,
            "ambient_field": 100.0,
            "world_width": 800,
            "world_height": 600,
            "bounds": (800, 600),
            "sensor_pull": 0.0,
            "actuator_pull": 0.0,
            "peer_organism_pull": 0.0,
            "niche_pressure": 0.0,
            "world_load_derivative": 0.0,
            "intrinsic_speed": 0.0,
            "memory_stress_ema": 0.0,
            "memory_field_ema": 0.0,
            "memory_speed_ema": 0.0,
        }
        dec = brain.think(obs, 0.05)
        ax0 = float(dec.get("ax", 0.0))
        ay0 = float(dec.get("ay", 0.0))
        obs["nutrient_grad_x"] = 0.0
        obs["nutrient_grad_y"] = 1.0
        dec2 = brain.think(obs, 0.05)
        ax1 = float(dec2.get("ax", 0.0))
        ay1 = float(dec2.get("ay", 0.0))
        self.assertEqual(ax0, ax1)
        self.assertEqual(ay0, ay1)


class MembraneSpawnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_organism_with_membrane_spawn_creates_periphery(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        gv = GameViewport()
        gv.scene_runtime_entities = []
        gv._sr_membrane_attach = {}
        gv._sr_structural_edges = []
        gv._sr_signal_edges = []
        gv._scene_runtime_edges = []
        gv._scene_runtime_neighbor_ids = {}
        gv._sr_spawn_seq = 0
        req = {
            "type": "organism_with_membrane",
            "hub_id": "evo_test_hub",
            "position": (200.0, 150.0),
            "radius": 24.0,
            "energy": 90.0,
            "generation": 1,
            "scripts": [],
            "edge_mutation_sigma": 0.1,
            "signal_edge_weights": [1.0, 1.2],
        }
        gv._process_organism_with_membrane_spawn(req, None)
        types = [str(getattr(e, "entity_type", "")) for e in gv.scene_runtime_entities]
        self.assertEqual(types.count("organism"), 1)
        self.assertGreaterEqual(types.count("sensor"), 2)
        self.assertGreaterEqual(types.count("actuator"), 2)
        self.assertIn("evo_test_hub_s1", gv._sr_membrane_attach)


class MembraneTemplateTests(unittest.TestCase):
    def test_resolve_membrane_template_overrides_cost(self) -> None:
        tpl = resolve_membrane_template(
            {"sr_membrane_template": {"organelle_birth_cost": 33, "default_edge_weight": 1.2}}
        )
        self.assertEqual(tpl["organelle_birth_cost"], 33)
        self.assertAlmostEqual(float(tpl["default_edge_weight"]), 1.2)

    def test_apply_explicit_signal_edges_overrides_weight(self) -> None:
        base = [
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.0},
        ]
        explicit = [
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 2.5},
        ]
        out = apply_explicit_signal_edges(base, explicit, {"s1", "a1"})
        self.assertAlmostEqual(float(out[0]["weight"]), 2.5)


class SignalEdgeDedupTests(unittest.TestCase):
    # 契约: 显式 sensor→actuator 边不被隐式全连接用 default_weight 覆盖

    def test_expand_dedupes_duplicate_chemo_pair(self) -> None:
        attachments = {"s1": ("hub", 0.0, 0.0), "a1": ("hub", 10.0, 0.0)}
        id_to_type = {"hub": "organism", "s1": "sensor", "a1": "actuator"}
        structural = [
            {"start": "hub", "end": "s1", "channel": "struct", "weight": 1.0},
            {"start": "hub", "end": "a1", "channel": "struct", "weight": 1.0},
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.25},
        ]
        edges = expand_signal_edges(structural, attachments, id_to_type, default_weight=1.0)
        pairs = [
            e
            for e in edges
            if e["start"] == "s1" and e["end"] == "a1" and e["channel"] == "chemo"
        ]
        self.assertEqual(len(pairs), 1)
        self.assertAlmostEqual(float(pairs[0]["weight"]), 1.25)

    # 契约: 父代 (ps1,pa1)/(ps1,pa2) 不同权重映射到子代 (cs1,ca1)/(cs1,ca2)

    def test_inherit_preserves_per_edge_weights(self) -> None:
        parent = [
            {"start": "ps1", "end": "pa1", "channel": "chemo", "weight": 1.1},
            {"start": "ps1", "end": "pa2", "channel": "chemo", "weight": 1.9},
        ]
        child = [
            {"start": "cs1", "end": "ca1", "channel": "chemo", "weight": 1.0},
            {"start": "cs1", "end": "ca2", "channel": "chemo", "weight": 1.0},
        ]
        out = inherit_chemo_edge_weights(
            child,
            parent,
            child_sensor_ids=["cs1"],
            child_actuator_ids=["ca1", "ca2"],
            parent_sensor_ids=["ps1"],
            parent_actuator_ids=["pa1", "pa2"],
        )
        w_by_end = {e["end"]: float(e["weight"]) for e in out}
        self.assertAlmostEqual(w_by_end["ca1"], 1.1)
        self.assertAlmostEqual(w_by_end["ca2"], 1.9)

    # 契约: mutate_signal_edges 在 inherit 之后应能改变 weight

    def test_mutate_changes_weights_after_inherit(self) -> None:
        edges = [
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.0},
        ]
        out = mutate_signal_edges(edges, 0.5, __import__("random").Random(42))
        self.assertNotAlmostEqual(float(out[0]["weight"]), 1.0)


class MembranePruneTests(unittest.TestCase):
    def test_expand_removal_drops_membrane_children(self) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        gv = GameViewport()
        gv._sr_membrane_attach = {"s1": ("hub", 10.0, 0.0), "a1": ("hub", -10.0, 0.0)}
        drop = gv._expand_removal_with_membrane(["hub"])
        self.assertEqual(drop, {"hub", "s1", "a1"})


if __name__ == "__main__":
    unittest.main()
