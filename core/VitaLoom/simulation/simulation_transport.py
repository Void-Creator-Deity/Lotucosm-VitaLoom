# -*- coding: utf-8 -*-
"""模拟 Transport 中枢：播放/暂停/停止/倍速的唯一编排入口。

第一性原理：模拟只有「改状态」与「改倍速」两类操作。
奥卡姆剃刀：工具栏负责 transport，游戏视口 HUD 只负责倍速与状态展示。

数据流::

    UI（工具栏 / 菜单 / 快捷键）
        → SimulationTransport.request_*
        → event_bus（simulation_play | pause | stop | speed_changed）
        → GameViewportPlugin → GameViewport

状态回写::

    GameViewport（start/pause/stop/speed）
        → SimulationTransport.sync_from_viewport
        → simulation_transport_state（刷新工具栏 ▶/⏸ 文案）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from core.VitaLoom.core.logger import get_logger

logger = get_logger("SimulationTransport")

_transport: Optional["SimulationTransport"] = None


@dataclass(frozen=True)
class SimulationTransportState:
    is_playing: bool = False
    is_paused: bool = False
    speed: float = 1.0


class SimulationTransport:
    """编排模拟生命周期，不直接 tick SR（tick 仍在 GameViewport）。"""

    EVENT_PLAY = "simulation_play"
    EVENT_PAUSE = "simulation_pause"
    EVENT_STOP = "simulation_stop"
    EVENT_SPEED = "simulation_speed_changed"
    EVENT_STATE = "simulation_transport_state"

    def __init__(self, editor_context: Any):
        self._ctx = editor_context
        self._state = SimulationTransportState()

    @property
    def state(self) -> SimulationTransportState:
        return self._state

    def _bus(self):
        return getattr(self._ctx, "event_bus", None)

    def _kernel(self):
        return getattr(self._ctx, "kernel", None)

    def request_play(self) -> None:
        """开始或从暂停恢复；自动切到游戏视口。"""
        kernel = self._kernel()
        if kernel and hasattr(kernel, "layout_manager"):
            try:
                kernel.layout_manager.switch_viewport("game")
            except Exception as e:
                logger.debug("切换游戏视口失败: %s", e)
        bus = self._bus()
        if bus:
            bus.publish(self.EVENT_PLAY)

    def request_pause(self) -> None:
        bus = self._bus()
        if bus:
            bus.publish(self.EVENT_PAUSE)

    def request_stop(self) -> None:
        bus = self._bus()
        if bus:
            bus.publish(self.EVENT_STOP)
        kernel = self._kernel()
        if kernel and hasattr(kernel, "layout_manager"):
            try:
                kernel.layout_manager.switch_viewport("scene")
            except Exception as e:
                logger.debug("切换场景视口失败: %s", e)

    def request_toggle(self) -> None:
        """运行中且未暂停 → 暂停；否则 → 播放/继续。"""
        if self._state.is_playing and not self._state.is_paused:
            self.request_pause()
        else:
            self.request_play()

    def set_speed(self, speed: float) -> None:
        speed = max(0.1, min(5.0, float(speed)))
        self._state = SimulationTransportState(
            is_playing=self._state.is_playing,
            is_paused=self._state.is_paused,
            speed=speed,
        )
        bus = self._bus()
        if bus:
            bus.publish(self.EVENT_SPEED, speed)
        self._emit_state()

    def sync_from_viewport(
        self,
        *,
        is_playing: bool,
        is_paused: bool,
        speed: Optional[float] = None,
    ) -> None:
        """由 GameViewport 在状态变化后回写，驱动工具栏文案刷新。"""
        self._state = SimulationTransportState(
            is_playing=bool(is_playing),
            is_paused=bool(is_paused),
            speed=float(speed if speed is not None else self._state.speed),
        )
        self._emit_state()

    def _emit_state(self) -> None:
        bus = self._bus()
        if bus:
            bus.publish(self.EVENT_STATE, self._state)

    def play_toolbar_label(self, tr: Callable[[str, str], str]) -> str:
        if self._state.is_playing and not self._state.is_paused:
            return f"⏸ {tr('toolbar.pause', '暂停')}"
        if self._state.is_playing and self._state.is_paused:
            return f"▶ {tr('toolbar.resume', '继续')}"
        return f"▶ {tr('toolbar.play', '运行')}"


def init_simulation_transport(editor_context: Any) -> SimulationTransport:
    """在内核绑定 event_bus 后调用一次。"""
    global _transport
    _transport = SimulationTransport(editor_context)
    editor_context.simulation_transport = _transport
    return _transport


def get_simulation_transport() -> Optional[SimulationTransport]:
    return _transport
