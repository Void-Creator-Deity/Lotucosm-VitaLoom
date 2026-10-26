# -*- coding: utf-8 -*-
"""PS 莲池演化实验服务：编辑器 Dock 与 CI 脚本共用入口。

职责: 封装 PsExperimentConfig / PsExperimentRunner；异步 QThread 不阻塞 UI。
时机: PsExperimentPlugin on_load 注册到 EditorContext.services['ps_experiment']。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt

from builtin.systems.ps_experiment_runner import PsExperimentRunner
from core.Lotucosm.experiment_config import PsExperimentConfig, load_experiment_config
from core.Lotucosm.runtime.ps_runtime_snapshot_authority import (
    PsRuntimeSnapshotAuthority,
)
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.runtime_capability_registry import (
    resolve_runtime_capability_registry,
)

logger = get_logger("PsExperimentService")

SERVICE_KEY = "ps_experiment"
EVENT_FINISHED = "ps_experiment_finished"
EVENT_STATE = "ps_experiment_state"
EVENT_CONFIG_CHANGED = "ps_experiment_config_changed"

PsExperimentPhase = Literal["idle", "running", "finished", "cancelled", "error"]


@dataclass(frozen=True)
class PsExperimentState:
    """PS 实验状态快照（对标 SimulationTransportState，供状态栏/工具栏订阅）。"""

    phase: PsExperimentPhase = "idle"
    is_running: bool = False
    name: str = ""
    tick: int = 0
    total_ticks: int = 0
    population: int = 0
    iteration: int = 0
    avg_fitness: float = 0.0
    avg_memory_count: float = 0.0
    cancelled: bool = False


class PsExperimentService:
    """莲池 PS 演化实验：同步 run_sync（CI）与异步 run_async（Dock）。"""

    def __init__(self, project_root: Optional[Path] = None):
        self._root = project_root or Path(__file__).resolve().parents[3]
        self.config: PsExperimentConfig = PsExperimentConfig()
        self.last_summary: Optional[Dict[str, Any]] = None
        self.last_output_dir: Optional[Path] = None
        self.is_running: bool = False
        self.progress_tick: int = 0
        self.progress_metrics: Dict[str, Any] = {}
        self._worker: Optional[_PsExperimentWorker] = None
        self._editor_context: Any = None
        self._state = PsExperimentState()
        self._project_open_handler = None
        self._applied_project_binding: tuple[str, str] | None = None
        self._runtime_snapshot_authority = PsRuntimeSnapshotAuthority()

    @property
    def state(self) -> PsExperimentState:
        return self._state

    def current_runtime_run_id(self) -> str | None:
        """Return the active opaque PS run ID without exposing worker state."""
        return self._runtime_snapshot_authority.current_run_id()

    def discover_runtime_organisms(self) -> Dict[str, Any]:
        """Acquire the active PS run and exact current organism identities."""
        return self._runtime_snapshot_authority.discover()

    def query_runtime_organism_snapshot(self, identity: object) -> Dict[str, Any]:
        """Query one live organism through the shared Qt-free Authority."""
        return self._runtime_snapshot_authority.query(identity)

    def bind_editor_context(self, editor_context: Any) -> None:
        """精确绑定一个 Editor Host context，并拥有 project_opened 订阅。"""
        if self._editor_context is editor_context:
            return
        if self._editor_context is not None:
            raise RuntimeError("PsExperimentService is already bound to another editor context")

        bus = getattr(editor_context, "event_bus", None)
        subscribe = getattr(bus, "subscribe", None)
        handler = self._on_project_opened_auto_load if callable(subscribe) else None
        self._editor_context = editor_context
        self._project_open_handler = handler
        try:
            if handler is not None:
                subscribe("project_opened", handler)
            self._on_project_opened_auto_load(
                getattr(editor_context, "current_project_path", None)
            )
        except BaseException:
            if handler is not None:
                unsubscribe = getattr(bus, "unsubscribe", None)
                if callable(unsubscribe):
                    try:
                        unsubscribe("project_opened", handler)
                    except BaseException:
                        logger.warning(
                            "PsExperimentService 绑定回滚未能取消 project_opened 订阅",
                            exc_info=True,
                        )
            self._project_open_handler = None
            self._editor_context = None
            raise

    def unbind_editor_context(self) -> None:
        """释放精确拥有的订阅；失败时保留状态以允许后续重试。"""
        editor_context = self._editor_context
        handler = self._project_open_handler
        if editor_context is None:
            return

        bus = getattr(editor_context, "event_bus", None)
        unsubscribe = getattr(bus, "unsubscribe", None)
        if handler is not None and callable(unsubscribe):
            unsubscribe("project_opened", handler)
        self._project_open_handler = None
        self._editor_context = None
        self._applied_project_binding = None

    def _on_project_opened_auto_load(self, data: Any) -> None:
        proj_path: Optional[str] = None
        if isinstance(data, dict):
            proj_path = str(data.get("project_path") or "") or None
        elif isinstance(data, str):
            proj_path = data or None
        if not proj_path and self._editor_context is not None:
            proj_path = getattr(self._editor_context, "current_project_path", None)
        if proj_path:
            self.load_project_bindings(proj_path)

    def load_project_bindings(self, project_path: str | Path) -> bool:
        """打开工程时自动加载 ps_experiment_preset 与 evolution_defaults。"""
        try:
            pj = (Path(project_path) / "project.json").resolve()
            raw = pj.read_bytes()
            meta = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            logger.warning("读取工程绑定失败: %s", exc)
            return False

        fingerprint = (str(pj), hashlib.sha256(raw).hexdigest())
        if fingerprint == self._applied_project_binding:
            return False
        self._applied_project_binding = fingerprint

        changed = False
        preset = meta.get("ps_experiment_preset")
        if preset:
            try:
                self.load_preset_relative(str(preset))
                changed = True
                logger.info("已自动加载 PS 实验预设: %s", preset)
            except Exception as exc:
                logger.warning("自动加载 PS 实验预设失败: %s", exc)

        try:
            from core.VitaLoom.project.evolution_context import (
                apply_developmental_profile_from_project,
                apply_evolution_defaults_to_ps_config,
                load_project_evolution_context,
            )

            defaults = load_project_evolution_context(meta)
            if defaults:
                apply_evolution_defaults_to_ps_config(self.config, defaults)
                changed = True
            if meta.get("developmental_profile"):
                apply_developmental_profile_from_project(self.config, meta)
                changed = True
        except Exception as exc:
            logger.debug("自动加载 evolution_defaults 失败: %s", exc)

        if changed:
            self._emit_config_changed()
        return changed

    def _emit_config_changed(self) -> None:
        bus = getattr(self._editor_context, "event_bus", None)
        if bus and hasattr(bus, "publish"):
            bus.publish(EVENT_CONFIG_CHANGED, {"config": self.config})

    def _register_ps_lane_stop(self) -> None:
        try:
            from core.VitaLoom.simulation.simulation_coordinator import (
                SimulationLane,
                get_simulation_coordinator,
            )

            coord = get_simulation_coordinator()
            if coord is not None:
                coord.register_lane_stop(SimulationLane.PS_BATCH)
        except Exception:
            __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)

    def _end_active_runtime_lifetime(self) -> None:
        """Best-effort cleanup for construction/export/dispatch failures."""
        run_id = self._runtime_snapshot_authority.current_run_id()
        if run_id is not None:
            self._runtime_snapshot_authority.end(run_id)

    def _output_runs_dir(self, output_dir: Optional[str] = None) -> Path:
        rel = output_dir or self.config.output_dir
        p = Path(rel)
        if not p.is_absolute():
            p = self._root / rel
        return p

    def _config_with_resolved_output_dir(
        self,
        config: PsExperimentConfig,
    ) -> PsExperimentConfig:
        output_dir = Path(config.output_dir)
        if output_dir.is_absolute():
            return config
        return replace(config, output_dir=str((self._root / output_dir).resolve()))

    def list_recent_runs(
        self,
        max_runs: int = 15,
        output_dir: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """扫描 experiment_runs 子目录，读取 summary.json（对标 Test Runner 历史列表）。"""
        base = self._output_runs_dir(output_dir)
        if not base.is_dir():
            return []
        runs: List[Dict[str, Any]] = []
        for child in base.iterdir():
            if not child.is_dir():
                continue
            summary_path = child / "summary.json"
            if not summary_path.is_file():
                continue
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                final = data.get("final") or {}
                cfg = data.get("config") or {}
                runs.append(
                    {
                        "dir": child,
                        "dir_name": child.name,
                        "finished_at": str(data.get("finished_at", "")),
                        "name": str(cfg.get("name", child.name)),
                        "population": int(final.get("population", 0)),
                        "iteration": int(final.get("iteration", 0)),
                        "avg_fitness": float(final.get("avg_fitness", 0.0)),
                        "avg_memory_count": float(final.get("avg_memory_count", 0.0)),
                        "cancelled": bool(data.get("cancelled", False)),
                    }
                )
            except Exception as exc:
                logger.debug("跳过无效实验目录 %s: %s", child, exc)
        runs.sort(key=lambda r: r.get("finished_at", ""), reverse=True)
        return runs[: max(1, max_runs)]

    def _emit_finished(self, summary: Dict[str, Any], out_dir: Optional[Path]) -> None:
        ctx = self._editor_context
        if ctx is None:
            return
        bus = getattr(ctx, "event_bus", None)
        if bus is None or not hasattr(bus, "publish"):
            return
        try:
            bus.publish(
                EVENT_FINISHED,
                {"summary": summary, "output_dir": out_dir},
            )
        except Exception as exc:
            logger.debug("发布 ps_experiment_finished 失败: %s", exc)

    def _state_from_metrics(
        self,
        phase: PsExperimentPhase,
        metrics: Optional[Dict[str, Any]] = None,
        *,
        cancelled: bool = False,
        name: Optional[str] = None,
    ) -> PsExperimentState:
        m = metrics or {}
        cfg = self.config
        return PsExperimentState(
            phase=phase,
            is_running=phase == "running",
            name=name or str(getattr(cfg, "name", "") or ""),
            tick=int(m.get("tick", self.progress_tick)),
            total_ticks=int(getattr(cfg, "ticks", 0) or 0),
            population=int(m.get("population", 0)),
            iteration=int(m.get("iteration", 0)),
            avg_fitness=float(m.get("avg_fitness", 0.0)),
            avg_memory_count=float(m.get("avg_memory_count", 0.0)),
            cancelled=cancelled,
        )

    def _emit_state(self, state: Optional[PsExperimentState] = None) -> None:
        if state is not None:
            self._state = state
        ctx = self._editor_context
        if ctx is None:
            return
        bus = getattr(ctx, "event_bus", None)
        if bus is None or not hasattr(bus, "publish"):
            return
        try:
            bus.publish(EVENT_STATE, self._state)
        except Exception as exc:
            logger.debug("发布 ps_experiment_state 失败: %s", exc)

    def _emit_progress_state(self, metrics: Dict[str, Any]) -> None:
        tick = int(metrics.get("tick", 0))
        total = int(self.config.ticks)
        if tick > 0 and tick < total and tick % 10 != 0:
            return
        self._emit_state(self._state_from_metrics("running", metrics))

    @property
    def experiments_dir(self) -> Path:
        return default_experiments_dir(self._root)

    def list_presets(self) -> List[tuple[str, Path]]:
        """返回 (显示名, 路径) 列表。"""
        d = self.experiments_dir
        if not d.is_dir():
            return []
        out: List[tuple[str, Path]] = []
        for p in sorted(d.glob("*.json")):
            out.append((p.stem, p))
        return out

    def load_preset(self, path: str | Path) -> PsExperimentConfig:
        self.config = load_experiment_config(path)
        return self.config

    def load_preset_relative(self, rel: str) -> PsExperimentConfig:
        p = Path(rel)
        if not p.is_absolute():
            p = self._root / rel
        return self.load_preset(p)

    def save_preset(self, path: str | Path, config: Optional[PsExperimentConfig] = None) -> Path:
        cfg = config or self.config
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def run_sync(
        self,
        config: Optional[PsExperimentConfig] = None,
        *,
        export: bool = True,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> tuple[Dict[str, Any], Optional[Path]]:
        """Run synchronously with deterministic lane and Authority cleanup."""
        cfg = config or self.config
        self.config = cfg
        from core.VitaLoom.simulation.simulation_coordinator import (
            SimulationLane,
            get_simulation_coordinator,
        )

        coord = get_simulation_coordinator()
        if coord is not None and not coord.register_lane_start(SimulationLane.PS_BATCH):
            raise RuntimeError(
                "PS experiment cannot start while the coordinator disallows parallel SR/PS execution"
            )
        self.is_running = True
        self.progress_tick = 0
        self.progress_metrics = {}
        self._emit_state(self._state_from_metrics("running", name=cfg.name))

        try:
            runner = PsExperimentRunner(
                self._config_with_resolved_output_dir(cfg),
                snapshot_authority=self._runtime_snapshot_authority,
            )

            def _prog(m: Dict[str, Any]) -> None:
                self.progress_tick = int(m.get("tick", 0))
                self.progress_metrics = dict(m)
                if progress_callback:
                    progress_callback(m)
                self._emit_progress_state(m)

            summary = runner.run(progress_callback=_prog)
            out_dir: Optional[Path] = None
            if export:
                out_dir = runner.export(summary)
            self.is_running = False
            self.last_summary = summary
            self.last_output_dir = out_dir
            self.progress_metrics = dict(summary.get("final") or {})
            self.progress_tick = int(self.progress_metrics.get("tick", 0))
            cancelled = bool(summary.get("cancelled"))
            phase: PsExperimentPhase = "cancelled" if cancelled else "finished"
            self._emit_state(
                self._state_from_metrics(
                    phase,
                    self.progress_metrics,
                    cancelled=cancelled,
                    name=cfg.name,
                )
            )
            self._emit_finished(summary, out_dir)
            return summary, out_dir
        except Exception:
            self.is_running = False
            self._emit_state(
                PsExperimentState(phase="error", is_running=False, name=cfg.name)
            )
            raise
        finally:
            self.is_running = False
            self._end_active_runtime_lifetime()
            self._register_ps_lane_stop()
            self._emit_state(PsExperimentState())

    def run_async(
        self,
        config: Optional[PsExperimentConfig] = None,
        *,
        export: bool = True,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_finished: Optional[Callable[[Dict[str, Any], Optional[Path]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Start the worker Adapter and roll back every failed start path."""
        if self.is_running:
            return False
        cfg = config or self.config
        self.config = cfg
        from core.VitaLoom.simulation.simulation_coordinator import (
            SimulationLane,
            get_simulation_coordinator,
        )

        coord = get_simulation_coordinator()
        if coord is not None and not coord.register_lane_start(SimulationLane.PS_BATCH):
            return False
        self.is_running = True
        self.progress_tick = 0
        self.progress_metrics = {}
        self._emit_state(self._state_from_metrics("running", name=cfg.name))

        worker: Optional[_PsExperimentWorker] = None
        try:
            worker = _PsExperimentWorker(
                self._config_with_resolved_output_dir(cfg),
                export_results=export,
                snapshot_authority=self._runtime_snapshot_authority,
            )
            self._worker = worker

            def _prog(m: dict) -> None:
                if self._worker is not worker:
                    return
                self.progress_tick = int(m.get("tick", 0))
                self.progress_metrics = dict(m)
                self._emit_progress_state(m)
                if on_progress:
                    on_progress(m)

            def _done(summary: dict, out_dir: object) -> None:
                if self._worker is not worker:
                    return
                self._end_active_runtime_lifetime()
                self.is_running = False
                self.last_summary = summary
                self.last_output_dir = out_dir if isinstance(out_dir, Path) else None
                self._worker = None
                self._register_ps_lane_stop()
                final = summary.get("final") or {}
                self.progress_metrics = dict(final)
                cancelled = bool(summary.get("cancelled"))
                phase: PsExperimentPhase = "cancelled" if cancelled else "finished"
                self._emit_state(
                    self._state_from_metrics(
                        phase,
                        final,
                        cancelled=cancelled,
                        name=cfg.name,
                    )
                )
                self._emit_finished(summary, self.last_output_dir)
                self._emit_state(PsExperimentState())
                if on_finished:
                    on_finished(summary, self.last_output_dir)

            def _fail(msg: str) -> None:
                if self._worker is not worker:
                    return
                self._end_active_runtime_lifetime()
                self.is_running = False
                self._worker = None
                self._register_ps_lane_stop()
                self._emit_state(
                    PsExperimentState(phase="error", is_running=False, name=cfg.name)
                )
                self._emit_state(PsExperimentState())
                if on_error:
                    on_error(msg)

            worker.progress.connect(_prog, Qt.ConnectionType.QueuedConnection)
            worker.finished_ok.connect(_done, Qt.ConnectionType.QueuedConnection)
            worker.failed.connect(_fail, Qt.ConnectionType.QueuedConnection)
            worker.start()
            return True
        except Exception as exc:
            if worker is None or self._worker is worker:
                self._end_active_runtime_lifetime()
                self.is_running = False
                self._worker = None
                self._register_ps_lane_stop()
                self._emit_state(
                    PsExperimentState(phase="error", is_running=False, name=cfg.name)
                )
                self._emit_state(PsExperimentState())
            logger.exception("PS experiment worker failed to start")
            if on_error:
                on_error(str(exc))
            return False

    def request_cancel(self) -> None:
        if self._worker is not None:
            self._worker.request_cancel()

    def get_ecology_snapshot(self) -> Dict[str, Any]:
        """供 EcologyDashboard 只读展示。"""
        if self.is_running:
            m = self.progress_metrics
            return {
                "ps_active": True,
                "ps_tick": self.progress_tick,
                "ps_total_ticks": int(self.config.ticks),
                "ps_population": int(m.get("population", 0)),
                "ps_iteration": int(m.get("iteration", 0)),
                "ps_avg_fitness": float(m.get("avg_fitness", 0.0)),
                "ps_avg_memory_count": float(m.get("avg_memory_count", 0.0)),
                "ps_avg_memory_gene_count": float(m.get("avg_memory_gene_count", 0.0)),
                "ps_avg_social_memory_count": float(m.get("avg_social_memory_count", 0.0)),
                "ps_avg_developmental_stage": float(m.get("avg_developmental_stage", 0.0)),
                "ps_pct_at_stage_s4": float(m.get("pct_at_stage_s4", 0.0)),
                "ps_developmental_ladder_enabled": bool(m.get("developmental_ladder_enabled", False)),
                "ps_avg_verify_success": float(m.get("avg_verify_success", 0.0)),
                "ps_reproduction_events": int(m.get("reproduction_events", 0) or 0),
                "ps_war_phase": m.get("war_phase"),
                "ps_population_at_war_end": m.get("population_at_war_end"),
                "ps_war_population_min": m.get("war_population_min"),
            }
        if self.last_summary:
            final = self.last_summary.get("final") or {}
            return {
                "ps_active": False,
                "ps_tick": int(final.get("tick", 0)),
                "ps_total_ticks": int(self.config.ticks),
                "ps_population": int(final.get("population", 0)),
                "ps_iteration": int(final.get("iteration", 0)),
                "ps_avg_fitness": float(final.get("avg_fitness", 0.0)),
                "ps_avg_memory_count": float(final.get("avg_memory_count", 0.0)),
                "ps_avg_memory_gene_count": float(final.get("avg_memory_gene_count", 0.0)),
                "ps_avg_social_memory_count": float(final.get("avg_social_memory_count", 0.0)),
                "ps_avg_developmental_stage": float(final.get("avg_developmental_stage", 0.0)),
                "ps_pct_at_stage_s4": float(final.get("pct_at_stage_s4", 0.0)),
                "ps_developmental_ladder_enabled": bool(
                    final.get("developmental_ladder_enabled", self.config.developmental_ladder_enabled)
                ),
                "ps_avg_verify_success": float(final.get("avg_verify_success", 0.0)),
                "ps_reproduction_events": int(final.get("reproduction_events", 0) or 0),
                "ps_war_phase": final.get("war_phase"),
                "ps_population_at_war_end": final.get("population_at_war_end"),
                "ps_war_population_min": final.get("war_population_min"),
                "ps_cancelled": bool(self.last_summary.get("cancelled", False)),
            }
        return {"ps_active": False, "ps_has_result": False}


