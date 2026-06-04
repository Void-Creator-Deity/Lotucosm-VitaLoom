# -*- coding: utf-8 -*-
"""游戏视口：场景运行时（SR）宿主与内置 Simulation 回退。

SR 实现集中于 GameViewport：加载 .pond、每帧 tick、膜拓扑、会话摘要、HUD。
模块级函数 sr_* / build_sr_session_summary_* 供复盘与生态 Dock。

阅读顺序:
    类 GameViewport docstring（状态机）
    → # === SR: ... === 分区方法
    → core/Lotucosm/sr_membrane_topology.py（边与通道数学）
    → projects/pvaec-细胞演化/README.md「SR 运行时排错索引」
"""

from typing import Optional, Any, Dict, List
import importlib.util
import json
import os
import random
import math
from datetime import datetime, timezone
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPaintEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider

from core.VitaLoom.core.editor_context import get_editor_context, EditorMode
from core.VitaLoom.core.logger import get_logger
from core.Lotucosm.scene_runtime_ambient import ambient_field_and_gradient, nutrient_gradient_at
from core.Lotucosm.scene_runtime_world_state import niche_pressure_from_load, step_biosphere_load
from core.VitaLoom.viewports.sr_visual_renderer import SrVisualRenderer
from core.VitaLoom.viewports.sr_input_state import SrInputSnapshot, SrInputState
from core.VitaLoom.viewports.sr_sprite_assets import SrSpriteCatalog


