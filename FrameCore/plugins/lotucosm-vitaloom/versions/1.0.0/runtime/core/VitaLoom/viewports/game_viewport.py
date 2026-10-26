# -*- coding: utf-8 -*-
"""游戏视口：场景运行时（SR）宿主与内置 Simulation 回退。

SR 实现集中于 GameViewport：加载 .pond、每帧 tick、膜拓扑、会话摘要、HUD。
模块级函数 sr_* / build_sr_session_summary_* 供复盘与生态 Dock。

阅读顺序:
    类 GameViewport docstring（状态机）
    → # === SR: ... === 分区方法
    → core/Lotucosm/sr_membrane_topology.py（边与通道数学）
    → 当前工程 README「SR 运行时排错索引」
"""

from typing import Optional, Any, Dict, List
from collections.abc import Mapping
import importlib.util
import copy
import hashlib
import json
import os
import math
from datetime import datetime, timezone
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPaintEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider

from core.VitaLoom.core.editor_context import get_editor_context, EditorMode
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.project.project_world_capabilities import get_project_world_read_model
from core.Lotucosm.scene_runtime_ambient import ambient_field_and_gradient, nutrient_gradient_at
from core.Lotucosm.scene_runtime_world_state import niche_pressure_from_load, step_biosphere_load
from core.VitaLoom.viewports.sr_visual_renderer import SrVisualRenderer
from core.VitaLoom.viewports.qpainter_backend import QPainterViewportBackend, QPainterViewportFrame
from core.VitaLoom.viewports.graphics_backend_strategy import select_viewport_backend
from core.VitaLoom.viewports.opengl_backend import OpenGLViewportBackend
from core.VitaLoom.viewports.opengl_render_target import (
    DiagnosticOpenGLRenderTarget,
    QtOpenGLTextureTarget,
    QtOpenGLRenderTarget,
)
from core.VitaLoom.viewports.viewport_snapshot import build_viewport_frame_snapshot
from core.VitaLoom.viewports.viewport_profiler import ViewportFrameProfiler
from core.VitaLoom.viewports.simulation_driver import SimulationDriver
from core.VitaLoom.viewports.sr_input_state import SrInputSnapshot, SrInputState
from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog
from core.VitaLoom.simulation.sr_runtime_snapshot_authority import (
    SrRuntimeSnapshotAuthority,
)
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource
from core.Lotucosm.runtime.world_bridge_sr_runtime_randomness import (
    SrRuntimeRandomnessConfig,
    create_detached_sr_entity_randomness_rng,
    create_sr_runtime_randomness_rng,
    resolve_sr_runtime_randomness_config,
)
from core.Lotucosm.runtime.world_bridge_owner_gate import WorldBridgeOwnerGate


logger = get_logger("GameViewport")


def _current_project_world_config(editor_context=None) -> Dict[str, Any]:
    """Return a detached configuration snapshot through the runtime catalog."""

    return get_project_world_read_model(
        editor_context
    ).current_project_world_config()


