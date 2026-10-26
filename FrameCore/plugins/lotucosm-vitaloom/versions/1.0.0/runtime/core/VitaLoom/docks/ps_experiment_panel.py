# -*- coding: utf-8
"""莲池 PS 演化实验 Dock 面板。"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.Lotucosm.experiment_config import PsExperimentConfig
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.simulation.ps_experiment_service import (
    compare_run_metrics,
    get_ps_experiment_service,
)

logger = get_logger("PsExperimentPanel")


class PsExperimentPanel(QWidget):
    """配置并运行 PS 莲池演化实验（不阻塞 UI）。"""

    def __init__(self, editor_context: Any, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._ctx = editor_context
        self._service = get_ps_experiment_service(editor_context)
        self._preset_paths: dict[str, Path] = {}
        self._history_runs: list[dict] = []
        self._selected_history_dir: Optional[Path] = None
        self._last_result_metrics: Optional[dict] = None
        self._build_ui()
        self._reload_presets()
        self._sync_form_from_config()
        self._refresh_history_runs()
        self._refresh_project_preset_label()
        if self._service and getattr(self._ctx, "current_project_path", None):
            self._service.load_project_bindings(self._ctx.current_project_path)
            self._sync_form_from_config()
            self._refresh_project_preset_label()

    def _t(self, key: str, default: str) -> str:
        tr_fn = getattr(self._ctx, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default

    def retranslate_ui(self) -> None:
        """原地刷新静态文案，不重建 Dock/Panel 或修改用户运行状态。"""
        self._title_label.setText(self._t("ps_experiment.title", "莲池演化实验（PS）"))
        self._hint_label.setText(
            self._t(
                "ps_experiment.hint",
                "在织机内运行 PVAEC + 世代编排，无需终端。SR 场景播放与此并行。",
            )
        )
        self._preset_group.setTitle(self._t("ps_experiment.preset", "预设"))
        self._reload_btn.setText(self._t("ps_experiment.reload", "刷新"))
        self._project_group.setTitle(
            self._t("ps_experiment.project_binding", "工程绑定")
        )
        self._save_project_btn.setText(
            self._t("ps_experiment.save_preset_to_project", "将当前预设路径写入工程")
        )
        self._save_evolution_btn.setText(
            self._t(
                "ps_experiment.save_evolution_defaults",
                "将当前参数写入 evolution_defaults",
            )
        )
        self._params_group.setTitle(self._t("ps_experiment.params", "参数"))
        self.seed_spin.setSpecialValueText(
            self._t("ps_experiment.seed_random", "随机")
        )
        form_labels = (
            (self.ticks_spin, "ps_experiment.ticks", "帧数 ticks"),
            (self.seed_spin, "ps_experiment.seed", "随机种子"),
            (self.initial_org_spin, "ps_experiment.initial_organisms", "初始个体"),
            (self.max_pop_spin, "ps_experiment.max_population", "种群上限"),
            (self.gen_interval_spin, "ps_experiment.generation_interval", "世代间隔(帧)"),
            (self.mutation_spin, "ps_experiment.mutation_rate", "变异率"),
            (self.selection_spin, "ps_experiment.selection_pressure", "选择压力"),
            (self.elitism_spin, "ps_experiment.elitism_rate", "精英保留率"),
            (self.enable_gen_check, "ps_experiment.enable_generation", "启用世代编排"),
            (self.enable_pvaec_check, "ps_experiment.enable_pvaec", "每帧 PVAEC 循环"),
        )
        for field, key, default in form_labels:
            label = self._form_layout.labelForField(field)
            if label is not None:
                label.setText(self._t(key, default))
        self.run_btn.setText(self._t("ps_experiment.run", "运行实验"))
        self.cancel_btn.setText(self._t("ps_experiment.cancel", "取消"))
        self._history_group.setTitle(self._t("ps_experiment.history", "历史运行"))
        self._refresh_history_btn.setText(
            self._t("ps_experiment.refresh_history", "刷新")
        )
        self._baseline_label.setText(
            self._t("ps_experiment.compare_baseline", "对比基准")
        )
        if self.baseline_combo.count() > 0:
            self.baseline_combo.setItemText(
                0, self._t("ps_experiment.compare_none", "（不对比）")
            )
        self.open_history_dir_btn.setText(
            self._t("ps_experiment.open_history_dir", "打开该次目录")
        )
        self._result_group.setTitle(self._t("ps_experiment.result", "结果"))
        self.open_dir_btn.setText(
            self._t("ps_experiment.open_output", "打开导出目录")
        )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._title_label = QLabel(self._t("ps_experiment.title", "莲池演化实验（PS）"))
        self._title_label.setStyleSheet("font-weight: bold; color: #c0d8ff;")
        layout.addWidget(self._title_label)

        self._hint_label = QLabel(
            self._t(
                "ps_experiment.hint",
                "在织机内运行 PVAEC + 世代编排，无需终端。SR 场景播放与此并行。",
            )
        )
        self._hint_label.setWordWrap(True)
        self._hint_label.setStyleSheet("color: #8899aa; font-size: 11px;")
        layout.addWidget(self._hint_label)

        self._preset_group = QGroupBox(self._t("ps_experiment.preset", "预设"))
        preset_layout = QHBoxLayout(self._preset_group)
        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo, stretch=1)
        self._reload_btn = QPushButton(self._t("ps_experiment.reload", "刷新"))
        self._reload_btn.clicked.connect(self._reload_presets)
        preset_layout.addWidget(self._reload_btn)
        layout.addWidget(self._preset_group)

        self._project_group = QGroupBox(self._t("ps_experiment.project_binding", "工程绑定"))
        project_layout = QVBoxLayout(self._project_group)
        self.project_preset_label = QLabel("—")
        self.project_preset_label.setWordWrap(True)
        self.project_preset_label.setStyleSheet("color: #8899aa; font-size: 11px;")
        project_layout.addWidget(self.project_preset_label)
        self._save_project_btn = QPushButton(
            self._t("ps_experiment.save_preset_to_project", "将当前预设路径写入工程")
        )
        self._save_project_btn.clicked.connect(self._on_save_preset_to_project)
        project_layout.addWidget(self._save_project_btn)
        self._save_evolution_btn = QPushButton(
            self._t("ps_experiment.save_evolution_defaults", "将当前参数写入 evolution_defaults")
        )
        self._save_evolution_btn.clicked.connect(self._on_save_evolution_defaults)
        project_layout.addWidget(self._save_evolution_btn)
        layout.addWidget(self._project_group)

        self._params_group = QGroupBox(self._t("ps_experiment.params", "参数"))
        self._form_layout = QFormLayout(self._params_group)
        form = self._form_layout

        self.ticks_spin = QSpinBox()
        self.ticks_spin.setRange(1, 100000)
        self.ticks_spin.setValue(300)
        form.addRow(self._t("ps_experiment.ticks", "帧数 ticks"), self.ticks_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(-1, 2147483647)
        self.seed_spin.setSpecialValueText(self._t("ps_experiment.seed_random", "随机"))
        self.seed_spin.setValue(-1)
        form.addRow(self._t("ps_experiment.seed", "随机种子"), self.seed_spin)

        self.initial_org_spin = QSpinBox()
        self.initial_org_spin.setRange(1, 500)
        form.addRow(self._t("ps_experiment.initial_organisms", "初始个体"), self.initial_org_spin)

        self.max_pop_spin = QSpinBox()
        self.max_pop_spin.setRange(1, 500)
        form.addRow(self._t("ps_experiment.max_population", "种群上限"), self.max_pop_spin)

        self.gen_interval_spin = QSpinBox()
        self.gen_interval_spin.setRange(0, 10000)
        form.addRow(
            self._t("ps_experiment.generation_interval", "世代间隔(帧)"),
            self.gen_interval_spin,
        )

        self.mutation_spin = QDoubleSpinBox()
        self.mutation_spin.setRange(0.0, 1.0)
        self.mutation_spin.setSingleStep(0.01)
        self.mutation_spin.setDecimals(3)
        form.addRow(self._t("ps_experiment.mutation_rate", "变异率"), self.mutation_spin)

        self.selection_spin = QDoubleSpinBox()
        self.selection_spin.setRange(0.0, 1.0)
        self.selection_spin.setSingleStep(0.05)
        self.selection_spin.setDecimals(3)
        form.addRow(self._t("ps_experiment.selection_pressure", "选择压力"), self.selection_spin)

        self.elitism_spin = QDoubleSpinBox()
        self.elitism_spin.setRange(0.0, 1.0)
        self.elitism_spin.setSingleStep(0.05)
        self.elitism_spin.setDecimals(3)
        form.addRow(self._t("ps_experiment.elitism_rate", "精英保留率"), self.elitism_spin)

        self.enable_gen_check = QCheckBox()
        self.enable_gen_check.setChecked(True)
        form.addRow(self._t("ps_experiment.enable_generation", "启用世代编排"), self.enable_gen_check)

        self.enable_pvaec_check = QCheckBox()
        self.enable_pvaec_check.setChecked(True)
        form.addRow(self._t("ps_experiment.enable_pvaec", "每帧 PVAEC 循环"), self.enable_pvaec_check)

        layout.addWidget(self._params_group)

        btn_row = QHBoxLayout()
        self.run_btn = QPushButton(self._t("ps_experiment.run", "运行实验"))
        self.run_btn.clicked.connect(self._on_run)
        btn_row.addWidget(self.run_btn)
        self.cancel_btn = QPushButton(self._t("ps_experiment.cancel", "取消"))
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self._history_group = QGroupBox(self._t("ps_experiment.history", "历史运行"))
        history_layout = QVBoxLayout(self._history_group)
        hist_row = QHBoxLayout()
        self.history_combo = QComboBox()
        self.history_combo.currentIndexChanged.connect(self._on_history_selected)
        hist_row.addWidget(self.history_combo, stretch=1)
        self._refresh_history_btn = QPushButton(self._t("ps_experiment.refresh_history", "刷新"))
        self._refresh_history_btn.clicked.connect(self._refresh_history_runs)
        hist_row.addWidget(self._refresh_history_btn)
        history_layout.addLayout(hist_row)
        baseline_row = QHBoxLayout()
        self._baseline_label = QLabel(
            self._t("ps_experiment.compare_baseline", "对比基准")
        )
        baseline_row.addWidget(self._baseline_label)
        self.baseline_combo = QComboBox()
        self.baseline_combo.currentIndexChanged.connect(self._on_baseline_changed)
        baseline_row.addWidget(self.baseline_combo, stretch=1)
        history_layout.addLayout(baseline_row)
        self.compare_label = QLabel("—")
        self.compare_label.setWordWrap(True)
        self.compare_label.setStyleSheet(
            "color: #7eb8a8; font-family: Consolas, 'Microsoft YaHei', sans-serif; font-size: 11px;"
        )
        history_layout.addWidget(self.compare_label)
        self.open_history_dir_btn = QPushButton(
            self._t("ps_experiment.open_history_dir", "打开该次目录")
        )
        self.open_history_dir_btn.setEnabled(False)
        self.open_history_dir_btn.clicked.connect(self._on_open_history_dir)
        history_layout.addWidget(self.open_history_dir_btn)
        layout.addWidget(self._history_group)

        self._result_group = QGroupBox(self._t("ps_experiment.result", "结果"))
        result_layout = QVBoxLayout(self._result_group)
        self.status_label = QLabel("—")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "color: #a8c0e0; font-family: Consolas, 'Microsoft YaHei', sans-serif; font-size: 11px;"
        )
        result_layout.addWidget(self.status_label)
        self.open_dir_btn = QPushButton(self._t("ps_experiment.open_output", "打开导出目录"))
        self.open_dir_btn.setEnabled(False)
        self.open_dir_btn.clicked.connect(self._on_open_output)
        result_layout.addWidget(self.open_dir_btn)
        layout.addWidget(self._result_group)

        layout.addStretch()

        if self._service is None:
            self.status_label.setText(
                self._t("ps_experiment.service_missing", "实验服务未注册（请确认 PVAEC 模拟包已加载）")
            )
            self._set_form_enabled(False)
        self._update_project_group_visibility()

    def _update_project_group_visibility(self) -> None:
        has_project = bool(getattr(self._ctx, "current_project_path", None))
        self._project_group.setVisible(has_project)

    def _refresh_project_preset_label(self) -> None:
        proj = getattr(self._ctx, "current_project_path", None)
        if not proj:
            self.project_preset_label.setText(
                self._t("ps_experiment.no_project", "未打开工程")
            )
            return
        try:
            import json

            pj = Path(proj) / "project.json"
            if pj.is_file():
                meta = json.loads(pj.read_text(encoding="utf-8"))
                preset = meta.get("ps_experiment_preset") or "—"
                self.project_preset_label.setText(str(preset))
            else:
                self.project_preset_label.setText("—")
        except Exception:
            self.project_preset_label.setText("—")

    def _current_preset_relative_path(self) -> Optional[str]:
        name = self.preset_combo.currentText()
        path = self._preset_paths.get(name)
        if path is None or self._service is None:
            return None
        try:
            return str(path.resolve().relative_to(self._service._root)).replace("\\", "/")
        except ValueError:
            return str(path)

    def _on_save_preset_to_project(self) -> None:
        rel = self._current_preset_relative_path()
        if not rel:
            self.status_label.setText(
                self._t("ps_experiment.save_preset_failed", "无法解析预设路径")
            )
            return
        try:
            from core.VitaLoom.commands.registry import get_command_registry

            project_path = str(getattr(self._ctx, "current_project_path", "") or "")
            result = get_command_registry().run(
                "project.set_ps_experiment_preset",
                {"project_path": project_path, "preset_path": rel},
            )
            ok = bool(result.get("ok"))
            if ok:
                self._refresh_project_preset_label()
                self.status_label.setText(
                    self._t("ps_experiment.save_preset_ok", "已写入 project.json: ")
                    + rel
                )
            else:
                error = result.get("error") or {}
                self.status_label.setText(
                    self._t("ps_experiment.save_preset_failed", "写入工程失败")
                    + f": {error.get('message', '')}"
                )
        except Exception as exc:
            logger.warning("保存工程预设失败: %s", exc)
            self.status_label.setText(f"写入失败: {exc}")

    def _refresh_history_runs(self) -> None:
        self.history_combo.blockSignals(True)
        self.baseline_combo.blockSignals(True)
        self.history_combo.clear()
        self.baseline_combo.clear()
        self.baseline_combo.addItem(
            self._t("ps_experiment.compare_none", "（不对比）"), None
        )
        self._history_runs = []
        self._selected_history_dir = None
        if self._service is not None:
            self._history_runs = self._service.list_recent_runs()
            for run in self._history_runs:
                label = (
                    f"{run.get('name', '?')} · pop={run.get('population', 0)} · "
                    f"fit={float(run.get('avg_fitness', 0)):.3f}"
                )
                self.history_combo.addItem(label)
                self.baseline_combo.addItem(label)
        self.history_combo.blockSignals(False)
        self.baseline_combo.blockSignals(False)
        if self.history_combo.count() > 0:
            self._on_history_selected(0)
        else:
            self.open_history_dir_btn.setEnabled(False)
        self._update_compare_display()

    def _on_baseline_changed(self, index: int) -> None:
        self._update_compare_display()

    def _baseline_run_metrics(self) -> Optional[dict]:
        idx = self.baseline_combo.currentIndex()
        if idx <= 0:
            return None
        run_idx = idx - 1
        if run_idx < 0 or run_idx >= len(self._history_runs):
            return None
        run = self._history_runs[run_idx]
        return {
            "population": int(run.get("population", 0)),
            "iteration": int(run.get("iteration", 0)),
            "avg_fitness": float(run.get("avg_fitness", 0.0)),
            "avg_memory_count": float(run.get("avg_memory_count", 0.0)),
        }

    def _current_compare_metrics(self) -> Optional[dict]:
        if self._last_result_metrics is not None:
            return self._last_result_metrics
        idx = self.history_combo.currentIndex()
        if idx < 0 or idx >= len(self._history_runs):
            return None
        run = self._history_runs[idx]
        return {
            "population": int(run.get("population", 0)),
            "iteration": int(run.get("iteration", 0)),
            "avg_fitness": float(run.get("avg_fitness", 0.0)),
            "avg_memory_count": float(run.get("avg_memory_count", 0.0)),
        }

    def _update_compare_display(self) -> None:
        baseline = self._baseline_run_metrics()
        current = self._current_compare_metrics()
        if baseline is None or current is None:
            self.compare_label.setText("—")
            return
        deltas = compare_run_metrics(baseline, current)
        fmt = self._t(
            "ps_experiment.compare_fmt",
            "Δpop={dp:+.0f} · Δgen={dg:+.0f} · Δfit={df:+.3f} · Δmem={dm:+.1f}",
        )
        self.compare_label.setText(
            fmt.format(
                dp=deltas["delta_population"],
                dg=deltas["delta_iteration"],
                df=deltas["delta_avg_fitness"],
                dm=deltas["delta_avg_memory_count"],
            )
        )

    def _on_history_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._history_runs):
            self._selected_history_dir = None
            self.open_history_dir_btn.setEnabled(False)
            return
        run = self._history_runs[index]
        self._selected_history_dir = run.get("dir")
        if isinstance(self._selected_history_dir, Path):
            self.open_history_dir_btn.setEnabled(True)
            cancelled = run.get("cancelled")
            tag = self._t("ps_experiment.cancelled", "已取消") if cancelled else ""
            self.status_label.setText(
                f"[历史] {run.get('name', '')} · pop={run.get('population', 0)} · "
                f"gen={run.get('iteration', 0)} · "
                f"fit={float(run.get('avg_fitness', 0)):.3f} {tag}".strip()
            )
            self._update_compare_display()
            self._push_replay_overlay_for_dir(self._selected_history_dir)
        else:
            self.open_history_dir_btn.setEnabled(False)

    def _on_open_history_dir(self) -> None:
        if self._selected_history_dir is None:
            return
        path = str(Path(self._selected_history_dir).resolve())
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def _on_experiment_finished(self, _data: Any) -> None:
        if self._service and self._service.last_summary:
            final = self._service.last_summary.get("final") or {}
            self._last_result_metrics = {
                "population": int(final.get("population", 0)),
                "iteration": int(final.get("iteration", 0)),
                "avg_fitness": float(final.get("avg_fitness", 0.0)),
                "avg_memory_count": float(final.get("avg_memory_count", 0.0)),
            }
        self._refresh_history_runs()
        if self._service and self._service.last_output_dir:
            self.open_dir_btn.setEnabled(True)

    def _set_form_enabled(self, enabled: bool) -> None:
        for w in (
            self.preset_combo,
            self.ticks_spin,
            self.seed_spin,
            self.initial_org_spin,
            self.max_pop_spin,
            self.gen_interval_spin,
            self.mutation_spin,
            self.selection_spin,
            self.elitism_spin,
            self.enable_gen_check,
            self.enable_pvaec_check,
            self.run_btn,
        ):
            w.setEnabled(enabled)

    def _reload_presets(self) -> None:
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self._preset_paths.clear()
        if self._service is None:
            self.preset_combo.blockSignals(False)
            return
        for name, path in self._service.list_presets():
            self.preset_combo.addItem(name)
            self._preset_paths[name] = path
        self.preset_combo.blockSignals(False)
        if self.preset_combo.count() > 0:
            self._on_preset_changed(0)

    def _on_preset_changed(self, index: int) -> None:
        if index < 0 or self._service is None:
            return
        name = self.preset_combo.currentText()
        path = self._preset_paths.get(name)
        if path is None:
            return
        try:
            self._service.load_preset(path)
            self._sync_form_from_config()
        except Exception as exc:
            logger.warning("加载预设失败: %s", exc)

    def _on_config_changed(self, _data: Any) -> None:
        self._sync_form_from_config()
        self._refresh_project_preset_label()
        self._update_project_group_visibility()

    def _on_project_opened(self, data: Any) -> None:
        if self._service is None:
            return
        proj_path = None
        if isinstance(data, dict):
            proj_path = data.get("project_path")
        elif isinstance(data, str):
            proj_path = data
        if not proj_path:
            proj_path = getattr(self._ctx, "current_project_path", None)
        if proj_path:
            self._service.load_project_bindings(proj_path)
        self._sync_form_from_config()
        self._refresh_project_preset_label()
        self._update_project_group_visibility()

    def _apply_evolution_defaults_from_project(self, proj_path: Optional[str]) -> None:
        if self._service is None:
            return
        try:
            import json

            from core.VitaLoom.project.evolution_context import (
                apply_evolution_defaults_to_ps_config,
                load_project_evolution_context,
            )

            path = proj_path or getattr(self._ctx, "current_project_path", None)
            if not path:
                return
            pj = Path(path) / "project.json"
            if not pj.is_file():
                return
            meta = json.loads(pj.read_text(encoding="utf-8"))
            defaults = load_project_evolution_context(meta)
            if defaults:
                apply_evolution_defaults_to_ps_config(self._service.config, defaults)
                self._sync_form_from_config()
        except Exception as exc:
            logger.debug("加载 evolution_defaults 失败: %s", exc)

    def _on_save_evolution_defaults(self) -> None:
        try:
            from core.VitaLoom.project.evolution_context import (
                evolution_defaults_from_ps_config,
            )
            from core.VitaLoom.commands.registry import get_command_registry

            cfg = self._form_to_config()
            defaults = evolution_defaults_from_ps_config(cfg)
            project_path = str(getattr(self._ctx, "current_project_path", "") or "")
            result = get_command_registry().run(
                "project.set_evolution_defaults",
                {"project_path": project_path, "defaults": defaults},
            )
            ok = bool(result.get("ok"))
            if ok:
                self.status_label.setText(
                    self._t("ps_experiment.save_evolution_ok", "已写入 evolution_defaults")
                )
            else:
                error = result.get("error") or {}
                self.status_label.setText(
                    self._t("ps_experiment.save_evolution_failed", "写入 evolution_defaults 失败")
                    + f": {error.get('message', '')}"
                )
        except Exception as exc:
            logger.warning("保存 evolution_defaults 失败: %s", exc)

    def _push_replay_overlay_for_dir(self, run_dir: Optional[Path]) -> None:
        if run_dir is None:
            return
        try:
            from core.VitaLoom.simulation.ps_replay_overlay import (
                push_overlay_to_game_viewport,
            )

            push_overlay_to_game_viewport(self._ctx, Path(run_dir))
        except Exception as exc:
            logger.debug("replay overlay 失败: %s", exc)

    def _sync_form_from_config(self) -> None:
        if self._service is None:
            return
        cfg = self._service.config
        self.ticks_spin.setValue(int(cfg.ticks))
        self.seed_spin.setValue(int(cfg.seed) if cfg.seed is not None else -1)
        self.initial_org_spin.setValue(int(cfg.initial_organisms))
        self.max_pop_spin.setValue(int(cfg.max_population))
        self.gen_interval_spin.setValue(int(cfg.evolution_generation_interval))
        self.mutation_spin.setValue(float(cfg.mutation_rate))
        self.selection_spin.setValue(float(cfg.selection_pressure))
        self.elitism_spin.setValue(float(cfg.elitism_rate))
        self.enable_gen_check.setChecked(bool(cfg.enable_generation_orchestrator))
        self.enable_pvaec_check.setChecked(bool(cfg.enable_pvaec_cycle_per_tick))

    def _form_to_config(self) -> PsExperimentConfig:
        if self._service is not None:
            cfg = PsExperimentConfig.from_dict(self._service.config.to_dict())
        else:
            cfg = PsExperimentConfig()
        cfg.ticks = int(self.ticks_spin.value())
        seed_val = int(self.seed_spin.value())
        cfg.seed = None if seed_val < 0 else seed_val
        cfg.initial_organisms = int(self.initial_org_spin.value())
        cfg.max_population = int(self.max_pop_spin.value())
        cfg.evolution_generation_interval = int(self.gen_interval_spin.value())
        cfg.mutation_rate = float(self.mutation_spin.value())
        cfg.selection_pressure = float(self.selection_spin.value())
        cfg.elitism_rate = float(self.elitism_spin.value())
        cfg.enable_generation_orchestrator = self.enable_gen_check.isChecked()
        cfg.enable_pvaec_cycle_per_tick = self.enable_pvaec_check.isChecked()
        return cfg

    def _on_run(self) -> None:
        if self._service is None:
            return
        cfg = self._form_to_config()
        self._service.config = cfg
        self.open_dir_btn.setEnabled(False)
        self._last_result_metrics = None
        self.cancel_btn.setEnabled(True)
        self._set_form_enabled(False)
        self.status_label.setText(self._t("ps_experiment.running", "实验运行中…"))

        def on_progress(m: dict) -> None:
            tick = int(m.get("tick", 0))
            pop = int(m.get("population", 0))
            it = int(m.get("iteration", 0))
            fit = float(m.get("avg_fitness", 0.0))
            self.status_label.setText(
                f"tick {tick}/{cfg.ticks} · pop={pop} · gen={it} · avg_fitness={fit:.3f}"
            )

        def on_finished(summary: dict, out_dir: Optional[Path]) -> None:
            self.cancel_btn.setEnabled(False)
            self._set_form_enabled(True)
            final = summary.get("final") or {}
            cancelled = bool(summary.get("cancelled"))
            tag = self._t("ps_experiment.cancelled", "已取消") if cancelled else self._t(
                "ps_experiment.done", "完成"
            )
            self.status_label.setText(
                f"{tag} · pop={final.get('population', 0)} · "
                f"iteration={final.get('iteration', 0)} · "
                f"avg_fitness={float(final.get('avg_fitness', 0)):.3f} · "
                f"avg_mem={float(final.get('avg_memory_count', 0)):.1f}"
            )
            self._last_result_metrics = {
                "population": int(final.get("population", 0)),
                "iteration": int(final.get("iteration", 0)),
                "avg_fitness": float(final.get("avg_fitness", 0.0)),
                "avg_memory_count": float(final.get("avg_memory_count", 0.0)),
            }
            if out_dir is not None:
                self.open_dir_btn.setEnabled(True)
            self._refresh_history_runs()
            self._update_compare_display()
            self._publish_console(tag, final, out_dir)

        def on_error(msg: str) -> None:
            self.cancel_btn.setEnabled(False)
            self._set_form_enabled(True)
            self.status_label.setText(f"错误: {msg}")

        started = self._service.run_async(
            cfg,
            export=True,
            on_progress=on_progress,
            on_finished=on_finished,
            on_error=on_error,
        )
        if not started:
            self._set_form_enabled(True)
            self.cancel_btn.setEnabled(False)
            self.status_label.setText(self._t("ps_experiment.already_running", "已有实验在运行"))

    def _on_cancel(self) -> None:
        if self._service is not None:
            self._service.request_cancel()

    def _on_open_output(self) -> None:
        if self._service is None or self._service.last_output_dir is None:
            return
        path = str(self._service.last_output_dir.resolve())
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def _publish_console(self, tag: str, final: dict, out_dir: Optional[Path]) -> None:
        if not hasattr(self._ctx, "event_bus"):
            return
        msg = (
            f"[莲池实验] {tag} pop={final.get('population')} "
            f"iteration={final.get('iteration')} "
            f"avg_fitness={float(final.get('avg_fitness', 0)):.3f}"
        )
        if out_dir:
            msg += f" → {out_dir}"
        try:
            self._ctx.event_bus.publish("console_log", {"level": "info", "message": msg})
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
