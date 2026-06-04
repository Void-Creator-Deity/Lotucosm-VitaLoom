# -*- coding: utf-8 -*-
"""模拟控制面板：播放/暂停/停止与速度、参数信号（由 SR 视口消费）。

排错: 见 core/VitaLoom/README.md「模拟播放」、docs/pvaec_cell_evolution.md
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
    QCheckBox, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.VitaLoom.core.editor_context import get_editor_context, EditorMode


class SimulationControlPanel(QWidget):
    """职责: 倍速与 PVAEC 参数；播放/暂停/停止由 SimulationTransport（工具栏）驱动。
    时机: 模拟 Dock 或工具栏嵌入。
    不变量: 按钮优先调用 transport；无 transport 时回退 Qt 信号。
    排错: 点击无反应 → 检查 get_simulation_transport() 是否已注册。
    """

    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    speed_changed = pyqtSignal(float)
    parameters_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("simControlPanel")
        self.editor_context = get_editor_context()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 状态条
        self.status_frame = QFrame()
        self.status_frame.setObjectName("simControlStatus")
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(10, 6, 10, 6)
        self.status_label = QLabel(
            self._t(
                "sim_control.status.idle",
                "就绪 · 顶部 ▶ 运行；本面板可调倍速与参数",
            )
        )
        self.status_label.setObjectName("simControlStatusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        layout.addWidget(self.status_frame)

        # 播放控制
        play_group = QGroupBox(self._t("sim_control.group.playback", "播放控制"))
        play_group.setObjectName("simControlGroup")
        play_layout = QHBoxLayout()
        play_layout.setSpacing(6)

        self.play_btn = QPushButton(self._t("sim_control.play", "▶ 播放"))
        self.play_btn.setObjectName("simControlPlay")
        self.play_btn.setMinimumHeight(32)
        self.play_btn.clicked.connect(self._on_play)  # type: ignore
        play_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton(self._t("sim_control.pause", "⏸ 暂停"))
        self.pause_btn.setObjectName("simControlSecondary")
        self.pause_btn.setMinimumHeight(32)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause)  # type: ignore
        play_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton(self._t("sim_control.stop", "⏹ 停止"))
        self.stop_btn.setObjectName("simControlSecondary")
        self.stop_btn.setMinimumHeight(32)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)  # type: ignore
        play_layout.addWidget(self.stop_btn)

        play_group.setLayout(play_layout)
        layout.addWidget(play_group)

        # 速度
        speed_group = QGroupBox(self._t("sim_control.group.speed", "速度"))
        speed_group.setObjectName("simControlGroup")
        speed_layout = QVBoxLayout()

        preset_row = QHBoxLayout()
        for mult, label in ((0.5, "0.5×"), (1.0, "1×"), (2.0, "2×"), (4.0, "4×")):
            btn = QPushButton(label)
            btn.setObjectName("simControlPreset")
            btn.setMinimumHeight(26)
            btn.clicked.connect(lambda _=False, m=mult: self.set_speed(m))  # type: ignore
            preset_row.addWidget(btn)
        speed_layout.addLayout(preset_row)

        speed_control_layout = QHBoxLayout()
        speed_control_layout.addWidget(QLabel(self._t("sim_control.speed", "倍速")))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(500)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)  # type: ignore
        self.speed_label = QLabel("1.0×")
        self.speed_label.setMinimumWidth(44)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        speed_control_layout.addWidget(self.speed_slider, stretch=1)
        speed_control_layout.addWidget(self.speed_label)
        speed_layout.addLayout(speed_control_layout)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # 参数
        params_group = QGroupBox(self._t("sim_control.group.params", "模拟参数"))
        params_group.setObjectName("simControlGroup")
        params_layout = QFormLayout()
        params_layout.setSpacing(6)

        self.fps_limit_spin = QSpinBox()
        self.fps_limit_spin.setMinimum(1)
        self.fps_limit_spin.setMaximum(1000)
        self.fps_limit_spin.setValue(60)
        self.fps_limit_spin.valueChanged.connect(self._on_params_changed)  # type: ignore
        params_layout.addRow(self._t("sim_control.fps_limit", "帧率上限"), self.fps_limit_spin)

        self.time_step_spin = QDoubleSpinBox()
        self.time_step_spin.setMinimum(0.001)
        self.time_step_spin.setMaximum(1.0)
        self.time_step_spin.setSingleStep(0.001)
        self.time_step_spin.setValue(0.016)
        self.time_step_spin.setDecimals(3)
        self.time_step_spin.valueChanged.connect(self._on_params_changed)  # type: ignore
        params_layout.addRow(self._t("sim_control.time_step", "时间步长"), self.time_step_spin)

        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(False)
        self.auto_save_check.stateChanged.connect(self._on_params_changed)  # type: ignore
        params_layout.addRow(self._t("sim_control.auto_save", "自动保存"), self.auto_save_check)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        hint = QLabel(
            self._t(
                "sim_control.hint.pvaec",
                "主世界 SR：膜 chemo 趋食 + 中枢 PVAEC 内稳态验证。详见 docs/pvaec_cell_evolution.md",
            )
        )
        hint.setObjectName("simControlHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()
        self.setLayout(layout)

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _on_play(self):
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self._set_status(self._t("sim_control.status.playing", "模拟运行中 · PVAEC 帧循环 + 世代编排"))
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_play()
        else:
            self.play_requested.emit()

    def _on_pause(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self._set_status(self._t("sim_control.status.paused", "已暂停 · 可继续播放或停止"))
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_pause()
        else:
            self.pause_requested.emit()

    def _on_stop(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self._set_status(self._t("sim_control.status.stopped", "已停止 · 下次播放将重载场景"))
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.request_stop()
        else:
            self.stop_requested.emit()

    def _on_speed_changed(self, value: int):
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}×")
        from core.VitaLoom.simulation.simulation_transport import get_simulation_transport

        transport = get_simulation_transport()
        if transport:
            transport.set_speed(speed)
        else:
            self.speed_changed.emit(speed)

    def _on_params_changed(self):
        self.parameters_changed.emit(self.get_parameters())

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "fps_limit": self.fps_limit_spin.value(),
            "time_step": self.time_step_spin.value(),
            "physics_freq": 60,
            "auto_save": self.auto_save_check.isChecked(),
        }

    def set_speed(self, speed: float):
        value = int(max(10, min(500, speed * 100)))
        self.speed_slider.setValue(value)
        self.speed_label.setText(f"{speed:.1f}×")
        self.speed_changed.emit(speed)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def reset(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.set_speed(1.0)
        self._set_status(self._t("sim_control.status.idle", "就绪 · 顶部 ▶ 运行；本面板可调倍速与参数"))
