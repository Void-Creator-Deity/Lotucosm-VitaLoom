# -*- coding: utf-8
"""PS 实验快照视口叠加（vitalloom.runtime.replay 骨架）。"""
from __future__ import annotations

from typing import Any, Dict

from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
from core.VitaLoom.core.logger import get_logger

logger = get_logger("PsReplayOverlayPlugin")


class PsReplayOverlayPlugin(IRuntimePlugin):
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PsReplayOverlayPlugin",
            "version": "0.1.0",
            "author": "VitaLoom Team",
            "description": "PS 实验 run 在游戏视口只读叠加（不合并 tick）",
            "dependencies": ["PsExperimentPlugin"],
            "provides": ["runtime.ps_replay_overlay"],
            "activation_context": "runtime",
        }

    def on_load(self, editor_context: Any) -> None:
        self.context = editor_context
        if hasattr(editor_context, "event_bus"):
            editor_context.event_bus.subscribe(
                "ps_experiment_finished", self._on_experiment_finished
            )

    def on_unload(self) -> None:
        if hasattr(self, "context") and self.context:
            try:
                self.context.event_bus.unsubscribe(
                    "ps_experiment_finished", self._on_experiment_finished
                )
            except Exception:
                __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)

    def _on_experiment_finished(self, data: Any) -> None:
        if not isinstance(data, dict):
            return
        out = data.get("output_dir")
        if out is None:
            return
        try:
            from pathlib import Path

            from core.VitaLoom.simulation.ps_replay_overlay import (
                push_overlay_to_game_viewport,
            )

            n = push_overlay_to_game_viewport(self.context, Path(out))
            if n > 0:
                logger.info("PS replay overlay: %s 点", n)
        except Exception as exc:
            logger.debug("PS replay overlay 更新失败: %s", exc)

