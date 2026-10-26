"""Qt-free Editor workflow declarations with bounded current-Host Qt bridges.

The plugin owns canonical commands for Pond import/export, clipboard summary,
dependency scanning, and Player export.  PyQt is imported only by the concrete
legacy Editor Host bridge methods near the end of this Module.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping

from core.VitaLoom.commands.registry import CommandSpec, command_error, command_ok
from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider, IRuntimePlugin
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.service_keys import UI_CONSOLE_PANEL

logger = get_logger("EditorWorkflow")


class EditorWorkflowPlugin(IRuntimePlugin, ICommandProvider):
    """Own portable Editor workflow commands and current-Host interaction bridges."""

    def __init__(self) -> None:
        self.context: object | None = None
        self.kernel: object | None = None

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "EditorWorkflowPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "剪贴板、莲池导入导出、场景依赖检查等",
            "dependencies": ["LocalizationPlugin"],
            "provides": ["command", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "editor_workflow.copy_pond_summary",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "edit",
                            "label_key": "menu.edit",
                            "default_label": "编辑",
                        }
                    ],
                    "label_key": "editor_workflow.copy_pond_summary",
                    "default_label": "复制莲池摘要",
                    "command_id": "plugin.editor_workflow.copy_pond_summary",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 10,
                },
                {
                    "id": "editor_workflow.export_pond",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "file",
                            "label_key": "menu.file",
                            "default_label": "文件",
                        }
                    ],
                    "label_key": "editor_workflow.export_pond",
                    "default_label": "导出当前莲池…",
                    "command_id": "plugin.editor_workflow.export_pond",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 20,
                },
                {
                    "id": "editor_workflow.import_pond",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "file",
                            "label_key": "menu.file",
                            "default_label": "文件",
                        }
                    ],
                    "label_key": "editor_workflow.import_pond",
                    "default_label": "导入莲池…",
                    "command_id": "plugin.editor_workflow.import_pond",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 30,
                },
                {
                    "id": "editor_workflow.scan_dependencies",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "file",
                            "label_key": "menu.file",
                            "default_label": "文件",
                        }
                    ],
                    "label_key": "editor_workflow.scan_dependencies",
                    "default_label": "检查场景依赖…",
                    "command_id": "plugin.editor_workflow.scan_dependencies",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 40,
                },
                {
                    "id": "editor_workflow.export_player",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "file",
                            "label_key": "menu.file",
                            "default_label": "文件",
                        }
                    ],
                    "label_key": "editor_workflow.export_player",
                    "default_label": "导出可运行 Player…",
                    "command_id": "plugin.editor_workflow.export_player",
                    "command_payload": {},
                    "shortcut": None,
                    "order": 50,
                },
            ],
        }

    def get_command_specs(self) -> list[CommandSpec]:
        common = {
            "input_schema": {"type": "object", "properties": {}},
            "output_schema": {"type": "object"},
            "mutates": True,
            "undoable": False,
            "requires_gui": True,
            "capability": "vitalloom.editor_essentials",
            "owner": "EditorWorkflowPlugin",
        }
        return [
            CommandSpec(
                id="plugin.editor_workflow.copy_pond_summary",
                title="Copy active Pond summary",
                description="Copy a JSON summary of the active Pond through the current Host clipboard bridge.",
                handler=self._copy_pond_summary_command,
                **common,
            ),
            CommandSpec(
                id="plugin.editor_workflow.export_pond",
                title="Export active Pond",
                description="Choose a JSON target and serialize the active Pond with the canonical Pond serializer.",
                handler=self._export_pond_command,
                **common,
            ),
            CommandSpec(
                id="plugin.editor_workflow.import_pond",
                title="Import Pond",
                description="Load Pond JSON and replace the active world or create and activate a new world.",
                handler=self._import_pond_command,
                **common,
            ),
            CommandSpec(
                id="plugin.editor_workflow.scan_dependencies",
                title="Scan scene dependencies",
                description="Scan the current project and publish an escaped report to the existing Console capability.",
                handler=self._scan_dependencies_command,
                **common,
            ),
            CommandSpec(
                id="plugin.editor_workflow.export_player",
                title="Export runnable Player",
                description="Export the current project through the existing Player export authority.",
                handler=self._export_player_command,
                **common,
            ),
        ]

    def on_load(self, editor_context: object) -> None:
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)

    def on_unload(self) -> None:
        self.context = None
        self.kernel = None

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return str(tr_fn(key, default))
        return default or key

    def _copy_pond_summary_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        return self.copy_pond_summary()

    def _export_pond_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        return self.export_active_pond()

    def _import_pond_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        return self.import_pond_json()

    def _scan_dependencies_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        return self.scan_scene_dependencies()

    def _export_player_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        return self.export_player_build()

    def _active_pond(self) -> object | None:
        try:
            from core.Lotucosm.cosmos import get_cosmos

            cosmos = get_cosmos()
            pond = cosmos.get_active_world()
            if pond is None and cosmos.worlds:
                pond = next(iter(cosmos.worlds.values()))
            return pond
        except Exception as exc:
            logger.warning("获取莲池失败: %s", exc)
            return None

    def copy_pond_summary(self) -> Dict[str, Any]:
        pond = self._active_pond()
        if pond is None:
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.no_pond", "没有可用的莲池。"),
            )
            return command_error(
                "editor_workflow_no_pond",
                "No active or fallback Pond is available",
            )
        try:
            summary = {
                "name": getattr(pond, "name", ""),
                "time": getattr(pond, "time", 0),
                "organisms": list(getattr(pond, "organisms", {}).keys()),
                "floating_components": len(
                    getattr(pond, "floating_components", []) or []
                ),
            }
            text = json.dumps(summary, ensure_ascii=False, indent=2)
            portable_summary = json.loads(text)
            self._write_clipboard_text(text)
            return command_ok(
                {
                    "status": "copied",
                    "summary": portable_summary,
                    "text": text,
                }
            )
        except Exception as exc:
            logger.exception("复制莲池摘要失败")
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.copy_summary_fail",
                    "复制莲池摘要失败：{err}",
                ).format(err=exc),
            )
            return command_error(
                "pond_summary_copy_failed",
                "Failed to copy the active Pond summary",
                details={"error": str(exc)},
            )

    def export_active_pond(self) -> Dict[str, Any]:
        pond = self._active_pond()
        if pond is None:
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.no_pond", "没有可用的莲池。"),
            )
            return command_error(
                "editor_workflow_no_pond",
                "No active or fallback Pond is available",
            )
        path = self._choose_save_pond_path()
        if not path:
            return command_ok({"status": "cancelled", "operation": "export_pond"})
        try:
            from builtin.systems.pond_serializer import PondSerializer

            ok = bool(PondSerializer(save_format="json").save_pond(pond, path))
            if not ok:
                self._show_warning(
                    self._t("dialog.warning.title", "警告"),
                    self._t(
                        "editor_workflow.export_fail",
                        "导出失败，请查看日志。",
                    ),
                )
                return command_error(
                    "pond_export_failed",
                    "PondSerializer rejected the export",
                    details={"path": str(path)},
                )
            self._show_information(
                self._t("dialog.success.title", "成功"),
                self._t("editor_workflow.export_ok", "莲池已导出。"),
            )
            return command_ok({"status": "exported", "path": str(path)})
        except Exception as exc:
            logger.exception("导出莲池失败")
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.export_fail",
                    "导出失败，请查看日志。",
                ),
            )
            return command_error(
                "pond_export_failed",
                "Failed to export the active Pond",
                details={"path": str(path), "error": str(exc)},
            )

    def import_pond_json(self) -> Dict[str, Any]:
        path = self._choose_open_pond_path()
        if not path:
            return command_ok(
                {"status": "cancelled", "operation": "import_pond", "stage": "file"}
            )
        try:
            from builtin.systems.pond_serializer import PondSerializer

            loaded = PondSerializer(save_format="json").load_pond(path)
            if loaded is None:
                self._show_warning(
                    self._t("dialog.warning.title", "警告"),
                    self._t(
                        "editor_workflow.import_fail",
                        "导入失败，请查看日志或检查 JSON。",
                    ),
                )
                return command_error(
                    "pond_import_failed",
                    "PondSerializer could not load the selected JSON",
                    details={"path": str(path)},
                )

            mode = self._choose_import_mode()
            if mode is None:
                return command_ok(
                    {
                        "status": "cancelled",
                        "operation": "import_pond",
                        "stage": "mode",
                        "path": str(path),
                    }
                )
            if mode not in {"replace_active", "new_world"}:
                return command_error(
                    "pond_import_mode_invalid",
                    "The current Host returned an unsupported import mode",
                    details={"mode": str(mode)},
                )

            import uuid
            from core.Lotucosm.cosmos import get_cosmos

            cosmos = get_cosmos()
            active = cosmos.get_active_world()
            wid_active = cosmos.active_world_id
            if mode == "replace_active":
                world_id = wid_active or "default"
                if wid_active and active is not None:
                    if hasattr(active, "_apply_loaded_pond_state"):
                        active._apply_loaded_pond_state(loaded)
                    cosmos.worlds[wid_active] = active
                    cosmos.set_active_world(wid_active)
                else:
                    if world_id in cosmos.worlds and cosmos.worlds[world_id] is not None:
                        target = cosmos.worlds[world_id]
                        if hasattr(target, "_apply_loaded_pond_state"):
                            target._apply_loaded_pond_state(loaded)
                        else:
                            cosmos.worlds[world_id] = loaded
                    else:
                        cosmos.worlds[world_id] = loaded
                    cosmos.set_active_world(world_id)
            else:
                world_id = f"imported_{uuid.uuid4().hex[:8]}"
                cosmos.worlds[world_id] = loaded
                cosmos.set_active_world(world_id)

            self._show_information(
                self._t("dialog.success.title", "成功"),
                self._t("editor_workflow.import_ok", "莲池已导入。"),
            )
            return command_ok(
                {
                    "status": "imported",
                    "mode": mode,
                    "world_id": str(world_id),
                    "path": str(path),
                }
            )
        except Exception as exc:
            logger.exception("导入莲池失败")
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.import_fail",
                    "导入失败，请查看日志或检查 JSON。",
                ),
            )
            return command_error(
                "pond_import_failed",
                "Failed to import the selected Pond JSON",
                details={"path": str(path), "error": str(exc)},
            )

    def scan_scene_dependencies(self) -> Dict[str, Any]:
        path = str(getattr(self.context, "current_project_path", None) or "").strip()
        if not path or not os.path.isdir(path):
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.scan_no_project",
                    "请先打开一个工程目录。",
                ),
            )
            return command_error(
                "editor_workflow_project_unavailable",
                "Scene dependency scanning requires an active project directory",
                details={"path": path},
            )
        try:
            from builtin.editor_extensions.asset_dependency_scan import (
                dependency_summary,
                format_dependency_scan_report,
                scan_project_dependencies,
            )

            edges = scan_project_dependencies(path)
            summary = dict(dependency_summary(edges))
            missing = [edge for edge in edges if not edge.exists]
            report = str(format_dependency_scan_report(path, edges, summary))
            logger.info(
                "场景依赖扫描: project=%s summary=%s missing=%s",
                path,
                summary,
                len(missing),
            )
            console_published = self._push_dependency_report_to_console(
                report, bool(missing)
            )
            if missing:
                self._show_dependency_missing_report(
                    report,
                    len(missing),
                    int(summary.get("total_edges", 0)),
                )
            else:
                self._show_information(
                    self._t("editor_workflow.scan_title", "场景依赖"),
                    self._t(
                        "editor_workflow.scan_all_ok",
                        "共扫描 {t} 条依赖边，未发现缺失文件。",
                    ).format(t=summary.get("total_edges", 0)),
                )
            return command_ok(
                {
                    "status": "scanned",
                    "project_path": path,
                    "summary": summary,
                    "missing_count": len(missing),
                    "console_published": console_published,
                    "report": report,
                }
            )
        except Exception as exc:
            logger.exception("场景依赖扫描失败")
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.scan_fail",
                    "场景依赖扫描失败：{err}",
                ).format(err=exc),
            )
            return command_error(
                "dependency_scan_failed",
                "Failed to scan scene dependencies",
                details={"project_path": path, "error": str(exc)},
            )

    def _push_dependency_report_to_console(
        self, report: str, has_missing: bool
    ) -> bool:
        services = getattr(self.context, "services", None)
        if services is None or not hasattr(services, "get"):
            return False
        panel = services.get(UI_CONSOLE_PANEL)
        if panel is None:
            return False
        level = "warning" if has_missing else "info"
        safe = html.escape(report, quote=False)
        if hasattr(panel, "log"):
            panel.log(safe, level)
            return True
        if hasattr(panel, "append_text"):
            panel.append_text(safe)
            return True
        return False

    def export_player_build(self) -> Dict[str, Any]:
        path = str(getattr(self.context, "current_project_path", None) or "").strip()
        if not path or not os.path.isdir(path):
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.export_player_no_project",
                    "请先打开一个工程目录。",
                ),
            )
            return command_error(
                "editor_workflow_project_unavailable",
                "Player export requires an active project directory",
                details={"path": path},
            )
        try:
            from tools.export_player import export_project

            output = export_project(Path(path))
            self._show_information(
                self._t("dialog.success.title", "成功"),
                self._t(
                    "editor_workflow.export_player_ok",
                    "Player 导出完成：\n{path}",
                ).format(path=output),
            )
            return command_ok(
                {
                    "status": "exported",
                    "project_path": path,
                    "output_path": str(output),
                }
            )
        except Exception as exc:
            logger.exception("导出 Player 失败")
            self._show_warning(
                self._t("dialog.warning.title", "警告"),
                self._t(
                    "editor_workflow.export_player_fail",
                    "导出失败：{err}",
                ).format(err=exc),
            )
            return command_error(
                "player_export_failed",
                "Failed to export the current project as a runnable Player",
                details={"project_path": path, "error": str(exc)},
            )

    # Concrete current-Host bridges.  These are intentionally narrow and lazy;
    # they are not portable contribution metadata or a new universal UI system.
    def _qt_parent(self) -> object | None:
        return self.kernel if self.kernel is not None else None

    def _choose_save_pond_path(self) -> str:
        from PyQt6.QtWidgets import QFileDialog

        path, _selected_filter = QFileDialog.getSaveFileName(
            self._qt_parent(),
            self._t("editor_workflow.export_pond", "导出当前莲池"),
            "",
            "JSON (*.json)",
        )
        return str(path or "")

    def _choose_open_pond_path(self) -> str:
        from PyQt6.QtWidgets import QFileDialog

        path, _selected_filter = QFileDialog.getOpenFileName(
            self._qt_parent(),
            self._t("editor_workflow.import_pond_title", "导入莲池"),
            "",
            "JSON (*.json)",
        )
        return str(path or "")

    def _choose_import_mode(self) -> str | None:
        from PyQt6.QtWidgets import QMessageBox

        message = QMessageBox(self._qt_parent())
        message.setIcon(QMessageBox.Icon.Question)
        message.setWindowTitle(
            self._t("editor_workflow.import_mode_title", "导入莲池")
        )
        message.setText(
            self._t("editor_workflow.import_mode_prompt", "请选择导入方式。")
        )
        replace_button = message.addButton(
            self._t(
                "editor_workflow.import_replace_active",
                "替换当前激活莲池",
            ),
            QMessageBox.ButtonRole.AcceptRole,
        )
        new_button = message.addButton(
            self._t(
                "editor_workflow.import_as_new_world",
                "新建世界并激活",
            ),
            QMessageBox.ButtonRole.ActionRole,
        )
        cancel_button = message.addButton(QMessageBox.StandardButton.Cancel)
        message.exec()
        clicked = message.clickedButton()
        if clicked is None or clicked == cancel_button:
            return None
        if clicked == replace_button:
            return "replace_active"
        if clicked == new_button:
            return "new_world"
        return None

    def _write_clipboard_text(self, text: str) -> None:
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(str(text))

    def _show_warning(self, title: str, text: str) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(self._qt_parent(), str(title), str(text))

    def _show_information(self, title: str, text: str) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(self._qt_parent(), str(title), str(text))

    def _show_dependency_missing_report(
        self, report: str, missing_count: int, total_edges: int
    ) -> None:
        from PyQt6.QtWidgets import QMessageBox

        message = QMessageBox(self._qt_parent())
        message.setIcon(QMessageBox.Icon.Warning)
        message.setWindowTitle(
            self._t("editor_workflow.scan_title", "场景依赖")
        )
        message.setText(
            self._t(
                "editor_workflow.scan_missing_summary",
                "发现 {n} 条缺失引用（共 {t} 条边）。",
            ).format(n=missing_count, t=total_edges)
        )
        message.setDetailedText(str(report))
        message.exec()
