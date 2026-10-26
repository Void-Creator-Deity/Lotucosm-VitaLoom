# -*- coding: utf-8 -*-
"""Player 瘦窗口：仅 GameViewport + 场景加载，不加载编辑器插件。"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from typing import Optional
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QMainWindow

from core.VitaLoom.core.editor_context import EditorMode, get_editor_context
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.kernel.event_bus import EventBus


logger = get_logger("PlayerShell")


def validate_player_project_runtime(repo_root: str, project_path: str):
    """Validate product/capability closure before Player opens a project."""
    from core.VitaLoom.suite.project_lock import resolve_project_runtime
    from FrameCore.project_lock import load_project_lock, project_script_trust_lock_matches
    from core.Lotucosm.script_trust_policy import validate_project_script_trust_sources

    resolved = resolve_project_runtime(project_path, repo_root=repo_root)
    errors: list[str] = []
    if resolved.lock_error:
        errors.append(resolved.lock_error)
    if resolved.product_version_missing:
        errors.append(
            f"product version missing: {resolved.product_id} {resolved.product_version}"
        )
    if resolved.missing_capabilities:
        errors.append(
            "missing capabilities: " + ", ".join(resolved.missing_capabilities)
        )
    if resolved.capability_constraint_mismatches:
        errors.append(
            "capability constraint mismatch: "
            + ", ".join(resolved.capability_constraint_mismatches)
        )
    if resolved.capability_version_mismatches:
        errors.append(
            "capability version mismatch: "
            + ", ".join(resolved.capability_version_mismatches)
        )
    if resolved.runtime_backend_selection_mismatch:
        errors.append(
            "runtime backend selection does not match project.lock.json"
        )
    if os.environ.get("VITALOOM_EXPORT_ROOT") and resolved.lock_missing:
        errors.append("exported Player project is missing project.lock.json")
    project_data = {}
    try:
        project_data = json.loads((Path(project_path) / "project.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("project.json could not be read for script trust validation")
    if isinstance(project_data, dict) and "script_trust" in project_data:
        lock = load_project_lock(project_path)
        try:
            trust_matches = project_script_trust_lock_matches(
                project_path,
                lock,
                repo_root=repo_root,
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            trust_matches = False
        if not trust_matches:
            errors.append("project.lock.json script trust digest is stale or missing")
        source_validation = validate_project_script_trust_sources(project_path)
        if not source_validation.get("trusted"):
            errors.append(
                "project script trust source validation failed: "
                + str(source_validation.get("reason", "unknown"))
            )
    if errors:
        raise RuntimeError("; ".join(errors))
    return resolved


class PlayerShell(QMainWindow):
    """轻量 Player：中央 GameViewport，Esc 退出。"""

    def __init__(
        self,
        repo_root: str,
        project_path: str,
        parent=None,
        project_world_host=None,
        capability_registry: object | None = None,
        event_bus: object | None = None,
    ):
        super().__init__(parent)
        self._repo_root = os.path.abspath(repo_root)
        self._project_path = os.path.abspath(project_path)
        self._viewport = None

        self._project_world_host_lease = None
        self.project_world_capabilities: dict[str, object] = {}
        try:
            from core.VitaLoom.core.bundle_paths import resource_root

            if os.environ.get("VITALOOM_EXPORT_ROOT"):
                self._repo_root = str(resource_root())
            self._runtime_resolution = validate_player_project_runtime(
                self._repo_root,
                self._project_path,
            )

            # Bind the L1 runtime registry before constructing nested Host
            # Adapters. The legacy ProjectManager obtains EditorContext during
            # construction and must observe this composition's registry rather
            # than creating an unrelated default instance first.
            ctx = (
                get_editor_context()
                if capability_registry is None
                else get_editor_context(capability_registry)
            )
            self.capability_registry = ctx.services
            from core.VitaLoom.core.runtime_event_bus import require_runtime_event_bus

            ctx.event_bus = (
                EventBus()
                if event_bus is None
                else require_runtime_event_bus(event_bus)
            )

            if project_world_host is None:
                from core.VitaLoom.project.project_world_host_composition import (
                    acquire_project_world_host,
                )

                self._project_world_host_lease = acquire_project_world_host(
                    "player-shell"
                )
                project_world_host = self._project_world_host_lease.host
            self._project_world_host = project_world_host

            from core.VitaLoom.project.project_world_capabilities import (
                register_project_world_host_capabilities,
            )

            try:
                self.project_world_capabilities = register_project_world_host_capabilities(
                    ctx.services, self._project_world_host
                )
            except TypeError as exc:
                self.project_world_capabilities = {}
                logger.debug("Player Project World capability catalog unavailable: %s", exc)
            setattr(ctx, "project_root", self._repo_root)
            ctx.kernel = None

            from core.VitaLoom.simulation.simulation_transport import init_simulation_transport
            from core.VitaLoom.simulation.simulation_coordinator import init_simulation_coordinator

            init_simulation_transport(ctx)
            init_simulation_coordinator(ctx)

            project_name = self._load_project_metadata()
            self.setWindowTitle(f"{project_name} — VitaLoom Player")
            self.setGeometry(80, 80, 1280, 720)
            self.menuBar().hide()

            try:
                from core.VitaLoom.ui.theme_manager import ThemeType, get_theme_manager

                get_theme_manager().apply_theme(ThemeType.DARK)
            except Exception as exc:
                logger.debug("Player 主题应用失败: %s", exc)

            self._init_viewport(ctx)
            self._load_project_scene()
            self._bind_shortcuts()

            QTimer.singleShot(400, self._auto_start_playback)
        except Exception:
            self._release_viewport_host()
            self._release_project_world_host_lease()
            raise

    def _release_viewport_host(self) -> bool:
        """Unpublish only the SR Host capabilities owned by this Player Adapter."""

        viewport = getattr(self, "_viewport", None)
        if viewport is None:
            return True
        unregister = getattr(viewport, "unregister_as_sr_host", None)
        if not callable(unregister):
            return True
        try:
            unregister()
        except Exception as exc:
            logger.exception("Failed to unregister Player viewport Host: %s", exc)
            return False
        return True
    def _release_project_world_host_lease(self) -> bool:
        """Unpublish this shell's capabilities and release only an owned Host."""

        capabilities = getattr(self, "project_world_capabilities", {})
        if capabilities:
            try:
                from core.VitaLoom.project.project_world_capabilities import (
                    unregister_project_world_host_capabilities,
                )

                unregister_project_world_host_capabilities(
                    self.capability_registry, capabilities
                )
                self.project_world_capabilities = {}
            except Exception as exc:
                logger.exception(
                    "Failed to unregister Player Project World capabilities: %s", exc
                )
                return False

        lease = getattr(self, "_project_world_host_lease", None)
        if lease is None:
            return True
        try:
            released = lease.release()
        except Exception as exc:
            logger.exception("Failed to release Player Project World Host: %s", exc)
            return False
        if released or lease.released:
            self._project_world_host_lease = None
        return bool(released or lease.released)

    def _load_project_metadata(self) -> str:
        pj = os.path.join(self._project_path, "project.json")
        try:
            with open(pj, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                setattr(get_editor_context(), "current_project_config", data)
                return str(data.get("name") or os.path.basename(self._project_path))
        except Exception as exc:
            logger.warning("读取 project.json 失败: %s", exc)
        return os.path.basename(self._project_path)

    def _init_viewport(self, ctx) -> None:
        from core.VitaLoom.viewports.game_viewport import GameViewport

        self._viewport = GameViewport()
        if hasattr(self._viewport, "editor_context"):
            self._viewport.editor_context = ctx
        if hasattr(self._viewport, "register_as_sr_host"):
            self._viewport.register_as_sr_host()
        self.setCentralWidget(self._viewport)

    def _load_project_scene(self) -> None:
        open_world = getattr(self._project_world_host, "open_project", None)
        if not callable(open_world) or not bool(open_world(self._project_path)):
            logger.error("Player 打开工程失败: %s", self._project_path)
            return
        ctx = get_editor_context()
        ctx.set_mode(EditorMode.PLAY)

    def _auto_start_playback(self) -> None:
        if self._viewport and hasattr(self._viewport, "start_simulation"):
            try:
                self._viewport.start_simulation()
                logger.info("Player 已自动开始播放")
            except Exception as exc:
                logger.exception("Player 自动播放失败: %s", exc)

    def _bind_shortcuts(self) -> None:
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self.close)  # type: ignore

    def closeEvent(self, event) -> None:
        try:
            if self._viewport and hasattr(self._viewport, "stop_simulation"):
                self._viewport.stop_simulation()
            flush_world = getattr(self._project_world_host, "flush_current_project", None)
            if callable(flush_world):
                report = flush_world()
                if report.get("status") not in {"flushed", "noop"}:
                    logger.warning(
                        "Player 退出前 Project World flush 未完成 [%s]: %s",
                        report.get("code", "project_world_flush_failed"),
                        report.get("message", ""),
                    )
        except Exception as exc:
            logger.debug("Player 退出清理: %s", exc)
        if not PlayerShell._release_viewport_host(self):
            ignore = getattr(event, "ignore", None)
            if callable(ignore):
                ignore()
            return
        if not PlayerShell._release_project_world_host_lease(self):
            ignore = getattr(event, "ignore", None)
            if callable(ignore):
                ignore()
            return
        super().closeEvent(event)

