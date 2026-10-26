# -*- coding: utf-8
"""PsExperimentPanel 冒烟：offscreen 实例化。"""
from __future__ import annotations

import os
import unittest

from PyQt6.QtWidgets import QApplication

from core.VitaLoom.core.editor_context import EditorContext
from core.VitaLoom.simulation.ps_experiment_service import SERVICE_KEY, PsExperimentService


class PsExperimentPanelSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls._app = QApplication.instance() or QApplication([])

    def test_panel_instantiate_with_service(self):
        from pathlib import Path

        from core.VitaLoom.docks.ps_experiment_panel import PsExperimentPanel

        ctx = EditorContext()
        root = Path(__file__).resolve().parents[1]
        svc = PsExperimentService(root)
        ctx.services.register(SERVICE_KEY, svc)
        panel = PsExperimentPanel(ctx)
        self.assertIsNotNone(panel.run_btn)
        self.assertGreater(panel.preset_combo.count(), 0)


if __name__ == "__main__":
    unittest.main()