def _sr_snapshot_number(value: object) -> float | None:
    """Project an arbitrary runtime numeric value into finite JSON data."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _sr_snapshot_render_identity(visual: Any) -> dict[str, Any] | None:
    """Project the renderer-owned visual identity into finite, JSON-safe data.

    ``sr_visual`` is optional on runtime entities; when it is absent the
    snapshot omits the field, matching the producer whitelist policy.
    ``flip_x`` and ``alpha`` are the render inputs the runtime owns today;
    sprite/anim asset resolution stays with the renderer and is not
    checkpoint state.
    """
    if visual is None:
        return None
    alpha = _sr_snapshot_number(getattr(visual, "alpha", None))
    if alpha is None:
        return None
    return {
        "flip_x": bool(getattr(visual, "flip_x", False)),
        "alpha": min(1.0, max(0.0, alpha)),
    }


def sr_all_play_goals_satisfied(
    goals: Dict[str, Any],
    sim_time: float,
    pop_peak: int,
    entities: Optional[List[Any]] = None,
) -> bool:
    """演示目标是否全部满足（存活时长 AND 种群峰值 AND/或 HUD 键，若配置了对应键）。"""
    if not isinstance(goals, dict) or not goals:
        return False
    has_any = False
    ok = True
    if "survive_seconds" in goals:
        has_any = True
        try:
            need_t = float(goals["survive_seconds"])
        except (TypeError, ValueError):
            ok = False
        else:
            ok = ok and (float(sim_time) >= need_t)
    if "peak_population" in goals:
        has_any = True
        try:
            need_p = int(goals["peak_population"])
        except (TypeError, ValueError):
            ok = False
        else:
            ok = ok and (int(pop_peak) >= need_p)
    hud_key = goals.get("hud_victory_key")
    if isinstance(hud_key, str) and hud_key.strip():
        has_any = True
        ok = ok and sr_hud_victory_satisfied(hud_key.strip(), entities or [])
    return has_any and ok


def sr_hud_victory_satisfied(hud_key: str, entities: List[Any]) -> bool:
    """任意实体的 sr_debug_hud[hud_key] == 1 即视为达成。"""
    for ent in entities:
        hud = getattr(ent, "sr_debug_hud", None)
        if isinstance(hud, dict) and hud.get(hud_key) == 1:
            return True
    return False


def sr_pause_on_complete_enabled(goals: Dict[str, Any]) -> bool:
    if not isinstance(goals, dict):
        return False
    return goals.get("pause_on_complete") is True


_EPISODE_SR_GOAL_CONFIG_KEYS = frozenset(
    (
        "survive_seconds",
        "peak_population",
        "pause_on_complete",
        "hint_zh",
        "hint_en",
        "hint",
        "victory_title_zh",
        "victory_title_en",
        "victory_banner_zh",
        "victory_banner_en",
        "extinction_title_zh",
        "extinction_title_en",
        "extinction_banner_zh",
        "extinction_banner_en",
        "hud_victory_key",
        "hud_defeat_key",
        "defeat_title_zh",
        "defeat_title_en",
        "defeat_banner_zh",
        "defeat_banner_en",
    )
)


def sr_resolve_session_banner(
    kind: str,
    goals: Dict[str, Any],
    *,
    chinese: bool = True,
) -> tuple[str, str, str]:
    """从 sr_play_goals 解析横幅 title / message / hint（含 i18n 键与默认文案）。"""
    goals = goals if isinstance(goals, dict) else {}
    if kind == "victory":
        title = (
            str(goals.get("victory_title_zh" if chinese else "victory_title_en") or "").strip()
            or ("目标达成" if chinese else "Victory")
        )
        message = (
            str(goals.get("victory_banner_zh" if chinese else "victory_banner_en") or "").strip()
            or (
                "演示目标已全部达成 — 已自动暂停，可按「继续」再玩。"
                if chinese
                else "All demo goals met — auto-paused. Press Resume to continue."
            )
        )
        hint = goals.get("hint_zh" if chinese else "hint_en") or goals.get("hint")
        hint_s = str(hint).strip() if hint else ""
        if not hint_s:
            hint_s = "按顶部 ▶ 继续 或 ⏹ 停止" if chinese else "Press ▶ Resume or ⏹ Stop"
        return title, message, hint_s
    if kind == "defeat":
        title = (
            str(goals.get("defeat_title_zh" if chinese else "defeat_title_en") or "").strip()
            or ("游戏结束" if chinese else "Game Over")
        )
        message = (
            str(goals.get("defeat_banner_zh" if chinese else "defeat_banner_en") or "").strip()
            or ("本局失败 — 已自动暂停。" if chinese else "Run failed — auto-paused.")
        )
        hint_s = "按 ⏹ 停止 后重试" if chinese else "Press ⏹ Stop and retry"
        return title, message, hint_s
    title = (
        str(goals.get("extinction_title_zh" if chinese else "extinction_title_en") or "").strip()
        or ("种群灭绝" if chinese else "Extinction")
    )
    message = (
        str(goals.get("extinction_banner_zh" if chinese else "extinction_banner_en") or "").strip()
        or (
            "种群已灭绝 — 已自动暂停。可「停止」后重开或调整场景。"
            if chinese
            else "Population extinct — auto-paused."
        )
    )
    hint_s = "按 ⏹ 停止 后调整场景再试" if chinese else "Press ⏹ Stop and adjust the scene"
    return title, message, hint_s


def sr_play_goals_episode_config_snapshot(goals: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(goals, dict) or not goals:
        return None
    out: Dict[str, Any] = {}
    for key in _EPISODE_SR_GOAL_CONFIG_KEYS:
        if key not in goals:
            continue
        val = goals[key]
        if val is None or isinstance(val, (bool, int, float, str)):
            out[key] = val
    return out if out else None


_SR_SESSION_END_REASON_ZH = {
    "stopped": "手动停止",
    "goals_complete": "演示目标达成",
    "extinction": "种群灭绝",
    "scene_changed": "场景或项目已切换",
}
_SR_SESSION_FINAL_REASONS = frozenset(("goals_complete", "extinction", "scene_changed"))


def build_sr_session_summary_payload(
    *,
    session_stamp: str,
    end_reason: str,
    sim_time: float,
    organism_count: int,
    organism_peak: int,
    entity_count: int,
    play_goals: Dict[str, Any],
    victory_pause_done: bool,
    extinction_pause_done: bool,
    project_path: Optional[str] = None,
    scene_name: Optional[str] = None,
    membrane_sensor_count: Optional[int] = None,
    mean_edge_weight: Optional[float] = None,
    mean_chemo_channel: Optional[float] = None,
    war_phase: Optional[str] = None,
    population_at_war_end: Optional[int] = None,
    war_population_min: Optional[int] = None,
    combat_score_total: Optional[int] = None,
    war_kills: Optional[int] = None,
    respawn_count: Optional[int] = None,
) -> Dict[str, Any]:
    """构造 SR 一局结束时的可序列化摘要（供 JSON / Markdown 落盘）。

    时机: _write_sr_session_summary；end_reason 为 stopped/goals_complete/extinction 等。
    排错: 勿在换场景后用当前 SceneManager 填 scene_name，须用 _capture_sr_session_context 快照。
    """
    goals = play_goals if isinstance(play_goals, dict) else {}
    has_metrics = "survive_seconds" in goals or "peak_population" in goals
    payload: Dict[str, Any] = {
        "session_stamp": session_stamp,
        "end_reason": end_reason,
        "end_reason_zh": _SR_SESSION_END_REASON_ZH.get(end_reason, end_reason),
        "sim_time_end": float(sim_time),
        "organism_count": int(organism_count),
        "organism_peak": int(organism_peak),
        "entity_count": int(entity_count),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sr_play_goals_config": sr_play_goals_episode_config_snapshot(goals),
        "sr_victory_pause_triggered": bool(victory_pause_done),
        "sr_extinction_pause_triggered": bool(extinction_pause_done),
    }
    if project_path:
        payload["project_path"] = project_path
    if scene_name:
        payload["scene_name"] = scene_name
    if membrane_sensor_count is not None:
        payload["membrane_sensor_count"] = int(membrane_sensor_count)
    if mean_edge_weight is not None:
        payload["mean_edge_weight"] = float(mean_edge_weight)
    if mean_chemo_channel is not None:
        payload["mean_chemo_channel"] = float(mean_chemo_channel)
    if war_phase:
        payload["war_phase"] = war_phase
    if population_at_war_end is not None:
        payload["population_at_war_end"] = int(population_at_war_end)
    if war_population_min is not None:
        payload["war_population_min"] = int(war_population_min)
    if combat_score_total is not None:
        payload["combat_score_total"] = int(combat_score_total)
    if war_kills is not None:
        payload["war_kills"] = int(war_kills)
    if respawn_count is not None:
        payload["respawn_count"] = int(respawn_count)
    if has_metrics:
        payload["sr_play_goals_satisfied"] = sr_all_play_goals_satisfied(
            goals, float(sim_time), int(organism_peak)
        )
    else:
        payload["sr_play_goals_satisfied"] = None
    return payload


def format_sr_session_summary_markdown(payload: Dict[str, Any], *, chinese: bool = True) -> str:
    """将摘要转为便于人工阅读的 Markdown（不写文件）。"""
    reason = (
        str(payload.get("end_reason_zh", payload.get("end_reason", "")))
        if chinese
        else str(payload.get("end_reason", ""))
    )
    lines = [
        f"# SR 会话摘要 · {reason}" if chinese else f"# SR session · {reason}",
        "",
        f"- 模拟时间: {float(payload.get('sim_time_end', 0.0)):.1f} s"
        if chinese
        else f"- sim_time: {float(payload.get('sim_time_end', 0.0)):.1f} s",
        f"- 细胞数: {payload.get('organism_count', 0)}（峰值 {payload.get('organism_peak', 0)}）"
        if chinese
        else f"- organisms: {payload.get('organism_count', 0)} (peak {payload.get('organism_peak', 0)})",
        f"- 实体总数: {payload.get('entity_count', 0)}"
        if chinese
        else f"- entities: {payload.get('entity_count', 0)}",
    ]
    cfg = payload.get("sr_play_goals_config")
    if isinstance(cfg, dict) and cfg:
        lines.append("")
        lines.append("## 演示目标配置" if chinese else "## play goals")
        for k, v in sorted(cfg.items()):
            lines.append(f"- {k}: {v}")
    sat = payload.get("sr_play_goals_satisfied")
    if sat is not None:
        lines.append("")
        lines.append(
            f"- 目标已全部达成: {'是' if sat else '否'}"
            if chinese
            else f"- all goals met: {bool(sat)}"
        )
    if payload.get("sr_victory_pause_triggered"):
        lines.append("- 曾触发目标达成自动暂停" if chinese else "- victory auto-pause")
    if payload.get("sr_extinction_pause_triggered"):
        lines.append("- 曾触发灭绝自动暂停" if chinese else "- extinction auto-pause")
    if "membrane_sensor_count" in payload:
        lines.append("")
        lines.append("## 膜拓扑" if chinese else "## membrane topology")
        lines.append(
            f"- 膜受体数: {payload.get('membrane_sensor_count', 0)}"
            if chinese
            else f"- membrane sensors: {payload.get('membrane_sensor_count', 0)}"
        )
        if "mean_edge_weight" in payload:
            lines.append(
                f"- 平均 chemo 边权重: {float(payload.get('mean_edge_weight', 0.0)):.3f}"
                if chinese
                else f"- mean chemo edge weight: {float(payload.get('mean_edge_weight', 0.0)):.3f}"
            )
        if "mean_chemo_channel" in payload:
            lines.append(
                f"- 纤毛平均 chemo 通道: {float(payload.get('mean_chemo_channel', 0.0)):.3f}"
                if chinese
                else f"- mean chemo channel at actuators: {float(payload.get('mean_chemo_channel', 0.0)):.3f}"
            )
    if payload.get("war_phase"):
        lines.append("")
        lines.append("## 战争后进化" if chinese else "## post-war recovery")
        phase = str(payload.get("war_phase", ""))
        if chinese:
            from core.Lotucosm.sr_war_recovery import phase_label_zh

            phase = phase_label_zh(phase)  # type: ignore[arg-type]
        lines.append(f"- 结束阶段: {phase}" if chinese else f"- end phase: {phase}")
        if payload.get("population_at_war_end") is not None:
            lines.append(
                f"- 战争结束时种群: {payload.get('population_at_war_end')}"
                if chinese
                else f"- population at war end: {payload.get('population_at_war_end')}"
            )
        if payload.get("war_population_min") is not None:
            lines.append(
                f"- 战争期种群最低: {payload.get('war_population_min')}"
                if chinese
                else f"- war population min: {payload.get('war_population_min')}"
            )
        if payload.get("combat_score_total") is not None:
            lines.append(
                f"- 互攻积分合计: {payload.get('combat_score_total')}"
                if chinese
                else f"- combat score total: {payload.get('combat_score_total')}"
            )
        if payload.get("war_kills") is not None:
            lines.append(
                f"- 击杀数: {payload.get('war_kills')}" if chinese else f"- kills: {payload.get('war_kills')}"
            )
        if payload.get("respawn_count") is not None:
            lines.append(
                f"- 复活次数: {payload.get('respawn_count')}"
                if chinese
                else f"- respawns: {payload.get('respawn_count')}"
            )
    ts = payload.get("timestamp_utc")
    if ts:
        lines.extend(["", f"UTC: {ts}"])
    return "\n".join(lines)


class GameViewport(QWidget):
    """游戏视图：模拟模式绘制与 SR 场景运行时宿主。

    SR 运行时状态机（非 SR 时走 builtin Simulation）::

        Idle --_start_simulation--> Playing
        Playing --_pause_simulation--> Paused
        Paused --_resume_simulation--> Playing（若 _scene_runtime_needs_reload 则先重载）
        Playing/Paused --_stop_simulation--> Idle
        Playing/Paused --_on_external_scene_context_changed--> Idle（换项目/场景）

    关键字段::

        _sr_runtime_dirty / (_sr_runtime_project_path, _sr_runtime_scene_path)
            与当前编辑器上下文比对，决定 resume 是否重载 .pond 实体。
        _sr_session_scene_name / _sr_session_project_path
            开局快照，写 logs/sr_sessions 时用，避免换场景后 scene_name 张冠李戴。

    分区索引: 见类内 ``# === SR: ... ===`` 注释块；每帧顺序见
    ``_update_scene_runtime_entities`` 顶部「顺序契约」。
    """

    # 自定义信号
    simulation_started = pyqtSignal()
    simulation_stopped = pyqtSignal()
    simulation_paused = pyqtSignal()
    simulation_resumed = pyqtSignal()

    class _SrCanvas(QWidget):
        """SR 绘图画布（与 HUD 控制条分离，避免布局挤占绘制区）。"""

        def __init__(self, host: "GameViewport"):
            super().__init__(host)
            self._host = host
            self.setObjectName("gameViewportCanvas")
            self.setMinimumSize(400, 300)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        def paintEvent(self, event: Optional[QPaintEvent]):
            self._host._paint_sr_canvas(self, event)

        def keyPressEvent(self, event) -> None:
            if event is None or event.isAutoRepeat():
                return
            mods = event.modifiers()
            if (
                getattr(self._host, "_sr_game_mode", False)
                and mods & Qt.KeyboardModifier.ControlModifier
                and mods & Qt.KeyboardModifier.ShiftModifier
                and event.key() == Qt.Key.Key_C
            ):
                self._host._copy_proc_seed_to_clipboard()
                event.accept()
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            k = key_from_qt_event(event)
            if k:
                self._host._sr_input_press(k)
            event.accept()

        def keyReleaseEvent(self, event) -> None:
            if event is None or event.isAutoRepeat():
                return
            from core.VitaLoom.viewports.sr_input_state import key_from_qt_event

            k = key_from_qt_event(event)
            if k:
                self._host._sr_input_release(k)
            event.accept()

        def mouseMoveEvent(self, event) -> None:
            if event is None:
                return
            pos = event.position()
            sx, sy = self._host._widget_to_scene(float(pos.x()), float(pos.y()))
            if self._host._enqueue_worldbridge_input(
                "mouse_move", {"scene_xy": [sx, sy]}
            ) is None:
                return
            self._host._sr_input.set_mouse_scene(sx, sy)
            event.accept()

        def mousePressEvent(self, event) -> None:
            if event is None:
                return
            from PyQt6.QtCore import Qt

            pos = event.position()
            sx, sy = self._host._widget_to_scene(float(pos.x()), float(pos.y()))
            if self._host._enqueue_worldbridge_input(
                "mouse_move", {"scene_xy": [sx, sy]}
            ) is None:
                return
            if event.button() == Qt.MouseButton.LeftButton:
                if self._host._enqueue_worldbridge_input(
                    "mouse_down", {"button": "left", "scene_xy": [sx, sy]}
                ) is None:
                    return
                self._host._sr_input.set_mouse_scene(sx, sy)
                self._host._sr_input.mouse_press_left()
            else:
                self._host._sr_input.set_mouse_scene(sx, sy)
            event.accept()

        def mouseReleaseEvent(self, event) -> None:
            if event is None:
                return
            from PyQt6.QtCore import Qt

            pos = event.position()
            sx, sy = self._host._widget_to_scene(float(pos.x()), float(pos.y()))
            if event.button() == Qt.MouseButton.LeftButton:
                if self._host._enqueue_worldbridge_input(
                    "mouse_up", {"button": "left", "scene_xy": [sx, sy]}
                ) is None:
                    return
                self._host._sr_input.set_mouse_scene(sx, sy)
                self._host._sr_input.mouse_release_left()
            else:
                self._host._sr_input.set_mouse_scene(sx, sy)
            event.accept()

    def __init__(self, *, identity_source: DeterministicIdentitySource | None = None):
        """GameViewport.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setObjectName("gameViewport")
        self._sr_visual = SrVisualRenderer()
        self._viewport_backend = select_viewport_backend(renderer=self._sr_visual).backend
        self._viewport_profiler = ViewportFrameProfiler()
        self._last_opengl_canvas_snapshot: dict[str, Any] | None = None
        self._last_opengl_target_snapshot: dict[str, Any] | None = None
        self._simulation_driver = SimulationDriver()
        self._sr_input = SrInputState()
        from core.Lotucosm.runtime.world_bridge_input_sequence import WorldBridgeInputSequence
        from core.Lotucosm.runtime.world_bridge_tick_authority import WorldBridgeTickAuthority

        self._worldbridge_tick_authority = WorldBridgeTickAuthority(
            input_sequence=WorldBridgeInputSequence(
                scheduler_owner_id="game_viewport.input_scheduler",
                max_pending=256,
                overflow_policy="reject_newest",
            )
        )
        self._worldbridge_input_sequence = self._worldbridge_tick_authority.input_sequence
        self._worldbridge_last_input_backpressure: dict[str, Any] | None = None
        self._worldbridge_input_events_last_tick: list[dict[str, Any]] = []
        self._worldbridge_last_tick_receipt: dict[str, Any] | None = None
        self._worldbridge_tick_authority_violation: dict[str, Any] | None = None
        self._worldbridge_shared_state_sequence = 0
        self._worldbridge_last_shared_state_envelope: dict[str, Any] | None = None
        self._worldbridge_shared_state_receiver: Any | None = None
        self._worldbridge_last_shared_state_receipt: dict[str, Any] | None = None
        self._sr_runtime_randomness_config = resolve_sr_runtime_randomness_config({})
        self._sr_runtime_rng = create_sr_runtime_randomness_rng(
            self._sr_runtime_randomness_config
        )
        self._worldbridge_owner_gate = WorldBridgeOwnerGate()
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 获取编辑器上下文
        self.editor_context = get_editor_context()
        self._sr_host_publication = None
        
        # 模拟状态
        self.simulation: Optional[Any] = None
        self.scene_runtime_entities: list[Any] = []
        self._sr_script_entropy_audits: list[dict[str, Any]] = []
        self._sr_script_entropy_receipts: list[dict[str, Any]] = []
        self._sr_script_failure_receipts: list[dict[str, Any]] = []
        self._scene_runtime_edges: list[tuple[str, str]] = []
        self._scene_runtime_emissions_prev: dict[str, float] = {}
        self._scene_runtime_neighbor_ids: dict[str, frozenset[str]] = {}
        self._sr_structural_edges: list[dict[str, Any]] = []
        self._sr_connection_edges: list[dict[str, Any]] = []
        self._sr_spring_links: list[Any] = []
        self._sr_signal_edges: list[dict[str, Any]] = []
        self._sr_membrane_attach: dict[str, tuple[str, float, float]] = {}
        self._sr_membrane_template: dict[str, Any] = {}
        self._sr_runtime_project_path: Optional[str] = None
        self._sr_runtime_scene_path: Optional[str] = None
        self._sr_identity_source = identity_source
        self._sr_runtime_snapshot_authority = SrRuntimeSnapshotAuthority(
            identity_source=identity_source
        )
        self._sr_runtime_epoch: str | None = None
        self._worldbridge_clock_owner_token = "game_viewport_clock"
        self._worldbridge_clock_decision_sequence = 0
        self._worldbridge_clock_decision: dict[str, Any] | None = None
        self._sr_serialized_scene_entity_ids: set[str] = set()
        self._sr_runtime_dirty = True
        self._sr_play_hint_shown = False
        self._unified_pond: Optional[Any] = None
        self._unified_pond_mode = False
        # A labelled handoff failure can follow partial live mutation. Keep the
        # opt-in feature configured, but do not retry current SR/PS instances.
        self._worldbridge_handoff_suspended = False
        self._worldbridge_last_handoff_failure: Optional[dict[str, Any]] = None
        self._worldbridge_last_recovery_decision: Optional[dict[str, Any]] = None
        self._worldbridge_last_quarantine_admission: Optional[dict[str, Any]] = None
        self._worldbridge_pond_lifetime_sequence = 0
        self._worldbridge_active_pond_lifetime_token: Optional[str] = None
        self._worldbridge_checkpoint_sequence = 0
        self._worldbridge_failure_lifecycle: Optional[dict[str, Any]] = None
        self._worldbridge_disposal_observation: Optional[dict[str, Any]] = None
        self._using_scene_runtime = False
        self._scene_runtime_time = 0.0
        self.is_playing = False
        self.is_paused = False
        self.simulation_speed = 1.0
        # 主世界 Episode 日志（默认关）：环境变量 LOTUCOSM_EPISODE_LOG=1 或 editor_context.episode_logging_enabled=True
        _ep = getattr(self.editor_context, "episode_logging_enabled", None)
        if _ep is None:
            self._episode_log_enabled = os.environ.get("LOTUCOSM_EPISODE_LOG", "").strip().lower() in ("1", "true", "yes")
        else:
            self._episode_log_enabled = bool(_ep)
        try:
            self._episode_duration_sim_time = float(
                getattr(self.editor_context, "episode_duration_sim_time", None)
                or os.environ.get("LOTUCOSM_EPISODE_DURATION", "120")
            )
        except ValueError:
            self._episode_duration_sim_time = 120.0
        self._episode_sim_accumulator = 0.0
        self._episode_index = 0
        self._sr_biosphere_load = 0.0
        self._sr_biosphere_prev_load = 0.0
        self._sr_load_max = 50.0
        self._sr_spawn_seq = 0
        self._sr_reproduction_events = 0
        self._sr_evo_pop_cap = 96
        self._sr_demo_legend: Optional[Dict[str, Any]] = None
        self._sr_nutrient_target_count = 0
        self._sr_nutrient_target_peace = 0
        self._sr_war_recovery: dict[str, Any] = {}
        self._sr_war_profile = None
        self._sr_war_recovery_override_until = 0.0
        self._sr_war_phase_last: str = "peace"
        self._sr_war_phase_announced: set[str] = set()
        self._sr_pop_at_war_end: Optional[int] = None
        self._sr_war_pop_min: Optional[int] = None
        self._sr_war_nutrient_purge_acc = 0.0
        self._sr_war_phase_tick_cache: Optional[str] = None
        self._sr_war_combat_profile = None
        self._sr_combat_lineage: dict[str, dict[str, Any]] = {}
        self._sr_war_respawn_queue: list[dict[str, Any]] = []
        self._sr_war_kills_total = 0
        self._sr_war_respawn_count = 0
        self._sr_war_pending_casualties: list[dict[str, Any]] = []
        self._sr_pop_peak = 0
        self._sr_play_goals: Dict[str, Any] = {}
        self._sr_goal_announced: Dict[str, bool] = {"survive": False, "peak": False}
        self._sr_victory_banner: Optional[str] = None
        self._sr_victory_pause_done = False
        self._sr_victory_notice_done = False
        self._sr_pause_on_extinction = False
        self._sr_game_mode = False
        self._sr_defeat_pause_done = False
        self._sr_extinction_pause_done = False
        self._sr_extinction_banner: Optional[str] = None
        self._sr_banner_kind: Optional[str] = None
        self._sr_banner_shown_at: float = 0.0
        self._sr_banner_title: Optional[str] = None
        self._sr_banner_hint: Optional[str] = None
        self._sr_session_stamp: Optional[str] = None
        self._sr_last_session_md_path: Optional[Path] = None
        self._sr_last_session_end_reason: Optional[str] = None
        self._sr_session_scene_name: Optional[str] = None
        self._sr_session_project_path: Optional[str] = None
        _sl = getattr(self.editor_context, "sr_session_logging_enabled", None)
        if _sl is None:
            self._sr_session_log_enabled = os.environ.get(
                "LOTUCOSM_SR_SESSION_LOG", "1"
            ).strip().lower() not in ("0", "false", "no")
        else:
            self._sr_session_log_enabled = bool(_sl)

        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_simulation)  # type: ignore
        
        # 创建控制栏
        self._create_control_bar()
        from core.VitaLoom.viewports.sr_gpu_canvas import create_sr_canvas_class

        canvas_cls = create_sr_canvas_class(type(self))
        self._canvas = canvas_cls(self)
        self._main_layout.addWidget(self._canvas, stretch=1)
        try:
            self.editor_context.event_bus.subscribe(
                "simulation_speed_changed", self._on_transport_speed
            )
        except Exception as e:
            logger.debug("订阅 simulation_speed_changed 失败: %s", e)
        
        # 连接编辑器上下文信号
        self.editor_context.mode_changed.connect(self._on_mode_changed)
        try:
            self.editor_context.project_changed.connect(self._on_external_scene_context_changed)
        except Exception as e:
            logger.debug("订阅 project_changed 失败: %s", e)
        try:
            self.editor_context.event_bus.subscribe("scene_loaded", self._on_external_scene_context_changed)
            self.editor_context.event_bus.subscribe("project_opened", self._on_external_scene_context_changed)
        except Exception as e:
            logger.debug("订阅 scene/project 事件失败: %s", e)
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            get_scene_manager().scene_loaded.connect(self._on_external_scene_context_changed)
        except Exception as e:
            logger.debug("订阅 SceneManager.scene_loaded 失败: %s", e)
        # Host composition publishes this Adapter after assigning its context.

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _create_control_bar(self):
        """轻量 HUD：仅状态与倍速（播放/暂停/停止统一由顶部工具栏驱动）。"""
        self.control_bar = QWidget(self)
        self.control_bar.setObjectName("gameViewportHud")
        self.control_bar.setMaximumHeight(40)
        control_layout = QHBoxLayout(self.control_bar)
        control_layout.setContentsMargins(10, 4, 10, 4)
        control_layout.setSpacing(8)

        self._sr_hud_hint = QLabel(
            self._t("game_viewport.control.hint", "使用顶部工具栏 ▶ 运行 控制模拟")
        )
        self._sr_hud_hint.setObjectName("gameViewportHudHint")
        control_layout.addWidget(self._sr_hud_hint)

        self._sr_hud_label = QLabel("")
        self._sr_hud_label.setObjectName("gameViewportHudStatus")
        self._sr_hud_label.setVisible(False)
        self._sr_hud_label.setMinimumWidth(280)
        self._sr_hud_label.setMaximumWidth(720)
        self._sr_hud_label.setWordWrap(True)
        control_layout.addWidget(self._sr_hud_label)

        control_layout.addStretch()

        speed_label = QLabel(self._t("game_viewport.control.speed", "倍速"))
        speed_label.setObjectName("gameViewportHudLabel")
        control_layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setObjectName("gameViewportSpeedSlider")
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(100)
        self.speed_slider.setMinimumWidth(120)
        self.speed_slider.setMaximumWidth(160)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)  # type: ignore
        control_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel(self._t("game_viewport.control.speed_value", "{speed:.1f}x").format(speed=1.0))
        self.speed_label.setObjectName("gameViewportSpeedValue")
        self.speed_label.setMinimumWidth(44)
        control_layout.addWidget(self.speed_label)

        self._main_layout.addWidget(self.control_bar)

    def _copy_proc_seed_to_clipboard(self) -> None:
        from PyQt6.QtWidgets import QApplication

        seed = int(getattr(self, "_sr_proc_seed", 0))
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(str(seed))

    def _sr_input_press(self, key: str) -> None:
        from core.VitaLoom.viewports.sr_input_state import normalize_sr_key

        normalized = normalize_sr_key(key)
        if self._enqueue_worldbridge_input("key_down", {"key": normalized}) is None:
            return
        self._sr_input.press(key)
        if normalize_sr_key(key) == "W":
            self._trigger_manual_war_from_key()

    def _sr_input_release(self, key: str) -> None:
        from core.VitaLoom.viewports.sr_input_state import normalize_sr_key

        normalized = normalize_sr_key(key)
        if self._enqueue_worldbridge_input("key_up", {"key": normalized}) is None:
            return
        self._sr_input.release(key)

    def _enqueue_worldbridge_input(
        self,
        kind: str,
        payload: Mapping[str, Any],
        *,
        event_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Enqueue one canonical event; retain a detached backpressure receipt."""
        from core.Lotucosm.runtime.world_bridge_input_sequence import (
            WorldBridgeInputBackpressureError,
        )

        self._worldbridge_last_input_backpressure = None
        try:
            return self._worldbridge_input_sequence.append(
                kind,
                payload,
                event_id=event_id,
            )
        except WorldBridgeInputBackpressureError as exc:
            self._worldbridge_last_input_backpressure = copy.deepcopy(exc.receipt)
            return None

    def _sr_input_clear(self, *, lifecycle_action: str = "reset") -> None:
        """Clear both lane-local input and the current PS handoff batch.

        The input sequence owns the pause/reset epoch.  Lifecycle callers pass
        their actual action so a pause, resume, and new runtime cannot be
        conflated as an implicit generic reset.
        """
        self._sr_input.clear()
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None:
            authority.reset(lifecycle_action=lifecycle_action)
        else:
            self._worldbridge_input_sequence.lifecycle(lifecycle_action)
        self._worldbridge_last_tick_receipt = None
        self._worldbridge_input_events_last_tick = []
        pond = getattr(self, "_unified_pond", None)
        clear_pond_inputs = getattr(pond, "apply_worldbridge_input_events", None)
        if callable(clear_pond_inputs):
            clear_pond_inputs([])

    def capture_worldbridge_input_events(self) -> list[dict[str, Any]]:
        """Return and consume canonical events at the SR snapshot boundary."""
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None:
            events = authority.consume_inputs()
        else:
            events = self._worldbridge_input_sequence.consume()
        self._worldbridge_input_events_last_tick = events
        return events

    def capture_worldbridge_shared_state_envelope(
        self,
        delta_time: float,
        *,
        lifecycle_action: str = "tick",
    ) -> dict[str, Any]:
        """Capture one ordered, digest-sealed SR/PS observation envelope.

        This is a quarantine-only transport artifact.  It binds the events
        consumed for the current SR snapshot to both lane clocks and the
        current bridge links, but it never restores live state or admits replay.
        """
        from core.Lotucosm.runtime.world_bridge import capture_bridge_identity_links
        from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
            build_worldbridge_shared_state_envelope,
        )

        pond = getattr(self, "_unified_pond", None)
        sr_revision = 0
        epoch = getattr(self, "_sr_runtime_epoch", None)
        if epoch is not None:
            revision_probe = self.query_sr_runtime_entity_snapshot(
                {
                    "track": "sr_play",
                    "runtime_epoch": epoch,
                    "scene_path": getattr(self, "_sr_runtime_scene_path", ""),
                    "entity_id": "__missing__",
                }
            )
            sr_revision = int(revision_probe.get("revision", 0) or 0)
        ps_tick = int(getattr(pond, "time", 0) or 0) if pond is not None else 0
        ps_time = float(getattr(pond, "simulation_time", 0.0) or 0.0) if pond is not None else 0.0
        randomness_context = getattr(
            self, "_worldbridge_opt_in_deterministic_randomness_context", None
        )
        randomness_snapshot = (
            randomness_context.snapshot() if randomness_context is not None else None
        )
        next_sequence = int(
            getattr(self, "_worldbridge_shared_state_sequence", 0)
        ) + 1
        envelope = build_worldbridge_shared_state_envelope(
            envelope_id=f"viewport-shared-{next_sequence}",
            capture_epoch=next_sequence,
            sequence=next_sequence - 1,
            input_events=[
                {
                    "event_id": event["event_id"],
                    "kind": event["kind"],
                    "payload": {
                        "canonical_sequence": event["sequence"],
                        "pause_reset_epoch": event["pause_reset_epoch"],
                        "event_digest": event["event_digest"],
                        "data": event["payload"],
                    },
                }
                for event in getattr(self, "_worldbridge_input_events_last_tick", [])
            ],
            pause_reset_epoch=self._worldbridge_input_sequence.pause_reset_epoch,
            clock_provenance={
                "sr": {
                    "domain": "sr",
                    "tick": sr_revision,
                    "delta": float(delta_time),
                    "time": float(getattr(self, "_scene_runtime_time", 0.0)),
                    "source": "viewport_snapshot",
                },
                "ps": {
                    "domain": "ps",
                    "tick": ps_tick,
                    "delta": float(delta_time),
                    "time": ps_time,
                    "source": "pond_update",
                },
            },
            bridge_identity_links=capture_bridge_identity_links(
                getattr(self, "scene_runtime_entities", [])
            ),
            rng_context_snapshot=randomness_snapshot,
            lifecycle_action=lifecycle_action,
            playing=bool(getattr(self, "is_playing", False)),
            paused=bool(getattr(self, "is_paused", False)),
        )
        self._worldbridge_shared_state_sequence = next_sequence
        self._worldbridge_last_shared_state_envelope = envelope
        return envelope

    def consume_worldbridge_shared_state_envelope(
        self, envelope: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Accept one detached envelope without applying it to either lane."""
        from core.Lotucosm.runtime.world_bridge_shared_state_transport import (
            WorldBridgeSharedStateReceiver,
        )

        receiver = getattr(self, "_worldbridge_shared_state_receiver", None)
        if receiver is None:
            receiver = WorldBridgeSharedStateReceiver()
            self._worldbridge_shared_state_receiver = receiver
        accepted = receiver.accept(envelope)
        self._worldbridge_last_shared_state_receipt = accepted
        return accepted

    def _reset_worldbridge_shared_state_transport(self) -> None:
        """Start a new transport lifetime with no cross-scene continuity."""
        self._worldbridge_shared_state_sequence = 0
        self._worldbridge_shared_state_receiver = None
        self._worldbridge_last_shared_state_envelope = None
        self._worldbridge_last_shared_state_receipt = None

    def capture_sr_input_state(self) -> dict[str, Any]:
        """Capture the active SR-local input buffer without consuming edges."""
        if not self._using_scene_runtime or self._sr_runtime_epoch is None:
            raise RuntimeError("sr_input_capture_requires_active_epoch")
        return self._sr_input.capture_state()

    def restore_sr_input_state(self, state: Mapping[str, Any]) -> None:
        """Restore an SR-local input buffer; shared input replay remains disabled."""
        if not self._using_scene_runtime or self._sr_runtime_epoch is None:
            raise RuntimeError("sr_input_restore_requires_active_epoch")
        self._sr_input.restore_state(state)

    def _configure_sr_runtime_randomness(self, scene_data: object) -> SrRuntimeRandomnessConfig:
        """Create one explicit SR-local RNG owner for a loaded scene runtime.

        This never reseeds process-global Python/NumPy RNGs and intentionally
        does not establish cross-lane bridge randomness authority.
        """
        config = resolve_sr_runtime_randomness_config(scene_data)
        self._sr_runtime_randomness_config = config
        self._sr_runtime_rng = create_sr_runtime_randomness_rng(config)
        return config

    def _sr_input_snapshot(self) -> SrInputSnapshot:
        if self.is_playing and not self.is_paused:
            self.capture_worldbridge_input_events()
            return self._sr_input.snapshot()
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None:
            authority.clear_active_tick()
        self._worldbridge_input_events_last_tick = []
        return SrInputState.empty_snapshot()

    def _canvas_size(self) -> tuple[int, int]:
        if hasattr(self, "_canvas"):
            return max(1, self._canvas.width()), max(1, self._canvas.height())
        return max(1, self.width()), max(1, self.height())

    def _scene_bounds(self) -> tuple[float, float]:
        size = getattr(self, "_sr_scene_size", None)
        if isinstance(size, (list, tuple)) and len(size) >= 2:
            return max(1.0, float(size[0])), max(1.0, float(size[1]))
        w, h = self._canvas_size()
        return float(w), float(h)

    def _widget_to_scene(self, local_x: float, local_y: float) -> tuple[float, float]:
        cw, ch = self._canvas_size()
        sw, sh = self._scene_bounds()
        if cw <= 0 or ch <= 0:
            return local_x, local_y
        return local_x * (sw / float(cw)), local_y * (sh / float(ch))

    def _notify_transport(self) -> None:
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.sync_from_viewport(
                is_playing=self.is_playing,
                is_paused=self.is_paused,
                speed=self.simulation_speed,
            )

    def _on_transport_speed(self, speed: Any) -> None:
        try:
            self._apply_speed(float(speed))
        except (TypeError, ValueError):
            pass

    def _on_mode_changed(self, mode):
        """编辑器模式变化处理"""
        if mode == EditorMode.SIMULATE or mode == EditorMode.PLAY:
            if not self.is_playing:
                self._start_simulation()
        elif mode == EditorMode.PAUSE:
            if self.is_playing and not self.is_paused:
                self._pause_simulation()
        else:
            if self.is_playing:
                self._stop_simulation()

    def _toggle_play_pause(self):
        """切换播放/暂停（供工具栏事件链间接使用，视口内无重复按钮）。"""
        if not self.is_playing:
            self._start_simulation()
        elif self.is_paused:
            self._resume_simulation()
        else:
            self._pause_simulation()

    def _sync_hud_chrome(self) -> None:
        """同步 HUD 提示/状态条可见性。"""
        playing = bool(self.is_playing)
        if hasattr(self, "_sr_hud_hint"):
            self._sr_hud_hint.setVisible(not playing)
        if hasattr(self, "_sr_hud_label") and not playing:
            self._sr_hud_label.setVisible(False)

    # === SR: 生命周期与重载判定 ================================================

    def _runtime_context_key(self) -> tuple[Optional[str], Optional[str]]:
        """返回 (current_project_path, current_scene_path) 供重载判定。"""
        proj = getattr(self.editor_context, "current_project_path", None)
        scene_path: Optional[str] = None
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            scene_path = get_scene_manager().get_current_scene_path()
        except Exception as e:
            logger.debug("读取当前场景路径失败: %s", e)
        return (proj if isinstance(proj, str) else None, scene_path)

    def _scene_runtime_needs_reload(self) -> bool:
        """是否必须用当前 SceneManager 场景重建内存运行时。

        排错: 换项目后仍见旧 t/种群 → dirty 未置位或 resume 未走本判定；
        Simulation 回退后 path 已清空且 dirty=True，下次会重载 SR。
        """
        if getattr(self, "_sr_runtime_dirty", True):
            return True
        return self._runtime_context_key() != (
            getattr(self, "_sr_runtime_project_path", None),
            getattr(self, "_sr_runtime_scene_path", None),
        )

    # === SR: 会话摘要（logs/sr_sessions）====================================

    def _reset_sr_session_metadata(self, *, keep_last_replay: bool = True) -> None:
        """清除本局 stamp 与开局快照。

        职责: 丢弃 _sr_session_stamp / _sr_session_scene_name 等。
        时机: stop、discard、换场景未播放时。
        不变量: keep_last_replay=True 时保留 _sr_last_session_md_path 供暂停 HUD。
        排错: 复盘路径陈旧 → 新局 _start 会写新 stamp；勿在 discard 清 last_md 除非刻意。
        """
        self._sr_session_stamp = None
        self._sr_session_scene_name = None
        self._sr_session_project_path = None
        if not keep_last_replay:
            self._sr_last_session_md_path = None
            self._sr_last_session_end_reason = None

    def _capture_sr_session_context(self) -> None:
        """开局时快照场景/项目，避免换场景后写盘张冠李戴。

        职责: 写入 _sr_session_scene_name、_sr_session_project_path。
        时机: _start_simulation / _resume_simulation 重载成功后。
        排错: 摘要 scene_name 与统计不符 → _write 须用本快照而非 get_scene_data() 当前值。
        """
        proj, scene_path = self._runtime_context_key()
        self._sr_session_project_path = proj
        self._sr_session_scene_name = None
        if scene_path:
            try:
                self._sr_session_scene_name = Path(scene_path).stem
            except Exception:
                self._sr_session_scene_name = scene_path
        try:
            from core.VitaLoom.scene.scene_manager import get_scene_manager

            sd = get_scene_manager().get_scene_data() or {}
            name = str(sd.get("name", "")).strip()
            if name:
                self._sr_session_scene_name = name
        except Exception as e:
            logger.debug("读取场景名快照失败: %s", e)

    def _sr_component_connection_count(self, child_id: str) -> int:
        """Count distinct published SR topology edges incident to one attachment."""
        seen: set[tuple[str, str, str, str]] = set()
        for group, edges in (
            ("connection", self._sr_connection_edges),
            ("signal", self._sr_signal_edges),
        ):
            for edge in edges or []:
                if not isinstance(edge, dict):
                    continue
                start = str(edge.get("start", ""))
                end = str(edge.get("end", ""))
                if child_id not in (start, end):
                    continue
                edge_kind = str(
                    edge.get("type") or edge.get("channel") or edge.get("kind") or ""
                )
                seen.add((group, start, end, edge_kind))
        return len(seen)

    def _build_sr_component_facts(self, parent_id: str) -> list[dict[str, Any]]:
        """Project attachment-proven SR entities without claiming PS equivalence."""
        entities = {
            str(getattr(entity, "id", "")): entity
            for entity in self.scene_runtime_entities
        }
        facts: list[dict[str, Any]] = []
        for child_id, attachment in sorted(self._sr_membrane_attach.items()):
            if not isinstance(attachment, (list, tuple)) or len(attachment) != 3:
                continue
            attached_parent, dx, dy = attachment
            if str(attached_parent) != parent_id:
                continue
            child = entities.get(str(child_id))
            if child is None:
                continue
            component_type = str(getattr(child, "entity_type", "")).strip()
            if component_type not in {"sensor", "actuator"}:
                continue
            offset_x = _sr_snapshot_number(dx)
            offset_y = _sr_snapshot_number(dy)
            if offset_x is None or offset_y is None:
                continue
            facts.append(
                {
                    "source": "sr_attached_runtime_entity",
                    "identity_relation": (
                        "attached_projection_not_ps_component_equivalence"
                    ),
                    "component_id": str(child_id),
                    "component_type": component_type,
                    "location": "attached",
                    "attach_point": [offset_x, offset_y],
                    "connection_count": self._sr_component_connection_count(
                        str(child_id)
                    ),
                    "inspectable_properties": {},
                    "component_fields": {},
                }
            )
        return facts

    def _build_sr_entity_snapshot(self, entity: object) -> dict[str, Any]:
        """Project one live SR entity through a strict read-only JSON whitelist."""
        entity_id = str(getattr(entity, "id", ""))
        position = getattr(entity, "position", ())
        velocity = getattr(entity, "velocity", ())

        def pair(raw: object) -> list[float | None]:
            if not isinstance(raw, (list, tuple)) or len(raw) < 2:
                return [None, None]
            return [_sr_snapshot_number(raw[0]), _sr_snapshot_number(raw[1])]

        try:
            generation = int(getattr(entity, "generation", 0))
        except (TypeError, ValueError):
            generation = 0
        entity_type = str(getattr(entity, "entity_type", ""))
        snapshot = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "serialized_scene_counterpart": entity_id
            in self._sr_serialized_scene_entity_ids,
            "position": pair(position),
            "velocity": pair(velocity),
            "radius": _sr_snapshot_number(getattr(entity, "radius", None)),
            "energy": _sr_snapshot_number(getattr(entity, "energy", None)),
            "health": _sr_snapshot_number(getattr(entity, "health", None)),
            "max_energy": _sr_snapshot_number(
                getattr(entity, "max_energy", None)
            ),
            "max_health": _sr_snapshot_number(
                getattr(entity, "max_health", None)
            ),
            "generation": generation,
            "developmental_stage": int(
                getattr(entity, "developmental_stage", 0)
            ),
            "social_learning_enabled": bool(
                getattr(entity, "social_learning_enabled", True)
            ),
            "pinned": bool(getattr(entity, "pinned", False)),
            "membrane_locked": bool(getattr(entity, "membrane_locked", False)),
            "active": bool(getattr(entity, "active", True)),
            "visible": bool(getattr(entity, "visible", True)),
        }
        acceleration = getattr(entity, "acceleration", None)
        if isinstance(acceleration, (list, tuple)) and len(acceleration) == 2:
            snapshot["acceleration"] = pair(acceleration)
        render_identity = _sr_snapshot_render_identity(getattr(entity, "sr_visual", None))
        if render_identity is not None:
            snapshot["render_identity"] = render_identity
        raw_memory_genes = getattr(entity, "sr_memory_genes", None)
        if isinstance(raw_memory_genes, list):
            from core.Lotucosm.sr_memory_gene_bridge import memory_genes_to_dicts

            snapshot["memory_genes"] = memory_genes_to_dicts(raw_memory_genes)
        if entity_type == "organism":
            snapshot["component_facts"] = self._build_sr_component_facts(entity_id)
        return snapshot

    def _publish_sr_runtime_snapshots(self) -> int | None:
        """Replace the active authority snapshot from the current SR entity set."""
        epoch = self._sr_runtime_epoch
        if epoch is None:
            return None
        snapshots = [
            self._build_sr_entity_snapshot(entity)
            for entity in self.scene_runtime_entities
        ]
        try:
            return self._sr_runtime_snapshot_authority.publish(epoch, snapshots)
        except (RuntimeError, TypeError, ValueError) as exc:
            logger.warning("发布 SR 运行时只读快照失败: %s", exc)
            return None

    def _next_sr_entity_id(self, fallback: str) -> str:
        """Allocate one missing runtime entity ID through the viewport owner."""
        source = getattr(self, "_sr_identity_source", None)
        if source is None:
            return str(fallback)
        next_identity = getattr(source, "next", None)
        if not callable(next_identity):
            raise RuntimeError("SR identity source allocator unavailable")
        return str(next_identity("entity"))

    def _begin_sr_snapshot_lifetime(self) -> str | None:
        """Begin one epoch for the loaded .pond runtime and publish revision one."""
        self._end_sr_snapshot_lifetime()
        if not self._using_scene_runtime:
            return None
        scene_path = self._sr_runtime_scene_path
        if not isinstance(scene_path, str) or not scene_path.strip():
            return None
        # Script evidence observed while loading the scene has no active SR
        # epoch and cannot be restored as evidence for this runtime lifetime.
        # Reset the complete corpus together so its cross-record invariants
        # cannot be broken by retaining only one evidence category.
        self._sr_script_entropy_audits = []
        self._sr_script_entropy_receipts = []
        self._sr_script_failure_receipts = []
        self._sr_script_trust_denials = []
        self._sr_script_declared_paths = []
        epoch = self._sr_runtime_snapshot_authority.begin(scene_path)
        self._sr_runtime_epoch = epoch
        self._publish_sr_runtime_snapshots()
        return epoch

    def _end_sr_snapshot_lifetime(self) -> None:
        """End only this viewport's active SR authority epoch."""
        epoch = self._sr_runtime_epoch
        if epoch is not None:
            self._sr_runtime_snapshot_authority.end(epoch)
        self._sr_runtime_epoch = None

    def query_sr_runtime_entity_snapshot(self, identity: object) -> dict[str, Any]:
        """Read one copy-isolated SR snapshot without exposing live registries."""
        return self._sr_runtime_snapshot_authority.query(identity)

    def restore_sr_runtime_snapshot_slice(
        self,
        snapshots: list[dict[str, Any]],
        *,
        scene_time: float | None = None,
    ) -> float:
        """Opt-in restore of the producer's small, in-place SR state slice.

        The adapter is deliberately separate from the read-only authority:
        it restores existing entity identities only and does not recreate
        scripts, topology, RNG, lifecycle, or bridge state.
        """
        from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
            restore_sr_runtime_snapshot_slice,
        )

        if not self._using_scene_runtime or self._sr_runtime_epoch is None:
            raise RuntimeError("sr_runtime_restore_requires_active_epoch")
        if not isinstance(snapshots, list):
            raise TypeError("snapshots must be a list")
        next_time = float(self._scene_runtime_time if scene_time is None else scene_time)
        restored_time = restore_sr_runtime_snapshot_slice(
            self.scene_runtime_entities,
            snapshots,
            scene_time=next_time,
        )
        self._scene_runtime_time = restored_time
        self._publish_sr_runtime_snapshots()
        return restored_time

    SR_TOPOLOGY_OWNER_FIELDS = (
        "structural_edges",
        "connection_edges",
        "signal_edges",
        "scene_runtime_edges",
        "scene_runtime_neighbor_ids",
        "membrane_attach",
        "membrane_template",
        "spawn_seq",
    )

    def capture_sr_topology_owner_state(self) -> dict[str, Any]:
        """Capture the SR topology / membrane component owner graph.

        These attributes are one authority surface: edges, membrane
        attachments, membrane templates and the spawn sequence are only
        meaningful together, so snapshot and restore treat them as a single
        owner and never as independent read-only projections.
        """
        return {
            "structural_edges": copy.deepcopy(self._sr_structural_edges),
            "connection_edges": copy.deepcopy(self._sr_connection_edges),
            "signal_edges": copy.deepcopy(self._sr_signal_edges),
            "scene_runtime_edges": copy.deepcopy(self._scene_runtime_edges),
            "scene_runtime_neighbor_ids": {
                str(key): sorted(str(item) for item in values)
                for key, values in self._scene_runtime_neighbor_ids.items()
            },
            "membrane_attach": copy.deepcopy(self._sr_membrane_attach),
            "membrane_template": copy.deepcopy(self._sr_membrane_template),
            "spawn_seq": int(self._sr_spawn_seq),
        }

    def restore_sr_topology_owner_state(self, state: Mapping[str, Any]) -> None:
        """Write a captured SR topology owner state back onto a live viewport.

        The caller owns transactionality: this method writes the whole owner
        graph in one pass and rebuilds the derived spring links.  Envelope
        restore captures a pre-image before calling it so an injected
        failure can be compensated rather than leaving a half-applied graph.
        """
        if not isinstance(state, Mapping) or set(state) != set(self.SR_TOPOLOGY_OWNER_FIELDS):
            raise ValueError("sr_topology_owner_state_fields_invalid")
        self._sr_structural_edges = copy.deepcopy(state["structural_edges"])
        self._sr_connection_edges = copy.deepcopy(state["connection_edges"])
        self._sr_signal_edges = copy.deepcopy(state["signal_edges"])
        self._scene_runtime_edges = [
            tuple(edge) for edge in copy.deepcopy(state["scene_runtime_edges"])
        ]
        self._scene_runtime_neighbor_ids = {
            str(key): frozenset(str(item) for item in values)
            for key, values in state["scene_runtime_neighbor_ids"].items()
        }
        self._sr_membrane_attach = copy.deepcopy(state["membrane_attach"])
        self._sr_membrane_template = copy.deepcopy(state["membrane_template"])
        self._sr_spawn_seq = int(state["spawn_seq"])
        self._rebuild_sr_spring_links()

    def capture_sr_runtime_restore_envelope(self) -> dict[str, Any]:
        """Capture an epoch-bound, digestable SR state slice for opt-in restore."""
        from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
            SCHEMA_VERSION,
            snapshot_restore_digest,
        )

        if not self._using_scene_runtime or self._sr_runtime_epoch is None:
            raise RuntimeError("sr_runtime_capture_requires_active_epoch")
        snapshots = [
            self._build_sr_entity_snapshot(entity)
            for entity in self.scene_runtime_entities
        ]
        envelope: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "kind": "sr_runtime_restore_slice",
            "runtime_epoch": self._sr_runtime_epoch,
            "scene_path": self._sr_runtime_scene_path,
            "revision": self.query_sr_runtime_entity_snapshot(
                {
                    "track": "sr_play",
                    "runtime_epoch": self._sr_runtime_epoch,
                    "scene_path": self._sr_runtime_scene_path,
                    "entity_id": "__missing__",
                }
            ).get("revision", 0),
            "scene_time": float(self._scene_runtime_time),
            "snapshots": snapshots,
            # Topology is an SR owner state, not a cross-lane authority. Keep
            # it in the portable envelope so rollback does not silently lose
            # membrane edges when the mutable entity slice is restored.
            "topology": self.capture_sr_topology_owner_state(),
            "transient": {
                "biosphere_load": float(self._sr_biosphere_load),
                "biosphere_prev_load": float(self._sr_biosphere_prev_load),
                "emissions_prev": {
                    str(key): float(value)
                    for key, value in self._scene_runtime_emissions_prev.items()
                },
                "channel_out_prev": {
                    str(getattr(entity, "id", "")): dict(
                        getattr(entity, "sr_channel_out_prev", {}) or {}
                    )
                    for entity in self.scene_runtime_entities
                },
                "visual_phases": {
                    str(getattr(entity, "id", "")): {
                        "signal": float(getattr(entity, "_sr_vis_signal_phase", 0.0)),
                        "membrane": float(getattr(entity, "_sr_vis_membrane_phase", 0.0)),
                    }
                    for entity in self.scene_runtime_entities
                    if hasattr(entity, "_sr_vis_signal_phase")
                    or hasattr(entity, "_sr_vis_membrane_phase")
                },
            },
        }
        envelope["digest"] = snapshot_restore_digest(envelope)
        return envelope

    def restore_sr_runtime_restore_envelope(self, envelope: Mapping[str, Any]) -> float:
        """Restore an epoch-bound SR slice after validating its digest/context."""
        from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
            SCHEMA_VERSION,
            snapshot_restore_digest,
        )

        if not isinstance(envelope, Mapping):
            raise TypeError("restore envelope must be a mapping")
        candidate = dict(envelope)
        digest = candidate.pop("digest", None)
        if not isinstance(digest, str) or digest != snapshot_restore_digest(candidate):
            raise ValueError("sr_runtime_restore_digest_mismatch")
        if candidate.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("sr_runtime_restore_schema_mismatch")
        if candidate.get("kind") != "sr_runtime_restore_slice":
            raise ValueError("sr_runtime_restore_kind_mismatch")
        if candidate.get("runtime_epoch") != self._sr_runtime_epoch:
            raise RuntimeError("sr_runtime_restore_epoch_mismatch")
        if candidate.get("scene_path") != self._sr_runtime_scene_path:
            raise RuntimeError("sr_runtime_restore_scene_mismatch")
        snapshots = candidate.get("snapshots")
        if not isinstance(snapshots, list):
            raise TypeError("restore envelope snapshots must be a list")
        topology = candidate.get("topology")
        if topology is not None:
            if not isinstance(topology, Mapping):
                raise ValueError("sr_runtime_restore_topology_invalid")
            required_topology = {
                "structural_edges",
                "connection_edges",
                "signal_edges",
                "scene_runtime_edges",
                "scene_runtime_neighbor_ids",
                "membrane_attach",
                "membrane_template",
                "spawn_seq",
            }
            if set(topology) != required_topology:
                raise ValueError("sr_runtime_restore_topology_fields_invalid")
            if any(not isinstance(topology.get(field), list) for field in (
                "structural_edges", "connection_edges", "signal_edges", "scene_runtime_edges"
            )):
                raise ValueError("sr_runtime_restore_topology_edges_invalid")
            if not isinstance(topology.get("scene_runtime_neighbor_ids"), Mapping):
                raise ValueError("sr_runtime_restore_topology_neighbors_invalid")
            if not isinstance(topology.get("membrane_attach"), Mapping) or not isinstance(
                topology.get("membrane_template"), Mapping
            ):
                raise ValueError("sr_runtime_restore_topology_membrane_invalid")
            spawn_seq = topology.get("spawn_seq")
            if isinstance(spawn_seq, bool) or not isinstance(spawn_seq, int) or spawn_seq < 0:
                raise ValueError("sr_runtime_restore_topology_spawn_seq_invalid")

        # Validate the transient block before the first live mutation.  A
        # malformed envelope must be rejected without partially restoring the
        # entity slice, the topology owner, or the transient counters.
        transient = candidate.get("transient", {})
        if not isinstance(transient, Mapping):
            raise ValueError("sr_runtime_restore_transient_invalid")
        emissions = transient.get("emissions_prev", {})
        if not isinstance(emissions, Mapping):
            raise ValueError("sr_runtime_restore_emissions_invalid")
        channel_prev = transient.get("channel_out_prev", {})
        if not isinstance(channel_prev, Mapping):
            raise ValueError("sr_runtime_restore_channel_state_invalid")
        visual_phases = transient.get("visual_phases", {})
        if not isinstance(visual_phases, Mapping):
            raise ValueError("sr_runtime_restore_visual_state_invalid")
        by_id = {
            str(getattr(entity, "id", "")): entity
            for entity in self.scene_runtime_entities
        }
        for value in emissions.values():
            try:
                float(value)
            except (TypeError, ValueError):
                raise ValueError("sr_runtime_restore_emissions_invalid") from None
        for value in channel_prev.values():
            if not isinstance(value, Mapping):
                raise ValueError("sr_runtime_restore_channel_state_invalid")
        for entity_id, value in visual_phases.items():
            if by_id.get(str(entity_id)) is None or not isinstance(value, Mapping):
                raise ValueError("sr_runtime_restore_visual_state_invalid")
        for field in (
            "biosphere_load", "biosphere_prev_load"
        ):
            if field in transient:
                try:
                    float(transient[field])
                except (TypeError, ValueError):
                    raise ValueError("sr_runtime_restore_transient_invalid") from None

        from core.VitaLoom.simulation.sr_runtime_snapshot_restore import (
            SrRuntimeSnapshotRestoreError,
            _apply_entity_state as _apply_sr_entity_state,
            _capture_entity_state as _capture_sr_entity_state,
        )

        # Capture the topology, transient and entity owners before the first
        # live write so any injected failure can be compensated.  The
        # membrane graph is a single SR owner surface: an unrolled failure
        # here must not leave half of the checkpoint applied.
        topology_originals = self.capture_sr_topology_owner_state()
        entity_originals = {
            entity_id: _capture_sr_entity_state(entity)
            for entity_id, entity in by_id.items()
        }
        channel_originals = {
            entity_id: copy.deepcopy(getattr(entity, "sr_channel_out_prev", {}) or {})
            for entity_id, entity in by_id.items()
        }
        phase_originals = {
            entity_id: {
                "signal": float(getattr(entity, "_sr_vis_signal_phase", 0.0)),
                "membrane": float(getattr(entity, "_sr_vis_membrane_phase", 0.0)),
            }
            for entity_id, entity in by_id.items()
        }
        scene_time_original = float(self._scene_runtime_time)
        biosphere_original = (
            float(self._sr_biosphere_load),
            float(self._sr_biosphere_prev_load),
        )
        emissions_original = copy.deepcopy(self._scene_runtime_emissions_prev)
        authority = self._sr_runtime_snapshot_authority
        revision_original = int(authority._revision)

        def _restore_topology_owner() -> None:
            self.restore_sr_topology_owner_state(topology_originals)

        slice_applied = False
        try:
            restored_time = self.restore_sr_runtime_snapshot_slice(
                snapshots,
                scene_time=candidate.get("scene_time"),
            )
            slice_applied = True
            if topology is not None:
                self.restore_sr_topology_owner_state(topology)
            self._sr_biosphere_load = float(transient.get("biosphere_load", self._sr_biosphere_load))
            self._sr_biosphere_prev_load = float(transient.get("biosphere_prev_load", self._sr_biosphere_prev_load))
            self._scene_runtime_emissions_prev = {
                str(key): float(value) for key, value in emissions.items()
            }
            for entity_id, entity in by_id.items():
                entity.sr_channel_out_prev = dict(channel_prev.get(entity_id, {}))
            for entity_id, value in visual_phases.items():
                entity = by_id[str(entity_id)]
                entity._sr_vis_signal_phase = float(value.get("signal", 0.0))
                entity._sr_vis_membrane_phase = float(value.get("membrane", 0.0))
            # publish() advances the authority revision; restore must put the
            # observable cursor back to the checkpoint's exact revision.
            authority._revision = int(candidate.get("revision", authority._revision))
        except Exception as exc:
            rollback_errors: list[str] = []
            # restore_sr_runtime_snapshot_slice already compensates the
            # entity slice it owns; only re-apply it when this envelope
            # layer moved the entities past that point.
            try:
                if slice_applied:
                    for entity_id, entity in by_id.items():
                        _apply_sr_entity_state(entity, entity_originals[entity_id])
                if slice_applied:
                    for entity_id, entity in by_id.items():
                        entity.sr_channel_out_prev = copy.deepcopy(channel_originals[entity_id])
                if slice_applied:
                    for entity_id, entity in by_id.items():
                        phase = phase_originals[entity_id]
                        entity._sr_vis_signal_phase = phase["signal"]
                        entity._sr_vis_membrane_phase = phase["membrane"]
            except Exception as rollback_exc:  # pragma: no cover - defensive path
                rollback_errors.append(str(rollback_exc))
            try:
                _restore_topology_owner()
            except Exception as rollback_exc:  # pragma: no cover - defensive path
                rollback_errors.append(str(rollback_exc))
            self._scene_runtime_time = scene_time_original
            self._sr_biosphere_load, self._sr_biosphere_prev_load = biosphere_original
            self._scene_runtime_emissions_prev = emissions_original
            try:
                self._publish_sr_runtime_snapshots()
            except Exception as rollback_exc:  # pragma: no cover - defensive path
                rollback_errors.append(str(rollback_exc))
            authority._revision = revision_original
            detail = "; rollback failed: " + ", ".join(rollback_errors) if rollback_errors else ""
            raise SrRuntimeSnapshotRestoreError(
                f"sr runtime restore envelope failed: {exc}{detail}"
            ) from exc
        return restored_time


    def resolve_selected_sr_runtime_entity(
        self,
        *,
        explicit_identity: object | None = None,
        selection_scene_path: str | None = None,
    ) -> dict[str, Any]:
        """Correlate current editor selection with this viewport's active SR epoch."""
        from core.VitaLoom.simulation.sr_editor_selection_adapter import (
            project_editor_selection,
        )
        from core.VitaLoom.simulation.sr_selected_identity import (
            SrSelectedIdentityCorrelation,
        )

        scene_path = selection_scene_path
        if scene_path is None:
            try:
                from core.VitaLoom.scene.scene_manager import get_scene_manager

                scene_path = get_scene_manager().get_current_scene_path()
            except Exception:
                scene_path = None
        selection_snapshot = project_editor_selection(
            self.editor_context.selected_objects,
            scene_path,
        )
        runtime_context = {
            "track": "sr_play",
            "runtime_epoch": self._sr_runtime_epoch,
            "scene_path": self._sr_runtime_scene_path,
        }
        return SrSelectedIdentityCorrelation().resolve(
            selection_snapshot,
            runtime_context,
            self.query_sr_runtime_entity_snapshot,
            explicit_identity=explicit_identity,
        )

    def _discard_scene_runtime_state(self) -> None:
        """丢弃内存中的 SR 运行时（不写入局摘要）。

        职责: 清空实体、拓扑、目标、HUD；置 _sr_runtime_dirty 语义由调用方负责。
        时机: 未播放时换场景；resume 重载前。
        排错: 与 _stop_simulation(write_session=False) 区别：本方法不写盘、不强制 is_playing=False。
        """
        self._observe_worldbridge_quarantine_lifecycle_disposal(
            "scene_runtime_discard"
        )
        self._end_sr_snapshot_lifetime()
        self._sr_input_clear(lifecycle_action="reset")
        self._configure_sr_runtime_randomness({})
        self._using_scene_runtime = False
        self.scene_runtime_entities = []
        self._sr_script_entropy_audits = []
        self._sr_script_entropy_receipts = []
        self._sr_script_failure_receipts = []
        self._sr_script_trust_denials = []
        self._sr_serialized_scene_entity_ids = set()
        self._scene_runtime_edges = []
        self._scene_runtime_emissions_prev = {}
        self._scene_runtime_neighbor_ids = {}
        self._sr_structural_edges = []
        self._sr_connection_edges = []
        self._sr_spring_links = []
        self._sr_signal_edges = []
        self._sr_membrane_attach = {}
        self._sr_membrane_template = {}
        self._scene_runtime_time = 0.0
        self._unified_pond = None
        self._reset_worldbridge_shared_state_transport()
        self._worldbridge_active_pond_lifetime_token = None
        self._worldbridge_handoff_suspended = False
        self._sr_reproduction_events = 0
        self._sr_biosphere_load = 0.0
        self._sr_biosphere_prev_load = 0.0
        self._sr_pop_peak = 0
        self._sr_play_goals = {}
        self._sr_demo_legend = None
        self._sr_goal_announced = {"survive": False, "peak": False}
        self._sr_victory_banner = None
        self._sr_victory_pause_done = False
        self._sr_victory_notice_done = False
        self._sr_extinction_banner = None
        self._sr_extinction_pause_done = False
        self._sr_banner_kind = None
        self._sr_banner_shown_at = 0.0
        self._sr_banner_title = None
        self._sr_banner_hint = None
        self._sr_play_hint_shown = False
        if hasattr(self, "_sr_hud_label"):
            self._sr_hud_label.clear()
            self._sr_hud_label.setVisible(False)
        self._reset_sr_session_metadata(keep_last_replay=True)

    def _on_external_scene_context_changed(self, *_args: Any) -> None:
        """切换项目或场景后，避免继续用旧实体/旧 HUD 状态。

        订阅: project_changed, scene_loaded, project_opened（event_bus + SceneManager）。
        播放中: _stop_simulation(write_session=False) — SceneManager 已指向新场景，
        此时写 stopped 会把旧 sim_time 记到新 scene_name（历史坑，已禁止写盘）。
        """
        self._sr_runtime_dirty = True
        SrSpriteCatalog.invalidate_cache()
        if self.is_playing:
            logger.info("项目/场景已变更，自动停止模拟以便下次从当前场景重开")
            self._stop_simulation(write_session=False)
        else:
            self._discard_scene_runtime_state()
        self._refresh_entry_hud_hint()

    def _handle_empty_sr_runtime_tick(self, dt: float | None = None) -> None:
        """Advance an empty SR scene without owning session lifecycle.

        The scene-runtime dispatcher owns ticking and outcome resolution.  This
        method remains callable directly for compatibility; direct callers use
        the same speed-derived delta as the timer path.
        """
        if dt is None:
            dt = 0.05 * max(0.2, self.simulation_speed)
        self._scene_runtime_time += dt
        try:
            self._refresh_sr_hud([])
        except Exception as e:
            logger.warning("空运行时 HUD 刷新失败: %s", e)
        self._publish_sr_runtime_snapshots()

    def _prepare_simulation_backend(self) -> bool:
        """按当前项目场景重建运行时或回退内置 Simulation。

        成功加载 .pond 实体: _using_scene_runtime=True，记录 runtime path，dirty=False。
        回退 Simulation: 清空 runtime path，dirty=True（下次 resume 须再试 SR 加载）。
        """
        self.simulation = None
        self._using_scene_runtime = False
        if self._load_scene_runtime_entities():
            self._using_scene_runtime = True
            self._sr_runtime_dirty = False
            return True
        try:
            from builtin.systems.simulation import Simulation

            width = max(self._canvas_size()[0], 800)
            height = max(self._canvas_size()[1], 600)
            self.simulation = Simulation(
                width,
                height,
                randomness_rng=getattr(self, "_sr_runtime_rng", None),
            )
            # 回退路径：勿把 dirty 置 False，否则同 scene_path 下 resume 不会重载 SR
            self._sr_runtime_project_path = None
            self._sr_runtime_scene_path = None
            self._sr_runtime_dirty = True
            return True
        except ImportError as e:
            logger.warning("无法导入 Simulation: %s", e)
            return False
        except Exception as e:
            logger.exception("创建模拟对象失败: %s", e)
            return False

    def _sr_hud_verbose(self) -> bool:
        return os.environ.get("LOTUCOSM_SR_HUD_VERBOSE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )

    def _start_simulation(self):
        """开始模拟：_prepare_simulation_backend → 定时器；SR 时新建 session_stamp 并 _capture_sr_session_context。"""
        if self.is_playing and self.is_paused:
            self._resume_simulation()
            return
        if not self._prepare_simulation_backend():
            return
        from core.VitaLoom.simulation.simulation_coordinator import (
            SimulationLane,
            get_simulation_coordinator,
        )

        coord = get_simulation_coordinator()
        if coord is not None and not coord.register_lane_start(SimulationLane.SR_PLAY):
            logger.warning("SR 播放被协调器拒绝（工程可能禁止与 PS 并行）")
            return
        try:
            # A new SR lifetime must not consume pre-start adapter events.
            self._sr_input_clear(lifecycle_action="start")
            self.is_playing = True
            self.is_paused = False
            if self._using_scene_runtime:
                self._begin_sr_snapshot_lifetime()
            self._reset_worldbridge_shared_state_transport()
            self._sync_hud_chrome()
            
            # 确保速度不为0，避免除零错误
            if self.simulation_speed <= 0:
                self.simulation_speed = 1.0
            
            interval = max(1, int(50 / self.simulation_speed))  # 确保间隔至少为1ms
            self.update_timer.start(interval)
            self.simulation_started.emit()
            self.editor_context.current_mode = EditorMode.PLAY
            self._notify_transport()
            if hasattr(self, "_canvas"):
                self._canvas.setFocus()
            if self._using_scene_runtime:
                try:
                    self._refresh_unified_pond_mode(
                        _current_project_world_config(self.editor_context)
                    )
                except Exception:
                    pass
                self._sr_session_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                self._capture_sr_session_context()
                logger.info(
                    "场景运行时模拟已开始（实体数=%s，SR PVAEC tick）",
                    len(self.scene_runtime_entities),
                )
        except Exception as e:
            logger.exception("启动模拟失败: %s", e)

    def _pause_simulation(self):
        """暂停模拟"""
        self.is_paused = True
        self._sr_input_clear(lifecycle_action="pause")
        self._sync_hud_chrome()
        if self._session_banner_payload():
            self.update_timer.start(33)
        else:
            self.update_timer.stop()
        self.simulation_paused.emit()
        self.editor_context.current_mode = EditorMode.PAUSE
        self._notify_transport()

    def _resume_simulation(self):
        """恢复模拟；若 _scene_runtime_needs_reload 则先 discard+prepare+新 stamp。"""
        if self._scene_runtime_needs_reload():
            logger.info("场景/项目已切换，重新加载运行时后再继续")
            self._discard_scene_runtime_state()
            if not self._prepare_simulation_backend():
                return
            self.is_playing = True
            if self._using_scene_runtime:
                self._begin_sr_snapshot_lifetime()
                try:
                    self._refresh_unified_pond_mode(
                        _current_project_world_config(self.editor_context)
                    )
                except Exception:
                    pass
                self._sr_session_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                self._capture_sr_session_context()
        try:
            # Drop events received while paused; there is no shared queued-input log.
            self._sr_input_clear(lifecycle_action="resume")
            self.is_paused = False
            self._sr_victory_banner = None
            self._sr_extinction_banner = None
            self._sr_banner_kind = None
            self._sr_banner_shown_at = 0.0
            self._sr_banner_title = None
            self._sr_banner_hint = None
            self._sync_hud_chrome()
            
            # 确保速度不为0，避免除零错误
            if self.simulation_speed <= 0:
                self.simulation_speed = 1.0
            
            interval = max(1, int(50 / self.simulation_speed))  # 确保间隔至少为1ms
            self.update_timer.start(interval)
            if hasattr(self, "_canvas"):
                self._canvas.setFocus()
            self.simulation_resumed.emit()
            self.editor_context.current_mode = EditorMode.PLAY
            self._notify_transport()
        except Exception as e:
            logger.exception("恢复模拟失败: %s", e)

    def _stop_simulation(self, *, write_session: bool = True) -> None:
        """停止模拟并释放运行时。

        write_session=False: 换场景/项目触发，避免错误 stopped 摘要。
        已写过 goals_complete/extinction/scene_changed 时不再写 stopped（防重复日志）。
        """
        if (
            write_session
            and self._using_scene_runtime
            and getattr(self, "_sr_session_log_enabled", False)
        ):
            prior = getattr(self, "_sr_last_session_end_reason", None)
            if prior not in _SR_SESSION_FINAL_REASONS:
                self._write_sr_session_summary("stopped")
        from core.VitaLoom.simulation.simulation_coordinator import (
            SimulationLane,
            get_simulation_coordinator,
        )

        coord = get_simulation_coordinator()
        if coord is not None:
            coord.register_lane_stop(SimulationLane.SR_PLAY)
        self._observe_worldbridge_quarantine_lifecycle_disposal(
            "simulation_stop"
        )
        self._end_sr_snapshot_lifetime()
        self.is_playing = False
        self.is_paused = False
        self._sr_input_clear(lifecycle_action="stop")
        self._configure_sr_runtime_randomness({})
        self.simulation = None
        self._using_scene_runtime = False
        self._sr_runtime_dirty = True
        self._scene_runtime_time = 0.0
        # Discard the old Pond; a fresh host start is not state restoration.
        self._unified_pond = None
        self._reset_worldbridge_shared_state_transport()
        self._worldbridge_active_pond_lifetime_token = None
        self._worldbridge_handoff_suspended = False
        self.scene_runtime_entities = []
        self._sr_script_entropy_audits = []
        self._sr_script_entropy_receipts = []
        self._sr_script_failure_receipts = []
        self._sr_script_trust_denials = []
        self._sr_serialized_scene_entity_ids = set()
        self._scene_runtime_edges = []
        self._scene_runtime_emissions_prev = {}
        self._scene_runtime_neighbor_ids = {}
        self._sr_structural_edges = []
        self._sr_connection_edges = []
        self._sr_spring_links = []
        self._sr_signal_edges = []
        self._sr_membrane_attach = {}
        self._sr_membrane_template = {}
        self._sr_runtime_project_path = None
        self._sr_runtime_scene_path = None
        self._sr_play_hint_shown = False
        self._episode_sim_accumulator = 0.0
        self._sr_biosphere_load = 0.0
        self._sr_biosphere_prev_load = 0.0
        self._sr_nutrient_target_count = 0
        self._sr_nutrient_target_peace = 0
        self._sr_war_recovery: dict[str, Any] = {}
        self._sr_war_profile = None
        self._sr_war_recovery_override_until = 0.0
        self._sr_war_phase_last: str = "peace"
        self._sr_war_phase_announced: set[str] = set()
        self._sr_pop_at_war_end: Optional[int] = None
        self._sr_war_pop_min: Optional[int] = None
        self._sr_war_nutrient_purge_acc = 0.0
        self._sr_war_phase_tick_cache: Optional[str] = None
        self._sr_war_combat_profile = None
        self._sr_combat_lineage: dict[str, dict[str, Any]] = {}
        self._sr_war_respawn_queue: list[dict[str, Any]] = []
        self._sr_war_kills_total = 0
        self._sr_war_respawn_count = 0
        self._sr_war_pending_casualties: list[dict[str, Any]] = []
        self._sr_pop_peak = 0
        self._sr_play_goals = {}
        self._sr_goal_announced = {"survive": False, "peak": False}
        self._sr_victory_banner = None
        self._sr_victory_pause_done = False
        self._sr_victory_notice_done = False
        self._sr_pause_on_extinction = False
        self._sr_game_mode = False
        self._sr_defeat_pause_done = False
        self._sr_extinction_pause_done = False
        self._sr_extinction_banner = None
        self._reset_sr_session_metadata(keep_last_replay=True)
        if hasattr(self, "_sr_hud_label"):
            self._sr_hud_label.clear()
            self._sr_hud_label.setVisible(False)
        self._sync_hud_chrome()
        self.update_timer.stop()
        self.simulation_stopped.emit()
        self.editor_context.current_mode = EditorMode.EDIT
        self._notify_transport()

    def register_as_sr_host(self) -> None:
        """发布 SR Host capabilities，并绑定到当前 Adapter 生命周期。"""
        try:
            from core.VitaLoom.core.capability_publication import (
                publish_capabilities,
            )
            from core.VitaLoom.core.service_keys import (
                SIMULATION_SR_HOST,
                SR_SELECTED_IDENTITY_HOST,
                WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST,
            )

            self.unregister_as_sr_host()
            services = getattr(self.editor_context, "services", None)
            if services is None:
                return
            self._sr_host_publication = publish_capabilities(
                services,
                owner="adapter.game-viewport.sr-host",
                capabilities={
                    SIMULATION_SR_HOST: self,
                    SR_SELECTED_IDENTITY_HOST: self,
                    WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST: self,
                },
            )
        except Exception as e:
            logger.debug("注册 SIMULATION_SR_HOST 失败: %s", e)

    def unregister_as_sr_host(self):
        """仅撤销仍指向本 GameViewport 的 SR Host capabilities。"""
        publication = getattr(self, "_sr_host_publication", None)
        if publication is None:
            return None
        report = publication.release()
        self._sr_host_publication = None
        return report

    def dispose_runtime_capabilities(self):
        """Release runtime capabilities owned by this UI Adapter."""
        return self.unregister_as_sr_host()

    def is_sr_playing(self) -> bool:
        return bool(self.is_playing)

    def refresh_canvas(self) -> None:
        canvas = getattr(self, "_canvas", None)
        if canvas is not None and hasattr(canvas, "update"):
            canvas.update()

    def start_simulation(self) -> None:
        self._start_simulation()

    def pause_simulation(self) -> None:
        self._pause_simulation()

    def stop_simulation(self, *, write_session: bool = True) -> None:
        self._stop_simulation(write_session=write_session)

    def _repo_relative_path(self, path: Path) -> str:
        """仓库根下的相对路径，便于控制台与 HUD 展示。"""
        from core.VitaLoom.core.bundle_paths import application_root

        root = application_root()
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return str(path)

    def _write_sr_session_summary(self, end_reason: str) -> Optional[Path]:
        """将本局 SR 摘要写入 logs/sr_sessions/（JSON + Markdown）。

        职责: 使用 _sr_session_scene_name / _sr_session_project_path 快照，不用当前 SceneManager。
        时机: stopped、goals_complete、extinction；换场景不写（见 _on_external_*）。
        返回: Markdown 路径供 HUD 展示。
        """
        if not getattr(self, "_sr_session_log_enabled", False):
            return None
        stamp = getattr(self, "_sr_session_stamp", None) or datetime.now(timezone.utc).strftime(
            "%Y%m%d_%H%M%S"
        )
        orgs = [
            e for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "organism"
        ]
        proj = getattr(self, "_sr_session_project_path", None)
        if not isinstance(proj, str):
            proj = getattr(self.editor_context, "current_project_path", None)
        scene_name = getattr(self, "_sr_session_scene_name", None)
        if not scene_name:
            try:
                from core.VitaLoom.scene.scene_manager import get_scene_manager

                sd = get_scene_manager().get_scene_data() or {}
                scene_name = str(sd.get("name", "")).strip() or None
            except Exception as e:
                logger.debug("读取场景名失败: %s", e)
        chinese = isinstance(getattr(self, "_sr_demo_legend", None), dict)
        mem_stats = self._sr_membrane_runtime_stats()
        combat_total = 0
        for o in orgs:
            hud = getattr(o, "sr_debug_hud", None)
            if isinstance(hud, dict):
                combat_total += int(hud.get("combat_score", 0) or 0)
        payload = build_sr_session_summary_payload(
            session_stamp=stamp,
            end_reason=end_reason,
            sim_time=float(self._scene_runtime_time),
            organism_count=len(orgs),
            organism_peak=int(getattr(self, "_sr_pop_peak", 0) or 0),
            entity_count=len(self.scene_runtime_entities),
            play_goals=getattr(self, "_sr_play_goals", None) or {},
            victory_pause_done=bool(getattr(self, "_sr_victory_pause_done", False)),
            extinction_pause_done=bool(getattr(self, "_sr_extinction_pause_done", False)),
            project_path=proj if isinstance(proj, str) else None,
            scene_name=scene_name,
            membrane_sensor_count=mem_stats.get("membrane_sensor_count"),
            mean_edge_weight=mem_stats.get("mean_edge_weight"),
            mean_chemo_channel=mem_stats.get("mean_chemo_channel"),
            war_phase=self._current_war_phase() if getattr(self, "_sr_war_profile", None) else None,
            population_at_war_end=getattr(self, "_sr_pop_at_war_end", None),
            war_population_min=getattr(self, "_sr_war_pop_min", None),
            combat_score_total=combat_total if combat_total > 0 else None,
            war_kills=int(getattr(self, "_sr_war_kills_total", 0) or 0) or None,
            respawn_count=int(getattr(self, "_sr_war_respawn_count", 0) or 0) or None,
        )
        try:
            state_home = os.environ.get("VITALOOM_STATE_HOME", "").strip()
            if state_home:
                root = Path(state_home)
            else:
                from core.VitaLoom.core.bundle_paths import application_root

                root = application_root()
            out_dir = root / "logs" / "sr_sessions"
            out_dir.mkdir(parents=True, exist_ok=True)
            base = f"session_{stamp}_{end_reason}"
            json_path = out_dir / f"{base}.json"
            md_path = out_dir / f"{base}.md"
            json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            md_path.write_text(
                format_sr_session_summary_markdown(payload, chinese=chinese),
                encoding="utf-8",
            )
            self._sr_last_session_md_path = md_path
            self._sr_last_session_end_reason = end_reason
            rel = self._repo_relative_path(md_path)
            logger.info("SR 会话摘要已写入: %s", json_path)
            if chinese:
                logger.info("【主世界】本局摘要已保存，请打开: %s", rel)
            else:
                logger.info("SR session summary saved: %s", rel)
            return md_path
        except Exception as e:
            logger.warning("SR 会话摘要写入失败: %s", e)
            return None

    def _on_speed_changed(self, value: int):
        """倍速滑块 → Transport 中枢 → 回写本视口。"""
        try:
            speed = max(0.01, value / 100.0)
            from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

            transport = get_simulation_transport()
            if transport:
                transport.set_speed(speed)
            else:
                self._apply_speed(speed)
        except Exception as e:
            logger.warning("速度变化处理失败: %s", e)

    def _apply_speed(self, speed: float) -> None:
        self.simulation_speed = max(0.01, float(speed))
        if hasattr(self, "speed_label"):
            self.speed_label.setText(
                self._t("game_viewport.control.speed_value", "{speed:.1f}x").format(
                    speed=self.simulation_speed
                )
            )
        if hasattr(self, "speed_slider"):
            target = int(self.simulation_speed * 100)
            if self.speed_slider.value() != target:
                self.speed_slider.blockSignals(True)
                self.speed_slider.setValue(target)
                self.speed_slider.blockSignals(False)
        if self.is_playing and not self.is_paused:
            interval = max(1, int(50 / self.simulation_speed))
            self.update_timer.setInterval(interval)

    def _update_simulation(self):
        """定时器入口：Cosmos + SR 场景 tick 或 builtin Simulation。

        SR: 即使 scene_runtime_entities 为空也须进 _handle_empty_sr_runtime_tick，
        否则灭绝暂停与 HUD 冻结（历史坑）。
        """
        try:
            from core.VitaLoom.viewports.sr_render_perf import sr_skip_cosmos_update

            if not (self._using_scene_runtime and sr_skip_cosmos_update()):
                from core.Lotucosm.cosmos import get_cosmos

                get_cosmos().update()
        except Exception as cosmos_err:
            logger.debug("Cosmos 更新跳过: %s", cosmos_err)

        try:
            if self.is_paused:
                if self._session_banner_payload() and hasattr(self, "_canvas"):
                    self._canvas.update()
                return

            if self._using_scene_runtime:
                from core.Lotucosm.runtime.world_bridge_clock_ordering_authority import (
                    issue_worldbridge_frame_clock_decision,
                    resolve_worldbridge_frame_delta,
                )

                dt = resolve_worldbridge_frame_delta(
                    self.simulation_speed,
                    paused=self.is_paused,
                )
                decision = None
                if bool(vars(self).get("_unified_pond_mode", False)) and self._sr_runtime_epoch is not None:
                    entities = list(getattr(self, "scene_runtime_entities", ()) or ())
                    handoff_requested = (
                        not bool(vars(self).get("_sr_game_mode", False))
                        and any(
                            str(getattr(entity, "entity_type", "")) == "organism"
                            for entity in entities
                        )
                    )
                    sequence = int(
                        vars(self).get("_worldbridge_clock_decision_sequence", 0)
                    ) + 1
                    vars(self)["_worldbridge_clock_decision_sequence"] = sequence
                    decision = issue_worldbridge_frame_clock_decision(
                        self.simulation_speed,
                        paused=False,
                        owner_token=str(
                            vars(self).get(
                                "_worldbridge_clock_owner_token",
                                "game_viewport_clock",
                            )
                        ),
                        runtime_epoch=self._sr_runtime_epoch,
                        decision_sequence=sequence,
                        bridge_handoff_requested=handoff_requested,
                    )
                    vars(self)["_worldbridge_clock_decision"] = decision
                if decision is None:
                    self._update_scene_runtime_entities(dt)
                else:
                    self._update_scene_runtime_entities(dt, clock_decision=decision)
                self._canvas.update()
            elif self.simulation:
                if hasattr(self.simulation, "update"):
                    self.simulation.update()
                self._canvas.update()
        except Exception as e:
            logger.warning("更新模拟失败: %s", e)
            try:
                self._stop_simulation()
            except Exception as stop_error:
                logger.exception("更新失败后停止模拟也失败: %s", stop_error)

    def _sprite_catalog(self) -> Optional[SrSpriteCatalog]:
        proj = getattr(self, "_sr_runtime_project_path", None)
        if not isinstance(proj, str) or not proj.strip():
            proj = getattr(self.editor_context, "current_project_path", None)
        if not isinstance(proj, str):
            return None
        return SrSpriteCatalog.for_project(proj)

    def _sr_ui_chinese(self) -> bool:
        lang = getattr(self.editor_context, "current_language", None)
        if isinstance(lang, str) and lang.lower().startswith("en"):
            return False
        if isinstance(getattr(self, "_sr_demo_legend", None), dict):
            return True
        return lang is None or not str(lang).lower().startswith("en")

    def _session_banner_payload(self) -> Optional[dict[str, Any]]:
        kind = getattr(self, "_sr_banner_kind", None)
        if kind not in ("victory", "extinction"):
            return None
        msg = getattr(self, "_sr_victory_banner", None) if kind == "victory" else getattr(
            self, "_sr_extinction_banner", None
        )
        if not isinstance(msg, str) or not msg.strip():
            return None
        elapsed = float(self._scene_runtime_time) - float(getattr(self, "_sr_banner_shown_at", 0.0))
        payload: dict[str, Any] = {
            "kind": kind,
            "message": msg.strip(),
            "elapsed": max(0.0, elapsed),
        }
        title = getattr(self, "_sr_banner_title", None)
        hint = getattr(self, "_sr_banner_hint", None)
        if isinstance(title, str) and title.strip():
            payload["title"] = title.strip()
        if isinstance(hint, str) and hint.strip():
            payload["hint"] = hint.strip()
        return payload

    def _show_session_banner(
        self,
        kind: str,
        message: str,
        *,
        title: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        self._sr_banner_kind = kind
        self._sr_banner_shown_at = float(self._scene_runtime_time)
        self._sr_banner_title = title
        self._sr_banner_hint = hint
        if kind == "victory":
            self._sr_victory_banner = message
        elif kind == "extinction":
            self._sr_extinction_banner = message
        if hasattr(self, "_canvas"):
            self._canvas.update()
        try:
            from core.VitaLoom.feedback.sr_session_feedback import play_session_feedback

            play_session_feedback(kind)
        except Exception as e:
            logger.debug("会话反馈音跳过: %s", e)

    def _refresh_entry_hud_hint(self) -> None:
        """从 project.json presentation 刷新未运行时的 HUD 引导文案。"""
        if not hasattr(self, "_sr_hud_hint") or self.is_playing:
            return
        hint = self._t("game_viewport.control.hint", "使用顶部工具栏 ▶ 运行 控制模拟")
        try:
            cfg = _current_project_world_config(self.editor_context)
            pres = cfg.get("presentation", {})
            if isinstance(pres, dict):
                custom = pres.get("editor_entry_hint_zh") or pres.get("tagline_zh")
                if isinstance(custom, str) and custom.strip():
                    hint = custom.strip()
        except Exception as e:
            logger.debug("读取项目 presentation 失败: %s", e)
        self._sr_hud_hint.setText(hint)
        self._sync_hud_chrome()

    def _build_sr_viewport_frame_snapshot(self, width: int, height: int):
        return build_viewport_frame_snapshot(
            self.scene_runtime_entities or [],
            width=width,
            height=height,
            scene_time=float(getattr(self, "_scene_runtime_time", 0.0)),
            edges=[
                {"source_id": src, "target_id": dst, "kind": "hard"}
                for src, dst in (self._scene_runtime_edges or [])
            ],
            metadata={"source": "GameViewport"},
        )

    def _initialize_sr_opengl_canvas(self, canvas: QWidget) -> None:
        snapshot = getattr(canvas, "opengl_lifecycle_snapshot", None)
        self._last_opengl_canvas_snapshot = snapshot() if callable(snapshot) else None

    def _resize_sr_opengl_canvas(self, canvas: QWidget, width: int, height: int) -> None:
        self._viewport_backend.resize(int(width), int(height))
        snapshot = getattr(canvas, "opengl_lifecycle_snapshot", None)
        self._last_opengl_canvas_snapshot = snapshot() if callable(snapshot) else None

    def _paint_sr_opengl_canvas(self, canvas: QWidget) -> None:
        if not isinstance(self._viewport_backend, OpenGLViewportBackend):
            self._last_opengl_target_snapshot = {
                "target": "qt_opengl_canvas",
                "fallback_required": True,
                "fallback_reason": "selected viewport backend is not OpenGL",
            }
            return
        cw, ch = canvas.width(), canvas.height()
        frame = self._build_sr_viewport_frame_snapshot(cw, ch)
        with self._viewport_profiler.measure("render"):
            try:
                pixel_ratio_reader = getattr(canvas, "devicePixelRatioF", None)
                pixel_ratio = float(pixel_ratio_reader()) if callable(pixel_ratio_reader) else 1.0
                target = QtOpenGLTextureTarget(width=cw, height=ch, pixel_ratio=pixel_ratio)
            except Exception:
                target = DiagnosticOpenGLRenderTarget()
            self._viewport_backend.render(target, frame)
        canvas_snapshot = getattr(canvas, "opengl_lifecycle_snapshot", None)
        target_snapshot = getattr(target, "snapshot", None)
        self._last_opengl_canvas_snapshot = canvas_snapshot() if callable(canvas_snapshot) else None
        self._last_opengl_target_snapshot = target_snapshot() if callable(target_snapshot) else None

    def _paint_sr_canvas(self, canvas: QWidget, event: Optional[QPaintEvent]) -> None:
        if callable(getattr(canvas, "opengl_lifecycle_snapshot", None)):
            self._paint_sr_opengl_canvas(canvas)
            return
        self._paint_sr_qpainter_canvas(canvas, event)

    def _paint_sr_qpainter_canvas(self, canvas: QWidget, event: Optional[QPaintEvent]) -> None:
        """在独立画布上绘制 SR / 回退模拟（HUD 与控制条不在此区域）。"""
        try:
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        except Exception as e:
            logger.warning("初始化绘制器失败: %s", e)
            return

        cw, ch = canvas.width(), canvas.height()
        scene_t = float(getattr(self, "_scene_runtime_time", 0.0))

        if self._using_scene_runtime:
            with self._viewport_profiler.measure("render"):
                if isinstance(self._viewport_backend, OpenGLViewportBackend):
                    frame = build_viewport_frame_snapshot(
                        self.scene_runtime_entities or [],
                        width=cw,
                        height=ch,
                        scene_time=scene_t,
                        edges=[
                            {"source_id": src, "target_id": dst, "kind": "hard"}
                            for src, dst in (self._scene_runtime_edges or [])
                        ],
                        metadata={"source": "GameViewport"},
                    )
                    try:
                        target = QtOpenGLRenderTarget(painter)
                    except Exception:
                        target = DiagnosticOpenGLRenderTarget()
                    self._viewport_backend.render(target, frame)
                else:
                    frame = QPainterViewportFrame(
                        width=cw,
                        height=ch,
                        entities=list(self.scene_runtime_entities or []),
                        structural_edges=self._scene_runtime_edges or [],
                        signal_edges=getattr(self, "_sr_signal_edges", ()) or [],
                        connection_edges=getattr(self, "_sr_connection_edges", ()) or [],
                        spring_links=getattr(self, "_sr_spring_links", ()) or (),
                        scene_time=scene_t,
                        demo_legend=getattr(self, "_sr_demo_legend", None),
                        show_legend=bool(self.is_playing),
                        session_banner=self._session_banner_payload(),
                        sprite_catalog=self._sprite_catalog(),
                        game_mode=bool(getattr(self, "_sr_game_mode", False)),
                        game_fx=getattr(self, "_sr_game_fx", None),
                        game_player_id=str(getattr(self, "_sr_player_id", "player")),
                        emissions_prev=getattr(self, "_scene_runtime_emissions_prev", None),
                        niche_pressure=niche_pressure_from_load(
                            float(getattr(self, "_sr_biosphere_prev_load", 0.0)),
                            load_max=float(getattr(self, "_sr_load_max", 1.0)),
                        ),
                    )
                    self._viewport_backend.render(painter, frame)
        elif self.simulation:
            painter.setBrush(QBrush(QColor(20, 20, 25)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, cw, ch)
            painter.setPen(QPen(QColor(100, 150, 255), 2))
            painter.setBrush(QBrush(QColor(100, 150, 255, 50)))
            if hasattr(self.simulation, 'organisms'):
                try:
                    organisms = self.simulation.organisms
                    if organisms:
                        for organism in organisms:
                            try:
                                if hasattr(organism, 'position'):
                                    pos = organism.position
                                    if hasattr(pos, '__getitem__'):
                                        try:
                                            pos_x = float(pos[0])
                                            pos_y = float(pos[1])
                                        except (IndexError, TypeError, ValueError):
                                            continue
                                    elif hasattr(pos, 'x') and hasattr(pos, 'y'):
                                        pos_x = float(pos.x)
                                        pos_y = float(pos.y)
                                    else:
                                        continue
                                    radius = float(getattr(organism, 'radius', getattr(organism, 'size', 20)))
                                    x = int(pos_x - radius)
                                    y = int(pos_y - radius)
                                    w = int(radius * 2)
                                    h = int(radius * 2)
                                    if w > 0 and h > 0:
                                        painter.drawEllipse(x, y, w, h)
                            except Exception:
                                continue
                except Exception:
                    __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        else:
            from core.VitaLoom.viewports.sr_visual_renderer import paint_sr_background

            paint_sr_background(painter, cw, ch, 0.0)
        self._paint_ps_replay_overlay(painter, cw, ch)
        if (
            self._using_scene_runtime
            and self.is_playing
            and getattr(self, "_sr_war_profile", None) is not None
        ):
            from core.VitaLoom.viewports.sr_visual_renderer import paint_war_phase_tint

            paint_war_phase_tint(
                painter,
                cw,
                ch,
                self._current_war_phase(),
                scene_time=scene_t,
            )
        painter.end()

    def get_viewport_profiler_snapshot(self) -> dict[str, dict[str, float | int]]:
        return self._viewport_profiler.snapshot()

    def set_ps_replay_overlay_points(self, points: list[tuple[float, float]]) -> None:
        """PS 实验快照只读叠加（C.2）；SR 播放时由绘制逻辑忽略。"""
        self._ps_replay_overlay_points = list(points)

    def _paint_ps_replay_overlay(self, painter: QPainter, cw: int, ch: int) -> None:
        if self.is_playing:
            return
        points = getattr(self, "_ps_replay_overlay_points", None)
        if not points:
            return
        try:
            from PyQt6.QtGui import QBrush, QColor, QPen

            painter.setPen(QPen(QColor(120, 200, 180, 140), 1))
            painter.setBrush(QBrush(QColor(80, 160, 140, 70)))
            for nx, ny in points:
                x = int(float(nx) * max(1, cw - 1))
                y = int(float(ny) * max(1, ch - 1))
                painter.drawEllipse(x - 5, y - 5, 10, 10)
        except Exception as exc:
            logger.debug("PS replay overlay 绘制失败: %s", exc)

    def set_simulation(self, simulation: Any):
        """设置模拟对象。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.simulation = simulation

    class _SceneRuntimeEntity:
        """轻量运行时实体：位置/速度/脚本/sr_channel_out；膜子体 membrane_locked。"""

        def __init__(
            self,
            entity_id: str | None,
            entity_type: str,
            position: tuple[float, float],
            radius: float = 18.0,
            *,
            rng: Any | None = None,
            identity_source: Any | None = None,
        ):
            """_SceneRuntimeEntity.__init__。

            
                职责:
                    执行本函数声明的对外行为（见实现）。
            
                时机:
                    由调用方在对应生命周期内调用。
            
                不变量:
                    不破坏模块顶 docstring 与同级契约。
            
                排错:
                    异常时见本文件模块说明与子树 README 排错表。
            """
            if entity_id is None:
                next_identity = getattr(identity_source, "next", None)
                if not callable(next_identity):
                    raise RuntimeError("runtime entity ID requires identity source")
                entity_id = str(next_identity("entity"))
            self.id = str(entity_id)
            self.entity_type = entity_type
            self.pond = None
            self.randomness_rng = rng
            self.position = [float(position[0]), float(position[1])]
            velocity_rng = rng or create_detached_sr_entity_randomness_rng(
                entity_id,
                entity_type,
                position,
                radius,
            )
            self.velocity = [
                velocity_rng.uniform(-20.0, 20.0),
                velocity_rng.uniform(-20.0, 20.0),
            ]
            self.radius = float(radius)
            self.scripts: list[Any] = []
            self.emission_strength = 0.0
            self.energy: Optional[float] = None
            self.health: Optional[float] = None
            self.max_energy: Optional[float] = None
            self.max_health: Optional[float] = None
            self.generation = 0
            self.developmental_stage = 0
            self.social_learning_enabled = True
            self.pinned = entity_type in ("nutrient", "environment_well")
            self.membrane_locked = False
            # Lifecycle/visibility owners are SR-local runtime state.  They are
            # captured by the SR restore envelope but never bridged as visible
            # (only ``active`` participates in the WorldBridge mapper).
            self.active = True
            self.visible = True
            # Render identity lives on the runtime entity so capture/restore
            # has a stable owner even before the scene loader or a dynamic
            # spawn path assigns the concrete visual.
            from core.Lotucosm.sr_entity_visual import SrEntityVisual

            self.sr_visual = SrEntityVisual()
            self.sr_channel_out: dict[str, float] = {}
            self.sr_channel_out_prev: dict[str, float] = {}
            self.sr_chemo_gain_scale = 1.0
            color_map = {
                "organism": QColor(120, 210, 255),
                "sensor": QColor(130, 240, 170),
                "actuator": QColor(255, 190, 120),
                "central_brain": QColor(255, 130, 160),
                "empty": QColor(180, 180, 180),
                "nutrient": QColor(195, 225, 120),
                "environment_well": QColor(150, 190, 255),
            }
            self.color = color_map.get(entity_type, QColor(140, 170, 255))

        def set_position(self, position: tuple[float, float] | list[float]) -> None:
            values = (float(position[0]), float(position[1]))
            if not all(math.isfinite(value) for value in values):
                raise ValueError("position must contain finite values")
            self.position[0], self.position[1] = values

        def set_velocity(self, velocity: tuple[float, float] | list[float]) -> None:
            values = (float(velocity[0]), float(velocity[1]))
            if not all(math.isfinite(value) for value in values):
                raise ValueError("velocity must contain finite values")
            self.velocity[0], self.velocity[1] = values

        def set_acceleration(self, acceleration: tuple[float, float] | list[float]) -> None:
            values = (float(acceleration[0]), float(acceleration[1]))
            if not all(math.isfinite(value) for value in values):
                raise ValueError("acceleration must contain finite values")
            current = getattr(self, "acceleration", None)
            if current is None:
                self.acceleration = [0.0, 0.0]
                current = self.acceleration
            current[0], current[1] = values

        def restore_motion_state(
            self,
            *,
            position: tuple[float, float],
            velocity: tuple[float, float],
            acceleration: tuple[float, float],
        ) -> None:
            values = tuple(tuple(float(v) for v in vector) for vector in (position, velocity, acceleration))
            if any(len(vector) != 2 or not all(math.isfinite(v) for v in vector) for vector in values):
                raise ValueError("motion state must contain finite 2-vectors")
            self.set_position(values[0])
            self.set_velocity(values[1])
            self.set_acceleration(values[2])

        def set_radius(self, radius: float) -> None:
            value = float(radius)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError("radius must be a positive finite number")
            self.radius = value

        def set_size(self, size: float) -> None:
            self.set_radius(size)

        def set_energy(self, energy: float) -> None:
            value = float(energy)
            if not math.isfinite(value):
                raise ValueError("energy must be finite")
            self.energy = value
            if self.max_energy is None:
                self.max_energy = max(0.0, value)

        def set_health(self, health: float) -> None:
            value = float(health)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("health must be a non-negative finite number")
            self.health = value
            if self.max_health is None:
                self.max_health = value

        def set_max_energy(self, max_energy: float) -> None:
            value = float(max_energy)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    "max_energy must be a non-negative finite number"
                )
            self.max_energy = value

        def set_max_health(self, max_health: float) -> None:
            value = float(max_health)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    "max_health must be a non-negative finite number"
                )
            self.max_health = value

        def set_developmental_stage(self, stage: int) -> None:
            value = int(stage)
            if value < 0:
                raise ValueError("developmental_stage must be non-negative")
            self.developmental_stage = value

        def set_social_learning_enabled(self, enabled: bool) -> None:
            if not isinstance(enabled, bool):
                raise TypeError("social_learning_enabled must be boolean")
            self.social_learning_enabled = enabled

        def set_generation(self, generation: int) -> None:
            value = int(generation)
            if value < 0:
                raise ValueError("generation must be non-negative")
            self.generation = value

        def add_script(self, script: Any):
            """_SceneRuntimeEntity.add_script。

            
                职责:
                    执行本函数声明的对外行为（见实现）。
            
                时机:
                    由调用方在对应生命周期内调用。
            
                不变量:
                    不破坏模块顶 docstring 与同级契约。
            
                排错:
                    异常时见本文件模块说明与子树 README 排错表。
            """
            self.scripts.append(script)
            if hasattr(script, "on_attach"):
                script.on_attach(self)

        def remove_script(self, script: Any) -> None:
            """Detach one live script and notify it through the SR lifecycle.

            Mirrors ``core.Lotucosm.entity.EntityBase.remove_script`` so the
            SR runtime entity exposes the same reversible script seam as its
            PS counterpart instead of being append-only.
            """
            if script not in self.scripts:
                return
            self.scripts.remove(script)
            on_detach = getattr(script, "on_detach", None)
            if callable(on_detach):
                on_detach(self)

        def replace_scripts(self, scripts: Any) -> None:
            """Atomically replace the live script set and keep attach order.

            The new scripts are attached before the old ones are detached so
            a failing ``on_attach`` leaves the previous script set in place;
            the caller captures a pre-image for cross-owner rollback.
            """
            replacement = list(scripts)
            previous = list(self.scripts)
            if replacement == previous:
                return
            attached: list[Any] = []
            try:
                for script in replacement:
                    on_attach = getattr(script, "on_attach", None)
                    if callable(on_attach):
                        on_attach(self)
                    attached.append(script)
            except Exception:
                for script in reversed(attached):
                    on_detach = getattr(script, "on_detach", None)
                    if callable(on_detach):
                        on_detach(self)
                raise
            self.scripts = replacement
            for script in previous:
                on_detach = getattr(script, "on_detach", None)
                if callable(on_detach):
                    on_detach(self)

        def step_scripts(self, ctx):
            """_SceneRuntimeEntity.step_scripts。

            
                职责:
                    执行本函数声明的对外行为（见实现）。
            
                时机:
                    由调用方在对应生命周期内调用。
            
                不变量:
                    不破坏模块顶 docstring 与同级契约。
            
                排错:
                    异常时见本文件模块说明与子树 README 排错表。
            """
            # SR tick：pvaec_step（默认委托 sr_step）或 legacy update
            if self.scripts:
                for script in self.scripts:
                    try:
                        if hasattr(script, "_randomness_execution_ticks"):
                            script._randomness_execution_ticks += 1
                        if hasattr(script, "pvaec_step"):
                            script.pvaec_step(ctx, ctx.delta_time)
                        elif hasattr(script, "sr_step"):
                            script.sr_step(ctx, ctx.delta_time)
                        elif hasattr(script, "update"):
                            script.update(ctx.delta_time)
                    except Exception as exc:
                        sink = getattr(ctx, "runtime_failure_sink", None)
                        if callable(sink):
                            sink(
                                getattr(script, "_scene_script_path", self.id),
                                "runtime",
                                "execution_failed",
                                exc,
                            )
                        raise

        def step_physics(self, dt: float, width: int, height: int):
            """委托官方 SR 2D 积分器（接触解算由 ``SrPhysics2DWorld.step`` 统一处理）。"""
            from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
            from core.Lotucosm.sr_physics2d.integrator import integrate_entity

            cfg = getattr(self, "_sr_physics_cfg", None)
            if not isinstance(cfg, SrPhysics2DConfig):
                cfg = SrPhysics2DConfig()
            integrate_entity(self, dt, float(width), float(height), cfg)

    def _paint_sr_demo_legend_overlay(self, painter: Any) -> None:
        """兼容旧调用；实际绘制已委托 SrVisualRenderer。"""
        demo = getattr(self, "_sr_demo_legend", None)
        if not isinstance(demo, dict) or not self.is_playing:
            return
        from core.VitaLoom.viewports.sr_visual_renderer import paint_sr_demo_legend

        paint_sr_demo_legend(painter, self.width(), self.height(), demo)

    def _load_scene_runtime_entities(self) -> bool:
        """从 SceneManager 当前 .pond 构建内存运行时（拓扑/膜模板/信号边）。

        流程: 实体+脚本 → resolve_membrane_template → expand+explicit+dedupe 信号边
        → _assign_organism_signal_edge_genes；记录 _sr_runtime_*_path。
        排错: 换场景后数据不对 → 须 _prepare 重载，勿假定本方法每帧调用。
        """
        from core.VitaLoom.scene.scene_manager import get_scene_manager

        scene_manager = get_scene_manager()
        raw_scene = scene_manager.get_scene_data() or {}
        project_path = getattr(self.editor_context, "current_project_path", None)
        if project_path:
            project_root = Path(str(project_path))
            if (project_root / "project.json").is_file():
                from FrameCore.project_lock import resolve_project_runtime
                from core.VitaLoom.core.bundle_paths import resource_root

                runtime_resolution = resolve_project_runtime(
                    project_root,
                    repo_root=resource_root(),
                )
                if runtime_resolution.runtime_backend_selection_mismatch:
                    raise RuntimeError(
                        "project runtime backend selection does not match project.lock.json"
                    )
        from core.Lotucosm.sr_game_scene import normalize_game_scene_data
        from core.VitaLoom.project.evolution_context import merge_evolution_defaults_into_scene_data
        scene_data = normalize_game_scene_data(raw_scene, project_path)
        proj_cfg = _current_project_world_config(self.editor_context)
        self._refresh_unified_pond_mode(proj_cfg)
        scene_data = merge_evolution_defaults_into_scene_data(scene_data, proj_cfg)
        self._configure_sr_runtime_randomness(scene_data)
        pond_cfg = scene_data.get("pond_config")
        if isinstance(pond_cfg, dict):
            raw_size = pond_cfg.get("size")
            if isinstance(raw_size, (list, tuple)) and len(raw_size) >= 2:
                self._sr_scene_size = (float(raw_size[0]), float(raw_size[1]))
            else:
                self._sr_scene_size = None
        else:
            self._sr_scene_size = None
        entities_data = scene_data.get("entities", [])
        self._sr_serialized_scene_entity_ids = set()
        if not entities_data:
            return False

        self.scene_runtime_entities = []
        self._sr_script_entropy_audits = []
        self._sr_script_entropy_receipts = []
        self._sr_script_trust_denials = []
        self._sr_script_declared_paths = []
        for entity_data in entities_data:
            raw_entity_id = entity_data.get("id")
            entity_id = (
                str(raw_entity_id).strip()
                if isinstance(raw_entity_id, str) and raw_entity_id.strip()
                else self._next_sr_entity_id("entity")
            )
            entity_type = entity_data.get("type", "empty")
            raw_pos = entity_data.get("position", [entity_data.get("x", 0.0), entity_data.get("y", 0.0)])
            if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
                raw_pos = [0.0, 0.0]
            radius = float(entity_data.get("radius", 18.0))
            runtime_entity = self._SceneRuntimeEntity(
                entity_id=entity_id,
                entity_type=entity_type,
                position=(float(raw_pos[0]), float(raw_pos[1])),
                radius=radius,
                rng=self._sr_runtime_rng,
            )
            if entity_data.get("pinned") is True:
                runtime_entity.pinned = True
            runtime_entity.active = bool(entity_data.get("active", True))
            runtime_entity.visible = bool(entity_data.get("visible", True))
            if "energy" in entity_data:
                try:
                    runtime_entity.set_energy(float(entity_data["energy"]))
                except (TypeError, ValueError):
                    pass
            for field_name, setter_name in (
                ("health", "set_health"),
                ("max_energy", "set_max_energy"),
                ("max_health", "set_max_health"),
            ):
                if field_name in entity_data:
                    try:
                        getattr(runtime_entity, setter_name)(
                            float(entity_data[field_name])
                        )
                    except (TypeError, ValueError):
                        pass
            if runtime_entity.max_energy is None and runtime_entity.energy is not None:
                runtime_entity.set_max_energy(runtime_entity.energy)
            if runtime_entity.max_health is None and runtime_entity.health is not None:
                runtime_entity.set_max_health(runtime_entity.health)
            if "developmental_stage" in entity_data:
                try:
                    runtime_entity.set_developmental_stage(
                        int(entity_data["developmental_stage"])
                    )
                except (TypeError, ValueError):
                    pass
            if "social_learning_enabled" in entity_data:
                try:
                    runtime_entity.set_social_learning_enabled(
                        entity_data["social_learning_enabled"]
                    )
                except TypeError:
                    pass
            if "generation" in entity_data:
                try:
                    runtime_entity.set_generation(int(entity_data["generation"]))
                except (TypeError, ValueError):
                    runtime_entity.set_generation(0)

            from core.Lotucosm.sr_entity_visual import parse_sr_visual
            from core.Lotucosm.sr_game_defaults import (
                default_sr_visual_for_entity,
                infer_sr_game_mode,
                normalize_sr_play_goals_for_game_mode,
            )

            runtime_entity.sr_visual = parse_sr_visual(
                entity_data.get("sr_visual"),
                sprite_path=entity_data.get("sprite_path"),
            )

            for script_data in entity_data.get("scripts", []):
                script = self._instantiate_scene_script(script_data, project_path)
                if script is not None:
                    runtime_entity.add_script(script)

            self.scene_runtime_entities.append(runtime_entity)

        self._sr_serialized_scene_entity_ids = {
            str(entity.id) for entity in self.scene_runtime_entities
        }

        legend = scene_data.get("sr_demo_legend")
        self._sr_demo_legend = legend if isinstance(legend, dict) else None

        raw_goals = scene_data.get("sr_play_goals")
        self._sr_play_goals = raw_goals if isinstance(raw_goals, dict) else {}
        self._sr_goal_announced = {"survive": False, "peak": False}
        self._sr_victory_banner = None
        self._sr_victory_pause_done = False
        self._sr_victory_notice_done = False
        self._sr_extinction_banner = None
        self._sr_extinction_pause_done = False
        self._sr_banner_kind = None
        self._sr_banner_shown_at = 0.0
        self._sr_banner_title = None
        self._sr_banner_hint = None
        self._sr_pause_on_extinction = scene_data.get("sr_pause_on_extinction") is True
        self._sr_game_mode = infer_sr_game_mode(scene_data, project_path)
        from core.Lotucosm.sr_game_contract import resolve_player_id

        self._sr_player_id = resolve_player_id(scene_data)
        if self._sr_game_mode:
            self._sr_pause_on_extinction = False
            self._sr_play_goals = normalize_sr_play_goals_for_game_mode(self._sr_play_goals)
            from core.Lotucosm.sr_game_effects import create_fx_state
            from core.Lotucosm.sr_game_procedural import proc_seed_from_scene

            self._sr_game_fx = create_fx_state()
            proc_seed, proc_count = proc_seed_from_scene(scene_data)
            self._sr_proc_seed = proc_seed
            self._sr_proc_obstacles = proc_count
            if isinstance(self._sr_demo_legend, dict):
                legend = dict(self._sr_demo_legend)
                lines = list(legend.get("lines") or [])
                seed_line = f"路引 #{proc_seed}（Ctrl+Shift+C 复制）"
                if not any(str(l).startswith("路引 #") for l in lines):
                    lines.append(seed_line)
                legend["lines"] = lines
                self._sr_demo_legend = legend
        else:
            self._sr_game_fx = None
            self._sr_proc_seed = 12345
            self._sr_proc_obstacles = 0
        self._sr_defeat_pause_done = False

        for runtime_entity in self.scene_runtime_entities:
            vis = getattr(runtime_entity, "sr_visual", None)
            if self._sr_game_mode and (vis is None or not getattr(vis, "sprite", "")):
                runtime_entity.sr_visual = default_sr_visual_for_entity(
                    str(getattr(runtime_entity, "id", "")),
                    str(getattr(runtime_entity, "entity_type", "")),
                )

        from core.Lotucosm.sr_link_physics import (
            build_spring_links,
            merge_signal_edge_lists,
            partition_link_edges,
            step_spring_network,
        )
        from core.Lotucosm.sr_membrane_topology import (
            apply_explicit_signal_edges,
            build_membrane_attachments,
            dedupe_signal_edges,
            expand_signal_edges,
            parse_weighted_edges,
            resolve_membrane_template,
        )

        self._sr_membrane_template = resolve_membrane_template(scene_data)

        entity_ids = {e.id for e in self.scene_runtime_entities}
        id_to_type = {e.id: str(e.entity_type) for e in self.scene_runtime_entities}
        raw_conns = scene_data.get("connections", [])
        parsed_conns = [
            e
            for e in parse_weighted_edges(raw_conns)
            if e["start"] in entity_ids and e["end"] in entity_ids
        ]
        hard_edges, soft_sig_conn, soft_mech = partition_link_edges(parsed_conns, id_to_type)
        self._sr_connection_edges = hard_edges + soft_sig_conn + soft_mech
        self._sr_structural_edges = list(hard_edges)
        edges: list[tuple[str, str]] = [
            (e["start"], e["end"]) for e in self._sr_connection_edges
        ]
        self._scene_runtime_edges = edges

        nb: dict[str, set[str]] = {}
        for sa, sb in edges:
            nb.setdefault(sa, set()).add(sb)
            nb.setdefault(sb, set()).add(sa)
        self._scene_runtime_neighbor_ids = {k: frozenset(v) for k, v in nb.items()}

        self._sr_membrane_attach = build_membrane_attachments(
            self.scene_runtime_entities, hard_edges
        )
        expand_src = merge_signal_edge_lists(hard_edges, soft_sig_conn)
        self._sr_signal_edges = expand_signal_edges(
            expand_src,
            self._sr_membrane_attach,
            id_to_type,
        )
        explicit_sig = parse_weighted_edges(scene_data.get("sr_signal_connections") or [])
        for ex in explicit_sig:
            ex.setdefault("link_kind", "soft")
        self._sr_signal_edges = apply_explicit_signal_edges(
            self._sr_signal_edges, explicit_sig, entity_ids
        )
        self._sr_signal_edges = dedupe_signal_edges(self._sr_signal_edges)
        self._sr_spring_links = build_spring_links(self.scene_runtime_entities, soft_mech)
        from core.Lotucosm.sr_physics2d import SrPhysics2DConfig, SrPhysics2DWorld

        self._sr_physics_cfg = SrPhysics2DConfig.from_scene_data(scene_data)
        requested_backend = "auto"
        if isinstance(proj_cfg, dict):
            requested_backend = str(proj_cfg.get("sr2d_backend", "auto") or "auto")
        self._sr2d_backend_request = requested_backend.strip().lower()
        self._sr_physics_world = SrPhysics2DWorld(
            self._sr_physics_cfg,
            backend_request=self._sr2d_backend_request,
        )
        from core.Lotucosm.sr_field_grid import SrFieldGrid, SrFieldGridConfig
        from core.Lotucosm.sr_fluid_flow import SrFluidCouplingConfig

        self._sr_fluid_coupling_cfg = SrFluidCouplingConfig.from_scene_data(scene_data)
        fg_cfg = SrFieldGridConfig.from_scene_data(scene_data)
        sw, sh = self._scene_bounds()
        self._sr_field_grid = SrFieldGrid(sw, sh, fg_cfg) if fg_cfg.enabled else None
        self._assign_organism_signal_edge_genes()

        self._scene_runtime_emissions_prev = {}

        self._scene_runtime_time = 0.0
        self._sr_biosphere_load = 0.0
        self._sr_biosphere_prev_load = 0.0
        self._sr_nutrient_target_count = sum(
            1 for e in entities_data if str(e.get("type", "")) == "nutrient"
        )
        self._sr_nutrient_target_peace = int(self._sr_nutrient_target_count)
        wr_raw = scene_data.get("sr_war_recovery") if isinstance(scene_data, dict) else None
        self._sr_war_recovery = dict(wr_raw) if isinstance(wr_raw, dict) else {}
        from core.Lotucosm.sr_war_recovery import resolve_war_recovery
        from core.Lotucosm.sr_war_combat import resolve_war_combat

        self._sr_war_profile = resolve_war_recovery(scene_data if isinstance(scene_data, dict) else None)
        self._sr_war_combat_profile = resolve_war_combat(scene_data if isinstance(scene_data, dict) else None)
        self._sr_combat_lineage = {}
        self._sr_war_respawn_queue = []
        self._sr_war_kills_total = 0
        self._sr_war_respawn_count = 0
        self._sr_war_pending_casualties = []
        self._sr_war_recovery_override_until = 0.0
        self._sr_war_phase_last = "peace"
        self._sr_war_phase_announced = set()
        self._sr_pop_at_war_end = None
        self._sr_war_pop_min = None
        self._sr_war_nutrient_purge_acc = 0.0
        self._sr_war_phase_tick_cache = None
        if self._sr_war_profile.nutrient_target_peace > 0:
            self._sr_nutrient_target_peace = int(self._sr_war_profile.nutrient_target_peace)
        self._sr_pop_peak = sum(
            1 for e in entities_data if str(e.get("type", "")) == "organism"
        )
        proj, scene_path = self._runtime_context_key()
        self._sr_runtime_project_path = proj
        self._sr_runtime_scene_path = scene_path
        self._sr_runtime_dirty = False
        try:
            from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog

            SrSpriteCatalog.invalidate_cache()
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
        self._sr_play_hint_shown = False
        logger.info("游戏视口已加载场景运行时实体: %s", len(self.scene_runtime_entities))
        self._bootstrap_initial_organism_membranes(project_path)
        self._refresh_entry_hud_hint()
        self._ensure_unified_bridge_for_scene()
        return len(self.scene_runtime_entities) > 0

    def _assign_organism_signal_edge_genes(self) -> None:
        """为每个 organism 缓存 _sr_inherited_signal_edges（繁殖遗传用）。

        内容: 与该 hub 膜子节点相关的 signal_edges 副本；
        evo 繁殖时作为 parent_signal_edges 传入 spawn。
        """
        attach = self._sr_membrane_attach
        for e in self.scene_runtime_entities:
            if str(getattr(e, "entity_type", "")) != "organism":
                continue
            kids = {cid for cid, (pid, _dx, _dy) in attach.items() if pid == e.id}
            inherited = [
                edge
                for edge in self._sr_signal_edges
                if edge.get("start") in kids or edge.get("end") in kids
            ]
            e._sr_inherited_signal_edges = [dict(edge) for edge in inherited]

    def _war_combat_mode_active(self) -> bool:
        from core.Lotucosm.sr_war_combat import combat_active_at_time

        try:
            combat = getattr(self, "_sr_war_combat_profile", None)
            profile = getattr(self, "_sr_war_profile", None)
        except RuntimeError:
            combat = None
            profile = None
        if combat is None or profile is None:
            return False
        try:
            t = float(getattr(self, "_scene_runtime_time", 0.0))
            override = float(getattr(self, "_sr_war_recovery_override_until", 0.0) or 0.0)
        except RuntimeError:
            t = 0.0
            override = 0.0
        return combat_active_at_time(
            t,
            profile,
            combat,
            war_override_until=override,
        )

    def _bootstrap_initial_organism_membranes(self, project_path: Optional[str]) -> None:
        """为无膜簇的开局 organism 按 sr_membrane_template 生成 sensor/actuator。"""
        combat = self._safe_war_combat_profile()
        if combat is None or not combat.combat_enabled_in_war:
            return
        hubs = [
            e
            for e in self.scene_runtime_entities
            if str(getattr(e, "entity_type", "")) == "organism"
        ]
        attached_any = False
        for hub in hubs:
            if self._membrane_children_of(str(hub.id)):
                continue
            self._attach_membrane_cluster_to_hub(str(hub.id), project_path)
            attached_any = True
        if not attached_any:
            return
        attach_ids = set(self._sr_membrane_attach.keys())
        drop = [
            str(e.id)
            for e in self.scene_runtime_entities
            if str(getattr(e, "entity_type", "")) in ("sensor", "actuator")
            and str(e.id) not in attach_ids
            and str(e.id).startswith(("sensor_mem_", "actuator_cilium_"))
        ]
        if drop:
            self._process_sr_removal_requests(drop)
        self._assign_organism_signal_edge_genes()
        self._sync_membrane_positions()
        lineage = getattr(self, "_sr_combat_lineage", None) or {}
        for hub in [
            e
            for e in self.scene_runtime_entities
            if str(getattr(e, "entity_type", "")) == "organism"
        ]:
            lid = str(hub.id)
            lineage.setdefault(
                lid,
                {"lineage_id": lid, "death_count": 0, "respawn_count": 0},
            )
            hud = getattr(hub, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                hub.sr_debug_hud = hud
            hud.setdefault("lineage_id", lid)
        self._sr_combat_lineage = lineage

    def _attach_membrane_cluster_to_hub(self, hub_id: str, project_path: Optional[str]) -> None:
        from core.Lotucosm.sr_membrane_topology import DEFAULT_MEMBRANE_TEMPLATE, expand_signal_edges

        hub = next((e for e in self.scene_runtime_entities if str(e.id) == hub_id), None)
        if hub is None:
            return
        tpl = getattr(self, "_sr_membrane_template", None) or DEFAULT_MEMBRANE_TEMPLATE
        cx, cy = float(hub.position[0]), float(hub.position[1])
        new_structural: list[dict[str, Any]] = []
        for spec in tpl.get("sensors", []):
            if not isinstance(spec, dict):
                continue
            self._sr_spawn_seq += 1
            cid = f"{hub_id}_{spec.get('suffix', 's')}"
            if any(str(e.id) == cid for e in self.scene_runtime_entities):
                continue
            dx, dy = float(spec.get("dx", 0.0)), float(spec.get("dy", 0.0))
            ent = self._SceneRuntimeEntity(
                entity_id=cid,
                entity_type="sensor",
                position=(cx + dx, cy + dy),
                radius=float(spec.get("radius", 14.0)),
                rng=self._sr_runtime_rng,
            )
            ent.membrane_locked = True
            sname = spec.get("script")
            if sname:
                script = self._instantiate_scene_script(
                    {"name": str(sname), "type": str(spec.get("type", "")), "properties": {}},
                    project_path,
                )
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
            self._sr_membrane_attach[cid] = (hub_id, dx, dy)
            new_structural.append(
                {"start": hub_id, "end": cid, "channel": "struct", "weight": 1.0, "link_kind": "hard"}
            )
        for spec in tpl.get("actuators", []):
            if not isinstance(spec, dict):
                continue
            self._sr_spawn_seq += 1
            cid = f"{hub_id}_{spec.get('suffix', 'a')}"
            if any(str(e.id) == cid for e in self.scene_runtime_entities):
                continue
            dx, dy = float(spec.get("dx", 0.0)), float(spec.get("dy", 0.0))
            ent = self._SceneRuntimeEntity(
                entity_id=cid,
                entity_type="actuator",
                position=(cx + dx, cy + dy),
                radius=float(spec.get("radius", 12.0)),
                rng=self._sr_runtime_rng,
            )
            ent.membrane_locked = True
            sname = spec.get("script")
            if sname:
                script = self._instantiate_scene_script(
                    {"name": str(sname), "type": str(spec.get("type", "")), "properties": {}},
                    project_path,
                )
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
            self._sr_membrane_attach[cid] = (hub_id, dx, dy)
            new_structural.append(
                {"start": hub_id, "end": cid, "channel": "struct", "weight": 1.0, "link_kind": "hard"}
            )
        if not new_structural:
            return
        self._sr_structural_edges.extend(new_structural)
        self._sr_connection_edges.extend(new_structural)
        for edge in new_structural:
            a, b = edge["start"], edge["end"]
            self._scene_runtime_edges.append((a, b))
            self._scene_runtime_neighbor_ids.setdefault(a, frozenset())
            self._scene_runtime_neighbor_ids.setdefault(b, frozenset())
        nb: dict[str, set[str]] = {k: set(v) for k, v in self._scene_runtime_neighbor_ids.items()}
        for sa, sb in self._scene_runtime_edges:
            nb.setdefault(sa, set()).add(sb)
            nb.setdefault(sb, set()).add(sa)
        self._scene_runtime_neighbor_ids = {k: frozenset(v) for k, v in nb.items()}
        id_to_type = {e.id: str(e.entity_type) for e in self.scene_runtime_entities}
        child_signal = expand_signal_edges(new_structural, self._sr_membrane_attach, id_to_type)
        self._sr_signal_edges.extend(child_signal)
        from core.Lotucosm.sr_membrane_topology import dedupe_signal_edges

        self._sr_signal_edges = dedupe_signal_edges(self._sr_signal_edges)
        self._rebuild_sr_spring_links()

    def _rebuild_sr_spring_links(self) -> None:
        from core.Lotucosm.sr_link_physics import build_spring_links, partition_link_edges

        id_to_type = {e.id: str(e.entity_type) for e in self.scene_runtime_entities}
        _hard, _sig, soft_mech = partition_link_edges(
            self._sr_connection_edges, id_to_type
        )
        self._sr_spring_links = build_spring_links(
            self.scene_runtime_entities, soft_mech
        )

    def _sync_membrane_positions(self) -> None:
        """每 tick 将膜子实体位置设为 hub 中心 + 附着偏移，速度同步 hub。"""
        id_to_ent = {e.id: e for e in self.scene_runtime_entities}
        for child_id, (parent_id, dx, dy) in self._sr_membrane_attach.items():
            parent = id_to_ent.get(parent_id)
            child = id_to_ent.get(child_id)
            if parent is None or child is None:
                continue
            child.position[0] = float(parent.position[0]) + dx
            child.position[1] = float(parent.position[1]) + dy
            child.velocity[0] = float(parent.velocity[0])
            child.velocity[1] = float(parent.velocity[1])

    def _snapshot_sr_channel_out_prev(self) -> None:
        """帧末保存 sr_channel_out → sr_channel_out_prev，供下帧 sensor 批 use_prev_inbound。"""
        for e in self.scene_runtime_entities:
            raw = getattr(e, "sr_channel_out", None)
            e.sr_channel_out_prev = dict(raw) if isinstance(raw, dict) else {}

    def _sr_inbound_for_entity(self, entity_id: str, *, use_prev: bool) -> dict[str, float]:
        """单实体 inbound；use_prev 与 tick 批次一致（见 _update_scene_runtime_entities 顺序契约）。"""
        from core.Lotucosm.sr_membrane_topology import aggregate_channel_signals

        all_in = aggregate_channel_signals(
            self._sr_signal_edges,
            self.scene_runtime_entities,
            use_prev=use_prev,
        )
        return dict(all_in.get(entity_id, {}))

    def _parent_organism_for_membrane_child(self, child_id: str) -> Any | None:
        """膜子实体 → 附着 hub（organism）；用于继承 sr_chemo_gain_scale。"""
        attach = self._sr_membrane_attach.get(child_id)
        if not attach:
            return None
        parent_id = attach[0]
        for e in self.scene_runtime_entities:
            if e.id == parent_id:
                return e
        return None

    def _sr_membrane_runtime_stats(self) -> Dict[str, float | int]:
        """膜受体数、chemo 边均权、纤毛侧 chemo 通道均值（供 Dock / 复盘）。"""
        entities = list(self.scene_runtime_entities)
        sensors = sum(
            1 for e in entities if str(getattr(e, "entity_type", "")) == "sensor"
        )
        chemo_weights: List[float] = []
        for edge in getattr(self, "_sr_signal_edges", ()) or []:
            if str(edge.get("channel", "chemo")) != "chemo":
                continue
            try:
                chemo_weights.append(float(edge.get("weight", 1.0)))
            except (TypeError, ValueError):
                chemo_weights.append(1.0)
        mean_w = sum(chemo_weights) / len(chemo_weights) if chemo_weights else 0.0
        from core.Lotucosm.sr_membrane_topology import aggregate_channel_signals

        inbound = aggregate_channel_signals(
            self._sr_signal_edges, entities, use_prev=False
        )
        chemo_vals: List[float] = []
        for e in entities:
            if str(getattr(e, "entity_type", "")) != "actuator":
                continue
            try:
                chemo_vals.append(float(inbound.get(e.id, {}).get("chemo", 0.0) or 0.0))
            except (TypeError, ValueError):
                pass
        mean_c = sum(chemo_vals) / len(chemo_vals) if chemo_vals else 0.0
        return {
            "membrane_sensor_count": int(sensors),
            "mean_edge_weight": float(mean_w),
            "mean_chemo_channel": float(mean_c),
        }

    def _run_script_tick_batch(
        self,
        *,
        all_e: list[Any],
        entities_batch: list[Any],
        dt: float,
        use_prev_inbound: bool,
        spawn_list: list[Any],
        remove_ids: list[str],
        damage_list: list[tuple[str, float]],
        fx_list: list[Any],
        niche_p: float,
        deriv: float,
        load_before: float,
        peer_scale: float,
        min_horizon: float,
        sr_caps: Any,
        w: int,
        h: int,
        input_snap: Any,
    ) -> None:
        """对一批同类型实体执行 SR tick（注入 env、inbound、input、spawn/removal 列表）。

        organism 批: use_prev_inbound=True，并写 sr_chemo_gain_scale 到 env。
        sensor 批: use_prev_inbound=True（读上帧 channel 快照；本帧初已清空 sr_channel_out）。
        actuator 批: use_prev_inbound=False（读当帧 sensor 输出）。
        膜 sensor/actuator 的 chemo_gain_scale 继承自 parent organism。
        """
        from core.Lotucosm.scene_runtime.tick_phases import run_script_tick_batch

        run_script_tick_batch(
            self,
            entities_batch=entities_batch,
            all_e=all_e,
            dt=dt,
            spawn_list=spawn_list,
            remove_ids=remove_ids,
            damage_list=damage_list,
            fx_list=fx_list,
            niche_p=niche_p,
            deriv=deriv,
            load_before=load_before,
            peer_scale=peer_scale,
            min_horizon=min_horizon,
            sr_caps=sr_caps,
            w=w,
            h=h,
            input_snap=input_snap,
            use_prev_inbound=use_prev_inbound,
        )

    def _bootstrap_spawned_membrane_clusters(
        self,
        hub_ids: list[str],
        *,
        all_e: list[Any],
        dt: float,
        spawn_list: list[Any],
        remove_ids: list[str],
        damage_list: list[tuple[str, float]],
        fx_list: list[Any],
        niche_p: float,
        deriv: float,
        load_before: float,
        peer_scale: float,
        min_horizon: float,
        sr_caps: Any,
        w: int,
        h: int,
        input_snap: Any,
    ) -> None:
        """繁殖当帧补跑 hub+膜组件脚本，避免首帧无代谢/通道。

        顺序契约: 与主 tick 相同 organism→sensor→actuator；见 _update_scene_runtime_entities 步骤 6。
        """
        if not hub_ids:
            return
        self._sync_membrane_positions()
        idset: set[str] = set()
        for hid in hub_ids:
            idset.add(hid)
            idset.update(self._membrane_children_of(hid))
        subset = [e for e in all_e if str(e.id) in idset]
        by_type = lambda t: [e for e in subset if str(getattr(e, "entity_type", "")) == t]
        common = dict(
            all_e=list(self.scene_runtime_entities),
            dt=dt,
            spawn_list=spawn_list,
            remove_ids=remove_ids,
            damage_list=damage_list,
            fx_list=fx_list,
            niche_p=niche_p,
            deriv=deriv,
            load_before=load_before,
            peer_scale=peer_scale,
            min_horizon=min_horizon,
            sr_caps=sr_caps,
            w=w,
            h=h,
            input_snap=input_snap,
        )
        self._run_script_tick_batch(
            entities_batch=by_type("organism"), use_prev_inbound=True, **common
        )
        self._run_script_tick_batch(
            entities_batch=by_type("sensor"), use_prev_inbound=True, **common
        )
        self._run_script_tick_batch(
            entities_batch=by_type("actuator"), use_prev_inbound=False, **common
        )

    def _process_organism_with_membrane_spawn(
        self,
        req: Dict[str, Any],
        project_path: Optional[str],
    ) -> str:
        """动态生成带膜簇的 organism（hub + sensor + actuator + 信号边）。

        边权流水线（顺序契约，勿调换）::
            expand_signal_edges
            → inherit_chemo_edge_weights（req 含 parent_signal_edges + parent_hub_id）
              或按序应用 signal_edge_weights 回退
            → mutate_signal_edges（edge_mutation_sigma）
            → dedupe_signal_edges

        历史: 勿在 mutate 前对全部 chemo 边写权重均值，否则突变无效。
        模板: req 无 template 时用 _sr_membrane_template（场景 sr_membrane_template）。
        """
        from core.Lotucosm.sr_membrane_topology import DEFAULT_MEMBRANE_TEMPLATE

        hub_id = str(req.get("hub_id") or self._next_sr_entity_id(
            f"evo_organism_{self._sr_spawn_seq:05d}"
        ))
        raw_pos = req.get("position", (0.0, 0.0))
        if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
            raw_pos = (0.0, 0.0)
        r_rad = float(req.get("radius", 22.0))
        cx, cy = float(raw_pos[0]), float(raw_pos[1])
        hub = self._SceneRuntimeEntity(
            entity_id=hub_id,
            entity_type="organism",
            position=(cx, cy),
            radius=r_rad,
            rng=self._sr_runtime_rng,
        )
        try:
            hub.set_energy(float(req.get("energy", 80.0)))
        except (TypeError, ValueError):
            hub.set_energy(80.0)
        try:
            hub.set_generation(int(req.get("generation", 1)))
        except (TypeError, ValueError):
            hub.set_generation(1)
        lineage_id = req.get("lineage_id")
        death_count = req.get("death_count")
        if lineage_id:
            hud = getattr(hub, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                hub.sr_debug_hud = hud
            hud["lineage_id"] = str(lineage_id)
            if death_count is not None:
                hud["death_count"] = int(death_count)
        for script_data in req.get("scripts", []):
            if isinstance(script_data, dict):
                script = self._instantiate_scene_script(script_data, project_path)
                if script is not None:
                    hub.add_script(script)
        self.scene_runtime_entities.append(hub)

        tpl = req.get("template") if isinstance(req.get("template"), dict) else None
        if tpl is None:
            tpl = getattr(self, "_sr_membrane_template", None) or DEFAULT_MEMBRANE_TEMPLATE
        new_structural: list[dict[str, Any]] = []
        child_ids: list[str] = []

        for spec in tpl.get("sensors", []):
            if not isinstance(spec, dict):
                continue
            self._sr_spawn_seq += 1
            cid = f"{hub_id}_{spec.get('suffix', 's')}"
            dx, dy = float(spec.get("dx", 0.0)), float(spec.get("dy", 0.0))
            rad = float(spec.get("radius", 14.0))
            ent = self._SceneRuntimeEntity(
                entity_id=cid,
                entity_type="sensor",
                position=(cx + dx, cy + dy),
                radius=rad,
                rng=self._sr_runtime_rng,
            )
            ent.membrane_locked = True
            ent.pinned = False
            sname = spec.get("script")
            if sname:
                script = self._instantiate_scene_script(
                    {"name": str(sname), "type": str(spec.get("type", "")), "properties": {}},
                    project_path,
                )
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
            self._sr_membrane_attach[cid] = (hub_id, dx, dy)
            new_structural.append(
                {
                    "start": hub_id,
                    "end": cid,
                    "channel": "struct",
                    "weight": 1.0,
                    "link_kind": "hard",
                }
            )
            child_ids.append(cid)

        for spec in tpl.get("actuators", []):
            if not isinstance(spec, dict):
                continue
            self._sr_spawn_seq += 1
            cid = f"{hub_id}_{spec.get('suffix', 'a')}"
            dx, dy = float(spec.get("dx", 0.0)), float(spec.get("dy", 0.0))
            rad = float(spec.get("radius", 12.0))
            ent = self._SceneRuntimeEntity(
                entity_id=cid,
                entity_type="actuator",
                position=(cx + dx, cy + dy),
                radius=rad,
                rng=self._sr_runtime_rng,
            )
            ent.membrane_locked = True
            ent.pinned = False
            sname = spec.get("script")
            if sname:
                script = self._instantiate_scene_script(
                    {"name": str(sname), "type": str(spec.get("type", "")), "properties": {}},
                    project_path,
                )
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
            self._sr_membrane_attach[cid] = (hub_id, dx, dy)
            new_structural.append(
                {
                    "start": hub_id,
                    "end": cid,
                    "channel": "struct",
                    "weight": 1.0,
                    "link_kind": "hard",
                }
            )
            child_ids.append(cid)

        sig_edges = req.get("signal_edges")
        if isinstance(sig_edges, list) and sig_edges:
            child_signal_edges = list(sig_edges)
        else:
            from core.Lotucosm.sr_membrane_topology import expand_signal_edges

            id_to_type = {e.id: str(e.entity_type) for e in self.scene_runtime_entities}
            child_signal_edges = expand_signal_edges(
                new_structural, self._sr_membrane_attach, id_to_type
            )
        from core.Lotucosm.sr_membrane_topology import (
            dedupe_signal_edges,
            inherit_chemo_edge_weights,
            learn_chemo_edge_weights,
            membrane_child_ids_for_hub,
            mutate_signal_edges,
        )

        # --- 边权：先 inherit，再 mutate；禁止最后再均值覆盖 ---
        parent_sig = req.get("parent_signal_edges")
        parent_hub = str(req.get("parent_hub_id", "")).strip()
        if isinstance(parent_sig, list) and parent_hub:
            id_to_type = {e.id: str(e.entity_type) for e in self.scene_runtime_entities}
            parent_ent = next(
                (e for e in self.scene_runtime_entities if str(e.id) == parent_hub),
                None,
            )
            if parent_ent is not None:
                reward = float(getattr(parent_ent, "_sr_last_verify_success", 0.5))
                stress = 0.0
                hud = getattr(parent_ent, "sr_debug_hud", None)
                if isinstance(hud, dict):
                    try:
                        stress = float(hud.get("stress", hud.get("niche_pressure", 0.0)) or 0.0)
                    except (TypeError, ValueError):
                        stress = 0.0
                parent_sig = learn_chemo_edge_weights(
                    [dict(e) for e in parent_sig],
                    reward=reward,
                    stress=min(1.0, stress / 80.0),
                    learn_rate=0.04,
                )
            cs, ca = membrane_child_ids_for_hub(
                hub_id, self._sr_membrane_attach, id_to_type
            )
            ps, pa = membrane_child_ids_for_hub(
                parent_hub, self._sr_membrane_attach, id_to_type
            )
            child_signal_edges = inherit_chemo_edge_weights(
                child_signal_edges,
                parent_sig,
                child_sensor_ids=cs,
                child_actuator_ids=ca,
                parent_sensor_ids=ps,
                parent_actuator_ids=pa,
            )
        else:
            raw_w = req.get("signal_edge_weights")
            if isinstance(raw_w, list) and raw_w:
                chemo_edges = [
                    e
                    for e in child_signal_edges
                    if str(e.get("channel", "chemo")) == "chemo"
                ]
                for i, w in enumerate(raw_w):
                    if i >= len(chemo_edges):
                        break
                    try:
                        chemo_edges[i]["weight"] = float(w)
                    except (TypeError, ValueError):
                        pass
        mut_sigma = req.get("edge_mutation_sigma")
        if mut_sigma is not None:
            try:
                # 顺序契约: 必须在 inherit / 有序 weights 之后
                child_signal_edges = mutate_signal_edges(
                    child_signal_edges, float(mut_sigma), self._sr_runtime_rng
                )
            except (TypeError, ValueError):
                pass
        child_signal_edges = dedupe_signal_edges(child_signal_edges)

        self._sr_signal_edges.extend(child_signal_edges)

        self._sr_structural_edges.extend(new_structural)
        self._sr_connection_edges.extend(new_structural)
        for edge in new_structural:
            sa, sb = edge["start"], edge["end"]
            self._scene_runtime_edges.append((sa, sb))
            nb_a = set(self._scene_runtime_neighbor_ids.get(sa, frozenset()))
            nb_b = set(self._scene_runtime_neighbor_ids.get(sb, frozenset()))
            nb_a.add(sb)
            nb_b.add(sa)
            self._scene_runtime_neighbor_ids[sa] = frozenset(nb_a)
            self._scene_runtime_neighbor_ids[sb] = frozenset(nb_b)
            for cid in child_ids:
                nb_h = set(self._scene_runtime_neighbor_ids.get(hub_id, frozenset()))
                nb_h.add(cid)
                self._scene_runtime_neighbor_ids[hub_id] = frozenset(nb_h)
                nb_c = set(self._scene_runtime_neighbor_ids.get(cid, frozenset()))
                nb_c.add(hub_id)
                self._scene_runtime_neighbor_ids[cid] = frozenset(nb_c)

        hub._sr_inherited_signal_edges = [dict(edge) for edge in child_signal_edges]
        self._rebuild_sr_spring_links()
        self._sync_membrane_positions()
        if (
            getattr(self, "_unified_pond_mode", False)
            and self._worldbridge_opt_in_bridge_entry_admitted("spawn_bridge")
        ):
            try:
                from core.Lotucosm.runtime.world_bridge import bridge_spawned_organism

                bridge_spawned_organism(hub, self._ensure_unified_pond(), req)
            except Exception as exc:
                logger.debug("bridge_spawned_organism: %s", exc)
        return hub_id

    def _effective_sr_nutrient_target(self) -> int:
        """和平/恢复用 nutrient_target_peace；战争窗用 nutrient_target_war。"""
        from core.Lotucosm.sr_war_recovery import nutrient_target_for_phase

        profile = self._safe_war_profile()
        if profile is None:
            return int(getattr(self, "_sr_nutrient_target_count", 0) or 0)
        return nutrient_target_for_phase(self._current_war_phase(), profile)

    def _safe_war_profile(self) -> Any:
        try:
            return getattr(self, "_sr_war_profile", None)
        except RuntimeError:
            return None

    def _safe_war_combat_profile(self) -> Any:
        try:
            return getattr(self, "_sr_war_combat_profile", None)
        except RuntimeError:
            return None

    def _safe_war_override_until(self) -> float:
        try:
            return float(getattr(self, "_sr_war_recovery_override_until", 0.0) or 0.0)
        except RuntimeError:
            return 0.0

    def _refresh_war_phase_tick_cache(self) -> None:
        profile = self._safe_war_profile()
        if profile is None:
            self._sr_war_phase_tick_cache = None
            return
        from core.Lotucosm.sr_war_recovery import phase_at_time

        try:
            t = float(getattr(self, "_scene_runtime_time", 0.0))
        except RuntimeError:
            t = 0.0
        override = self._safe_war_override_until()
        self._sr_war_phase_tick_cache = phase_at_time(t, profile, war_override_until=override)

    def _apply_sr_respawn_mind_mutation(
        self,
        mind_snapshot: dict[str, float],
        sigma: float,
        lineage_id: str,
        death_count: int,
        now: float,
    ) -> dict[str, float]:
        """Apply the existing SR/PS mind mutation, optionally using one named stream."""
        opt_in = getattr(self, "_worldbridge_opt_in_named_stream", None)
        if opt_in is not None:
            from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
                mutate_sr_mind_with_worldbridge_named_stream,
            )

            adapted = mutate_sr_mind_with_worldbridge_named_stream(
                opt_in["context"],
                opt_in["stream_name"],
                mind_snapshot,
                float(sigma),
            )
            return dict(adapted["child"])

        from core.Lotucosm.sr_mind_gene import mind_dict_mutate

        # A real viewport owns this state from construction/load. Keep direct
        # test/tool invocation deterministic too, without restoring a module
        # global RNG or recreating the removed hash-derived legacy stream.
        rng = getattr(self, "_sr_runtime_rng", None)
        if rng is None:
            rng = create_detached_sr_entity_randomness_rng(
                lineage_id,
                "sr_respawn_mind",
                (float(death_count), float(now)),
                float(sigma),
            )
        child_mind, _deltas = mind_dict_mutate(
            mind_snapshot,
            float(sigma),
            rng,
        )
        return child_mind

    def _apply_sr_respawn_mind_mutation_if_admitted(
        self,
        mind_snapshot: dict[str, float],
        sigma: float,
        probability: float,
        lineage_id: str,
        death_count: int,
        now: float,
    ) -> tuple[dict[str, float], bool]:
        """Run the explicit two-stream pilot or preserve the legacy decision path."""
        opt_in = getattr(self, "_worldbridge_opt_in_respawn_streams", None)
        if opt_in is not None:
            from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
                run_worldbridge_named_stream_sr_respawn_handoff,
            )

            result = run_worldbridge_named_stream_sr_respawn_handoff(
                opt_in["context"],
                opt_in["decision_stream_name"],
                opt_in["mutation_stream_name"],
                mind_snapshot,
                float(sigma),
                float(probability),
            )
            return dict(result["child"]), bool(result["admitted"])

        if self._sr_runtime_rng.random() >= float(probability):
            return dict(mind_snapshot), False
        return (
            self._apply_sr_respawn_mind_mutation(
                mind_snapshot, sigma, lineage_id, death_count, now
            ),
            True,
        )

    def set_worldbridge_opt_in_named_stream(self, context: object | None, *, stream_name: str) -> None:
        """Attach one caller-owned named stream to the explicit SR respawn seam.

        No context is created here. Passing ``None`` removes the opt-in seam; the
        ordinary GameViewport path then retains its legacy randomness behavior.
        """
        if context is None:
            self.__dict__.pop("_worldbridge_opt_in_named_stream", None)
            return
        from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
            validate_worldbridge_named_stream_sr_mind_adapter,
        )

        validate_worldbridge_named_stream_sr_mind_adapter(context, stream_name)
        self._worldbridge_opt_in_named_stream = {
            "context": context,
            "stream_name": stream_name,
        }

    def set_worldbridge_opt_in_respawn_random_streams(
        self,
        context: object | None,
        *,
        decision_stream_name: str,
        mutation_stream_name: str,
    ) -> None:
        """Attach distinct caller-owned decision and mutation streams to respawn."""
        if context is None:
            self.__dict__.pop("_worldbridge_opt_in_respawn_streams", None)
            return
        from core.Lotucosm.runtime.world_bridge_named_stream_adapter import (
            validate_worldbridge_named_stream_sr_respawn_handoff,
        )

        validate_worldbridge_named_stream_sr_respawn_handoff(
            context, decision_stream_name, mutation_stream_name
        )
        self._worldbridge_opt_in_respawn_streams = {
            "context": context,
            "decision_stream_name": decision_stream_name,
            "mutation_stream_name": mutation_stream_name,
        }

    def set_worldbridge_opt_in_deterministic_randomness_context(self, context: object | None) -> None:
        """Attach a caller-owned named-stream context to explicit checkpoints only."""
        if context is None:
            self.__dict__.pop("_worldbridge_opt_in_deterministic_randomness_context", None)
            authority = vars(self).get("_worldbridge_tick_authority")
            if authority is not None:
                authority.bind_randomness_context(None)
            return
        from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
            WorldBridgeDeterministicRandomnessContext,
            register_worldbridge_deterministic_random_stream,
        )

        if not isinstance(context, WorldBridgeDeterministicRandomnessContext):
            raise TypeError("context must be a WorldBridgeDeterministicRandomnessContext")
        runtime_rng = getattr(self, "_sr_runtime_rng", None)
        if runtime_rng is not None:
            if "sr.runtime" not in context.stream_names:
                register_worldbridge_deterministic_random_stream(
                    context,
                    "sr.runtime",
                    "python_random",
                    stream=runtime_rng,
                )
            elif context.get_stream("sr.runtime") is not runtime_rng:
                raise RuntimeError("deterministic context sr.runtime is not the active SR owner")
        if "ps.pond" not in context.stream_names:
            register_worldbridge_deterministic_random_stream(
                context,
                "ps.pond",
                "numpy_pcg64_generator",
            )
        context.snapshot()
        from core.Lotucosm.script_entropy_audit import diagnose_script_entropy_admission

        admission = diagnose_script_entropy_admission(
            list(vars(self).get("_sr_script_entropy_audits", ())),
            list(vars(self).get("_sr_script_entropy_receipts", ())),
            owner_family=type(runtime_rng).__name__ if runtime_rng is not None else None,
            runtime_epoch=vars(self).get("_sr_runtime_epoch"),
            owner_stream_name="sr.runtime" if runtime_rng is not None else None,
            owner_registry_digest=(
                self._script_owner_registry_digest(runtime_rng)
                if runtime_rng is not None
                else None
            ),
        )
        self._sr_script_entropy_admission_diagnostic = admission
        if not admission["admitted"]:
            raise RuntimeError(
                "scene script entropy admission failed: " + ",".join(admission["reasons"])
            )
        self._worldbridge_opt_in_deterministic_randomness_context = context
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None:
            authority.bind_randomness_context(context)

    def _worldbridge_record_rng_phase(self, phase: str) -> None:
        """Record real SimulationDriver RNG boundaries for E502 evidence."""
        context = getattr(self, "_worldbridge_opt_in_deterministic_randomness_context", None)
        if context is None:
            return
        from core.Lotucosm.runtime.world_bridge_e502_rng_draw_order_witness import (
            capture_worldbridge_e502_rng_phase_boundary,
        )

        if phase == "sr.start":
            sessions = vars(self).setdefault("_worldbridge_e502_rng_observation_sessions", [])
            observations = []
            sessions.append(observations)
            self._worldbridge_e502_rng_observations = observations
        else:
            observations = vars(self).setdefault("_worldbridge_e502_rng_observations", [])
        order = len(observations)
        pond = vars(self).get("_unified_pond")
        ps_draw_count = int(getattr(pond, "_worldbridge_random_draw_count", 0) or 0)
        sr_draw_count = int(
            getattr(vars(self).get("_sr_runtime_rng"), "worldbridge_draw_count", 0) or 0
        )
        draw_counts = {"sr.runtime": sr_draw_count, "ps.pond": ps_draw_count}
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None and authority.current_tick() is not None:
            authority.record_rng_phase(phase, draw_counts=draw_counts)
        observations.append(
            capture_worldbridge_e502_rng_phase_boundary(
                context,
                phase,
                order,
                draw_counts=draw_counts,
            )
        )

    def _current_war_phase(self) -> str:
        try:
            cached = getattr(self, "_sr_war_phase_tick_cache", None)
        except RuntimeError:
            cached = None
        if cached is not None:
            return str(cached)
        from core.Lotucosm.sr_war_recovery import phase_at_time

        profile = self._safe_war_profile()
        if profile is None:
            return "peace"
        try:
            t = float(getattr(self, "_scene_runtime_time", 0.0))
        except RuntimeError:
            t = 0.0
        override = self._safe_war_override_until()
        return phase_at_time(t, profile, war_override_until=override)

    def _trigger_manual_war_from_key(self) -> None:
        profile = getattr(self, "_sr_war_profile", None)
        if profile is None or not profile.manual_trigger:
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        t = float(getattr(self, "_scene_runtime_time", 0.0))
        until = t + float(profile.manual_war_duration)
        if until <= float(getattr(self, "_sr_war_recovery_override_until", 0.0) or 0.0):
            return
        self._sr_war_recovery_override_until = until
        self._refresh_war_phase_tick_cache()
        chinese = isinstance(self._sr_demo_legend, dict)
        self._sr_victory_banner = "手动发动战争" if chinese else "Manual war triggered"

    def _maybe_trigger_manual_war(self, input_snap: Any) -> None:
        _ = input_snap

    def _preflush_war_nutrients(
        self, remove_ids: list[str], all_e: list[Any], dt: float
    ) -> None:
        """战争窗内在 organism 批次前清扫营养，避免导演 rest 批过晚。"""
        if self._war_combat_mode_active():
            return
        from core.Lotucosm.sr_war_recovery import WAR_NUTRIENT_PURGE_INTERVAL

        profile = self._safe_war_profile()
        if dt <= 0 or profile is None:
            return
        if self._current_war_phase() != "war":
            self._sr_war_nutrient_purge_acc = 0.0
            return
        self._sr_war_nutrient_purge_acc += dt
        if self._sr_war_nutrient_purge_acc < WAR_NUTRIENT_PURGE_INTERVAL:
            return
        self._sr_war_nutrient_purge_acc = 0.0
        pending = set(remove_ids)
        for e in all_e:
            if str(getattr(e, "entity_type", "")) != "nutrient":
                continue
            eid = str(getattr(e, "id", ""))
            if eid and eid not in pending:
                remove_ids.append(eid)
                pending.add(eid)

    def _track_war_phase_transition(self, all_e: list[Any]) -> None:
        phase = self._current_war_phase()
        prev = str(getattr(self, "_sr_war_phase_last", "peace"))
        if phase != prev:
            self._sr_war_phase_last = phase
            announced = getattr(self, "_sr_war_phase_announced", None) or set()
            if phase not in announced:
                announced.add(phase)
                self._sr_war_phase_announced = announced
                chinese = isinstance(self._sr_demo_legend, dict)
                if phase == "war":
                    msg = "战争开始" if chinese else "War began"
                elif phase == "recovery":
                    msg = "进入恢复期" if chinese else "Recovery phase"
                    orgs = sum(
                        1
                        for e in all_e
                        if str(getattr(e, "entity_type", "")) == "organism"
                    )
                    self._sr_pop_at_war_end = orgs
                else:
                    msg = ""
                if msg:
                    self._sr_victory_banner = msg
        orgs = sum(
            1 for e in all_e if str(getattr(e, "entity_type", "")) == "organism"
        )
        if phase == "war":
            cur_min = getattr(self, "_sr_war_pop_min", None)
            if cur_min is None or orgs < cur_min:
                self._sr_war_pop_min = orgs

    def _maybe_respawn_sr_nutrients(self, w: int, h: int) -> None:
        """有细胞时维持营养颗粒数量，避免吃光后空转。"""
        if self._war_combat_mode_active():
            return
        target = self._effective_sr_nutrient_target()
        if target <= 0 or w < 80 or h < 80:
            return
        orgs = sum(
            1 for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "organism"
        )
        if orgs < 1:
            return
        cur = [e for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "nutrient"]
        need = target - len(cur)
        if need <= 0:
            return
        margin = 24.0
        rad = 11.0
        for _ in range(need):
            self._sr_spawn_seq += 1
            eid = self._next_sr_entity_id(f"nutrient_sr_{self._sr_spawn_seq:05d}")
            cx = self._sr_runtime_rng.uniform(margin + rad, max(margin + rad + 1.0, float(w) - margin - rad))
            cy = self._sr_runtime_rng.uniform(margin + rad, max(margin + rad + 1.0, float(h) - margin - rad))
            ent = self._SceneRuntimeEntity(
                entity_id=eid,
                entity_type="nutrient",
                position=(cx, cy),
                radius=rad,
                rng=self._sr_runtime_rng,
            )
            ent.pinned = True
            self.scene_runtime_entities.append(ent)

    def _record_sr_reproduction_spawn(self, count: int = 1) -> None:
        self._sr_reproduction_events = int(getattr(self, "_sr_reproduction_events", 0) or 0) + max(
            0, int(count)
        )

    def _process_sr_spawn_requests(
        self, requests: List[Any], project_path: Optional[str]
    ) -> list[str]:
        """消费 spawn_requests；organism_with_membrane 走 _process_organism_with_membrane_spawn。

        返回: 本帧新生 hub_id 列表，供 bootstrap 与二次 spawn 使用。
        """
        new_hubs: list[str] = []
        for req in requests:
            if not isinstance(req, dict):
                continue
            et = str(req.get("type", "organism"))
            if et in ("game_prop", "game_actor"):
                eid = str(req.get("id") or self._next_sr_entity_id(
                    f"game_spawn_{self._sr_spawn_seq + 1:05d}"
                ))
                if any(str(getattr(e, "id", "")) == eid for e in self.scene_runtime_entities):
                    continue
                self._sr_spawn_seq += 1
                raw_pos = req.get("position", (0.0, 0.0))
                if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
                    raw_pos = (0.0, 0.0)
                r_rad = float(req.get("radius", 20.0))
                ent = self._SceneRuntimeEntity(
                    entity_id=eid,
                    entity_type=et,
                    position=(float(raw_pos[0]), float(raw_pos[1])),
                    radius=r_rad,
                    rng=self._sr_runtime_rng,
                )
                if req.get("pinned") is True:
                    ent.pinned = True
                from core.Lotucosm.sr_entity_visual import parse_sr_visual

                ent.sr_visual = parse_sr_visual(req.get("sr_visual"))
                for script_data in req.get("scripts", []):
                    if not isinstance(script_data, dict):
                        continue
                    script = self._instantiate_scene_script(script_data, project_path)
                    if script is not None:
                        ent.add_script(script)
                self.scene_runtime_entities.append(ent)
                continue
            orgs = sum(1 for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "organism")
            if orgs >= int(getattr(self, "_sr_evo_pop_cap", 96)):
                continue
            if str(req.get("type", "")) == "organism_with_membrane":
                self._sr_spawn_seq += 1
                hub_id = self._process_organism_with_membrane_spawn(req, project_path)
                new_hubs.append(hub_id)
                self._record_sr_reproduction_spawn(1)
                continue
            self._sr_spawn_seq += 1
            eid = str(req.get("id") or self._next_sr_entity_id(
                f"evo_organism_{self._sr_spawn_seq:05d}"
            ))
            raw_pos = req.get("position", (0.0, 0.0))
            if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
                raw_pos = (0.0, 0.0)
            r_rad = float(req.get("radius", 22.0))
            ent = self._SceneRuntimeEntity(
                entity_id=eid,
                entity_type=str(req.get("type", "organism")),
                position=(float(raw_pos[0]), float(raw_pos[1])),
                radius=r_rad,
                rng=self._sr_runtime_rng,
            )
            try:
                ent.set_energy(float(req.get("energy", 80.0)))
            except (TypeError, ValueError):
                ent.set_energy(80.0)
            try:
                ent.set_generation(int(req.get("generation", 1)))
            except (TypeError, ValueError):
                ent.set_generation(1)
            for script_data in req.get("scripts", []):
                if not isinstance(script_data, dict):
                    continue
                script = self._instantiate_scene_script(script_data, project_path)
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
            self._record_sr_reproduction_spawn(1)
        requests.clear()
        if getattr(self, "_unified_pond_mode", False):
            pond = self._ensure_unified_pond()
            for entity in self.scene_runtime_entities:
                if getattr(entity, "pond", None) is None:
                    entity.pond = pond
        return new_hubs

    def _membrane_children_of(self, parent_id: str) -> list[str]:
        return [cid for cid, (pid, _dx, _dy) in self._sr_membrane_attach.items() if pid == parent_id]

    def _expand_removal_with_membrane(self, ids: List[str]) -> set[str]:
        """营养移除等场景下，顺带清理已断开膜附着的孤儿组件。"""
        drop: set[str] = {str(x) for x in ids}
        changed = True
        while changed:
            changed = False
            for child_id, (pid, _dx, _dy) in list(self._sr_membrane_attach.items()):
                if child_id in drop:
                    continue
                if pid in drop:
                    drop.add(child_id)
                    changed = True
        return drop

    def _prune_topology_for_removed(self, drop: set[str]) -> None:
        self._sr_membrane_attach = {
            k: v for k, v in self._sr_membrane_attach.items() if k not in drop and v[0] not in drop
        }
        self._sr_structural_edges = [
            e
            for e in self._sr_structural_edges
            if e.get("start") not in drop and e.get("end") not in drop
        ]
        self._sr_connection_edges = [
            e
            for e in self._sr_connection_edges
            if e.get("start") not in drop and e.get("end") not in drop
        ]
        self._sr_signal_edges = [
            e
            for e in self._sr_signal_edges
            if e.get("start") not in drop and e.get("end") not in drop
        ]
        self._scene_runtime_edges = [
            (a, b) for a, b in self._scene_runtime_edges if a not in drop and b not in drop
        ]
        nb: dict[str, set[str]] = {}
        for sa, sb in self._scene_runtime_edges:
            nb.setdefault(sa, set()).add(sb)
            nb.setdefault(sb, set()).add(sa)
        self._scene_runtime_neighbor_ids = {k: frozenset(v) for k, v in nb.items()}
        self._rebuild_sr_spring_links()

    def _process_sr_removal_requests(self, ids: List[str]) -> None:
        if not ids:
            return
        drop = self._expand_removal_with_membrane(ids)
        self.scene_runtime_entities = [e for e in self.scene_runtime_entities if str(e.id) not in drop]
        self._prune_topology_for_removed(drop)
        ids.clear()

    def _sr_overlay_point_count(self) -> int:
        if self.is_playing:
            return 0
        pts = getattr(self, "_ps_replay_overlay_points", None) or []
        return len(pts)

    def get_sr_ecology_snapshot(self) -> Dict[str, Any]:
        """生态 Dock 只读快照；暂停时 sim_running 仍为 True，active=False。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        sim_running = bool(self._using_scene_runtime and self.is_playing)
        out: Dict[str, Any] = {
            "active": bool(sim_running and not self.is_paused),
            "sim_running": sim_running,
            "paused": bool(self.is_paused) if sim_running else False,
            "sim_time": float(self._scene_runtime_time) if sim_running else 0.0,
            "population": 0,
            "population_peak": int(getattr(self, "_sr_pop_peak", 0) or 0) if sim_running else 0,
            "avg_generation": 0.0,
            "wander_amp_variance": 0.0,
            "total_energy": 0.0,
            "play_goals_satisfied": None,
            "membrane_sensor_count": 0,
            "mean_edge_weight": 0.0,
            "mean_chemo_channel": 0.0,
            "unified_bridge_enabled": bool(getattr(self, "_unified_pond_mode", False)),
            "bridged_organism_count": 0,
            "reproduction_events": int(getattr(self, "_sr_reproduction_events", 0) or 0),
        }
        if not sim_running:
            out["overlay_point_count"] = self._sr_overlay_point_count()
            return out
        goals = getattr(self, "_sr_play_goals", None) or {}
        if isinstance(goals, dict) and (
            "survive_seconds" in goals or "peak_population" in goals
        ):
            out["play_goals_satisfied"] = sr_all_play_goals_satisfied(
                goals,
                float(self._scene_runtime_time),
                int(getattr(self, "_sr_pop_peak", 0) or 0),
            )
        orgs = [e for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "organism"]
        out["population"] = len(orgs)
        if not orgs:
            out["overlay_point_count"] = self._sr_overlay_point_count()
            return out
        from core.Lotucosm.sr_memory_gene_bridge import count_entity_memory_genes
        from core.Lotucosm.ps_verify import developmental_stage_from_entity
        from core.Lotucosm.social_memory import sr_social_memories

        gens: List[float] = []
        energies: List[float] = []
        wanders: List[float] = []
        memory_gene_counts: List[int] = []
        social_memory_counts: List[int] = []
        dev_stages: List[int] = []
        ladder_enabled = False
        for e in orgs:
            try:
                energies.append(float(getattr(e, "energy", 0.0) or 0.0))
            except (TypeError, ValueError):
                energies.append(0.0)
            try:
                gens.append(float(getattr(e, "generation", 0)))
            except (TypeError, ValueError):
                gens.append(0.0)
            hud = getattr(e, "sr_debug_hud", None)
            if isinstance(hud, dict) and "wander_amp" in hud:
                try:
                    wanders.append(float(hud["wander_amp"]))
                except (TypeError, ValueError):
                    pass
            memory_gene_counts.append(count_entity_memory_genes(e))
            social_memory_counts.append(len(sr_social_memories(e)))
            stage = developmental_stage_from_entity(e)
            if stage is not None:
                dev_stages.append(stage)
                ladder_enabled = True
        out["total_energy"] = sum(energies)
        out["avg_generation"] = sum(gens) / len(gens) if gens else 0.0
        if len(wanders) >= 2:
            mean_w = sum(wanders) / len(wanders)
            out["wander_amp_variance"] = sum((w - mean_w) ** 2 for w in wanders) / len(wanders)
        elif len(wanders) == 1:
            out["wander_amp_variance"] = 0.0
        if memory_gene_counts:
            out["avg_memory_gene_count"] = sum(memory_gene_counts) / len(memory_gene_counts)
        else:
            out["avg_memory_gene_count"] = 0.0
        if social_memory_counts:
            out["avg_social_memory_count"] = sum(social_memory_counts) / len(social_memory_counts)
        else:
            out["avg_social_memory_count"] = 0.0
        if dev_stages:
            out["avg_developmental_stage"] = sum(dev_stages) / len(dev_stages)
            out["pct_at_stage_s4"] = sum(1 for s in dev_stages if s >= 4) / len(dev_stages)
        else:
            out["avg_developmental_stage"] = 0.0
            out["pct_at_stage_s4"] = 0.0
        out["developmental_ladder_enabled"] = ladder_enabled
        from core.Lotucosm.runtime.world_bridge import BRIDGE_ORGANISM_ATTR

        out["bridged_organism_count"] = sum(
            1 for e in orgs if getattr(e, BRIDGE_ORGANISM_ATTR, None)
        )
        mem = self._sr_membrane_runtime_stats()
        out["membrane_sensor_count"] = int(mem.get("membrane_sensor_count", 0))
        out["mean_edge_weight"] = float(mem.get("mean_edge_weight", 0.0))
        out["mean_chemo_channel"] = float(mem.get("mean_chemo_channel", 0.0))
        out["overlay_point_count"] = self._sr_overlay_point_count()
        if self._safe_war_profile() is not None:
            out["war_phase"] = self._current_war_phase()
            pop_war_end = getattr(self, "_sr_pop_at_war_end", None)
            if pop_war_end is not None:
                out["population_at_war_end"] = int(pop_war_end)
            pop_min = getattr(self, "_sr_war_pop_min", None)
            if pop_min is not None:
                out["war_population_min"] = int(pop_min)
        return out

    def _apply_actuator_coupling(self, entities: list[Any], dt: float) -> None:
        """脚本阶段后，用膜 chemo 通道对拓扑相邻 organism 施加推力。

        与 actuator_pulse 脚本叠加；chemo 来自当帧 aggregate(use_prev=False)。
        """
        gain = 88.0
        chemo_push_gain = 120.0
        from core.Lotucosm.sr_membrane_topology import aggregate_channel_signals

        all_inbound = aggregate_channel_signals(
            self._sr_signal_edges, entities, use_prev=False
        )
        for a in entities:
            if str(getattr(a, "entity_type", "")) != "actuator":
                continue
            q = float(getattr(a, "emission_strength", 0.0))
            if q < 0.07:
                continue
            linked = self._scene_runtime_neighbor_ids.get(a.id, frozenset())
            ax_ = float(a.position[0])
            ay_ = float(a.position[1])
            ra = float(getattr(a, "radius", 18.0))
            inb = all_inbound.get(a.id, {})
            chemo = float(inb.get("chemo", 0.0) or 0.0)
            cdx = float(inb.get("chemo_dir_x", 0.0) or 0.0)
            cdy = float(inb.get("chemo_dir_y", 0.0) or 0.0)
            cg = math.hypot(cdx, cdy) + 1e-6
            for p in entities:
                if p is a:
                    continue
                if getattr(p, "pinned", False):
                    continue
                if str(getattr(p, "entity_type", "")) != "organism":
                    continue
                if p.id not in linked:
                    continue
                dx = float(p.position[0]) - ax_
                dy = float(p.position[1]) - ay_
                dist = math.hypot(dx, dy) + 1e-6
                rp = float(getattr(p, "radius", 18.0))
                reach = 42.0 + q * 62.0 + ra * 1.15
                if dist > ra + rp + reach:
                    continue
                # 已重叠时交给 sr_body_physics 接触解算，避免高斯式吸在一起
                if dist < ra + rp + 1.5:
                    continue
                geom = math.sqrt(max(ra * rp, 1.0))
                push = q * gain * dt / (dist + 28.0) * (geom / 22.0)
                p.velocity[0] += push * dx / dist
                p.velocity[1] += push * dy / dist
                if chemo > 0.02:
                    chemo_push = chemo * chemo_push_gain * dt * (0.5 + 0.5 * q)
                    p.velocity[0] += chemo_push * (cdx / cg)
                    p.velocity[1] += chemo_push * (cdy / cg)

    def _sr_caps_game(self) -> Any:
        from types import MappingProxyType

        return MappingProxyType({"dynamic_spawn": True, "dynamic_despawn": True})

    def _project_addon_lifecycle_evidence(self) -> dict[str, Any] | None:
        """Expose the active Qt-free Project Host evidence to checkpoint adapters."""
        context = getattr(self, "editor_context", None)
        loader = getattr(context, "plugin_loader", None)
        host = getattr(loader, "project_scoped_plugin_host", None)
        provider = getattr(host, "lifecycle_evidence", None)
        if not callable(provider):
            return None
        evidence = provider()
        return evidence if isinstance(evidence, dict) else None

    def _worldbridge_current_lifecycle_evidence(self) -> dict[str, Any] | None:
        """Read the adapter-local opaque SR/Pond lifetime pair without construction."""
        from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
            build_worldbridge_quarantine_lifecycle_evidence,
        )

        return build_worldbridge_quarantine_lifecycle_evidence(
            sr_runtime_epoch=vars(self).get("_sr_runtime_epoch"),
            pond_lifetime_token=vars(self).get(
                "_worldbridge_active_pond_lifetime_token"
            ),
        )

    def _observe_worldbridge_quarantine_lifecycle_disposal(
        self,
        disposal_boundary: str,
    ) -> None:
        """Record only an existing stop/discard of the captured quarantined pair."""
        from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
            build_worldbridge_quarantine_disposal_observation,
        )

        observation = build_worldbridge_quarantine_disposal_observation(
            failure_lifecycle=vars(self).get("_worldbridge_failure_lifecycle"),
            active_lifecycle=self._worldbridge_current_lifecycle_evidence(),
            disposal_boundary=disposal_boundary,
            handoff_suspended=bool(
                vars(self).get("_worldbridge_handoff_suspended", False)
            ),
        )
        if observation is not None:
            self._worldbridge_disposal_observation = observation

    def _worldbridge_opt_in_bridge_entry_admitted(self, entry_point: str) -> bool:
        """Classify one adapter bridge writer without clearing current quarantine."""
        from core.Lotucosm.runtime.world_bridge_quarantine_readmission_authority import (
            classify_worldbridge_opt_in_bridge_admission,
        )

        decision = classify_worldbridge_opt_in_bridge_admission(
            entry_point,
            unified_pond_mode=bool(vars(self).get("_unified_pond_mode", False)),
            handoff_suspended=bool(vars(self).get("_worldbridge_handoff_suspended", False)),
            current_pond_present=vars(self).get("_unified_pond") is not None,
        )
        self._worldbridge_last_quarantine_admission = decision
        return bool(decision["admitted"])

    def query_worldbridge_quarantine_diagnostic(self) -> dict[str, Any]:
        """Return a copy-isolated E240 diagnostic projection without control authority."""
        from core.Lotucosm.runtime.world_bridge_quarantine_diagnostic_provenance import (
            project_worldbridge_quarantine_diagnostic,
        )

        diagnostic = project_worldbridge_quarantine_diagnostic(
            handoff_suspended=bool(vars(self).get("_worldbridge_handoff_suspended", False)),
            failure_receipt=vars(self).get("_worldbridge_last_handoff_failure"),
            recovery_decision=vars(self).get("_worldbridge_last_recovery_decision"),
            quarantine_admission=vars(self).get("_worldbridge_last_quarantine_admission"),
            restore_diagnostic=vars(self).get("_worldbridge_restore_diagnostic"),
        )
        from core.Lotucosm.script_entropy_audit import project_script_entropy_admission

        owner_registry_digest = None
        if vars(self).get("_sr_script_entropy_audits") and vars(self).get(
            "_sr_runtime_rng"
        ) is not None:
            try:
                owner_registry_digest = self._script_owner_registry_digest()
            except (TypeError, ValueError):
                # Status projection must remain available while invalid owners
                # stay quarantined; admission paths still fail closed.
                owner_registry_digest = None

        diagnostic["script_entropy_admission"] = project_script_entropy_admission(
            vars(self).get("_sr_script_entropy_audits", []),
            vars(self).get("_sr_script_entropy_receipts", []),
            owner_family=(
                type(vars(self).get("_sr_runtime_rng")).__name__
                if vars(self).get("_sr_runtime_rng") is not None
                else None
            ),
            runtime_epoch=vars(self).get("_sr_runtime_epoch"),
            owner_stream_name=(
                "sr.runtime" if vars(self).get("_sr_runtime_rng") is not None else None
            ),
            owner_registry_digest=owner_registry_digest,
            trust_denials=vars(self).get("_sr_script_trust_denials", ()),
        )
        diagnostic["script_failure_receipts"] = copy.deepcopy(
            list(vars(self).get("_sr_script_failure_receipts", ()))
        )
        return diagnostic

    def _worldbridge_gate_handle(self) -> WorldBridgeOwnerGate:
        gate = vars(self).get("_worldbridge_owner_gate")
        if not isinstance(gate, WorldBridgeOwnerGate):
            gate = WorldBridgeOwnerGate()
            vars(self)["_worldbridge_owner_gate"] = gate
        return gate

    def worldbridge_owner_gate_snapshot(self) -> dict[str, Any]:
        """Expose detached process-local tick/checkpoint serialization evidence."""
        return GameViewport._worldbridge_gate_handle(self).snapshot()

    def capture_worldbridge_live_checkpoint(self, checkpoint_id: str | None = None) -> dict[str, Any]:
        """Capture a checkpoint-only snapshot without requiring a completed tick."""
        with GameViewport._worldbridge_gate_handle(self).hold(
            "capture_live_checkpoint"
        ):
            locked = getattr(
                self, "_capture_worldbridge_live_checkpoint_locked", None
            )
            if callable(locked):
                return locked(checkpoint_id)
            return GameViewport._capture_worldbridge_live_checkpoint_locked(
                self, checkpoint_id
            )

    def _capture_worldbridge_live_checkpoint_locked(
        self, checkpoint_id: str | None = None
    ) -> dict[str, Any]:
        from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
            WorldBridgeLiveCheckpointCoordinator,
        )
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
            create_game_viewport_live_checkpoint_adapters,
        )

        sequence = int(getattr(self, "_worldbridge_checkpoint_sequence", 0))
        identifier = checkpoint_id or f"viewport-{self._sr_runtime_epoch}-{sequence}"
        adapters = create_game_viewport_live_checkpoint_adapters(self)
        coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None or bool(
            vars(self).get("_unified_pond_mode", False)
        ):
            transaction = coordinator.capture_legacy_transaction(
                checkpoint_id=identifier,
                sequence=sequence,
            )
            checkpoint = transaction.checkpoint
        else:
            # Lightweight and pre-unified hosts historically expose only the
            # portable checkpoint owners. Keep that path independent from the
            # optional live PS transaction callback.
            checkpoint = coordinator.capture(
                checkpoint_id=identifier,
                sequence=sequence,
            )
        self._worldbridge_checkpoint_sequence = sequence + 1
        return copy.deepcopy(dict(checkpoint))

    def capture_worldbridge_live_checkpoint_transaction(
        self, checkpoint_id: str | None = None
    ) -> Any:
        """Capture a strict transaction bound to the last completed authoritative tick."""
        with GameViewport._worldbridge_gate_handle(self).hold(
            "capture_live_checkpoint_transaction"
        ):
            locked = getattr(
                self,
                "_capture_worldbridge_live_checkpoint_transaction_locked",
                None,
            )
            if callable(locked):
                return locked(checkpoint_id)
            return (
                GameViewport._capture_worldbridge_live_checkpoint_transaction_locked(
                    self, checkpoint_id
                )
            )

    def _capture_worldbridge_live_checkpoint_transaction_locked(
        self, checkpoint_id: str | None = None
    ) -> Any:
        from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
            WorldBridgeLiveCheckpointCoordinator,
        )
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
            create_game_viewport_live_checkpoint_adapters,
        )

        sequence = int(getattr(self, "_worldbridge_checkpoint_sequence", 0))
        identifier = checkpoint_id or f"viewport-{self._sr_runtime_epoch}-{sequence}"
        adapters = create_game_viewport_live_checkpoint_adapters(self)
        coordinator = WorldBridgeLiveCheckpointCoordinator(adapters)
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None and bool(vars(self).get("_unified_pond_mode", False)):
            transaction = coordinator.capture_transaction(
                checkpoint_id=identifier,
                sequence=sequence,
            )
        else:
            from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
                WorldBridgeLiveTransactionCheckpoint,
            )

            checkpoint = coordinator.capture(
                checkpoint_id=identifier,
                sequence=sequence,
            )
            transaction = WorldBridgeLiveTransactionCheckpoint(
                checkpoint=checkpoint,
                live_ps_state=None,
                live_ps_state_digest=hashlib.sha256(
                    json.dumps(
                        None,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest(),
            )
        self._worldbridge_checkpoint_sequence = sequence + 1
        return transaction

    def restore_worldbridge_live_checkpoint(self, checkpoint: Mapping[str, Any]) -> dict[str, Any]:
        """Restore checkpoint-only state while rejecting any active tick."""
        with GameViewport._worldbridge_gate_handle(self).hold(
            "restore_live_checkpoint"
        ):
            locked = getattr(
                self, "_restore_worldbridge_live_checkpoint_locked", None
            )
            if callable(locked):
                return locked(checkpoint)
            return GameViewport._restore_worldbridge_live_checkpoint_locked(
                self, checkpoint
            )

    def _restore_worldbridge_live_checkpoint_locked(
        self, checkpoint: Mapping[str, Any]
    ) -> dict[str, Any]:
        from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
            WorldBridgeLiveCheckpointCoordinator,
        )
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
            create_game_viewport_live_checkpoint_adapters,
            _validate_project_runtime_binding_for_restore,
        )

        lifecycle = checkpoint.get("lifecycle")
        if isinstance(lifecycle, Mapping):
            _validate_project_runtime_binding_for_restore(self, lifecycle)
        adapters = create_game_viewport_live_checkpoint_adapters(self)
        result = WorldBridgeLiveCheckpointCoordinator(adapters).restore(
            checkpoint,
            allow_active_tick=False,
        )
        self._worldbridge_checkpoint_sequence = max(
            int(getattr(self, "_worldbridge_checkpoint_sequence", 0)),
            int(checkpoint.get("sequence", 0)) + 1,
        )
        return result

    def restore_worldbridge_live_checkpoint_transaction(
        self, transaction: Any
    ) -> dict[str, Any]:
        """Restore one tick-bound transaction, including an active handoff scope."""
        with GameViewport._worldbridge_gate_handle(self).hold(
            "restore_live_checkpoint_transaction"
        ):
            locked = getattr(
                self,
                "_restore_worldbridge_live_checkpoint_transaction_locked",
                None,
            )
            if callable(locked):
                return locked(transaction)
            return (
                GameViewport._restore_worldbridge_live_checkpoint_transaction_locked(
                    self, transaction
                )
            )

    def _restore_worldbridge_live_checkpoint_transaction_locked(
        self, transaction: Any
    ) -> dict[str, Any]:
        from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
            WorldBridgeLiveCheckpointCoordinator,
        )
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
            create_game_viewport_live_checkpoint_adapters,
            _validate_project_runtime_binding_for_restore,
        )

        checkpoint = getattr(transaction, "checkpoint", None)
        if not isinstance(checkpoint, Mapping):
            raise TypeError("transaction must expose a checkpoint mapping")
        lifecycle = checkpoint.get("lifecycle")
        if isinstance(lifecycle, Mapping):
            _validate_project_runtime_binding_for_restore(self, lifecycle)
        tick_scope = copy.deepcopy(getattr(transaction, "tick_scope", None))
        adapters = create_game_viewport_live_checkpoint_adapters(self)
        result = WorldBridgeLiveCheckpointCoordinator(adapters).restore(
            checkpoint,
            live_ps_state=getattr(transaction, "live_ps_state", None),
            transactional_ps=True,
            tick_binding=copy.deepcopy(getattr(transaction, "tick_binding", None)),
            tick_scope=tick_scope,
            tick_authority_state=copy.deepcopy(
                getattr(transaction, "tick_authority_state", None)
            ),
            allow_active_tick=tick_scope is not None,
        )
        self._worldbridge_checkpoint_sequence = max(
            int(getattr(self, "_worldbridge_checkpoint_sequence", 0)),
            int(checkpoint.get("sequence", 0)) + 1,
        )
        return result

    def export_worldbridge_checkpoint_artifact(
        self,
        *,
        persistence_envelope: Mapping[str, Any],
        admission_witness: Mapping[str, Any],
        checkpoint: Mapping[str, Any] | None = None,
    ) -> bytes:
        """Export a validated diagnostic bundle without mutating live runtime state."""
        from core.Lotucosm.runtime.world_bridge_checkpoint_artifact import (
            build_worldbridge_checkpoint_artifact,
            encode_worldbridge_checkpoint_artifact,
        )

        candidate = checkpoint or self.capture_worldbridge_live_checkpoint()
        artifact = build_worldbridge_checkpoint_artifact(
            checkpoint=candidate,
            persistence_envelope=persistence_envelope,
            admission_witness=admission_witness,
        )
        return encode_worldbridge_checkpoint_artifact(artifact)

    def import_worldbridge_checkpoint_artifact(
        self, encoded: bytes | bytearray | memoryview
    ) -> dict[str, Any]:
        """Validate a diagnostic bundle; this API never restores live state."""
        from core.Lotucosm.runtime.world_bridge_checkpoint_artifact import (
            decode_worldbridge_checkpoint_artifact,
        )

        try:
            artifact = decode_worldbridge_checkpoint_artifact(encoded)
            persistence = artifact["persistence_envelope"]
            project_path = getattr(self, "_sr_runtime_project_path", None)
            runtime_epoch = getattr(self, "_sr_runtime_epoch", None)
            scene_path = getattr(self, "_sr_runtime_scene_path", None)
            if all(isinstance(value, str) and value.strip() for value in (project_path, runtime_epoch, scene_path)):
                from FrameCore.project_lock import load_project_lock
                from core.Lotucosm.runtime.world_bridge_component_identity_persistence import (
                    validate_worldbridge_component_identity_persistence_envelope,
                )

                project_lock = load_project_lock(project_path)
                if project_lock is None:
                    raise ValueError("project_lock_unavailable")
                binding = validate_worldbridge_component_identity_persistence_envelope(
                    persistence,
                    project_path=str(project_path),
                    project_lock=project_lock,
                    runtime_epoch=str(runtime_epoch),
                    scene_path=str(scene_path),
                )
                if not binding["valid"]:
                    raise ValueError(",".join(binding["errors"]))
            return {
                "valid": True,
                "status": "worldbridge_checkpoint_artifact_imported",
                "artifact": artifact,
                "live_restore_performed": False,
                "replay_admitted": False,
                "default_ready": False,
            }
        except (TypeError, ValueError, KeyError, OverflowError) as exc:
            diagnostic = {
                "code": "worldbridge_checkpoint_artifact_rejected",
                "errors": [str(exc) or type(exc).__name__],
            }
            diagnostic_payload = {"schema_version": 1, **diagnostic}
            diagnostic_payload["diagnostic_digest"] = hashlib.sha256(
                json.dumps(
                    diagnostic_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            self._worldbridge_restore_diagnostic = {
                **diagnostic_payload,
            }
            return {
                "valid": False,
                "status": "worldbridge_checkpoint_artifact_rejected",
                "diagnostic": copy.deepcopy(self._worldbridge_restore_diagnostic),
                "live_restore_performed": False,
                "replay_admitted": False,
                "default_ready": False,
            }

    def export_worldbridge_replay_persistence_envelope(
        self,
        *,
        corpus: Mapping[str, Any],
        restore_diagnostic: Mapping[str, Any],
    ) -> bytes:
        """Export E509 replay evidence without changing live runtime state."""
        from FrameCore.project_lock import load_project_lock
        from core.Lotucosm.runtime.world_bridge_e509_replay_persistence import (
            build_worldbridge_e509_replay_persistence_envelope,
            encode_worldbridge_e509_replay_persistence_envelope,
        )

        project_path = getattr(self, "_sr_runtime_project_path", None)
        scene_path = getattr(self, "_sr_runtime_scene_path", None)
        if not isinstance(project_path, str) or not isinstance(scene_path, str):
            raise ValueError("runtime_project_binding_unavailable")
        project_lock = load_project_lock(project_path)
        if project_lock is None:
            raise ValueError("project_lock_unavailable")
        envelope = build_worldbridge_e509_replay_persistence_envelope(
            project_path=project_path,
            project_lock=project_lock,
            scene_path=scene_path,
            corpus=corpus,
            restore_diagnostic=restore_diagnostic,
        )
        return encode_worldbridge_e509_replay_persistence_envelope(envelope)

    def import_worldbridge_replay_persistence_envelope(
        self, encoded: bytes | bytearray | memoryview
    ) -> dict[str, Any]:
        """Inspect E509 replay evidence; never restore or admit replay."""
        try:
            from FrameCore.project_lock import load_project_lock
            from core.Lotucosm.runtime.world_bridge_e509_replay_persistence import (
                decode_worldbridge_e509_replay_persistence_envelope,
            )

            project_path = getattr(self, "_sr_runtime_project_path", None)
            scene_path = getattr(self, "_sr_runtime_scene_path", None)
            if not isinstance(project_path, str) or not isinstance(scene_path, str):
                raise ValueError("runtime_project_binding_unavailable")
            project_lock = load_project_lock(project_path)
            if project_lock is None:
                raise ValueError("project_lock_unavailable")
            envelope = decode_worldbridge_e509_replay_persistence_envelope(
                encoded,
                project_path=project_path,
                project_lock=project_lock,
                scene_path=scene_path,
            )
            return {
                "valid": True,
                "status": "worldbridge_replay_persistence_imported",
                "envelope": envelope,
                "live_restore_performed": False,
                "replay_admitted": False,
                "default_ready": False,
            }
        except (TypeError, ValueError, KeyError, OverflowError) as exc:
            diagnostic = {
                "schema_version": 1,
                "code": "worldbridge_replay_persistence_rejected",
                "errors": [str(exc) or type(exc).__name__],
            }
            diagnostic["diagnostic_digest"] = hashlib.sha256(
                json.dumps(diagnostic, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            ).hexdigest()
            self._worldbridge_restore_diagnostic = copy.deepcopy(diagnostic)
            return {
                "valid": False,
                "status": "worldbridge_replay_persistence_rejected",
                "diagnostic": diagnostic,
                "live_restore_performed": False,
                "replay_admitted": False,
                "default_ready": False,
            }

    def build_worldbridge_live_checkpoint_admission_witness(
        self,
        checkpoint: Mapping[str, Any] | None = None,
        *,
        rollback_evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build explicit parity evidence for one live checkpoint.

        This is an inspection operation only.  It does not attach to the tick
        loop or mutate the viewport.  Failure rollback is intentionally an
        injected caller-owned evidence input because proving it requires a
        controlled failing adapter, not a production mutation.
        """
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_admission import (
            build_worldbridge_live_checkpoint_admission_witness,
        )
        from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
            canonical_ps_serializer_projection,
            create_game_viewport_live_checkpoint_adapters,
        )
        from core.Lotucosm.runtime.world_bridge_fresh_restore_parity import (
            capture_canonical_ps_state,
            restore_ps_state_to_fresh_pond,
        )
        from core.VitaLoom.core.bundle_paths import editor_version

        candidate = (
            dict(checkpoint)
            if checkpoint is not None
            else self.capture_worldbridge_live_checkpoint()
        )
        adapters = create_game_viewport_live_checkpoint_adapters(self)
        ps_state = candidate.get("ps_state")
        fresh_parity = False
        if isinstance(ps_state, Mapping):
            try:
                fresh = restore_ps_state_to_fresh_pond(
                    dict(ps_state), pond_class=type(self._unified_pond)
                )
                # The checkpoint carries side overlays for owners the
                # serializer drops; a fresh Pond never has them.  Compare
                # both sides as serializer-owned projections so the extra
                # metadata cannot be reported as a false parity break,
                # while every real serializer field must still match.
                fresh_parity = (
                    canonical_ps_serializer_projection(
                        capture_canonical_ps_state(fresh)
                    )
                    == canonical_ps_serializer_projection(dict(ps_state))
                )
            except Exception:
                fresh_parity = False
        # Compare the serializer's JSON state, not Python tuple/list spelling.
        # The checkpoint coordinator canonicalizes JSON containers during capture.
        try:
            current_ps_state = json.loads(
                json.dumps(adapters.capture_ps(), ensure_ascii=False, allow_nan=False)
            )
            in_place_parity = current_ps_state == ps_state
        except (TypeError, ValueError):
            in_place_parity = False
        identity_parity = adapters.capture_bridge() == candidate.get(
            "bridge_identity_links"
        )
        restore_diagnostic = vars(self).get("_worldbridge_restore_diagnostic")
        if isinstance(restore_diagnostic, Mapping):
            restore_diagnostic = {
                **dict(restore_diagnostic),
                "checkpoint_id": candidate.get("checkpoint_id"),
                "checkpoint_digest": candidate.get("digest"),
            }
        return build_worldbridge_live_checkpoint_admission_witness(
            checkpoint=candidate,
            versioned_bundle={
                "runtime_version": editor_version(),
                "sr_schema_version": 1,
                "ps_schema_version": 1,
                "bridge_schema_version": 1,
            },
            fresh_restore={"parity": fresh_parity},
            in_place_restore={"parity": in_place_parity},
            identity_registration={"parity": identity_parity},
            rollback=rollback_evidence or {},
            restore_diagnostic=restore_diagnostic,
        )

    def _ensure_unified_bridge_for_scene(self) -> None:
        """Pre-bridge scene organisms only when this runtime is admitted."""
        if not getattr(self, "_unified_pond_mode", False):
            return
        if not self._worldbridge_opt_in_bridge_entry_admitted("scene_prebridge"):
            return
        try:
            from core.Lotucosm.runtime.world_bridge import ensure_bridged_organisms

            hubs = [
                e
                for e in self.scene_runtime_entities
                if str(getattr(e, "entity_type", "")) == "organism"
            ]
            if not hubs:
                return
            pond = self._ensure_unified_pond()
            for entity in self.scene_runtime_entities:
                entity.pond = pond
            dev_profile = self._unified_bridge_profile().get("developmental")
            ensure_bridged_organisms(
                hubs,
                pond,
                profile={"developmental": dev_profile} if dev_profile else None,
                equip_pvaec=True,
            )
        except Exception:
            logger.exception("unified bridge scene prebridge failed")
            raise

    def query_worldbridge_quarantine_lifecycle_correlation(self) -> dict[str, Any]:
        """Return E241 same-adapter lifecycle evidence without runtime control."""
        from core.Lotucosm.runtime.world_bridge_quarantine_lifecycle_correlation import (
            project_worldbridge_quarantine_lifecycle_correlation,
        )

        return project_worldbridge_quarantine_lifecycle_correlation(
            diagnostic=self.query_worldbridge_quarantine_diagnostic(),
            failure_lifecycle=vars(self).get("_worldbridge_failure_lifecycle"),
            disposal_observation=vars(self).get(
                "_worldbridge_disposal_observation"
            ),
            current_lifecycle=self._worldbridge_current_lifecycle_evidence(),
        )

    def query_worldbridge_quarantine_operator_presentation(self) -> dict[str, Any]:
        """Return bounded lifecycle evidence plus the latest artifact rejection reason."""
        from core.Lotucosm.runtime.world_bridge_quarantine_operator_presentation import (
            present_worldbridge_quarantine_lifecycle,
        )

        diagnostic = vars(self).get("_worldbridge_restore_diagnostic")
        artifact_diagnostic = None
        replay_diagnostic = None
        if isinstance(diagnostic, Mapping) and diagnostic.get("code") == "worldbridge_checkpoint_artifact_rejected":
            artifact_diagnostic = {
                "recorded": True,
                "schema_version": diagnostic.get("schema_version"),
                "code": diagnostic.get("code"),
                "errors": diagnostic.get("errors"),
                "diagnostic_digest": diagnostic.get("diagnostic_digest"),
            }
        if isinstance(diagnostic, Mapping) and diagnostic.get("code") == "worldbridge_replay_persistence_rejected":
            replay_diagnostic = {
                "recorded": True,
                "schema_version": diagnostic.get("schema_version"),
                "code": diagnostic.get("code"),
                "errors": diagnostic.get("errors"),
                "diagnostic_digest": diagnostic.get("diagnostic_digest"),
            }
            replay_diagnostic["diagnostic_digest"] = hashlib.sha256(
                json.dumps(
                    {
                        "schema_version": replay_diagnostic["schema_version"],
                        "code": replay_diagnostic["code"],
                        "errors": replay_diagnostic["errors"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
        return present_worldbridge_quarantine_lifecycle(
            self.query_worldbridge_quarantine_lifecycle_correlation(),
            artifact_import_diagnostic=artifact_diagnostic,
            replay_persistence_diagnostic=replay_diagnostic,
        )

    def query_worldbridge_e512_provenance_receipt(self) -> dict[str, Any]:
        """Return only a validated, copy-isolated E512 receipt bound to this host."""
        from core.Lotucosm.runtime.world_bridge_e512_provenance_receipt import (
            validate_worldbridge_e512_provenance_receipt,
        )

        receipt = vars(self).get("_worldbridge_e512_provenance_receipt")
        if not isinstance(receipt, Mapping):
            raise ValueError("worldbridge_e512_provenance_receipt_unavailable")
        candidate = copy.deepcopy(dict(receipt))
        validation = validate_worldbridge_e512_provenance_receipt(candidate)
        if validation["valid"] is not True:
            raise ValueError("invalid E512 provenance receipt: " + ",".join(validation["errors"]))
        return candidate

    def _refresh_unified_pond_mode(self, project_config: Optional[dict] = None) -> None:
        try:
            from core.Lotucosm.runtime.world_bridge import unified_pond_enabled

            if project_config is None:
                project_config = _current_project_world_config(self.editor_context)
            enabled = unified_pond_enabled(project_config)
            if not enabled:
                self._unified_pond = None
                self._worldbridge_active_pond_lifetime_token = None
            self._unified_pond_mode = bool(enabled)
        except Exception:
            self._unified_pond_mode = False

    def _ensure_unified_pond(self) -> Any:
        if self._unified_pond is None:
            from core.Lotucosm.pond import Pond

            sw, sh = self._scene_bounds()
            self._unified_pond = Pond(
                name="unified_bridge",
                size=(float(sw), float(sh)),
                initial_organisms=0,
                initial_components=0,
                randomness_rng=self._worldbridge_ps_randomness_rng(),
            )
            self._unified_pond.identity_source = getattr(
                self, "_sr_identity_source", None
            )
            sequence = int(
                vars(self).get("_worldbridge_pond_lifetime_sequence", 0)
            ) + 1
            self._worldbridge_pond_lifetime_sequence = sequence
            self._worldbridge_active_pond_lifetime_token = (
                f"adapter_pond_lifetime_{sequence}"
            )
        opt_in_rng = self._worldbridge_ps_randomness_rng()
        if opt_in_rng is not None:
            self._unified_pond.randomness_rng = opt_in_rng
        return self._unified_pond

    def _worldbridge_ps_randomness_rng(self) -> Any:
        """Return the opt-in caller-owned PS Generator, if one is bound."""
        context = getattr(self, "_worldbridge_opt_in_deterministic_randomness_context", None)
        if context is None:
            return None
        from core.Lotucosm.runtime.world_bridge_deterministic_randomness_context import (
            register_worldbridge_deterministic_random_stream,
        )

        if "ps.pond" not in context.stream_names:
            register_worldbridge_deterministic_random_stream(
                context, "ps.pond", "numpy_pcg64_generator"
            )
        return context.get_stream("ps.pond")

    def _unified_bridge_profile(self) -> dict:
        cfg = _current_project_world_config(self.editor_context)
        dev = cfg.get("developmental_profile")
        if dev is None:
            return {}
        if not isinstance(dev, dict):
            raise TypeError("developmental_profile must be a mapping")
        return {"developmental": dev}

    def _run_unified_pond_bridge_tick(
        self,
        dt: float,
        *,
        capture_trace: bool = False,
        transactional: bool = False,
    ) -> dict[str, Any] | None:
        with GameViewport._worldbridge_gate_handle(self).hold("bridge_handoff"):
            locked = getattr(
                self, "_run_unified_pond_bridge_tick_locked", None
            )
            if callable(locked):
                return locked(
                    dt,
                    capture_trace=capture_trace,
                    transactional=transactional,
                )
            return GameViewport._run_unified_pond_bridge_tick_locked(
                self,
                dt,
                capture_trace=capture_trace,
                transactional=transactional,
            )

    def _run_unified_pond_bridge_tick_locked(
        self,
        dt: float,
        *,
        capture_trace: bool = False,
        transactional: bool = False,
    ) -> dict[str, Any] | None:
        # Some tests construct a GameViewport proxy with __new__.
        if not bool(vars(self).get("_unified_pond_mode", False)):
            return None
        # When the production tick authority owns this tick, the bridge must
        # consume exactly that delta and input batch or stay fail-closed.
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None and authority.current_tick() is not None:
            active_tick = authority.current_tick()
            binding_kwargs: dict[str, Any] = {
                "delta_time": dt,
                "input_events": list(getattr(self, "_worldbridge_input_events_last_tick", ())),
            }
            decision_digest = (
                active_tick.get("clock_decision_digest")
                if isinstance(active_tick, Mapping)
                else None
            )
            if decision_digest is not None:
                binding_kwargs["clock_decision_digest"] = decision_digest
            binding = authority.check_tick_binding(
                **binding_kwargs,
            )
            if not binding["valid"]:
                violations = list(binding["errors"])
                self._worldbridge_tick_authority_violation = {
                    "stage": "unified_pond_bridge_tick",
                    "errors": violations,
                }
                if transactional:
                    raise ValueError(
                        "unified bridge tick authority violation: "
                        + ", ".join(violations)
                    )
                return None
        # Quarantine denies every known current-runtime bridge writer before Pond reuse.
        # Keep this explicit adapter boundary visible for the E238 containment seam.
        if bool(vars(self).get("_worldbridge_handoff_suspended", False)):
            self._worldbridge_opt_in_bridge_entry_admitted("tick_handoff")
            return None
        if not self._worldbridge_opt_in_bridge_entry_admitted("tick_handoff"):
            return None
        try:
            from core.Lotucosm.runtime.world_bridge import (
                ensure_bridged_organisms,
                iter_bridged_entities,
                unified_pond_step,
                unified_pond_step_with_trace,
            )
            transaction_coordinator = None
            if transactional:
                from core.Lotucosm.runtime.world_bridge_live_checkpoint import (
                    WorldBridgeLiveCheckpointCoordinator,
                )
                from core.Lotucosm.runtime.world_bridge_live_checkpoint_adapter import (
                    create_game_viewport_live_checkpoint_adapters,
                )

                transaction_coordinator = WorldBridgeLiveCheckpointCoordinator(
                    create_game_viewport_live_checkpoint_adapters(self)
                )

            hubs = [
                e
                for e in self.scene_runtime_entities
                if str(getattr(e, "entity_type", "")) == "organism"
            ]
            if not hubs:
                return None
            pond = self._ensure_unified_pond()
            dev_profile = self._unified_bridge_profile().get("developmental")

            def prepare_bridge_mutation() -> None:
                for entity in self.scene_runtime_entities:
                    entity.pond = pond
                ensure_bridged_organisms(
                    hubs,
                    pond,
                    profile={"developmental": dev_profile} if dev_profile else None,
                    equip_pvaec=True,
                )

            if capture_trace:
                # Capture SR before preparation so the trace covers the same
                # write boundary as the transactional handoff.
                sr_checkpoint = self.get_sr_ecology_snapshot()
                physics_world = getattr(self, "_sr_physics_world", None)
                if physics_world is not None and callable(
                    getattr(physics_world, "backend_capability", None)
                ):
                    sr_checkpoint["physics_backend"] = physics_world.backend_capability()
                trace = unified_pond_step_with_trace(
                    pond,
                    hubs,
                    sr_checkpoint=sr_checkpoint,
                    delta_time=dt,
                    input_events=list(
                        getattr(self, "_worldbridge_input_events_last_tick", ())
                    ),
                    transaction_coordinator=transaction_coordinator,
                    mutation_preparation=prepare_bridge_mutation,
                )
                retired_hub_ids = [
                    str(row["sr_entity_id"])
                    for row in trace["trace"]["lanes"]["ps"]["checkpoint"].get(
                        "retired_bridge_links", []
                    )
                ]
                self._worldbridge_record_clock_consumer("ps")
                self._process_sr_removal_requests(retired_hub_ids)
                return trace
            unified_pond_step(
                pond,
                hubs,
                delta_time=dt,
                input_events=list(
                    getattr(self, "_worldbridge_input_events_last_tick", ())
                ),
                transaction_coordinator=transaction_coordinator,
                mutation_preparation=prepare_bridge_mutation,
            )
            retired_hub_ids = [
                str(entity.id)
                for entity, organism_id in iter_bridged_entities(hubs)
                if organism_id not in pond.organisms
            ]
            self._worldbridge_record_clock_consumer("ps")
            self._process_sr_removal_requests(retired_hub_ids)
        except Exception as exc:
            from core.Lotucosm.runtime.world_bridge_transaction_authority import WorldBridgeHandoffFailure

            if isinstance(exc, WorldBridgeHandoffFailure):
                from core.Lotucosm.runtime.world_bridge_recovery_authority import (
                    classify_worldbridge_handoff_failure,
                )

                receipt = dict(exc.receipt)
                self._worldbridge_last_handoff_failure = receipt
                classification = classify_worldbridge_handoff_failure(receipt)
                self._worldbridge_last_recovery_decision = classification["decision"]
                self._worldbridge_failure_lifecycle = (
                    self._worldbridge_current_lifecycle_evidence()
                )
                self._worldbridge_disposal_observation = None
                # Only verified opt-in compensation keeps this runtime eligible
                # for subsequent handoffs. Legacy or incomplete recovery stays
                # quarantined for the current lifecycle and must remain fail-closed.
                self._worldbridge_handoff_suspended = bool(
                    classification["handoff_suspended"]
                )
            if transactional:
                raise
            logger.debug("unified_pond bridge tick: %s", exc)
        return None

    def _append_unified_pond_bridge_capture_session_sample(
        self,
        dt: float,
        session: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Feed one explicit bridge hand-off into the Qt-free E219 session."""
        from core.Lotucosm.runtime.world_bridge_live_capture_session import (
            append_worldbridge_live_capture_session_evidence,
        )

        trace = self._run_unified_pond_bridge_tick(dt, capture_trace=True)
        if trace is None:
            return None
        return append_worldbridge_live_capture_session_evidence(session, trace)

    def _update_scene_runtime_entities(
        self,
        dt: float,
        *,
        clock_decision: Mapping[str, Any] | None = None,
    ) -> None:
        with GameViewport._worldbridge_gate_handle(self).hold(
            "scene_runtime_tick"
        ):
            locked = getattr(
                self, "_update_scene_runtime_entities_locked", None
            )
            if callable(locked):
                return locked(dt, clock_decision=clock_decision)
            return GameViewport._update_scene_runtime_entities_locked(
                self,
                dt,
                clock_decision=clock_decision,
            )

    def _update_scene_runtime_entities_locked(
        self,
        dt: float,
        *,
        clock_decision: Mapping[str, Any] | None = None,
    ) -> None:
        """Run one scene-runtime tick inside the viewport-owned transaction boundary.

        PVAEC, game-mode and empty-entity scenes share one begin/complete/abort
        lifetime.  Session outcomes are resolved only after the receipt has been
        sealed, because a pause may intentionally invalidate the viewport receipt.
        """
        begin_kwargs = {} if clock_decision is None else {"clock_decision": clock_decision}
        self._worldbridge_begin_tick(dt, **begin_kwargs)
        self._worldbridge_record_clock_consumer("sr")
        try:
            entities = getattr(self, "scene_runtime_entities", None)
            empty_scene = entities is not None and not list(entities)
            record_rng = getattr(self, "_worldbridge_record_rng_phase", None)
            if empty_scene:
                if callable(record_rng):
                    record_rng("sr.start")
                # Empty scenes still consume the tick's canonical input batch.
                self._sr_input_snapshot()
                self._handle_empty_sr_runtime_tick(dt)
                if callable(record_rng):
                    record_rng("sr.complete")
                    record_rng("ps.start")
                    record_rng("ps.complete")
            elif getattr(self, "_sr_game_mode", False):
                from core.Lotucosm.scene_runtime.game_tick import step_game_runtime

                if callable(record_rng):
                    record_rng("sr.start")
                step_game_runtime(self, dt)
                if callable(record_rng):
                    record_rng("sr.complete")
                    record_rng("ps.start")
                    record_rng("ps.complete")
            else:
                # SimulationDriver records the four PVAEC/SR-PS RNG boundaries.
                self._simulation_driver.tick(self, dt)
        except BaseException:
            self._worldbridge_abort_tick()
            raise

        self._worldbridge_complete_tick()
        from core.Lotucosm.scene_runtime.session_outcome import resolve_session_outcomes

        resolve_session_outcomes(self)

    def _worldbridge_begin_tick(
        self,
        dt: float,
        *,
        clock_decision: Mapping[str, Any] | None = None,
    ) -> None:
        """Open the single production delta/input/RNG binding for this tick."""
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is None or not bool(vars(self).get("_unified_pond_mode", False)):
            # The default dual path does not own an authoritative tick.  Drop a
            # binding left by an opt-in transition and invalidate its viewport
            # receipt, while preserving completed authority history and the
            # scheduler-owned input lifecycle epoch.
            if authority is not None and authority.current_tick() is not None:
                authority.clear_active_tick()
            vars(self)["_worldbridge_last_tick_receipt"] = None
            vars(self)["_worldbridge_input_events_last_tick"] = []
            return
        if authority.current_tick() is not None:
            return
        begin_kwargs: dict[str, Any] = {
            "paused": bool(vars(self).get("is_paused", False)),
            "lifecycle_action": "tick",
            "source": "game_viewport_tick",
        }
        if clock_decision is not None:
            begin_kwargs.update(
                clock_decision=clock_decision,
                clock_owner_token=vars(self).get("_worldbridge_clock_owner_token"),
                clock_runtime_epoch=vars(self).get("_sr_runtime_epoch"),
            )
        try:
            context = authority.begin_tick(dt, **begin_kwargs)
        except BaseException:
            vars(self)["_worldbridge_clock_decision"] = None
            raise
        self._worldbridge_input_events_last_tick = list(context["input_events"])

    def _worldbridge_record_clock_consumer(self, consumer: str) -> None:
        """Bind SR/PS consumption only when this tick carries a clock decision."""
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is None:
            return
        current = authority.current_tick()
        if not isinstance(current, Mapping) or "clock_decision" not in current:
            return
        authority.record_clock_consumer(consumer)

    def _worldbridge_abort_tick(self) -> None:
        """Drop the active tick binding after a failed phase without committing it."""
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is not None:
            authority.clear_active_tick()
        vars(self)["_worldbridge_clock_decision"] = None
        vars(self)["_worldbridge_last_tick_receipt"] = None
        vars(self)["_worldbridge_input_events_last_tick"] = []

    def _worldbridge_complete_tick(self) -> None:
        """Close the tick binding; evidence capture must never mutate lanes."""
        authority = vars(self).get("_worldbridge_tick_authority")
        if authority is None or authority.current_tick() is None:
            return
        try:
            self._worldbridge_last_tick_receipt = authority.complete_tick()
        except BaseException:
            authority.clear_active_tick()
            raise
        finally:
            vars(self)["_worldbridge_clock_decision"] = None

    def prepare_simulation_tick(self, dt: float) -> dict[str, Any]:
        from types import MappingProxyType

        self._scene_runtime_time += dt
        self._refresh_war_phase_tick_cache()
        sw, sh = self._scene_bounds()
        w, h = int(sw), int(sh)
        all_e = list(self.scene_runtime_entities)
        spawn_list: List[Dict[str, Any]] = []
        remove_ids: List[str] = []
        damage_list: List[tuple[str, float]] = []
        fx_list: List[Any] = []
        sr_caps = MappingProxyType({"dynamic_spawn": True, "dynamic_despawn": True})
        project_path = getattr(self.editor_context, "current_project_path", None)
        peer_scale = 14.0
        min_horizon = 340.0

        load_before = float(self._sr_biosphere_load)
        niche_p = niche_pressure_from_load(load_before, load_max=self._sr_load_max)
        deriv = (load_before - float(self._sr_biosphere_prev_load)) / dt if dt > 1e-9 else 0.0

        for entity in all_e:
            entity.emission_strength = 0.0
            entity.sr_channel_out = {}

        try:
            self._sync_membrane_positions()
        except Exception as e:
            logger.warning("膜位置同步失败: %s", e)

        input_snap = self._sr_input_snapshot()
        self._maybe_trigger_manual_war(input_snap)
        self._preflush_war_nutrients(remove_ids, all_e, dt)
        batch_common = dict(
            all_e=all_e,
            dt=dt,
            spawn_list=spawn_list,
            remove_ids=remove_ids,
            damage_list=damage_list,
            fx_list=fx_list,
            niche_p=niche_p,
            deriv=deriv,
            load_before=load_before,
            peer_scale=peer_scale,
            min_horizon=min_horizon,
            sr_caps=sr_caps,
            w=w,
            h=h,
            input_snap=input_snap,
        )
        return {
            "dt": dt,
            "w": w,
            "h": h,
            "all_e": all_e,
            "spawn_list": spawn_list,
            "remove_ids": remove_ids,
            "damage_list": damage_list,
            "fx_list": fx_list,
            "sr_caps": sr_caps,
            "project_path": project_path,
            "peer_scale": peer_scale,
            "min_horizon": min_horizon,
            "load_before": load_before,
            "niche_p": niche_p,
            "deriv": deriv,
            "input_snap": input_snap,
            "batch_common": batch_common,
        }

    def run_script_phase(self, state: dict[str, Any]) -> None:
        all_e = state["all_e"]
        batch_common = state["batch_common"]
        organisms = [e for e in all_e if str(getattr(e, "entity_type", "")) == "organism"]
        sensors = [e for e in all_e if str(getattr(e, "entity_type", "")) == "sensor"]
        actuators = [e for e in all_e if str(getattr(e, "entity_type", "")) == "actuator"]
        rest = [
            e
            for e in all_e
            if str(getattr(e, "entity_type", "")) not in ("organism", "sensor", "actuator")
        ]
        self._run_script_tick_batch(
            entities_batch=organisms, use_prev_inbound=True, **batch_common
        )
        self._run_script_tick_batch(entities_batch=sensors, use_prev_inbound=True, **batch_common)
        self._run_script_tick_batch(
            entities_batch=actuators, use_prev_inbound=False, **batch_common
        )
        self._run_script_tick_batch(entities_batch=rest, use_prev_inbound=False, **batch_common)

    def run_spawn_phase(self, state: dict[str, Any]) -> None:
        all_e = state["all_e"]
        spawn_list = state["spawn_list"]
        remove_ids = state["remove_ids"]
        damage_list = state["damage_list"]
        fx_list = state["fx_list"]
        project_path = state["project_path"]
        dt = state["dt"]
        niche_p = state["niche_p"]
        deriv = state["deriv"]
        load_before = state["load_before"]
        peer_scale = state["peer_scale"]
        min_horizon = state["min_horizon"]
        sr_caps = state["sr_caps"]
        w = state["w"]
        h = state["h"]
        input_snap = state["input_snap"]

        self._tick_war_respawn_queue(spawn_list)

        if self._war_combat_mode_active():
            try:
                self._process_sr_damage_requests(damage_list, remove_ids)
                self._process_war_combat_casualties(remove_ids, project_path=project_path)
            except Exception as e:
                logger.warning("战争互攻伤害处理失败: %s", e)
            try:
                from core.Lotucosm.sr_game_effects import create_fx_state, ingest_fx_requests

                if not hasattr(self, "_sr_game_fx") or self._sr_game_fx is None:
                    self._sr_game_fx = create_fx_state()
                ingest_fx_requests(self._sr_game_fx, fx_list)
            except Exception as e:
                logger.warning("战争特效入队失败: %s", e)

        if getattr(self, "_sr_game_mode", False):
            try:
                self._process_sr_damage_requests(damage_list, remove_ids)
            except Exception as e:
                logger.warning("游戏伤害处理失败: %s", e)
            try:
                from core.Lotucosm.sr_game_effects import create_fx_state, ingest_fx_requests

                if not hasattr(self, "_sr_game_fx") or self._sr_game_fx is None:
                    self._sr_game_fx = create_fx_state()
                ingest_fx_requests(self._sr_game_fx, fx_list)
            except Exception as e:
                logger.warning("游戏特效入队失败: %s", e)

        try:
            self._process_sr_removal_requests(remove_ids)
            all_e = list(self.scene_runtime_entities)
        except Exception as e:
            logger.warning("SR 移除实体失败: %s", e)

        try:
            new_hubs = self._process_sr_spawn_requests(spawn_list, project_path)
            all_e = list(self.scene_runtime_entities)
            if new_hubs:
                try:
                    # 顺序契约 步骤 6
                    self._bootstrap_spawned_membrane_clusters(
                        new_hubs,
                        all_e=all_e,
                        dt=dt,
                        spawn_list=spawn_list,
                        remove_ids=remove_ids,
                        damage_list=damage_list,
                        fx_list=fx_list,
                        niche_p=niche_p,
                        deriv=deriv,
                        load_before=load_before,
                        peer_scale=peer_scale,
                        min_horizon=min_horizon,
                        sr_caps=sr_caps,
                        w=w,
                        h=h,
                        input_snap=input_snap,
                    )
                    all_e = list(self.scene_runtime_entities)
                    # 顺序契约 步骤 7：bootstrap 内脚本可能再次登记 spawn
                    extra_hubs = self._process_sr_spawn_requests(spawn_list, project_path)
                    if extra_hubs:
                        try:
                            self._bootstrap_spawned_membrane_clusters(
                                extra_hubs,
                                all_e=list(self.scene_runtime_entities),
                                dt=dt,
                                spawn_list=spawn_list,
                                remove_ids=remove_ids,
                                damage_list=damage_list,
                                fx_list=fx_list,
                                niche_p=niche_p,
                                deriv=deriv,
                                load_before=load_before,
                                peer_scale=peer_scale,
                                min_horizon=min_horizon,
                                sr_caps=sr_caps,
                                w=w,
                                h=h,
                                input_snap=input_snap,
                            )
                            all_e = list(self.scene_runtime_entities)
                        except Exception as boot2:
                            logger.warning("繁殖膜二次引导失败: %s", boot2)
                except Exception as boot_exc:
                    logger.warning("繁殖膜当帧引导失败: %s", boot_exc)
        except Exception as e:
            logger.warning("SR 动态生成实体失败: %s", e)

        all_e = list(self.scene_runtime_entities)
        state["all_e"] = all_e
        state["batch_common"]["all_e"] = all_e

    def run_actuator_phase(self, state: dict[str, Any]) -> None:
        all_e = state["all_e"]
        dt = state["dt"]
        try:
            self._apply_actuator_coupling(all_e, dt)
        except Exception as e:
            logger.warning("执行器耦合失败: %s", e)

    def run_fluid_phase(self, state: dict[str, Any]) -> None:
        all_e = state["all_e"]
        dt = state["dt"]
        niche_p = state["niche_p"]
        try:
            from core.Lotucosm.sr_fluid_flow import (
                apply_extracellular_drift,
                step_nutrient_field_exchange,
            )

            fluid_cfg = getattr(self, "_sr_fluid_coupling_cfg", None)
            if fluid_cfg is not None:
                step_nutrient_field_exchange(all_e, dt, fluid_cfg)
            em_snap = {
                str(getattr(e, "id", "")): float(max(0.0, getattr(e, "emission_strength", 0.0)))
                for e in all_e
            }
            grid = getattr(self, "_sr_field_grid", None)
            if grid is not None and getattr(grid, "enabled", False):
                grid.step(all_e, em_snap, dt, niche_pressure=niche_p)
            if fluid_cfg is not None:
                apply_extracellular_drift(
                    all_e,
                    em_snap,
                    dt,
                    fluid_cfg,
                    niche_pressure=niche_p,
                    field_grid=grid,
                )
        except Exception as e:
            logger.warning("胞外流体耦合失败: %s", e)

    def run_physics_phase(self, state: dict[str, Any]) -> None:
        all_e = state["all_e"]
        dt = state["dt"]
        w = state["w"]
        h = state["h"]
        try:
            from core.Lotucosm.sr_physics2d import Physics2DMode

            world = getattr(self, "_sr_physics_world", None)
            if world is None:
                from core.Lotucosm.sr_physics2d import SrPhysics2DWorld

                world = SrPhysics2DWorld()
                self._sr_physics_world = world
            world.step_for_viewport(self, all_e, dt, float(w), float(h))
        except Exception as e:
            logger.warning("SR 2D 物理步进失败: %s", e)

    def run_survival_phase(self, state: dict[str, Any]) -> None:
        w = state["w"]
        h = state["h"]
        try:
            survivors: List[Any] = []
            dead_hub_ids: set[str] = set()
            for e in self.scene_runtime_entities:
                en = getattr(e, "energy", None)
                if en is None:
                    survivors.append(e)
                    continue
                try:
                    ev = float(en)
                except (TypeError, ValueError):
                    survivors.append(e)
                    continue
                if ev > 0.05:
                    survivors.append(e)
                else:
                    if str(getattr(e, "entity_type", "")) == "organism":
                        dead_hub_ids.add(str(e.id))
                    gen = int(getattr(e, "generation", 0))
                    hud = getattr(e, "sr_debug_hud", None)
                    wa = float(hud.get("wander_amp", 0.0)) if isinstance(hud, dict) else 0.0
                    gh = float(hud.get("gain_high_stress", 0.0)) if isinstance(hud, dict) else 0.0
                    ma = float(hud.get("mem_alpha", 0.0)) if isinstance(hud, dict) else 0.0
                    logger.info(
                        "[消亡] 世代 %d 个体 id=%s 能量耗尽（最终 %.2f）| 基因摘要 wander=%.2f gain_hi=%.2f mem_a=%.3f",
                        gen,
                        getattr(e, "id", "?"),
                        ev,
                        wa,
                        gh,
                        ma,
                    )
            if dead_hub_ids:
                drop = set(dead_hub_ids)
                for child_id, (pid, _dx, _dy) in list(self._sr_membrane_attach.items()):
                    if pid in dead_hub_ids:
                        drop.add(child_id)
                survivors = [e for e in survivors if str(e.id) not in drop]
                self._prune_topology_for_removed(drop)
            self.scene_runtime_entities = survivors
        except Exception as e:
            logger.debug("SR 拓扑修剪失败: %s", e)

        self._maybe_respawn_sr_nutrients(w, h)
        state["all_e"] = list(self.scene_runtime_entities)

    def run_snapshot_phase(self, state: dict[str, Any]) -> None:
        dt = state["dt"]
        load_before = state["load_before"]
        all_e = list(self.scene_runtime_entities)
        state["all_e"] = all_e
        if self._safe_war_profile() is not None:
            self._track_war_phase_transition(all_e)

        self._scene_runtime_emissions_prev = {
            e.id: float(max(0.0, getattr(e, "emission_strength", 0.0))) for e in all_e
        }

        org_sum = sum(
            float(max(0.0, getattr(e, "emission_strength", 0.0)))
            for e in all_e
            if str(getattr(e, "entity_type", "")) == "organism"
        )
        self._sr_biosphere_prev_load = load_before
        self._sr_biosphere_load = step_biosphere_load(
            load_before, org_sum, dt, load_max=self._sr_load_max
        )

        if not getattr(self, "_sr_game_mode", False):
            try:
                self._advance_sr_visual_integrators(dt)
            except Exception as e:
                logger.debug("视觉积分器推进失败: %s", e)

        try:
            self._snapshot_sr_channel_out_prev()
        except Exception as e:
            logger.warning("通道信号快照失败: %s", e)

        self._refresh_sr_hud(list(self.scene_runtime_entities))
        self._run_unified_pond_bridge_tick(dt, transactional=True)
        self._publish_sr_runtime_snapshots()
        try:
            envelope = self.capture_worldbridge_shared_state_envelope(dt)
            self.consume_worldbridge_shared_state_envelope(envelope)
        except Exception as exc:
            # Evidence capture must not become a second simulation authority.
            logger.debug("capture shared-state envelope failed: %s", exc)
        self._maybe_log_scene_episode(dt)

    def _apply_membrane_edge_learning(self, entities: list[Any]) -> None:
        """保留 API；边权学习改在繁殖 inherit 时一次性应用，避免每帧漂移。"""
        return


    def _advance_sr_visual_integrators(self, dt: float) -> None:
        """按当帧 chemo 流量推进胞内信号相位 + 内外流体粒子（非 scene_time 循环）。"""
        from core.Lotucosm.sr_fluid_flow import advect_fluid_particles, build_cell_fluid_state
        from core.Lotucosm.scene_runtime_world_state import niche_pressure_from_load
        from core.VitaLoom.viewports.sr_visual_renderer import _build_cell_groups
        from core.VitaLoom.viewports.sr_visual_state import (
            advance_cell_visual_integrators,
            extract_cell_visual_state,
        )

        entities = list(self.scene_runtime_entities or [])
        if not entities:
            return
        emissions = getattr(self, "_scene_runtime_emissions_prev", {}) or {}
        niche_p = niche_pressure_from_load(
            float(getattr(self, "_sr_biosphere_prev_load", 0.0)),
            load_max=float(getattr(self, "_sr_load_max", 1.0)),
        )
        id_to_ent = {str(getattr(e, "id", "")): e for e in entities}
        id_to_type = {eid: str(getattr(ent, "entity_type", "")) for eid, ent in id_to_ent.items()}
        for hub_id, member_ids in _build_cell_groups(entities, self._scene_runtime_edges or []):
            hub = id_to_ent.get(hub_id)
            if hub is None:
                continue
            cell = extract_cell_visual_state(
                hub,
                member_ids,
                id_to_ent,
                id_to_type,
                self._sr_signal_edges or [],
                entities,
            )
            advance_cell_visual_integrators(
                hub,
                cell.signal_flow,
                dt,
                vitality=cell.vitality,
                energy=cell.energy,
                arousal=cell.arousal,
                speed=cell.speed,
                stress=cell.stress,
            )
            fluid = build_cell_fluid_state(
                hub,
                member_ids,
                id_to_ent,
                id_to_type,
                cell_energy=cell.energy,
                cell_signal_flow=cell.signal_flow,
                cell_speed=cell.speed,
                cell_stress=cell.stress,
                vel_x=cell.vel_x,
                vel_y=cell.vel_y,
                membrane_phase=cell.membrane_phase,
                by_entity=cell.by_entity,
                entities=entities,
                emissions_prev=emissions,
                niche_pressure=niche_p,
            )
            cx, cy = float(hub.position[0]), float(hub.position[1])
            base_r = max(26.0, float(getattr(hub, "radius", 22.0)) * 1.35)
            advect_fluid_particles(
                hub,
                fluid,
                cx=cx,
                cy=cy,
                membrane_radius=base_r,
                dt=dt,
                entities=entities,
                emissions_prev=emissions,
                niche_pressure=niche_p,
            )

    def _maybe_announce_sr_play_goals(self) -> None:
        goals = getattr(self, "_sr_play_goals", None) or {}
        if not goals:
            return
        ann = self._sr_goal_announced
        ss = goals.get("survive_seconds")
        if ss is not None and not ann.get("survive"):
            try:
                need_t = float(ss)
            except (TypeError, ValueError):
                need_t = None
            if need_t is not None and float(self._scene_runtime_time) >= need_t:
                ann["survive"] = True
                logger.info("【演示目标】存活时长已达成：≥%.1f 秒", need_t)
        pk = goals.get("peak_population")
        if pk is not None and not ann.get("peak"):
            try:
                need_p = int(pk)
            except (TypeError, ValueError):
                need_p = None
            if need_p is not None and int(self._sr_pop_peak) >= need_p:
                ann["peak"] = True
                logger.info("【演示目标】种群峰值已达成：≥%d 个体", need_p)

    def _compact_play_goals_fragment(self, chinese: bool) -> str:
        goals = getattr(self, "_sr_play_goals", None) or {}
        if not goals:
            return ""
        self._maybe_announce_sr_play_goals()
        parts: list[str] = []
        ss = goals.get("survive_seconds")
        if ss is not None:
            try:
                need_t = float(ss)
                cur = float(self._scene_runtime_time)
                parts.append(
                    f"存活{cur:.0f}/{need_t:.0f}s"
                    if chinese
                    else f"T{cur:.0f}/{need_t:.0f}s"
                )
            except (TypeError, ValueError):
                pass
        pk = goals.get("peak_population")
        if pk is not None:
            try:
                need_p = int(pk)
                peak = int(self._sr_pop_peak)
                parts.append(
                    f"种群{peak}/{need_p}" if chinese else f"pop{peak}/{need_p}"
                )
            except (TypeError, ValueError):
                pass
        return " · ".join(parts)

    def _maybe_try_sr_victory_pause(self) -> None:
        """演示目标达成且 pause_on_complete 时写 goals_complete 并暂停；属 _SR_SESSION_FINAL_REASONS。"""
        if getattr(self, "_sr_victory_pause_done", False):
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        goals = getattr(self, "_sr_play_goals", None) or {}
        if not sr_pause_on_complete_enabled(goals):
            return
        if not sr_all_play_goals_satisfied(
            goals,
            float(self._scene_runtime_time),
            int(self._sr_pop_peak),
            self.scene_runtime_entities,
        ):
            return
        self._sr_victory_pause_done = True
        goals = getattr(self, "_sr_play_goals", None) or {}
        chinese = self._sr_ui_chinese()
        title, banner_msg, hint = sr_resolve_session_banner("victory", goals, chinese=chinese)
        self._show_session_banner("victory", banner_msg, title=title, hint=hint)
        logger.info("【演示目标】已全部达成，已自动暂停。")
        self._write_sr_session_summary("goals_complete")
        self._refresh_sr_hud(list(self.scene_runtime_entities))
        self._pause_simulation()

    def _maybe_try_sr_victory_notice(self) -> None:
        """游戏模式且 pause_on_complete=false：达成 hud 目标时只闪横幅。"""
        if getattr(self, "_sr_victory_notice_done", False):
            return
        if not getattr(self, "_sr_game_mode", False):
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        goals = getattr(self, "_sr_play_goals", None) or {}
        if sr_pause_on_complete_enabled(goals):
            return
        hud_key = goals.get("hud_victory_key")
        if not isinstance(hud_key, str) or not hud_key.strip():
            return
        if not sr_hud_victory_satisfied(hud_key.strip(), self.scene_runtime_entities):
            return
        self._sr_victory_notice_done = True
        chinese = self._sr_ui_chinese()
        title, banner_msg, hint = sr_resolve_session_banner("victory", goals, chinese=chinese)
        self._show_session_banner("victory", banner_msg, title=title, hint=hint)
        logger.info("【游戏模式】关卡目标已达成，按场景配置继续运行。")
        self._refresh_sr_hud(list(self.scene_runtime_entities))

    def _maybe_try_sr_play_goals_notice(self) -> None:
        """PVAEC：演示目标全部达成时闪横幅一次，不暂停（pause_on_complete=false）。"""
        if getattr(self, "_sr_victory_notice_done", False):
            return
        if getattr(self, "_sr_victory_pause_done", False):
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        goals = getattr(self, "_sr_play_goals", None) or {}
        if sr_pause_on_complete_enabled(goals):
            return
        if not sr_all_play_goals_satisfied(
            goals,
            float(self._scene_runtime_time),
            int(self._sr_pop_peak),
            self.scene_runtime_entities,
        ):
            return
        self._sr_victory_notice_done = True
        chinese = self._sr_ui_chinese()
        title, banner_msg, hint = sr_resolve_session_banner("victory", goals, chinese=chinese)
        self._show_session_banner("victory", banner_msg, title=title, hint=hint)
        logger.info("【演示目标】已全部达成，模拟继续运行。")
        self._refresh_sr_hud(list(self.scene_runtime_entities))

    def _maybe_try_sr_defeat_pause(self) -> None:
        """游戏模式：hud_defeat_key 达成时显示 Game Over 并暂停。"""
        if getattr(self, "_sr_defeat_pause_done", False):
            return
        if getattr(self, "_sr_victory_pause_done", False):
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        goals = getattr(self, "_sr_play_goals", None) or {}
        key = goals.get("hud_defeat_key")
        if not isinstance(key, str) or not key.strip():
            return
        if not sr_hud_victory_satisfied(key.strip(), self.scene_runtime_entities):
            return
        self._sr_defeat_pause_done = True
        chinese = self._sr_ui_chinese()
        title, banner_msg, hint = sr_resolve_session_banner("defeat", goals, chinese=chinese)
        self._show_session_banner("extinction", banner_msg, title=title, hint=hint)
        logger.info("【游戏模式】失败条件已达成，已自动暂停。")
        self._write_sr_session_summary("extinction")
        self._refresh_sr_hud(list(self.scene_runtime_entities))
        self._pause_simulation()

    def _maybe_try_sr_extinction_pause(self) -> None:
        """细胞数为 0 且 sr_pause_on_extinction 时写 extinction 并暂停；跳过开局 0.15s。"""
        if getattr(self, "_sr_game_mode", False):
            return
        if getattr(self, "_sr_extinction_pause_done", False):
            return
        if getattr(self, "_sr_victory_pause_done", False):
            return
        if not self._using_scene_runtime or not self.is_playing or self.is_paused:
            return
        if not getattr(self, "_sr_pause_on_extinction", False):
            return
        n_org = sum(
            1 for e in self.scene_runtime_entities if str(getattr(e, "entity_type", "")) == "organism"
        )
        if n_org > 0:
            return
        if float(self._scene_runtime_time) < 0.15:
            return
        self._sr_extinction_pause_done = True
        goals = getattr(self, "_sr_play_goals", None) or {}
        chinese = self._sr_ui_chinese()
        title, banner_msg, hint = sr_resolve_session_banner("extinction", goals, chinese=chinese)
        self._show_session_banner("extinction", banner_msg, title=title, hint=hint)
        logger.info("【主世界】种群已灭绝，已自动暂停。")
        self._write_sr_session_summary("extinction")
        self._refresh_sr_hud(list(self.scene_runtime_entities))
        self._pause_simulation()

    def _process_sr_damage_requests(
        self,
        damage_requests: list[Any],
        remove_ids: list[str],
    ) -> None:
        if not damage_requests:
            return
        combat = getattr(self, "_sr_war_combat_profile", None)
        war_combat = self._war_combat_mode_active()
        id_to_ent = {str(getattr(e, "id", "")): e for e in self.scene_runtime_entities}
        pending = set(remove_ids)
        for item in damage_requests:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                tid = str(item[0])
                try:
                    amount = float(item[1])
                except (TypeError, ValueError):
                    amount = 0.0
                attacker_id = str(item[2]) if len(item) >= 3 else ""
            else:
                continue
            ent = id_to_ent.get(tid)
            if ent is None or tid in pending:
                continue
            hud = getattr(ent, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                ent.sr_debug_hud = hud
            if war_combat and combat is not None:
                if "hp" not in hud:
                    hud["hp"] = float(combat.base_hp)
                    hud["hp_max"] = float(combat.base_hp)
                try:
                    hp = float(hud.get("hp", combat.base_hp)) - amount
                except (TypeError, ValueError):
                    hp = 0.0
                hud["hp"] = hp
                hud["hit_flash"] = 0.18
                if attacker_id:
                    hud["last_attacker_id"] = attacker_id
                    atk = id_to_ent.get(attacker_id)
                    if atk is not None:
                        ah = getattr(atk, "sr_debug_hud", None)
                        if not isinstance(ah, dict):
                            ah = {}
                            atk.sr_debug_hud = ah
                        ah["last_hit_target"] = tid
                if hp <= 0.05:
                    pending.add(tid)
                    if not hasattr(self, "_sr_war_pending_casualties"):
                        self._sr_war_pending_casualties = []
                    self._sr_war_pending_casualties.append(
                        {"hub_id": tid, "attacker_id": attacker_id}
                    )
                continue
            try:
                hp = float(hud.get("hp", 30.0)) - amount
            except (TypeError, ValueError):
                hp = 0.0
            hud["hp"] = hp
            hud["hit_flash"] = 0.18
            if hp <= 0.05:
                pending.add(tid)
                remove_ids.append(tid)

    def _process_war_combat_casualties(
        self,
        remove_ids: list[str],
        *,
        project_path: Optional[str],
    ) -> None:
        pending = list(getattr(self, "_sr_war_pending_casualties", None) or [])
        self._sr_war_pending_casualties = []
        if not pending:
            return
        combat = getattr(self, "_sr_war_combat_profile", None)
        if combat is None:
            return
        id_to_ent = {str(getattr(e, "id", "")): e for e in self.scene_runtime_entities}
        lineage = getattr(self, "_sr_combat_lineage", None) or {}
        try:
            queue = getattr(self, "_sr_war_respawn_queue", None) or []
        except RuntimeError:
            queue = []
        now = float(getattr(self, "_scene_runtime_time", 0.0))
        for entry in pending:
            hub_id = str(entry.get("hub_id", ""))
            attacker_id = str(entry.get("attacker_id", ""))
            ent = id_to_ent.get(hub_id)
            if ent is None:
                continue
            hud = getattr(ent, "sr_debug_hud", None) or {}
            lineage_id = str(hud.get("lineage_id") or hub_id)
            state = dict(lineage.get(lineage_id) or {})
            death_count = int(state.get("death_count", hud.get("death_count", 0)) or 0)
            if attacker_id:
                atk = id_to_ent.get(attacker_id)
                if atk is not None:
                    ah = getattr(atk, "sr_debug_hud", None)
                    if isinstance(ah, dict):
                        ah["combat_score"] = int(ah.get("combat_score", 0) or 0) + int(combat.kill_score)
                        self._sr_war_kills_total = int(getattr(self, "_sr_war_kills_total", 0) or 0) + 1
            from core.Lotucosm.sr_war_combat import death_mutation_probability

            p_mut = death_mutation_probability(death_count, combat)
            mind_snapshot = dict(state.get("mind") or {})
            for script in getattr(ent, "scripts", []) or []:
                raw = getattr(script, "_scene_script_properties", None)
                if isinstance(raw, dict) and raw.get("mind"):
                    mind_snapshot = dict(raw.get("mind") or mind_snapshot)
                    break
            mutated = False
            if mind_snapshot:
                mind_snapshot, mutated = self._apply_sr_respawn_mind_mutation_if_admitted(
                    mind_snapshot,
                    float(combat.death_mutation_sigma),
                    p_mut,
                    lineage_id,
                    death_count,
                    now,
                )
            death_count += 1
            respawns = int(state.get("respawn_count", 0) or 0)
            state.update(
                {
                    "death_count": death_count,
                    "mind": mind_snapshot,
                    "mutated_last_death": mutated,
                    "lineage_id": lineage_id,
                    "respawn_count": respawns,
                }
            )
            lineage[lineage_id] = state
            props = {}
            for script in getattr(ent, "scripts", []) or []:
                raw = getattr(script, "_scene_script_properties", None)
                if isinstance(raw, dict):
                    props = dict(raw)
                    break
            if mind_snapshot:
                props = dict(props)
                props["mind"] = dict(mind_snapshot)
            scripts_data = [
                {
                    "name": "evo_war_recovery_brain_pvaec",
                    "type": "EvoWarRecoveryBrainPvaec",
                    "properties": props,
                }
            ]
            if respawns < int(combat.max_respawns_per_lineage):
                queue.append(
                    {
                        "lineage_id": lineage_id,
                        "at_time": now + float(combat.respawn_delay),
                        "position": list(ent.position),
                        "radius": float(getattr(ent, "radius", 28.0)),
                        "energy": float(getattr(ent, "energy", 100.0)),
                        "generation": int(getattr(ent, "generation", 0)) + (1 if mutated else 0),
                        "scripts": scripts_data,
                        "death_count": death_count,
                    }
                )
                state["respawn_count"] = respawns + 1
                lineage[lineage_id] = state
                self._sr_war_respawn_count = int(getattr(self, "_sr_war_respawn_count", 0) or 0) + 1
            drop = [hub_id] + self._membrane_children_of(hub_id)
            for did in drop:
                if did not in remove_ids:
                    remove_ids.append(did)
        self._sr_combat_lineage = lineage
        self._sr_war_respawn_queue = queue

    def _tick_war_respawn_queue(self, spawn_list: list[Any]) -> None:
        try:
            queue = list(getattr(self, "_sr_war_respawn_queue", None) or [])
        except RuntimeError:
            queue = []
        if not queue:
            return
        try:
            now = float(getattr(self, "_scene_runtime_time", 0.0))
        except RuntimeError:
            now = 0.0
        combat = self._safe_war_combat_profile()
        remain: list[dict[str, Any]] = []
        for item in queue:
            if float(item.get("at_time", 0.0)) > now:
                remain.append(item)
                continue
            lineage_id = str(item.get("lineage_id", "respawn"))
            self._sr_spawn_seq += 1
            hub_id = self._next_sr_entity_id(f"{lineage_id}_r{self._sr_spawn_seq:04d}")
            spawn_list.append(
                {
                    "type": "organism_with_membrane",
                    "hub_id": hub_id,
                    "position": item.get("position", (0.0, 0.0)),
                    "radius": item.get("radius", 28.0),
                    "energy": item.get("energy", 100.0),
                    "generation": item.get("generation", 0),
                    "scripts": item.get("scripts") or [],
                    "template": getattr(self, "_sr_membrane_template", None),
                    "lineage_id": lineage_id,
                    "death_count": item.get("death_count", 0),
                }
            )
            state = dict((getattr(self, "_sr_combat_lineage", None) or {}).get(lineage_id) or {})
            state["last_hub_id"] = hub_id
            self._sr_combat_lineage[lineage_id] = state
        self._sr_war_respawn_queue = remain

    # === SR: HUD（控制栏一行；图例在 paintEvent 画布左下角）====================

    def _refresh_sr_hud(self, all_e: list[Any]) -> None:
        """SR 控制栏：精简一行状态 + 可选第二行（横幅/复盘）。

        职责: 时间、细胞、目标片段、能量/趋化、膜通道均值；不重复 sr_demo_legend 全文。
        图例: _paint_sr_demo_legend_overlay。详细调试: LOTUCOSM_SR_HUD_VERBOSE=1。
        """
        if not hasattr(self, "_sr_hud_label"):
            return
        if not self._using_scene_runtime or not self.is_playing:
            self._sr_hud_label.setVisible(False)
            return
        chinese = isinstance(self._sr_demo_legend, dict)
        if getattr(self, "_sr_game_mode", False):
            player_id = str(getattr(self, "_sr_player_id", "player"))
            player = next(
                (e for e in all_e if str(getattr(e, "id", "")) == player_id),
                None,
            )
            parts = [f"t={self._scene_runtime_time:.1f}s"]
            if player is not None:
                hud = getattr(player, "sr_debug_hud", None)
                if isinstance(hud, dict):
                    hp = hud.get("hp")
                    hp_max = hud.get("hp_max")
                    if hp is not None and hp_max is not None:
                        parts.append(
                            f"生命{float(hp):.0f}/{float(hp_max):.0f}"
                            if chinese
                            else f"HP{float(hp):.0f}/{float(hp_max):.0f}"
                        )
                    elif hp is not None:
                        parts.append(f"生命{float(hp):.0f}" if chinese else f"HP{float(hp):.0f}")
            for ent in all_e:
                hud = getattr(ent, "sr_debug_hud", None)
                if not isinstance(hud, dict):
                    continue
                left = hud.get("enemies_left")
                total = hud.get("enemies_total")
                if left is not None and total is not None:
                    parts.append(f"敌{int(left)}/{int(total)}" if chinese else f"foes{int(left)}/{int(total)}")
                    break
                if left is not None:
                    parts.append(f"敌{int(left)}" if chinese else f"foes{int(left)}")
                    break
            goals_frag = self._compact_play_goals_fragment(chinese)
            if goals_frag:
                parts.append(goals_frag)
            self._sr_hud_label.setText(" · ".join(parts))
            self._sr_hud_label.setVisible(True)
            return
        orgs = [e for e in all_e if str(getattr(e, "entity_type", "")) == "organism"]
        n_org = len(orgs)
        if n_org > int(getattr(self, "_sr_pop_peak", 0) or 0):
            self._sr_pop_peak = n_org
        chinese = isinstance(self._sr_demo_legend, dict)
        peak = int(self._sr_pop_peak)
        goals_frag = self._compact_play_goals_fragment(chinese)
        parts = [
            f"t={self._scene_runtime_time:.1f}s",
            f"细胞{n_org}(峰{peak})" if chinese else f"org{n_org}(pk{peak})",
        ]
        if goals_frag:
            parts.append(goals_frag)
        war_phase = self._current_war_phase()
        profile = self._safe_war_profile()
        if profile is not None:
            from core.Lotucosm.sr_war_recovery import phase_countdown_hud, phase_label_zh

            pl = phase_label_zh(war_phase) if chinese else war_phase
            parts.append(f"阶段·{pl}" if chinese else f"phase·{pl}")
            countdown = phase_countdown_hud(
                float(self._scene_runtime_time),
                profile,
                war_override_until=self._safe_war_override_until(),
                chinese=chinese,
            )
            if countdown:
                parts.append(countdown)
            pop_min = getattr(self, "_sr_war_pop_min", None)
            if war_phase in ("war", "recovery") and pop_min is not None:
                parts.append(
                    f"战损低{int(pop_min)}" if chinese else f"war min {int(pop_min)}"
                )
            if profile.manual_trigger:
                parts.append("W发动战争" if chinese else "W=war")
            top_score = 0
            top_deaths = 0
            for o in orgs:
                h = getattr(o, "sr_debug_hud", None)
                if isinstance(h, dict):
                    top_score = max(top_score, int(h.get("combat_score", 0) or 0))
                    top_deaths = max(top_deaths, int(h.get("death_count", 0) or 0))
            if top_score > 0:
                parts.append(f"积分{top_score}" if chinese else f"score{top_score}")
            if top_deaths > 0:
                from core.Lotucosm.sr_war_combat import death_mutation_probability

                combat = self._safe_war_combat_profile()
                if combat is not None:
                    p = death_mutation_probability(top_deaths, combat)
                    parts.append(
                        f"战亡{top_deaths}·变异{p:.0%}" if chinese else f"deaths{top_deaths}·mut{p:.0%}"
                    )
        max_gen = 0
        for e in orgs:
            try:
                max_gen = max(max_gen, int(getattr(e, "generation", 0)))
            except (TypeError, ValueError):
                pass
        if max_gen > 0:
            parts.append(f"世代≤{max_gen}" if chinese else f"gen≤{max_gen}")
        brain = next((e for e in all_e if getattr(e, "id", "") == "ai_organism_01"), None)
        if brain is None:
            for e in orgs:
                h = getattr(e, "sr_debug_hud", None)
                if isinstance(h, dict) and "energy" in h:
                    brain = e
                    break
        if brain is not None:
            hud = getattr(brain, "sr_debug_hud", None)
            if isinstance(hud, dict) and "energy" in hud:
                cg = float(
                    hud.get(
                        "chemo_gain_scale",
                        getattr(brain, "sr_chemo_gain_scale", 1.0),
                    )
                )
                parts.append(
                    f"能量{float(hud.get('energy', 0.0)):.0f} 趋化{cg:.2f}"
                    if chinese
                    else f"E{float(hud.get('energy', 0.0)):.0f} chemo{cg:.2f}"
                )
        chemo_ch: list[float] = []
        for e in all_e:
            if str(getattr(e, "entity_type", "")) != "sensor":
                continue
            raw = getattr(e, "sr_channel_out", None)
            if isinstance(raw, dict):
                try:
                    chemo_ch.append(float(raw.get("chemo", 0.0)))
                except (TypeError, ValueError):
                    pass
        if chemo_ch:
            mc = sum(chemo_ch) / len(chemo_ch)
            parts.append(
                f"膜通道{mc:.2f}" if chinese else f"ch{mc:.2f}"
            )
        txt = " · ".join(parts)
        if n_org == 0:
            txt += " · 无存活细胞" if chinese else " · extinct"
        if self._sr_hud_verbose():
            niche_p = niche_pressure_from_load(
                float(self._sr_biosphere_load), load_max=self._sr_load_max
            )
            txt += f" · 生态位{niche_p:.2f}" if chinese else f" · niche{niche_p:.2f}"
        extra: list[str] = []
        vb = getattr(self, "_sr_victory_banner", None)
        if isinstance(vb, str) and vb.strip():
            extra.append(vb.strip())
        eb = getattr(self, "_sr_extinction_banner", None)
        if isinstance(eb, str) and eb.strip():
            extra.append(eb.strip())
        last_md = getattr(self, "_sr_last_session_md_path", None)
        if self.is_paused and last_md is not None and last_md.is_file():
            rel = self._repo_relative_path(last_md)
            extra.append(f"复盘 {rel}" if chinese else f"replay {rel}")
        if extra:
            txt += "\n" + " · ".join(extra)
        self._sr_hud_label.setText(txt)
        self._sr_hud_label.setVisible(True)

    def _maybe_log_scene_episode(self, dt: float) -> None:
        if not getattr(self, '_episode_log_enabled', False) or not self._using_scene_runtime:
            return
        self._episode_sim_accumulator += dt
        if self._episode_sim_accumulator < self._episode_duration_sim_time:
            return
        self._episode_sim_accumulator = 0.0
        self._episode_index += 1
        try:
            from core.VitaLoom.core.bundle_paths import application_root

            root = application_root()
            log_dir = root / 'logs' / 'episodes'
            log_dir.mkdir(parents=True, exist_ok=True)
            orgs = [e for e in self.scene_runtime_entities if str(getattr(e, 'entity_type', '')) == 'organism']
            speeds = []
            for e in orgs:
                v = getattr(e, 'velocity', [0, 0])
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    speeds.append(math.hypot(float(v[0]), float(v[1])))
            goals = getattr(self, "_sr_play_goals", None) or {}
            has_goal_metrics = isinstance(goals, dict) and (
                "survive_seconds" in goals or "peak_population" in goals
            )
            cfg_snap = sr_play_goals_episode_config_snapshot(goals)
            payload = {
                'episode_index': self._episode_index,
                'sim_time_end': self._scene_runtime_time,
                'entity_count': len(self.scene_runtime_entities),
                'organism_count': len(orgs),
                'mean_speed': sum(speeds) / len(speeds) if speeds else 0.0,
                'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                'sr_organism_peak': int(getattr(self, "_sr_pop_peak", 0) or 0),
                'sr_play_goals_config': cfg_snap,
            }
            if has_goal_metrics:
                payload["sr_play_goals_satisfied"] = sr_all_play_goals_satisfied(
                    goals,
                    float(self._scene_runtime_time),
                    int(self._sr_pop_peak),
                )
                payload["sr_play_goals_victory_pause_triggered"] = bool(
                    getattr(self, "_sr_victory_pause_done", False)
                )
            else:
                payload["sr_play_goals_satisfied"] = None
                payload["sr_play_goals_victory_pause_triggered"] = None
            payload["sr_extinction_pause_triggered"] = bool(
                getattr(self, "_sr_extinction_pause_done", False)
            )
            out = log_dir / f'scene_episode_{self._episode_index:05d}.json'
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.warning('Episode log failed: %s', e)

    def _instantiate_scene_script(self, script_data: dict[str, Any], project_path: Optional[str]) -> Optional[Any]:
        """动态 import 项目 scripts/*.py；匹配 ScriptBase 子类，properties 挂到 _scene_script_properties。"""
        script_path = ""
        try:
            script_path = script_data.get("path")
            script_name = script_data.get("name", "")
            if (not script_path) and project_path and script_name:
                script_path = os.path.join(project_path, "scripts", f"{script_name}.py")
            declared_paths = vars(self).setdefault("_sr_script_declared_paths", [])
            normalized_script_path = str(script_path or "")
            if normalized_script_path not in declared_paths:
                declared_paths.append(normalized_script_path)
            if not script_path or not os.path.exists(script_path):
                self._record_script_failure(script_path, "resolve", "script_not_found")
                return None

            from core.Lotucosm.script_entropy_audit import (
                audit_script_entropy,
                build_script_entropy_receipt,
            )

            source_bytes = Path(script_path).read_bytes()
            source_text = source_bytes.decode("utf-8")
            source_digest = hashlib.sha256(source_bytes).hexdigest()
            from core.Lotucosm.script_trust_policy import evaluate_project_script_trust

            trust = evaluate_project_script_trust(
                script_path,
                project_path,
                source_sha256=source_digest,
            )
            if not trust["trusted"]:
                vars(self).setdefault("_sr_script_trust_denials", []).append({
                    "path": str(script_path),
                    "reason": trust["reason"],
                })
                self._record_script_failure(script_path, "trust", str(trust["reason"]))
                return None
            entropy_audit = audit_script_entropy(source_text, path=str(script_path))
            entropy_audit["source_sha256"] = source_digest
            entropy_audit["trust"] = trust
            deterministic_context = vars(self).get(
                "_worldbridge_opt_in_deterministic_randomness_context"
            )
            if deterministic_context is not None and not entropy_audit["deterministic_ready"]:
                raise RuntimeError(
                    "scene script has undeclared entropy authorities: "
                    + str(script_path)
                )

            from core.Lotucosm.scripts import ScriptBase

            canonical_script_path = str(Path(script_path).resolve())
            script_identity = hashlib.sha256(
                canonical_script_path.encode("utf-8")
            ).hexdigest()[:16]
            module_name = f"vitaloom_user_script_{script_identity}"
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                self._record_script_failure(script_path, "load", "loader_unavailable")
                return None
            module = importlib.util.module_from_spec(spec)
            exec(compile(source_bytes, script_path, "exec"), module.__dict__)
            if hashlib.sha256(Path(script_path).read_bytes()).hexdigest() != source_digest:
                raise RuntimeError("scene script source changed during admission")

            candidates: list[type] = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ScriptBase) and attr is not ScriptBase:
                    candidates.append(attr)

            if not candidates:
                self._record_script_failure(script_path, "discover", "script_type_missing")
                return None

            type_name = (script_data.get("type") or "").strip()
            if type_name:
                for cls in candidates:
                    if cls.__name__ == type_name:
                        inst = cls()
                        if hashlib.sha256(Path(script_path).read_bytes()).hexdigest() != source_digest:
                            raise RuntimeError("scene script source changed during admission")
                        setattr(inst, "_scene_script_properties", script_data.get("properties") or {})
                        setattr(inst, "_scene_script_path", str(script_path))
                        setattr(inst, "_script_entropy_audit", entropy_audit)
                        receipt = self._build_script_entropy_receipt(
                            entropy_audit, source_digest, build_script_entropy_receipt
                        )
                        self._commit_script_entropy_evidence(entropy_audit, receipt)
                        return inst

            non_pvaec_base = [c for c in candidates if c.__name__ != "PvaecScript"]
            chosen = non_pvaec_base[0] if non_pvaec_base else candidates[0]
            inst = chosen()
            if hashlib.sha256(Path(script_path).read_bytes()).hexdigest() != source_digest:
                raise RuntimeError("scene script source changed during admission")
            setattr(inst, "_scene_script_properties", script_data.get("properties") or {})
            setattr(inst, "_scene_script_path", str(script_path))
            setattr(inst, "_script_entropy_audit", entropy_audit)
            receipt = self._build_script_entropy_receipt(
                entropy_audit, source_digest, build_script_entropy_receipt
            )
            self._commit_script_entropy_evidence(entropy_audit, receipt)
            return inst
        except Exception as e:
            reason = "source_changed" if "source changed" in str(e) else "construction_failed"
            if "undeclared entropy" in str(e):
                reason = "entropy_denied"
            elif "receipt requires" in str(e):
                reason = "receipt_unavailable"
            self._record_script_failure(script_path, "construct", reason, e)
            logger.warning("实例化场景脚本失败: %s (script=%s)", e, script_data)
            return None

    def _record_script_failure(
        self,
        script_path: Any,
        phase: str,
        reason: str,
        error: BaseException | None = None,
    ) -> None:
        """Record sanitized dynamic-script failure evidence without source text."""
        receipt = {
            "schema_version": 1,
            "status": "script_runtime_failure",
            "path": str(script_path or ""),
            "phase": str(phase),
            "reason": str(reason),
            "exception_type": type(error).__name__ if error is not None else None,
            "runtime_epoch": vars(self).get("_sr_runtime_epoch"),
            "entropy_evidence_committed": False,
            "identity_or_pond_mutation": False,
        }
        vars(self).setdefault("_sr_script_failure_receipts", []).append(receipt)

    def _record_script_runtime_failure(
        self,
        script_path: Any,
        phase: str,
        reason: str,
        error: BaseException | None = None,
    ) -> None:
        """Record runtime execution failure and conservatively mark mutation risk."""
        self._record_script_failure(script_path, phase, reason, error)
        receipt = vars(self).get("_sr_script_failure_receipts", [])[-1]
        receipt["identity_or_pond_mutation"] = True

    def _build_script_entropy_receipt(
        self,
        audit: dict[str, Any],
        source_digest: str,
        receipt_builder: Any,
    ) -> dict[str, Any]:
        """Build evidence against the exact source bytes executed for this script."""
        owner = vars(self).get("_sr_runtime_rng")
        epoch = vars(self).get("_sr_runtime_epoch")
        if owner is None or epoch is None:
            raise RuntimeError("script entropy receipt requires an active SR owner")
        return receipt_builder(
            audit,
            owner_family=type(owner).__name__,
            runtime_epoch=str(epoch),
            source_sha256=source_digest,
            owner_stream_name="sr.runtime",
            owner_registry_digest=self._script_owner_registry_digest(owner),
        )

    def _script_owner_registry_digest(self, owner: Any | None = None) -> str:
        """Return the stable identity digest for the active SR script owner."""
        from core.Lotucosm.runtime.world_bridge_randomness_authority import (
            build_caller_owned_stream_registry_digest,
        )

        runtime_owner = owner if owner is not None else vars(self).get("_sr_runtime_rng")
        if runtime_owner is None:
            raise RuntimeError("script owner registry requires an active SR owner")
        # Script entropy receipts bind project code to the SR caller-held
        # stream only. Pond creation must not invalidate already admitted
        # script evidence or make the digest depend on PS initialization order.
        return build_caller_owned_stream_registry_digest(
            {"sr.runtime": runtime_owner}
        )

    def _commit_script_entropy_evidence(
        self,
        audit: dict[str, Any],
        receipt: dict[str, Any],
    ) -> None:
        """Append the audit/receipt pair together after successful instantiation."""
        audits = vars(self).setdefault("_sr_script_entropy_audits", [])
        receipts = vars(self).setdefault("_sr_script_entropy_receipts", [])
        if not isinstance(audits, list) or not isinstance(receipts, list):
            raise RuntimeError("script entropy evidence stores are invalid")
        audit_path = str(audit.get("path") or "")
        receipt_path = str(receipt.get("path") or "")
        if not audit_path or audit_path != receipt_path:
            raise RuntimeError("script entropy evidence path mismatch")
        known_audits = [item for item in audits if item.get("path") == audit_path]
        known_receipts = [item for item in receipts if item.get("path") == receipt_path]
        if any(item != audit for item in known_audits) or any(
            item != receipt for item in known_receipts
        ):
            raise RuntimeError("script entropy evidence conflict")
        if not known_audits:
            audits.append(dict(audit))
        if not known_receipts:
            receipts.append(dict(receipt))

