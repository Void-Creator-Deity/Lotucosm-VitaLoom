"""Qt-free Hot Reload declarations with a concrete legacy dialog bridge."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from core.VitaLoom.commands.registry import CommandSpec, command_error, command_ok
from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider, IRuntimePlugin
from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host

logger = get_logger("HotReloadPlugin")


class HotReloadPlugin(IRuntimePlugin, ICommandProvider):
    """Own the canonical Hot Reload commands and portable Editor menu facts."""

    def __init__(self) -> None:
        self.context: object | None = None
        self.kernel: object | None = None

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "HotReloadPlugin",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "Command-backed development plugin hot reload",
            "dependencies": [],
            "provides": ["command", "editor_contribution"],
            "editor_contributions": [
                {
                    "id": "hot_reload.choose",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "develop",
                            "label_key": "menu.develop",
                            "default_label": "开发",
                        }
                    ],
                    "label_key": "hot_reload.menu.one",
                    "default_label": "热重载插件…",
                    "command_id": "plugin.hot_reload.choose",
                    "command_payload": {},
                    "shortcut": "F5",
                    "order": 10,
                },
                {
                    "id": "hot_reload.user_mod",
                    "kind": "menu_command",
                    "menu_path": [
                        {
                            "id": "develop",
                            "label_key": "menu.develop",
                            "default_label": "开发",
                        }
                    ],
                    "label_key": "hot_reload.menu.user_mod",
                    "default_label": "热重载全部 user_mod",
                    "command_id": "plugin.hot_reload.user_mod",
                    "command_payload": {},
                    "shortcut": "Ctrl+Shift+F5",
                    "order": 20,
                },
            ],
        }

    def get_command_specs(self) -> list[CommandSpec]:
        common = {
            "input_schema": {
                "type": "object",
                "properties": {},
            },
            "mutates": True,
            "undoable": False,
            "requires_gui": True,
            "capability": "vitalloom.editor.plugin_host_control",
            "owner": "HotReloadPlugin",
        }
        return [
            CommandSpec(
                id="plugin.hot_reload.choose",
                title="Choose plugin to hot reload",
                description=(
                    "Open the current Editor Host selection bridge and reload one "
                    "Host-observed reloadable plugin."
                ),
                output_schema={"type": "object"},
                handler=self._choose_reload_command,
                **common,
            ),
            CommandSpec(
                id="plugin.hot_reload.user_mod",
                title="Hot reload all user_mod plugins",
                description=(
                    "Reload every Host-observed reloadable plugin whose copied "
                    "catalog scope is user_mod."
                ),
                output_schema={"type": "object"},
                handler=self._reload_user_mod_command,
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

    def _observe_plugins(self) -> dict[str, Any]:
        if self.context is None:
            return {"reloadable_plugin_ids": [], "catalog": []}
        host = resolve_plugin_host(self.context)
        try:
            snapshot = host.observe_plugins()
        except Exception:
            logger.warning("Plugin observation is unavailable; Hot Reload has no targets")
            return {"reloadable_plugin_ids": [], "catalog": []}
        if not isinstance(snapshot, Mapping):
            return {"reloadable_plugin_ids": [], "catalog": []}
        return dict(snapshot)

    @staticmethod
    def _reloadable_plugins_from(snapshot: Mapping[str, Any]) -> list[str]:
        raw_ids = snapshot.get("reloadable_plugin_ids", [])
        if not isinstance(raw_ids, Sequence) or isinstance(
            raw_ids, (str, bytes, bytearray)
        ):
            return []
        return sorted(
            {
                str(plugin_id).strip()
                for plugin_id in raw_ids
                if str(plugin_id).strip()
            }
        )

    def _reloadable_plugins(self) -> list[str]:
        return self._reloadable_plugins_from(self._observe_plugins())

    @classmethod
    def _user_mod_targets(cls, snapshot: Mapping[str, Any]) -> list[str]:
        raw_catalog = snapshot.get("catalog", [])
        user_ids: set[str] = set()
        if isinstance(raw_catalog, Sequence) and not isinstance(
            raw_catalog, (str, bytes, bytearray)
        ):
            for row in raw_catalog:
                if not isinstance(row, Mapping) or row.get("scope") != "user_mod":
                    continue
                plugin_id = str(row.get("plugin_id", "") or "").strip()
                if plugin_id:
                    user_ids.add(plugin_id)
        return [
            plugin_id
            for plugin_id in cls._reloadable_plugins_from(snapshot)
            if plugin_id in user_ids
        ]

    def _choose_reload_candidate(self, candidates: Sequence[str]) -> str | None:
        """Current Qt Host implementation bridge; no Qt objects cross metadata."""
        if self.kernel is None:
            return None
        from PyQt6.QtWidgets import QInputDialog

        choice, accepted = QInputDialog.getItem(
            self.kernel,
            self._t("hot_reload.dialog.title", "热重载插件"),
            self._t("hot_reload.dialog.prompt", "选择要重载的插件："),
            list(candidates),
            0,
            False,
        )
        if not accepted or not choice:
            return None
        return str(choice)

    def _reload_plugin_report(self, plugin_id: str) -> dict[str, Any]:
        logger.info(
            self._t("hot_reload.start", "正在热重载插件: {name}").format(
                name=plugin_id
            )
        )
        if self.context is None:
            report: dict[str, Any] = {
                "status": "failed",
                "code": "editor_context_unavailable",
                "plugin_id": plugin_id,
            }
        else:
            host = resolve_plugin_host(self.context)
            try:
                raw_report = host.reload_plugin(plugin_id)
            except Exception:
                raw_report = {
                    "status": "failed",
                    "code": "plugin_reload_unavailable",
                    "plugin_id": plugin_id,
                }
            report = (
                dict(raw_report)
                if isinstance(raw_report, Mapping)
                else {
                    "status": "failed",
                    "code": "invalid_reload_report",
                    "plugin_id": plugin_id,
                }
            )
        if report.get("status") == "settled":
            logger.info(
                self._t("hot_reload.ok", "热重载成功: {name}").format(
                    name=plugin_id
                )
            )
        else:
            logger.warning(
                self._t("hot_reload.fail", "热重载失败: {name}").format(
                    name=plugin_id
                )
            )
        return report

    def _reload_plugin(self, plugin_name: str) -> bool:
        """Compatibility helper retained for existing legacy callers/tests."""
        if self.kernel is None:
            return False
        return self._reload_plugin_report(str(plugin_name)).get("status") == "settled"

    def _choose_reload_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        if self.kernel is None:
            return command_error(
                "editor_host_unavailable",
                "Hot Reload requires an active Editor Host",
            )
        candidates = self._reloadable_plugins()
        if not candidates:
            logger.warning(
                self._t("hot_reload.none", "没有可热重载的插件")
            )
            return command_ok({"status": "no_candidates", "candidates": []})

        choice = self._choose_reload_candidate(candidates)
        if choice is None:
            return command_ok(
                {"status": "cancelled", "candidates": list(candidates)}
            )
        if choice not in candidates:
            return command_error(
                "plugin_reload_choice_invalid",
                "Selected plugin is not in the copied reloadable set",
                details={"plugin_id": choice, "candidates": list(candidates)},
            )

        report = self._reload_plugin_report(choice)
        if report.get("status") != "settled":
            return command_error(
                "plugin_reload_failed",
                f"Hot reload failed: {choice}",
                details={"plugin_id": choice, "report": report},
            )
        return command_ok(
            {"status": "settled", "plugin_id": choice, "report": report}
        )

    def _reload_user_mod_command(
        self,
        _payload: Mapping[str, Any],
        _command_context: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        if self.kernel is None:
            return command_error(
                "editor_host_unavailable",
                "Hot Reload requires an active Editor Host",
            )
        snapshot = self._observe_plugins()
        targets = self._user_mod_targets(snapshot)
        if not targets:
            logger.info(
                self._t("hot_reload.no_user_mod", "未发现 user_mod 插件")
            )
            return command_ok(
                {
                    "status": "no_targets",
                    "targets": [],
                    "settled": [],
                    "failed": [],
                }
            )

        settled: list[str] = []
        failed: list[str] = []
        reports: dict[str, dict[str, Any]] = {}
        for plugin_id in targets:
            report = self._reload_plugin_report(plugin_id)
            reports[plugin_id] = report
            if report.get("status") == "settled":
                settled.append(plugin_id)
            else:
                failed.append(plugin_id)

        logger.info(
            self._t(
                "hot_reload.batch_done",
                "user_mod 热重载完成: {ok}/{total}",
            ).format(ok=len(settled), total=len(targets))
        )
        summary = {
            "targets": targets,
            "settled": settled,
            "failed": failed,
        }
        if failed:
            return command_error(
                "plugin_reload_batch_partial",
                "One or more user_mod plugins failed to hot reload",
                details={**summary, "reports": reports},
            )
        return command_ok({"status": "settled", **summary})

    def reload_selected_plugin(self) -> Dict[str, Any]:
        """Compatibility entry point routed through the canonical command handler."""
        return self._choose_reload_command({}, {"source": "legacy_method"})

    def reload_user_mod_plugins(self) -> Dict[str, Any]:
        """Compatibility entry point routed through the canonical command handler."""
        return self._reload_user_mod_command({}, {"source": "legacy_method"})



