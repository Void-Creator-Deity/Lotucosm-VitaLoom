"""Qt-free standard Editor menu/toolbar commands with bounded Host bridges.

StandardUI owns portable command declarations and declarative Editor contribution
facts. PyQt is imported only inside the concrete legacy dialog bridge methods.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from core.VitaLoom.commands.registry import (
    CommandSpec,
    command_error,
    command_ok,
    get_command_registry,
)
from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider, IRuntimePlugin
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.project.project_world_capabilities import (
    get_project_world_read_model,
)
from core.VitaLoom.ui.semantic_history import mirror_scene_save_history_snapshot


logger = get_logger("StandardUIPlugin")


def _menu_path(segment_id: str, label_key: str, default_label: str) -> list[dict[str, str]]:
    return [
        {
            "id": segment_id,
            "label_key": label_key,
            "default_label": default_label,
        }
    ]


def _nested_menu_path(
    parent_id: str,
    parent_label_key: str,
    parent_default_label: str,
    child_id: str,
    child_label_key: str,
    child_default_label: str,
) -> list[dict[str, str]]:
    return [
        {
            "id": parent_id,
            "label_key": parent_label_key,
            "default_label": parent_default_label,
        },
        {
            "id": child_id,
            "label_key": child_label_key,
            "default_label": child_default_label,
        },
    ]


def _menu_command(
    contribution_id: str,
    menu_path: list[dict[str, str]],
    label_key: str,
    default_label: str,
    command_id: str,
    shortcut: str | None,
    order: int,
) -> dict[str, Any]:
    return {
        "id": contribution_id,
        "kind": "menu_command",
        "menu_path": menu_path,
        "label_key": label_key,
        "default_label": default_label,
        "command_id": command_id,
        "command_payload": {},
        "shortcut": shortcut,
        "order": order,
    }


def _editor_contributions() -> list[dict[str, Any]]:
    file_menu = _menu_path("file", "menu.file", "文件")
    edit_menu = _menu_path("edit", "menu.edit", "编辑")
    view_menu = _menu_path("view", "menu.view", "视图")
    layout_menu = _nested_menu_path(
        "view", "menu.view", "视图", "layouts", "menu.layouts", "布局"
    )
    panels_menu = _nested_menu_path(
        "view", "menu.view", "视图", "panels", "menu.view_panels", "面板"
    )
    help_menu = _menu_path("help", "menu.help", "帮助")
    return [
        _menu_command(
            "standard_ui.menu.save_project", file_menu,
            "menu.save_project", "保存项目",
            "plugin.standard_ui.save_project", "Ctrl+Shift+P", 10,
        ),
        _menu_command(
            "standard_ui.menu.save_scene", file_menu,
            "menu.save_scene", "保存场景",
            "plugin.standard_ui.save_scene", "Ctrl+S", 20,
        ),
        _menu_command(
            "standard_ui.menu.exit", file_menu,
            "menu.exit", "退出",
            "plugin.standard_ui.exit", "Alt+F4", 30,
        ),
        _menu_command(
            "standard_ui.menu.undo", edit_menu,
            "menu.undo", "撤销",
            "plugin.standard_ui.undo", "Ctrl+Z", 40,
        ),
        _menu_command(
            "standard_ui.menu.redo", edit_menu,
            "menu.redo", "重做",
            "plugin.standard_ui.redo", "Ctrl+Y", 50,
        ),
        _menu_command(
            "standard_ui.menu.view.scene", view_menu,
            "menu.scene_view", "场景视图",
            "plugin.standard_ui.view.scene", "F1", 60,
        ),
        _menu_command(
            "standard_ui.menu.view.game", view_menu,
            "menu.game_view", "游戏视图",
            "plugin.standard_ui.view.game", "F2", 70,
        ),
        {
            "id": "standard_ui.menu.view.separator.primary",
            "kind": "menu_separator",
            "menu_path": view_menu,
            "order": 80,
        },
        _menu_command(
            "standard_ui.menu.layout.save", layout_menu,
            "menu.save_layout", "保存布局",
            "plugin.standard_ui.layout.save", None, 90,
        ),
        _menu_command(
            "standard_ui.menu.layout.restore", layout_menu,
            "menu.restore_layout", "恢复布局",
            "plugin.standard_ui.layout.restore", None, 100,
        ),
        _menu_command(
            "standard_ui.menu.layout.reset", layout_menu,
            "menu.reset_layout", "重置布局",
            "plugin.standard_ui.layout.reset", None, 110,
        ),
        {
            "id": "standard_ui.menu.view.separator.panels",
            "kind": "menu_separator",
            "menu_path": view_menu,
            "order": 120,
        },
        _menu_command(
            "standard_ui.menu.dock.simulation.reveal", panels_menu,
            "menu.show_simulation_dock", "显示模拟面板",
            "plugin.standard_ui.dock.simulation.reveal", "Ctrl+Shift+M", 130,
        ),
        _menu_command(
            "standard_ui.menu.dock.ecology.reveal", panels_menu,
            "menu.show_ecology_dock", "显示莲池生态",
            "plugin.standard_ui.dock.ecology.reveal", "Ctrl+Shift+E", 140,
        ),
        _menu_command(
            "standard_ui.menu.dock.ps_experiment.reveal", panels_menu,
            "menu.show_ps_experiment_dock", "莲池演化实验",
            "plugin.standard_ui.dock.ps_experiment.reveal", "Ctrl+Shift+P", 150,
        ),
        _menu_command(
            "standard_ui.menu.dock.inspector.toggle_floating", panels_menu,
            "menu.toggle_inspector_float", "检视器：切换浮动",
            "plugin.standard_ui.dock.inspector.toggle_floating", None, 160,
        ),
        _menu_command(
            "standard_ui.menu.dock.console.toggle_floating", panels_menu,
            "menu.toggle_console_float", "控制台：切换浮动",
            "plugin.standard_ui.dock.console.toggle_floating", None, 170,
        ),
        _menu_command(
            "standard_ui.menu.about", help_menu,
            "menu.about", "关于",
            "plugin.standard_ui.about", None, 180,
        ),
        {
            "id": "standard_ui.toolbar.save_project",
            "kind": "toolbar_command",
            "label_key": "toolbar.save",
            "default_label": "保存",
            "command_id": "plugin.standard_ui.save_project",
            "command_payload": {},
            "icon": "document-save",
            "group": "standard",
            "order": 10,
        },
        {
            "id": "standard_ui.toolbar.separator",
            "kind": "toolbar_separator",
            "group": "standard",
            "order": 15,
        },
        {
            "id": "simulation.toggle",
            "kind": "toolbar_command",
            "label_key": "toolbar.play",
            "default_label": "运行",
            "command_id": "simulation.toggle",
            "command_payload": {},
            "icon": "media-playback-start",
            "group": "simulation",
            "order": 20,
            "state": {
                "command_id": "simulation.transport.status",
                "result_field": "phase",
                "label_variants": {
                    "stopped": {"label_key": "toolbar.play", "default_label": "运行"},
                    "playing": {"label_key": "toolbar.pause", "default_label": "暂停"},
                    "paused": {"label_key": "toolbar.resume", "default_label": "继续"},
                },
                "refresh_events": ["simulation_transport_state"],
            },
        },
        {
            "id": "simulation.stop",
            "kind": "toolbar_command",
            "label_key": "toolbar.stop",
            "default_label": "停止",
            "command_id": "simulation.stop",
            "command_payload": {},
            "icon": "media-playback-stop",
            "group": "simulation",
            "order": 30,
        },
    ]


class StandardUIPlugin(IRuntimePlugin, ICommandProvider):
    """Own standard Editor workflow commands behind a small portable Interface."""

    def __init__(self) -> None:
        self.context: object | None = None
        self.kernel: object | None = None
        self._event_bus: object | None = None
        self._dock_guidance_seen: set[str] = set()

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "StandardUIPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "标准编辑器菜单和工具栏",
            "dependencies": ["LocalizationPlugin"],
            "provides": ["command", "editor_contribution"],
            "editor_contributions": _editor_contributions(),
            "protected": True,
        }

    def get_command_specs(self) -> list[CommandSpec]:
        common = {
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object"},
            "undoable": False,
            "requires_gui": True,
            "capability": "vitalloom.editor_essentials",
            "owner": "StandardUIPlugin",
        }
        declarations = [
            ("plugin.standard_ui.save_project", "Save project", self.save_project, True),
            ("plugin.standard_ui.save_scene", "Save scene", self.save_scene, True),
            ("plugin.standard_ui.exit", "Exit Editor", self.exit_application, True),
            ("plugin.standard_ui.undo", "Undo", self.undo, True),
            ("plugin.standard_ui.redo", "Redo", self.redo, True),
            ("plugin.standard_ui.view.scene", "Show scene view", self.switch_to_scene_view, True),
            ("plugin.standard_ui.view.game", "Show game view", self.switch_to_game_view, True),
            ("plugin.standard_ui.layout.save", "Save layout", self.save_layout, True),
            ("plugin.standard_ui.layout.restore", "Restore layout", self.restore_layout, True),
            ("plugin.standard_ui.layout.reset", "Reset layout", self.reset_layout, True),
            ("plugin.standard_ui.dock.simulation.reveal", "Reveal simulation dock", self.show_simulation_dock, True),
            ("plugin.standard_ui.dock.ecology.reveal", "Reveal ecology dock", self.show_ecology_dock, True),
            ("plugin.standard_ui.dock.ps_experiment.reveal", "Reveal PS experiment dock", self.show_ps_experiment_dock, True),
            ("plugin.standard_ui.dock.inspector.toggle_floating", "Toggle Inspector floating", self.toggle_inspector_float, True),
            ("plugin.standard_ui.dock.console.toggle_floating", "Toggle Console floating", self.toggle_console_float, True),
            ("plugin.standard_ui.about", "About VitaLoom", self.show_about, False),
        ]
        return [
            CommandSpec(
                id=command_id,
                title=title,
                description=title,
                handler=self._command_handler(operation),
                mutates=mutates,
                **common,
            )
            for command_id, title, operation, mutates in declarations
        ]

    @staticmethod
    def _command_handler(operation):
        def handle(
            _payload: Mapping[str, Any],
            _command_context: Mapping[str, Any] | None,
        ) -> Dict[str, Any]:
            return operation()

        return handle

    def on_load(self, editor_context):
        if self._event_bus is not None:
            self.on_unload()
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        self._dock_guidance_seen = set()
        event_bus = getattr(editor_context, "event_bus", None)
        if event_bus is not None:
            event_bus.subscribe("ps_experiment_state", self._on_ps_experiment_state)
            event_bus.subscribe("project_opened", self._on_project_opened)
            self._event_bus = event_bus

    def on_unload(self):
        event_bus = self._event_bus
        self._event_bus = None
        if event_bus is not None:
            for event_name, callback in (
                ("ps_experiment_state", self._on_ps_experiment_state),
                ("project_opened", self._on_project_opened),
            ):
                try:
                    event_bus.unsubscribe(event_name, callback)
                except Exception as exc:
                    logger.warning("取消 StandardUI 事件订阅失败 (%s): %s", event_name, exc)
        self.context = None
        self.kernel = None
        self._dock_guidance_seen = set()

    def _log_error(self, action: str, error: Exception) -> None:
        logger.exception("%s失败: %s", action, error)

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return str(tr_fn(key, default))
        return default or key

    @staticmethod
    def _state_value(state: object, field: str, default: Any = None) -> Any:
        if isinstance(state, Mapping):
            return state.get(field, default)
        return getattr(state, field, default)

    def _on_ps_experiment_state(self, state) -> None:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        statusbar = getattr(layout_manager, "statusbar", None)
        if statusbar is None:
            return
        phase = self._state_value(state, "phase")
        if phase == "running":
            tick = int(self._state_value(state, "tick", 0) or 0)
            total = int(self._state_value(state, "total_ticks", 0) or 0)
            population = int(self._state_value(state, "population", 0) or 0)
            fitness = float(self._state_value(state, "avg_fitness", 0.0) or 0.0)
            name = str(self._state_value(state, "name", "") or "")
            prefix = self._t("status.ps_experiment.running", "PS 实验")
            label = f"{name} · " if name else ""
            statusbar.showMessage(
                f"{prefix}: {label}tick {tick}/{total} · pop={population} · fit={fitness:.3f}",
                0,
            )
        elif phase in ("finished", "cancelled"):
            population = int(self._state_value(state, "population", 0) or 0)
            fitness = float(self._state_value(state, "avg_fitness", 0.0) or 0.0)
            message = (
                self._t("status.ps_experiment.cancelled", "PS 实验已取消")
                if phase == "cancelled"
                else self._t("status.ps_experiment.done", "PS 实验完成")
            )
            statusbar.showMessage(
                f"{message} · pop={population} · fit={fitness:.3f}", 6000
            )
        elif phase == "error":
            statusbar.showMessage(
                self._t("status.ps_experiment.error", "PS 实验失败"), 8000
            )

    def _on_project_opened(self, _path) -> None:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        statusbar = getattr(layout_manager, "statusbar", None)
        if statusbar is None or self.context is None:
            return
        try:
            config = get_project_world_read_model(
                self.context
            ).current_project_world_config()
            presentation = config.get("presentation", {})
            message = ""
            if isinstance(presentation, dict):
                message = str(
                    presentation.get("editor_entry_hint_zh")
                    or presentation.get("tagline_zh")
                    or ""
                ).strip()
            if message:
                statusbar.showMessage(message, 9000)
        except Exception as exc:
            logger.debug("项目引导状态栏失败: %s", exc)

    # Hub-only compatibility methods. They are intentionally absent from contributions.
    def new_project(self):
        self._show_hub_required_notice()
        return command_error("project_hub_required", "Project creation belongs to Hub")

    def open_project(self):
        self._show_hub_required_notice()
        return command_error("project_hub_required", "Project opening belongs to Hub")

    def save_scene(self):
        try:
            from core.VitaLoom.commands.registry import get_command_registry
            from core.VitaLoom.scene.scene_manager import get_scene_manager
            from core.VitaLoom.viewports.scene_viewport import SceneViewport

            scene_manager = get_scene_manager()
            scene_path = scene_manager.get_current_scene_path()
            if not scene_path:
                return command_error("scene_unavailable", "No active scene is available")

            viewport_data = None
            layout_manager = getattr(self.kernel, "layout_manager", None)
            providers = getattr(layout_manager, "viewport_providers", {}) or {}
            for viewport_provider in providers.values():
                viewport = getattr(viewport_provider, "viewport", None)
                if isinstance(viewport, SceneViewport):
                    viewport_data = viewport.get_scene_data()
                    break

            if not isinstance(viewport_data, dict):
                viewport_data = scene_manager.get_scene_data()
            if not isinstance(viewport_data, dict):
                return command_error("scene_unavailable", "No scene snapshot is available")
            result = get_command_registry().run(
                "scene.save", {"scene_path": str(scene_path), "data": viewport_data}
            )
            if result.get("ok"):
                persisted_data = (result.get("result") or {}).get("scene_data")
                scene_manager.commit_persisted_scene(
                    str(scene_path), persisted_data if isinstance(persisted_data, dict) else viewport_data
                )
                logger.info("场景保存成功: %s", scene_path)
                return command_ok(
                    {"status": "saved", "scene_path": str(scene_path)},
                    events=list(result.get("events", [])),
                    warnings=list(result.get("warnings", [])),
                )

            self._show_critical(
                self._t("dialog.error.title", "错误"),
                self._t("dialog.save_scene.failed", "保存场景失败"),
            )
            error = result.get("error") if isinstance(result, Mapping) else None
            return command_error(
                str((error or {}).get("code") or "scene_save_failed"),
                str((error or {}).get("message") or "Scene save failed"),
                details=dict((error or {}).get("details") or {}),
                warnings=list(result.get("warnings", [])) if isinstance(result, Mapping) else None,
            )
        except Exception as exc:
            self._log_error("保存场景", exc)
            self._show_critical(
                self._t("dialog.error.title", "错误"),
                self._t("dialog.save_scene.failed", "保存场景失败"),
            )
            return command_error(
                "scene_save_failed", "Scene save failed", details={"reason": str(exc)}
            )

    def save_project(self):
        """Save through the composition-root Project World session Host capability."""
        try:
            current_project_path = getattr(self.context, "current_project_path", "")
            if not current_project_path:
                self._show_warning(
                    self._t("dialog.warning.title", "警告"),
                    self._t(
                        "dialog.no_project",
                        "没有打开的项目，请先创建或打开一个项目",
                    ),
                )
                return command_error("project_unavailable", "No project is open")

            project_world_host = getattr(
                self.kernel, "project_world_session_host", None
            )
            save_project = getattr(project_world_host, "save_project", None)
            if not callable(save_project):
                raise RuntimeError(
                    "Project World session Host capability is unavailable"
                )
            if save_project():
                logger.info("项目保存成功: %s", current_project_path)
                return command_ok(
                    {"status": "saved", "project_path": str(current_project_path)}
                )

            self._show_critical(
                self._t("dialog.error.title", "错误"),
                self._t("dialog.save_project.failed", "保存项目失败"),
            )
            return command_error("project_save_failed", "Project save failed")
        except Exception as exc:
            self._log_error("保存项目", exc)
            self._show_critical(
                self._t("dialog.error.title", "错误"),
                self._t("dialog.save_project.failed", "保存项目失败"),
            )
            return command_error(
                "project_save_failed", "Project save failed", details={"reason": str(exc)}
            )

    def save_project_as(self):
        self._show_hub_required_notice()
        return command_error("project_hub_required", "Project duplication belongs to Hub")

    def _run_semantic_history_command(self, command_id: str) -> Dict[str, Any]:
        """Delegate history mutation to semantic authority and rehydrate its scene."""
        registry = get_command_registry()
        result = registry.run(command_id, {})
        if not result.get("ok", False):
            return result

        result_data = result.get("result") or {}
        if mirror_scene_save_history_snapshot(result):
            return result
        scene_path = str(result_data.get("scene_path") or "").strip()
        if scene_path and result_data.get("history_rehydrate_scene") is not False:
            registry.run("scene.open", {"scene_path": scene_path})
        return result

    def undo(self):
        return self._run_semantic_history_command("command.undo")

    def redo(self):
        return self._run_semantic_history_command("command.redo")

    def _switch_viewport(self, viewport_id: str) -> Dict[str, Any]:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        switch_viewport = getattr(layout_manager, "switch_viewport", None)
        if not callable(switch_viewport):
            return command_error("layout_unavailable", "Viewport switching is unavailable")
        switch_viewport(viewport_id)
        return command_ok({"status": "shown", "viewport_id": viewport_id})

    def switch_to_scene_view(self):
        return self._switch_viewport("scene")

    def switch_to_game_view(self):
        return self._switch_viewport("game")

    def _run_layout_action(self, method_name: str, status: str) -> Dict[str, Any]:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        operation = getattr(layout_manager, method_name, None)
        if not callable(operation):
            return command_error("layout_unavailable", f"Layout action {method_name} is unavailable")
        operation()
        return command_ok({"status": status})

    def save_layout(self):
        return self._run_layout_action("save_layout", "saved")

    def restore_layout(self):
        return self._run_layout_action("restore_layout", "restored")

    def reset_layout(self):
        return self._run_layout_action("reset_layout", "reset")

    def show_simulation_dock(self):
        return self._show_dock("Simulation")

    def show_ecology_dock(self):
        return self._show_dock("Ecology")

    def show_ps_experiment_dock(self):
        return self._show_dock("PS Experiment")

    def toggle_inspector_float(self):
        return self._toggle_dock_floating("Inspector")

    def toggle_console_float(self):
        return self._toggle_dock_floating("Console")

    def _show_dock(self, dock_title: str) -> Dict[str, Any]:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        docks = getattr(layout_manager, "docks", None)
        dock = docks.get(dock_title) if docks else None
        if dock is None:
            return command_error(
                "dock_unavailable", f"Dock is unavailable: {dock_title}",
                details={"dock_id": dock_title},
            )
        dock.setVisible(True)
        dock.show()
        dock.raise_()
        return command_ok({"status": "shown", "dock_id": dock_title})

    def _toggle_dock_floating(self, dock_title: str) -> Dict[str, Any]:
        layout_manager = getattr(self.kernel, "layout_manager", None)
        toggle = getattr(layout_manager, "toggle_dock_floating", None)
        if callable(toggle):
            toggle(dock_title)
            return command_ok({"status": "toggled", "dock_id": dock_title})

        docks = getattr(layout_manager, "docks", None)
        dock = docks.get(dock_title) if docks else None
        if dock is None:
            return command_error(
                "dock_unavailable", f"Dock is unavailable: {dock_title}",
                details={"dock_id": dock_title},
            )
        dock.setFloating(not dock.isFloating())
        dock.setVisible(True)
        dock.show()
        return command_ok({"status": "toggled", "dock_id": dock_title})

    def exit_application(self):
        close = getattr(self.kernel, "close", None)
        if not callable(close):
            return command_error("editor_close_unavailable", "Editor close is unavailable")
        close()
        return command_ok({"status": "closed"})

    def _show_hub_required_notice(self) -> None:
        self._show_warning(
            self._t("dialog.info.title", "提示"),
            self._t(
                "dialog.project_switch_hub_only",
                "项目创建、导入、打开和切换请回到 Hub。Editor 会话只服务当前项目。",
            ),
        )

    def _show_warning(self, title: str, message: str) -> None:
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self.kernel if self.kernel else None, title, message)
        except Exception:
            logger.warning("%s: %s", title, message)

    def _show_critical(self, title: str, message: str) -> None:
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self.kernel if self.kernel else None, title, message)
        except Exception:
            logger.error("%s: %s", title, message)

    def _show_about(self, title: str, message: str) -> None:
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.about(self.kernel if self.kernel else None, title, message)
        except Exception:
            logger.info("%s: %s", title, message)

    def show_about(self):
        self._show_about(
            self._t("about.title", "关于 VitaLoom Engine"),
            self._t(
                "about.content",
                "VitaLoom Engine v1.0.0\n\n基于继承算法的生命模拟引擎\n高度模块化插件架构\n\n© 2026 VitaLoom Team",
            ),
        )
        return command_ok({"status": "shown"})