def run_player_shell(
    app: QApplication,
    repo_root: str,
    project_path: str,
    *,
    capability_registry: object | None = None,
    event_bus: object | None = None,
) -> int:
    """显示 PlayerShell 并进入事件循环。"""
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
        require_runtime_capability_registry,
    )

    runtime_registry = (
        InMemoryRuntimeCapabilityRegistry()
        if capability_registry is None
        else require_runtime_capability_registry(capability_registry)
    )
    shell_kwargs: dict[str, object] = {
        "capability_registry": runtime_registry,
    }
    if event_bus is not None:
        shell_kwargs["event_bus"] = event_bus
    win = PlayerShell(repo_root, project_path, **shell_kwargs)
    win.show()
    return app.exec()


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def run_player_smoke(
    app: QApplication,
    repo_root: str,
    project_path: str,
    *,
    capability_registry: object | None = None,
    event_bus: object | None = None,
) -> int:
    """Construct PlayerShell offscreen against an isolated project copy."""
    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
        require_runtime_capability_registry,
    )

    runtime_registry = (
        InMemoryRuntimeCapabilityRegistry()
        if capability_registry is None
        else require_runtime_capability_registry(capability_registry)
    )
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    old_state_home = os.environ.get("VITALOOM_STATE_HOME")
    source_project = Path(project_path).resolve()
    if not (source_project / "project.json").is_file():
        raise FileNotFoundError(f"invalid project for Player smoke: {source_project}")
    with tempfile.TemporaryDirectory(prefix="vitaloom_player_smoke_") as tmp:
        tmp_path = Path(tmp)
        smoke_project = tmp_path / "project"
        shutil.copytree(source_project, smoke_project)
        from core.VitaLoom.core import bundle_paths
        from core.VitaLoom.project.project_world_host_composition import (
            dispose_project_world_host_if_idle,
        )

        os.environ["VITALOOM_STATE_HOME"] = str(tmp_path / "state")
        original_system_config_dir = bundle_paths.system_config_dir
        bundle_paths.system_config_dir = lambda: tmp_path / "workspace" / "state" / "system"
        if not dispose_project_world_host_if_idle():
            raise RuntimeError("Player smoke requires an idle Project World Host")
        shell = None
        try:
            shell_kwargs: dict[str, object] = {
                "capability_registry": runtime_registry,
            }
            if event_bus is not None:
                shell_kwargs["event_bus"] = event_bus
            shell = PlayerShell(
                repo_root,
                str(smoke_project),
                **shell_kwargs,
            )
            app.processEvents()
            ctx = get_editor_context()
            current_project = Path(ctx.current_project_path or "").resolve()
            if current_project != smoke_project.resolve():
                raise RuntimeError(
                    f"Player smoke opened wrong project: {current_project}"
                )
            if ctx.current_mode != EditorMode.PLAY:
                raise RuntimeError(f"Player smoke mode mismatch: {ctx.current_mode}")
            print(
                "Player smoke OK: "
                f"project={source_project.name} "
                f"mode={ctx.current_mode.value}"
            )
            return 0
        finally:
            if shell is not None:
                try:
                    shell.close()
                    app.processEvents()
                except Exception:
                    __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
            if not dispose_project_world_host_if_idle():
                raise RuntimeError(
                    "Player smoke leaked an active Project World Host lease"
                )
            bundle_paths.system_config_dir = original_system_config_dir
            _restore_env("VITALOOM_STATE_HOME", old_state_home)