def get_ps_experiment_service(editor_context: Any = None) -> Optional[PsExperimentService]:
    registry = resolve_runtime_capability_registry(editor_context)
    if registry is None and editor_context is None:
        try:
            from core.VitaLoom.core.editor_context import get_existing_editor_context

            registry = resolve_runtime_capability_registry(
                get_existing_editor_context()
            )
        except Exception:
            return None
    if registry is None:
        return None
    svc = registry.get(SERVICE_KEY)
    return svc if isinstance(svc, PsExperimentService) else None


def default_experiments_dir(project_root: Path) -> Path:
    return project_root / "workspace" / "experiments"


def compare_run_metrics(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
) -> Dict[str, float]:
    """历史 run 与当前/选中 run 的指标差（实验 Dock 对比行）。"""
    keys = (
        ("population", "delta_population"),
        ("iteration", "delta_iteration"),
        ("avg_fitness", "delta_avg_fitness"),
        ("avg_memory_count", "delta_avg_memory_count"),
    )
    out: Dict[str, float] = {}
    for src, dst in keys:
        out[dst] = float(current.get(src, 0) or 0) - float(baseline.get(src, 0) or 0)
    return out


class _PsExperimentWorker(QThread):
    progress = pyqtSignal(dict)
    finished_ok = pyqtSignal(dict, object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        config: PsExperimentConfig,
        *,
        export_results: bool = True,
        snapshot_authority: PsRuntimeSnapshotAuthority | None = None,
    ):
        super().__init__()
        self._config = config
        self._export = export_results
        self._runner = PsExperimentRunner(
            config,
            snapshot_authority=snapshot_authority,
        )

    def request_cancel(self) -> None:
        self._runner.request_cancel()

    def run(self) -> None:
        try:

            def _prog(m: Dict[str, Any]) -> None:
                self.progress.emit(m)

            summary = self._runner.run(progress_callback=_prog)
            out_dir: Optional[Path] = None
            if self._export:
                out_dir = self._runner.export(summary)
            self.finished_ok.emit(summary, out_dir)
        except Exception as exc:
            logger.exception("PS 实验线程失败")
            self.failed.emit(str(exc))
