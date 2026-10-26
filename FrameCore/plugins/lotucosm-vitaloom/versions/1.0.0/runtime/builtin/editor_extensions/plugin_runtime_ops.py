# -*- coding: utf-8 -*-
"""Legacy editor operations over the recursive plugin Host capability.

Transient reload/unload and project synchronization cross the Qt-free plugin
Host Interface. Project-persistent enable/disable still goes through the
AI-native command registry so UI, CLI, and MCP share one project state seam.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Optional

from core.VitaLoom.core.logger import get_logger
from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host
from core.VitaLoom.project.project_world_capabilities import get_project_world_read_model

logger = get_logger("PluginRuntimeOps")


class PluginRuntimeOpsMixin:
    """Mixin used by plugin manager docks.

    Subclasses provide `_runtime_selected_plugin_id` and `_runtime_refresh`.
    """

    kernel = None
    context = None

    def _runtime_selected_plugin_id(self) -> Optional[str]:
        raise NotImplementedError

    def _runtime_refresh(self) -> None:
        raise NotImplementedError

    def _runtime_plugin_host(self):
        return resolve_plugin_host(self.context)

    def _runtime_plugin_observation(self) -> dict:
        """Return copied public facts, treating an observation outage as unknown."""
        host = self._runtime_plugin_host()
        try:
            snapshot = host.observe_plugins()
        except Exception:
            logger.warning("Plugin observation is unavailable; public display uses unknown facts")
            return {}
        if not isinstance(snapshot, Mapping):
            logger.warning("Plugin observation is unavailable; public display uses unknown facts")
            return {}
        return dict(snapshot)

    def _runtime_active_plugin_ids(
        self, snapshot: Mapping | None = None
    ) -> Optional[set[str]]:
        """Read active ids from valid public facts, or ``None`` when unknown."""
        public_snapshot = snapshot if isinstance(snapshot, Mapping) else self._runtime_plugin_observation()
        active_ids = public_snapshot.get("active_plugin_ids")
        if not isinstance(active_ids, Sequence) or isinstance(
            active_ids, (str, bytes, bytearray)
        ):
            logger.warning("Plugin observation active ids are malformed; public display uses unknown facts")
            return None
        return {str(plugin_id) for plugin_id in active_ids}

    def _runtime_plugin_row_from_observation(
        self, plugin_id: str, snapshot: Mapping | None = None
    ) -> dict:
        """Return one copied matching catalog row from public observation facts."""
        public_snapshot = snapshot if isinstance(snapshot, Mapping) else self._runtime_plugin_observation()
        catalog = public_snapshot.get("catalog")
        if not isinstance(catalog, Sequence) or isinstance(
            catalog, (str, bytes, bytearray)
        ):
            logger.warning("Plugin observation catalog is malformed; catalog lookup denied")
            return {}

        for row in catalog:
            if isinstance(row, Mapping) and row.get("plugin_id") == plugin_id:
                return dict(row)
        return {}

    def _runtime_plugin_row(self, plugin_id: str) -> dict:
        return self._runtime_plugin_row_from_observation(
            plugin_id, self._runtime_plugin_observation()
        )

    def _runtime_t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def reload_selected_plugin(self) -> None:
        if not self.kernel:
            return
        plugin_name = self._runtime_selected_plugin_id()
        if not plugin_name:
            return
        host = self._runtime_plugin_host()
        row = self._runtime_plugin_row(plugin_name)
        if not row:
            logger.warning(
                "Plugin is absent from the public runtime catalog; reload denied: %s",
                plugin_name,
            )
            return
        if row.get("protected"):
            logger.warning("Protected plugin cannot be reloaded: %s", plugin_name)
            return
        logger.info("Reloading plugin: %s", plugin_name)
        try:
            report = host.reload_plugin(plugin_name)
        except Exception:
            logger.warning("Plugin reload is unavailable; refresh skipped: %s", plugin_name)
            return
        status = report.get("status") if isinstance(report, dict) else "failed"
        if status != "settled":
            logger.warning("Plugin reload did not settle: %s status=%s", plugin_name, status)
        self._runtime_refresh()

    def unload_selected_plugin(self) -> None:
        if not self.kernel:
            return
        plugin_name = self._runtime_selected_plugin_id()
        if not plugin_name:
            return
        host = self._runtime_plugin_host()
        row = self._runtime_plugin_row(plugin_name)
        if not row:
            logger.warning(
                "Plugin is absent from the public runtime catalog; unload denied: %s",
                plugin_name,
            )
            return
        if row.get("protected"):
            logger.warning("Protected plugin cannot be unloaded: %s", plugin_name)
            return
        logger.info("Unloading plugin: %s", plugin_name)
        try:
            host.unload_plugin(plugin_name)
        except Exception:
            logger.warning("Plugin unload is unavailable; refresh skipped: %s", plugin_name)
            return
        self._runtime_refresh()

    def disable_plugin_in_project(self) -> None:
        if not self.kernel:
            return
        plugin_name = self._runtime_selected_plugin_id()
        if not plugin_name:
            return
        row = self._runtime_plugin_row(plugin_name)
        if not row:
            logger.warning(
                "Plugin is absent from the public runtime catalog; project disable denied: %s",
                plugin_name,
            )
            return
        scope = row.get("scope", "unknown")
        if scope == "core_mod":
            logger.info("Core plugin cannot be disabled at project scope: %s", plugin_name)
            return
        if row.get("protected"):
            logger.warning("Protected plugin cannot be disabled at project scope: %s", plugin_name)
            return
        if self._run_project_plugin_command("plugin.disable", plugin_name):
            logger.info("Disabled plugin in project: %s", plugin_name)
            self._sync_plugins_for_current_project()
            self._runtime_refresh()

    def enable_plugin_in_project(self) -> None:
        if not self.kernel:
            return
        plugin_name = self._runtime_selected_plugin_id()
        if not plugin_name:
            return
        if self._run_project_plugin_command("plugin.enable", plugin_name):
            logger.info("Enabled plugin in project: %s", plugin_name)
            self._sync_plugins_for_current_project()
            self._runtime_refresh()

    def _run_project_plugin_command(self, command_id: str, plugin_name: str) -> bool:
        from core.VitaLoom.commands.registry import get_command_registry

        project_path = get_project_world_read_model(
            self.context
        ).current_project_world_path()
        if not project_path:
            logger.warning("No project is open; cannot persist plugin state")
            return False
        result = get_command_registry().run(
            command_id,
            {"project_path": str(project_path), "plugin_id": str(plugin_name)},
        )
        if result.get("ok"):
            return True
        error = result.get("error") if isinstance(result.get("error"), dict) else {}
        logger.warning(
            "Project plugin command failed: %s %s: %s",
            command_id,
            plugin_name,
            error.get("message") or error.get("code") or "unknown",
        )
        return False

    def _sync_plugins_for_current_project(self) -> None:
        if not self.kernel:
            return
        cfg = get_project_world_read_model(
            self.context
        ).current_project_world_config()
        if not isinstance(cfg, dict):
            return
        repo_root = getattr(self.context, "repo_root", None)
        host = self._runtime_plugin_host()
        try:
            host.sync_plugins_for_project(cfg, repo_root=repo_root)
        except Exception:
            logger.warning("Project plugin runtime sync is unavailable; refresh uses public facts")

    def _on_runtime_plugin_loaded(self, plugin_name: str) -> None:
        logger.info("Plugin loaded: %s", plugin_name)
        self._runtime_refresh()

    def _on_runtime_plugin_unloaded(self, plugin_name: str) -> None:
        logger.info("Plugin unloaded: %s", plugin_name)
        self._runtime_refresh()