logger = get_logger("GameViewport")


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
            self._host._sr_input.set_mouse_scene(sx, sy)
            event.accept()

        def mousePressEvent(self, event) -> None:
            if event is None:
                return
            from PyQt6.QtCore import Qt

            pos = event.position()
            sx, sy = self._host._widget_to_scene(float(pos.x()), float(pos.y()))
            self._host._sr_input.set_mouse_scene(sx, sy)
            if event.button() == Qt.MouseButton.LeftButton:
                self._host._sr_input.mouse_press_left()
            event.accept()

        def mouseReleaseEvent(self, event) -> None:
            if event is None:
                return
            from PyQt6.QtCore import Qt

            if event.button() == Qt.MouseButton.LeftButton:
                self._host._sr_input.mouse_release_left()
            event.accept()

    def __init__(self):
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
        self._sr_input = SrInputState()
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 获取编辑器上下文
        self.editor_context = get_editor_context()
        
        # 模拟状态
        self.simulation: Optional[Any] = None
        self.scene_runtime_entities: list[Any] = []
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
        self._sr_runtime_dirty = True
        self._sr_play_hint_shown = False
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
        self._sr_evo_pop_cap = 96
        self._sr_demo_legend: Optional[Dict[str, Any]] = None
        self._sr_nutrient_target_count = 0
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
        try:
            self.editor_context.sr_game_viewport = self
        except Exception as e:
            logger.debug("注册 sr_game_viewport 失败: %s", e)

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
        self._sr_input.press(key)

    def _sr_input_release(self, key: str) -> None:
        self._sr_input.release(key)

    def _sr_input_clear(self) -> None:
        self._sr_input.clear()

    def _sr_input_snapshot(self) -> SrInputSnapshot:
        if self.is_playing and not self.is_paused:
            return self._sr_input.snapshot()
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

    def _discard_scene_runtime_state(self) -> None:
        """丢弃内存中的 SR 运行时（不写入局摘要）。

        职责: 清空实体、拓扑、目标、HUD；置 _sr_runtime_dirty 语义由调用方负责。
        时机: 未播放时换场景；resume 重载前。
        排错: 与 _stop_simulation(write_session=False) 区别：本方法不写盘、不强制 is_playing=False。
        """
        self._using_scene_runtime = False
        self.scene_runtime_entities = []
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

    def _handle_empty_sr_runtime_tick(self) -> None:
        """运行时实体被清空时仍推进灭绝检测/HUD，避免定时器空转。

        时机: _update_simulation 在 _using_scene_runtime 且 entities 为空时。
        排错: 细胞死光但不停 → 查 _maybe_try_sr_extinction_pause；定时器空转 → 勿仅用
        ``if scene_runtime_entities`` 包住整段 tick。
        """
        dt = 0.05 * max(0.2, self.simulation_speed)
        self._scene_runtime_time += dt
        try:
            self._maybe_try_sr_extinction_pause()
        except Exception as e:
            logger.warning("空运行时灭绝检测失败: %s", e)
        try:
            self._refresh_sr_hud([])
        except Exception as e:
            logger.warning("空运行时 HUD 刷新失败: %s", e)

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
            self.simulation = Simulation(width, height)
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
        try:
            self.is_playing = True
            self.is_paused = False
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
        self._sr_input_clear()
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
                self._sr_session_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                self._capture_sr_session_context()
        try:
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
        self.is_playing = False
        self.is_paused = False
        self._sr_input_clear()
        self.simulation = None
        self._using_scene_runtime = False
        self._sr_runtime_dirty = True
        self._scene_runtime_time = 0.0
        self.scene_runtime_entities = []
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

    def _repo_relative_path(self, path: Path) -> str:
        """仓库根下的相对路径，便于控制台与 HUD 展示。"""
        root = Path(__file__).resolve().parents[3]
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
        )
        try:
            root = Path(__file__).resolve().parents[3]
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
                if self.scene_runtime_entities:
                    dt = 0.05 * max(0.2, self.simulation_speed)
                    self._update_scene_runtime_entities(dt)
                else:
                    self._handle_empty_sr_runtime_tick()
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
            from core.VitaLoom.project.project_manager import get_project_manager

            cfg = get_project_manager().get_current_project_config() or {}
            pres = cfg.get("presentation", {})
            if isinstance(pres, dict):
                custom = pres.get("editor_entry_hint_zh") or pres.get("tagline_zh")
                if isinstance(custom, str) and custom.strip():
                    hint = custom.strip()
        except Exception as e:
            logger.debug("读取项目 presentation 失败: %s", e)
        self._sr_hud_hint.setText(hint)
        self._sync_hud_chrome()

    def _paint_sr_canvas(self, canvas: QWidget, event: Optional[QPaintEvent]) -> None:
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
            self._sr_visual.paint_frame(
                painter,
                cw,
                ch,
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
                game_player_id=str(getattr(self, "_sr_player_id", "player_rl")),
                emissions_prev=getattr(self, "_scene_runtime_emissions_prev", None),
                niche_pressure=niche_pressure_from_load(
                    float(getattr(self, "_sr_biosphere_prev_load", 0.0)),
                    load_max=float(getattr(self, "_sr_load_max", 1.0)),
                ),
            )
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
                    pass
        else:
            from core.VitaLoom.viewports.sr_visual_renderer import paint_sr_background

            paint_sr_background(painter, cw, ch, 0.0)

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

        def __init__(self, entity_id: str, entity_type: str, position: tuple[float, float], radius: float = 18.0):
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
            self.id = entity_id
            self.entity_type = entity_type
            self.position = [float(position[0]), float(position[1])]
            self.velocity = [random.uniform(-20.0, 20.0), random.uniform(-20.0, 20.0)]
            self.radius = float(radius)
            self.scripts: list[Any] = []
            self.emission_strength = 0.0
            self.energy: Optional[float] = None
            self.generation = 0
            self.pinned = entity_type in ("nutrient", "environment_well")
            self.membrane_locked = False
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
                    if hasattr(script, "pvaec_step"):
                        script.pvaec_step(ctx, ctx.delta_time)
                    elif hasattr(script, "sr_step"):
                        script.sr_step(ctx, ctx.delta_time)
                    elif hasattr(script, "update"):
                        script.update(ctx.delta_time)

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
        from core.Lotucosm.sr_game_scene import normalize_game_scene_data

        scene_data = normalize_game_scene_data(raw_scene, project_path)
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
        if not entities_data:
            return False

        self.scene_runtime_entities = []
        for entity_data in entities_data:
            entity_id = entity_data.get("id", "entity")
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
            )
            if entity_data.get("pinned") is True:
                runtime_entity.pinned = True
            if "energy" in entity_data:
                try:
                    runtime_entity.energy = float(entity_data["energy"])
                except (TypeError, ValueError):
                    pass
            if "generation" in entity_data:
                try:
                    runtime_entity.generation = int(entity_data["generation"])
                except (TypeError, ValueError):
                    runtime_entity.generation = 0

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
        self._sr_physics_world = SrPhysics2DWorld(self._sr_physics_cfg)
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
            pass
        self._sr_play_hint_shown = False
        logger.info("游戏视口已加载场景运行时实体: %s", len(self.scene_runtime_entities))
        self._refresh_entry_hud_hint()
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

        hub_id = str(req.get("hub_id") or f"evo_organism_{self._sr_spawn_seq:05d}")
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
        )
        try:
            hub.energy = float(req.get("energy", 80.0))
        except (TypeError, ValueError):
            hub.energy = 80.0
        try:
            hub.generation = int(req.get("generation", 1))
        except (TypeError, ValueError):
            hub.generation = 1
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
            )
            ent.membrane_locked = True
            ent.pinned = False
            sname = str(spec.get("script", "sensor_patrol_pvaec"))
            script = self._instantiate_scene_script(
                {"name": sname, "type": "SensorPatrolPvaec", "properties": {}},
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
            )
            ent.membrane_locked = True
            ent.pinned = False
            sname = str(spec.get("script", "actuator_pulse_pvaec"))
            script = self._instantiate_scene_script(
                {"name": sname, "type": "ActuatorPulsePvaec", "properties": {}},
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
                    child_signal_edges, float(mut_sigma), random.Random()
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
        return hub_id

    def _maybe_respawn_sr_nutrients(self, w: int, h: int) -> None:
        """有细胞时维持营养颗粒数量，避免吃光后空转。"""
        target = int(getattr(self, "_sr_nutrient_target_count", 0) or 0)
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
            eid = f"nutrient_sr_{self._sr_spawn_seq:05d}"
            cx = random.uniform(margin + rad, max(margin + rad + 1.0, float(w) - margin - rad))
            cy = random.uniform(margin + rad, max(margin + rad + 1.0, float(h) - margin - rad))
            ent = self._SceneRuntimeEntity(
                entity_id=eid,
                entity_type="nutrient",
                position=(cx, cy),
                radius=rad,
            )
            ent.pinned = True
            self.scene_runtime_entities.append(ent)

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
                eid = str(req.get("id") or f"game_spawn_{self._sr_spawn_seq + 1:05d}")
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
                continue
            self._sr_spawn_seq += 1
            eid = str(req.get("id") or f"evo_organism_{self._sr_spawn_seq:05d}")
            raw_pos = req.get("position", (0.0, 0.0))
            if not isinstance(raw_pos, (list, tuple)) or len(raw_pos) < 2:
                raw_pos = (0.0, 0.0)
            r_rad = float(req.get("radius", 22.0))
            ent = self._SceneRuntimeEntity(
                entity_id=eid,
                entity_type=str(req.get("type", "organism")),
                position=(float(raw_pos[0]), float(raw_pos[1])),
                radius=r_rad,
            )
            try:
                ent.energy = float(req.get("energy", 80.0))
            except (TypeError, ValueError):
                ent.energy = 80.0
            try:
                ent.generation = int(req.get("generation", 1))
            except (TypeError, ValueError):
                ent.generation = 1
            for script_data in req.get("scripts", []):
                if not isinstance(script_data, dict):
                    continue
                script = self._instantiate_scene_script(script_data, project_path)
                if script is not None:
                    ent.add_script(script)
            self.scene_runtime_entities.append(ent)
        requests.clear()
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
        }
        if not sim_running:
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
            return out
        gens: List[float] = []
        energies: List[float] = []
        wanders: List[float] = []
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
        out["total_energy"] = sum(energies)
        out["avg_generation"] = sum(gens) / len(gens) if gens else 0.0
        if len(wanders) >= 2:
            mean_w = sum(wanders) / len(wanders)
            out["wander_amp_variance"] = sum((w - mean_w) ** 2 for w in wanders) / len(wanders)
        elif len(wanders) == 1:
            out["wander_amp_variance"] = 0.0
        mem = self._sr_membrane_runtime_stats()
        out["membrane_sensor_count"] = int(mem.get("membrane_sensor_count", 0))
        out["mean_edge_weight"] = float(mem.get("mean_edge_weight", 0.0))
        out["mean_chemo_channel"] = float(mem.get("mean_chemo_channel", 0.0))
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

    def _update_scene_runtime_entities(self, dt: float):
        """SR 单帧主循环。修改顺序前请读下方「顺序契约」。

        顺序契约（编号与实现步骤对应，勿乱序）::
            1. 清零 emission / sr_channel_out
            2. _sync_membrane_positions
            3. 脚本批: organism(use_prev) → sensor(use_prev) → actuator(当前通道) → rest
            4. _process_sr_removal_requests
            5. _process_sr_spawn_requests
            6. _bootstrap_spawned_membrane_clusters（新 hub 当帧补 tick）
            7. 二次 _process_sr_spawn_requests（bootstrap 内可能登记 spawn）
            8. 刷新 all_e / batch_common['all_e']
            9. _apply_actuator_coupling
            9b. step_nutrient_field_exchange + apply_extracellular_drift + sr_field_grid.step
            10. step_physics
            11. 能量死亡 + 膜子节点级联移除
            12. 营养重生、emissions 快照、HUD、胜利/灭绝暂停

        排错: 繁殖首帧无代谢 → 查 6–7；趋化晚一帧 → 查 3 批次与 use_prev；
        spawn 后 peers 陈旧 → 查 8 是否刷新 all_e。
        """
        if getattr(self, "_sr_game_mode", False):
            from core.Lotucosm.scene_runtime.game_tick import step_game_runtime

            step_game_runtime(self, dt)
            return

        from types import MappingProxyType

        self._scene_runtime_time += dt
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
        batch_common["all_e"] = all_e

        try:
            self._apply_actuator_coupling(all_e, dt)
        except Exception as e:
            logger.warning("执行器耦合失败: %s", e)

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

        all_e = list(self.scene_runtime_entities)

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
        self._maybe_log_scene_episode(dt)
        from core.Lotucosm.scene_runtime.session_outcome import resolve_session_outcomes

        resolve_session_outcomes(self)

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
        """游戏模式：达成 hud 目标时闪横幅，模拟继续运行。"""
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
        logger.info("【游戏模式】关卡目标已达成，模拟继续运行。")
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
        damage_requests: list[tuple[str, float]],
        remove_ids: list[str],
    ) -> None:
        if not damage_requests:
            return
        id_to_ent = {str(getattr(e, "id", "")): e for e in self.scene_runtime_entities}
        pending = set(remove_ids)
        for target_id, amount in damage_requests:
            tid = str(target_id)
            ent = id_to_ent.get(tid)
            if ent is None or tid in pending:
                continue
            hud = getattr(ent, "sr_debug_hud", None)
            if not isinstance(hud, dict):
                hud = {}
                ent.sr_debug_hud = hud
            try:
                hp = float(hud.get("hp", 30.0)) - float(amount)
            except (TypeError, ValueError):
                hp = 0.0
            hud["hp"] = hp
            hud["hit_flash"] = 0.18
            if hp <= 0.05:
                pending.add(tid)
                remove_ids.append(tid)

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
            player_id = str(getattr(self, "_sr_player_id", "player_rl"))
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
            root = Path(__file__).resolve().parents[3]
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
        try:
            script_path = script_data.get("path")
            script_name = script_data.get("name", "")
            if (not script_path) and project_path and script_name:
                script_path = os.path.join(project_path, "scripts", f"{script_name}.py")
            if not script_path or not os.path.exists(script_path):
                return None

            from core.Lotucosm.scripts import ScriptBase

            module_name = f"vitaloom_user_script_{abs(hash(script_path))}"
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            candidates: list[type] = []
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ScriptBase) and attr is not ScriptBase:
                    candidates.append(attr)

            if not candidates:
                return None

            type_name = (script_data.get("type") or "").strip()
            if type_name:
                for cls in candidates:
                    if cls.__name__ == type_name:
                        inst = cls()
                        setattr(inst, "_scene_script_properties", script_data.get("properties") or {})
                        return inst

            non_pvaec_base = [c for c in candidates if c.__name__ != "PvaecScript"]
            chosen = non_pvaec_base[0] if non_pvaec_base else candidates[0]
            inst = chosen()
            setattr(inst, "_scene_script_properties", script_data.get("properties") or {})
            return inst
        except Exception as e:
            logger.warning("实例化场景脚本失败: %s (script=%s)", e, script_data)
            return None
