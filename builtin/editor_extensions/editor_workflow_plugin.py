"""编辑器工作流插件：莲池导入导出、剪贴板摘要、场景依赖检查菜单项。

排错: 见 `builtin/README.md`、`asset_dependency_scan.py`。
"""

from __future__ import annotations

import json
import html
import os
from typing import Any, Dict, List

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication

from core.plugin.interfaces import IMenuProvider
from core.VitaLoom.core.logger import get_logger

logger = get_logger("EditorWorkflow")


class EditorWorkflowPlugin(IMenuProvider):
    """编辑辅助：莲池导入导出、剪贴板摘要、场景依赖扫描等。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "EditorWorkflow",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "剪贴板、莲池导入导出、场景依赖检查等",
            "dependencies": ["Localization"],
            "provides": ["menu"],
        }

    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = getattr(editor_context, "kernel", None)
        if hasattr(editor_context, "event_bus"):
            editor_context.event_bus.subscribe("language_changed", self._on_language_changed)

    def on_unload(self):
        if hasattr(self, "context") and self.context and hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception:
                pass

    def _on_language_changed(self, _data):
        if self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            if hasattr(lm, "remove_plugin_ui"):
                lm.remove_plugin_ui("EditorWorkflow")
            lm.add_menu_items(self.get_menu_items(), "EditorWorkflow")
            lm.add_toolbar_items(self.get_toolbar_items(), "EditorWorkflow")

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        return []

    def get_menu_items(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": f"{self._t('menu.edit', '编辑')}/{self._t('editor_workflow.copy_pond_summary', '复制莲池摘要')}",
                "action": self.copy_pond_summary,
            },
            {
                "path": f"{self._t('menu.file', '文件')}/{self._t('editor_workflow.export_pond', '导出当前莲池…')}",
                "action": self.export_active_pond,
            },
            {
                "path": f"{self._t('menu.file', '文件')}/{self._t('editor_workflow.import_pond', '导入莲池…')}",
                "action": self.import_pond_json,
            },
            {
                "path": f"{self._t('menu.file', '文件')}/{self._t('editor_workflow.scan_dependencies', '检查场景依赖…')}",
                "action": self.scan_scene_dependencies,
            },
        ]

    def scan_scene_dependencies(self):
        """扫描当前工程 scenes 与 project.json 活动场景的脚本/资源引用。"""
        path = getattr(self.context, "current_project_path", None) or ""
        path = str(path).strip()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.scan_no_project", "请先打开一个工程目录。"),
            )
            return
        from builtin.editor_extensions.asset_dependency_scan import (
            dependency_summary,
            format_dependency_scan_report,
            scan_project_dependencies,
        )

        edges = scan_project_dependencies(path)
        summ = dependency_summary(edges)
        missing = [e for e in edges if not e.exists]
        report = format_dependency_scan_report(path, edges, summ)

        logger.info(
            "场景依赖扫描: project=%s summary=%s missing=%s",
            path,
            summ,
            len(missing),
        )
        self._push_dependency_report_to_console(report, bool(missing))
        if missing:
            m = QMessageBox(self.kernel if self.kernel else None)
            m.setIcon(QMessageBox.Icon.Warning)
            m.setWindowTitle(self._t("editor_workflow.scan_title", "场景依赖"))
            m.setText(
                self._t(
                    "editor_workflow.scan_missing_summary",
                    "发现 {n} 条缺失引用（共 {t} 条边）。",
                ).format(n=len(missing), t=summ.get("total_edges", 0))
            )
            m.setDetailedText(report)
            m.exec()
        else:
            QMessageBox.information(
                self.kernel if self.kernel else None,
                self._t("editor_workflow.scan_title", "场景依赖"),
                self._t(
                    "editor_workflow.scan_all_ok",
                    "共扫描 {t} 条依赖边，未发现缺失文件。",
                ).format(t=summ.get("total_edges", 0)),
            )

    def _push_dependency_report_to_console(self, report: str, has_missing: bool) -> None:
        if not hasattr(self.context, "services"):
            return
        panel = self.context.services.get("ui.console_panel")
        if panel is None:
            return
        level = "warning" if has_missing else "info"
        safe = html.escape(report, quote=False)
        if hasattr(panel, "log"):
            panel.log(safe, level)
        elif hasattr(panel, "append_text"):
            panel.append_text(safe)

    def _active_pond(self):
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

    def copy_pond_summary(self):
        pond = self._active_pond()
        if pond is None:
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.no_pond", "没有可用的莲池。"),
            )
            return
        summary = {
            "name": getattr(pond, "name", ""),
            "time": getattr(pond, "time", 0),
            "organisms": list(getattr(pond, "organisms", {}).keys()),
            "floating_components": len(getattr(pond, "floating_components", []) or []),
        }
        text = json.dumps(summary, ensure_ascii=False, indent=2)
        QApplication.clipboard().setText(text)

    def export_active_pond(self):
        pond = self._active_pond()
        if pond is None:
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.no_pond", "没有可用的莲池。"),
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self.kernel if self.kernel else None,
            self._t("editor_workflow.export_pond", "导出当前莲池"),
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        from builtin.systems.pond_serializer import PondSerializer

        ok = PondSerializer(save_format="json").save_pond(pond, path)
        if ok:
            QMessageBox.information(
                self.kernel if self.kernel else None,
                self._t("dialog.success.title", "成功"),
                self._t("editor_workflow.export_ok", "莲池已导出。"),
            )
        else:
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.export_fail", "导出失败，请查看日志。"),
            )

    def import_pond_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self.kernel if self.kernel else None,
            self._t("editor_workflow.import_pond_title", "导入莲池"),
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        from builtin.systems.pond_serializer import PondSerializer

        loaded = PondSerializer(save_format="json").load_pond(path)
        if loaded is None:
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.import_fail", "导入失败，请查看日志或检查 JSON。"),
            )
            return

        try:
            import uuid
            from core.Lotucosm.cosmos import get_cosmos

            cosmos = get_cosmos()
            m = QMessageBox(self.kernel if self.kernel else None)
            m.setIcon(QMessageBox.Icon.Question)
            m.setWindowTitle(self._t("editor_workflow.import_mode_title", "导入莲池"))
            m.setText(self._t("editor_workflow.import_mode_prompt", "请选择导入方式。"))
            replace_btn = m.addButton(
                self._t("editor_workflow.import_replace_active", "替换当前激活莲池"),
                QMessageBox.ButtonRole.AcceptRole,
            )
            new_btn = m.addButton(
                self._t("editor_workflow.import_as_new_world", "新建世界并激活"),
                QMessageBox.ButtonRole.ActionRole,
            )
            cancel_btn = m.addButton(QMessageBox.StandardButton.Cancel)
            m.exec()
            clicked = m.clickedButton()
            if clicked is None or clicked == cancel_btn:
                return

            active = cosmos.get_active_world()
            wid_active = cosmos.active_world_id

            if clicked == replace_btn:
                if wid_active and active is not None:
                    if hasattr(active, "_apply_loaded_pond_state"):
                        active._apply_loaded_pond_state(loaded)
                    cosmos.worlds[wid_active] = active
                    cosmos.set_active_world(wid_active)
                else:
                    wid = wid_active or "default"
                    if wid in cosmos.worlds and cosmos.worlds[wid] is not None:
                        target = cosmos.worlds[wid]
                        if hasattr(target, "_apply_loaded_pond_state"):
                            target._apply_loaded_pond_state(loaded)
                        else:
                            cosmos.worlds[wid] = loaded
                    else:
                        cosmos.worlds[wid] = loaded
                    cosmos.set_active_world(wid)
            elif clicked == new_btn:
                wid = f"imported_{uuid.uuid4().hex[:8]}"
                cosmos.worlds[wid] = loaded
                cosmos.set_active_world(wid)

            QMessageBox.information(
                self.kernel if self.kernel else None,
                self._t("dialog.success.title", "成功"),
                self._t("editor_workflow.import_ok", "莲池已导入。"),
            )
        except Exception as exc:
            logger.exception("导入莲池失败")
            QMessageBox.warning(
                self.kernel if self.kernel else None,
                self._t("dialog.warning.title", "警告"),
                self._t("editor_workflow.import_fail", "导入失败，请查看日志或检查 JSON。"),
            )
