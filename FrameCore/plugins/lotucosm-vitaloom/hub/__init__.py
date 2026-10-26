# -*- coding: utf-8 -*-
"""VitaLoom Hub entry and FrameCore lifecycle Adapter."""
from __future__ import annotations

import os
import sys
from importlib import import_module
from typing import TYPE_CHECKING

from FrameCore.lifecycle import FrameApi

if TYPE_CHECKING:
    from hub.hub_window import HubWindow

__all__ = ["HubWindow", "LotucosmVitaLoomFramePlugin", "create_frame_plugin"]


class LotucosmVitaLoomFramePlugin:
    """L1 product plugin: owns Hub while version runtimes remain selectable children."""

    def __init__(self) -> None:
        self.frame_api: FrameApi | None = None

    def on_load(self, frame_api: object) -> None:
        if not isinstance(frame_api, FrameApi):
            raise TypeError("LotucosmVitaLoomFramePlugin requires FrameApi")
        self.frame_api = frame_api

    def on_unload(self) -> None:
        self.frame_api = None

    def run_entry(self, entry: str, args: list[str] | None = None) -> int:
        """Run a product-plugin entry without binding Hub to a runtime version."""
        _ = args
        if entry == "hub":
            return self._run_hub(smoke=False)
        if entry == "hub_smoke":
            return self._run_hub(smoke=True)
        raise RuntimeError(f"unknown lotucosm-vitaloom plugin entry: {entry}")

    def _run_hub(self, *, smoke: bool) -> int:
        api = self.frame_api
        if api is None:
            raise RuntimeError("lotucosm-vitaloom plugin is not loaded")
        if smoke:
            os.environ["QT_QPA_PLATFORM"] = "offscreen"

        from PyQt6 import QtWidgets
        from hub.hub_style import apply_app_baseline, hub_stylesheet
        from hub.hub_window import HubWindow

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        apply_app_baseline(app)
        app.setStyleSheet(hub_stylesheet())
        hub = HubWindow(api.app_root)
        hub.show()
        if not smoke:
            return app.exec()

        hub.refresh_projects()
        version = api.select_product_version(api.suite.product_id)
        print(
            "Hub smoke OK: "
            f"product={version.product_id}@{version.version} "
            f"projects={hub.list_widget.count()}"
        )
        hub.close()
        app.processEvents()
        return 0


def create_frame_plugin() -> LotucosmVitaLoomFramePlugin:
    """Manifest entry factory consumed by ``FrameApi.create_lifecycle_plugin``."""
    return LotucosmVitaLoomFramePlugin()


def __getattr__(name: str):
    if name == "HubWindow":
        value = getattr(import_module("hub.hub_window"), name)
        globals()[name] = value
        return value
    raise AttributeError(name)
