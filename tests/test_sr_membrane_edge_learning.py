# -*- coding: utf-8
"""chemo 边权学习。"""
from __future__ import annotations

import unittest

from core.Lotucosm.sr_membrane_topology import (
    learn_chemo_edge_weights,
    update_hub_chemo_edges_on_host,
)


class ChemoEdgeLearningTests(unittest.TestCase):
    def test_update_hub_edges(self) -> None:
        edges = [
            {"start": "s1", "end": "a1", "channel": "chemo", "weight": 1.0},
            {"start": "x", "end": "y", "channel": "chemo", "weight": 0.5},
        ]
        attach = {"s1": ("hub1", 0.0, 0.0), "a1": ("hub1", 0.0, 0.0)}
        out = update_hub_chemo_edges_on_host(
            edges, "hub1", attach, reward=0.85, stress=0.1
        )
        hub_w = next(e["weight"] for e in out if e["start"] == "s1")
        other_w = next(e["weight"] for e in out if e["start"] == "x")
        self.assertGreater(hub_w, 1.0)
        self.assertAlmostEqual(other_w, 0.5)

    def test_learn_clamps_weight(self) -> None:
        edges = [{"start": "s", "end": "a", "channel": "chemo", "weight": 2.9}]
        out = learn_chemo_edge_weights(edges, reward=1.0, stress=0.0, learn_rate=0.5)
        self.assertLessEqual(out[0]["weight"], 3.0)


if __name__ == "__main__":
    unittest.main()
