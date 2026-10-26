# -*- coding: utf-8 -*-
"""Qt-free execution Host for plugins nested under the VitaLoom engine plugin.

This Module is owned by the versioned runtime of the sole L1
``lotucosm-vitaloom`` FrameCore plugin.  It executes the lifecycle of L2
capability packages, L3 engine extensions, and L4 Project World addons without
knowing about PyQt, EditorKernel, LayoutManager, or legacy editor Interfaces.
Concrete Hosts attach side effects through :class:`RuntimePluginHostAdapter`.
"""
from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import inspect
import logging
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Protocol

from core.VitaLoom.commands.registry import CommandSpec, get_command_registry
from core.VitaLoom.core.editor_contribution_contract import (
    parse_editor_contributions,
)
from core.VitaLoom.core.plugin_activation_contract import (
    PluginActivationContractError,
    parse_plugin_activation_metadata,
)
from core.VitaLoom.core.runtime_plugin_contract import (
    ICommandProvider,
    IRuntimePlugin,
    IRuntimePluginTeardown,
)
from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id, normalize_dependency_ids
from core.VitaLoom.project.plugin_host_lifecycle import (
    PluginHostCatalogEntry,
    build_plugin_lifecycle_plan,
    normalize_plugin_provides,
)


logger = logging.getLogger(__name__)


class RuntimePluginHostAdapter(Protocol):
    """Narrow seam for concrete Host contributions around runtime callbacks."""

    def after_plugin_load(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Publish concrete Host contributions after ``on_load`` succeeds."""

    def before_plugin_unload(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Remove contributions after plugin teardown preparation, before ``on_unload``."""

    def after_plugin_deactivated(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Observe removal from the active registry."""


class NullRuntimePluginHostAdapter:
    """Headless Adapter used when no concrete Host side effects are required."""

    def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
        return None

    def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
        return None

    def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
        return None


@dataclass(frozen=True)
class _PluginDeactivationResult:
    ok: bool
    deactivated: bool = False
    failed_action: Dict[str, str] | None = None


@dataclass
class _PluginDeactivationProgress:
    """Private completed-stage facts for retrying one active plugin deactivation."""

    host_teardown_prepared: bool = False
    adapter_cleanup_completed: bool = False
    plugin_unload_completed: bool = False
    command_release_completed: bool = False


class RuntimePluginHost:
    """Own discovery, registry facts, dependency order, and runtime callbacks.

    The Interface is deliberately independent from an editor shell.  A legacy
    or future UI Host supplies an activation-context resolver and one Adapter;
    headless tools can use the defaults or pass their own runtime projection.
    """

    SCOPE_CORE = "core_mod"
    SCOPE_OFFICIAL = "official_mod"
    SCOPE_USER = "user_mod"
    SCOPE_EMBEDDED = "embedded_mod"
    SCOPE_UNKNOWN = "unknown"

    _SCOPE_PRIORITY = {
        SCOPE_UNKNOWN: 0,
        SCOPE_EMBEDDED: 1,
        SCOPE_USER: 2,
        SCOPE_OFFICIAL: 3,
        SCOPE_CORE: 4,
    }

    def __init__(
        self,
        *,
        activation_context_resolver: Callable[[Mapping[str, Any]], object] | None = None,
        adapter: RuntimePluginHostAdapter | None = None,
    ) -> None:
        self._activation_context_resolver = activation_context_resolver or (lambda info: None)
        self.adapter: RuntimePluginHostAdapter = adapter or NullRuntimePluginHostAdapter()

        self.plugin_registry: Dict[str, IRuntimePlugin] = {}
        self.loaded_plugins: Dict[str, IRuntimePlugin] = {}
        self._command_publications: Dict[
            str, tuple[tuple[str, CommandSpec], ...]
        ] = {}
        # A failed deactivation may already have completed Adapter cleanup.
        # Retain only Host-local stage facts so the next request resumes rather
        # than replaying already-applied teardown side effects.
        self._deactivation_progress: Dict[str, _PluginDeactivationProgress] = {}
        # Registration-time copied declarative facts. Observation must never
        # call live plugin objects or expose their mutable metadata.
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self.plugin_dependencies: Dict[str, List[str]] = {}
        self.plugin_order: List[str] = []
        self.failed_plugins: Dict[str, str] = {}
        self.discovery_errors: Dict[str, str] = {}
        self.plugin_scopes: Dict[str, str] = {}
        self.plugin_files: Dict[str, str] = {}
        self.protected_plugins: set[str] = set()
        self.scope_overrides: Dict[str, str] = {}
        self.last_lifecycle_report: Dict[str, Any] = {
            "status": "not_run",
            "completed": {"deactivated": [], "activated": []},
            "diagnostics": [],
        }

    def set_scope_overrides(self, overrides: Mapping[str, str]) -> None:
        """Replace scope overrides without invalidating compatibility aliases."""

        normalized = {
            str(plugin_id): (
                scope if scope in self._SCOPE_PRIORITY else self.SCOPE_UNKNOWN
            )
            for plugin_id, scope in overrides.items()
        }
        self.scope_overrides.clear()
        self.scope_overrides.update(normalized)

    def register_plugin(
        self,
        plugin: IRuntimePlugin,
        *,
        scope: str = SCOPE_UNKNOWN,
        source: str | Path = "",
        protected: bool | None = None,
    ) -> str:
        """Validate and register one imported plugin instance.

        Higher-priority scopes replace lower-priority duplicates.  A lower
        priority duplicate leaves the existing registry entry unchanged.
        """

        info = plugin.get_plugin_info()
        raw_name = info.get("name")
        if not raw_name:
            raise ValueError(f"plugin {type(plugin).__name__} is missing name")
        plugin_id = canonical_plugin_id(str(raw_name), type(plugin).__name__)
        source_text = str(source or "")
        activation = parse_plugin_activation_metadata(
            info,
            plugin_id=plugin_id,
            source=source_text,
        )
        dependencies = normalize_dependency_ids(info.get("dependencies", []))
        normalized_scope = scope if scope in self._SCOPE_PRIORITY else self.SCOPE_UNKNOWN
        effective_scope = self.scope_overrides.get(plugin_id, normalized_scope)
        existing_scope = self.plugin_scopes.get(plugin_id, self.SCOPE_UNKNOWN)
        if plugin_id in self.plugin_registry and (
            self._SCOPE_PRIORITY.get(effective_scope, 0)
            < self._SCOPE_PRIORITY.get(existing_scope, 0)
        ):
            logger.info(
                "ignored lower-priority plugin: id=%s scope=%s existing_scope=%s",
                plugin_id,
                effective_scope,
                existing_scope,
            )
            return plugin_id

        self.plugin_registry[plugin_id] = plugin
        self._cache_plugin_metadata(plugin_id, info, activation)
        self.plugin_dependencies[plugin_id] = dependencies
        self.plugin_scopes[plugin_id] = effective_scope
        self.plugin_files[plugin_id] = source_text
        is_protected = bool(info.get("protected", False)) if protected is None else bool(protected)
        if is_protected or effective_scope == self.SCOPE_CORE:
            self.protected_plugins.add(plugin_id)
        else:
            self.protected_plugins.discard(plugin_id)
        return plugin_id

    def _cache_plugin_metadata(self, plugin_id: str, info: Mapping[str, Any], activation) -> None:
        """Store only copied declarative facts needed by downstream observers."""

        contributions = parse_editor_contributions(
            plugin_id,
            info.get("editor_contributions", []),
        )
        self.plugin_metadata[str(plugin_id)] = {
            "name": str(plugin_id),
            "declared_name": str(info.get("name", plugin_id) or plugin_id),
            "version": str(info.get("version", "0.0.0") or "0.0.0"),
            "description": str(info.get("description", "") or ""),
            "provides": normalize_plugin_provides(info.get("provides", [])),
            "activation_context": str(activation.kind or "legacy_ui"),
            "activation_context_explicit": bool(activation.explicit),
            "editor_contributions": [item.to_dict() for item in contributions],
        }

    def _plugin_metadata_snapshot(
        self,
        plugin_id: str,
        *,
        fallback: Callable[[], Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Return one call-local metadata copy without exposing Host cache state."""

        if plugin_id in self.plugin_metadata:
            return deepcopy(self.plugin_metadata[plugin_id])
        return deepcopy(dict(fallback()))

    def cache_plugin_metadata(
        self, plugin_id: str, info: Mapping[str, Any], *, source: str | Path = ""
    ) -> None:
        """Cache validated plugin facts for registry paths that replace entries directly."""

        canonical_id = canonical_plugin_id(str(plugin_id))
        activation = parse_plugin_activation_metadata(
            info, plugin_id=canonical_id, source=str(source or "")
        )
        self._cache_plugin_metadata(canonical_id, info, activation)

    def cache_catalog_entry_metadata(self, entry: PluginHostCatalogEntry) -> None:
        """Cache an already-validated reload candidate without re-reading its object."""

        normalized = entry.normalized()
        self.plugin_metadata[normalized.plugin_id] = {
            "name": normalized.plugin_id,
            "declared_name": normalized.declared_name or normalized.plugin_id,
            "version": normalized.version,
            "description": normalized.description,
            "provides": normalize_plugin_provides(normalized.provides),
            "activation_context": normalized.activation_context,
            "activation_context_explicit": normalized.activation_context_explicit,
            "editor_contributions": deepcopy(list(normalized.editor_contributions)),
        }

    def scan_directory(self, path: Path, scope: str = SCOPE_UNKNOWN) -> None:
        """Discover every ``*_plugin.py`` file below one source directory."""

        for plugin_file in sorted(path.rglob("*_plugin.py"), key=lambda item: str(item)):
            try:
                self.discover_plugin(plugin_file, scope)
            except Exception as exc:
                self.discovery_errors[str(plugin_file)] = str(exc)
                logger.exception("plugin discovery failed: %s", plugin_file)

    def discover_plugin(self, file_path: Path, scope: str = SCOPE_UNKNOWN) -> list[str]:
        """Import a source file and register all concrete runtime plugin classes."""

        module = self._import_plugin_module(
            file_path,
            prefix="plugin",
            invalidate_bytecode=False,
        )
        discovered: list[str] = []
        for class_name, plugin_class in self._plugin_classes(module):
            try:
                plugin = plugin_class()
                plugin_id = self.register_plugin(
                    plugin,
                    scope=scope,
                    source=file_path,
                )
                discovered.append(plugin_id)
            except PluginActivationContractError as exc:
                self.discovery_errors[str(file_path)] = exc.code
                logger.error(
                    "plugin activation contract rejected: %s (%s)",
                    class_name,
                    exc.code,
                )
            except Exception as exc:
                self.discovery_errors[str(file_path)] = str(exc)
                logger.exception("plugin instantiation failed: %s", class_name)
        return discovered

    def resolve_dependencies(self) -> List[str]:
        """Update the compatibility order in place using deterministic topology."""

        in_degree = {plugin_id: 0 for plugin_id in self.plugin_registry}
        dependents = {plugin_id: [] for plugin_id in self.plugin_registry}
        for plugin_id in sorted(self.plugin_dependencies):
            for dependency in self.plugin_dependencies[plugin_id]:
                if dependency in self.plugin_registry:
                    dependents[dependency].append(plugin_id)
                    in_degree[plugin_id] += 1
                else:
                    logger.error(
                        "plugin dependency missing: plugin=%s dependency=%s",
                        plugin_id,
                        dependency,
                    )
        ready = sorted(
            plugin_id for plugin_id, degree in in_degree.items() if degree == 0
        )
        ordered: list[str] = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for dependent in sorted(dependents[current]):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready.append(dependent)
                    ready.sort()
        unresolved = sorted(set(self.plugin_registry).difference(ordered))
        if unresolved:
            logger.warning("plugin dependency cycle detected: %s", unresolved)
            ordered.extend(unresolved)
        self.plugin_order[:] = ordered
        return self.plugin_order

    def catalog_entries(self) -> List[PluginHostCatalogEntry]:
        """Project imported registry state into the lifecycle authority facts."""

        entries: List[PluginHostCatalogEntry] = []
        for plugin_id in sorted(self.plugin_registry):
            metadata = self.plugin_metadata.get(plugin_id, {})
            entries.append(
                PluginHostCatalogEntry(
                    plugin_id=plugin_id,
                    scope=self.plugin_scopes.get(plugin_id, self.SCOPE_UNKNOWN),
                    source=self.plugin_files.get(plugin_id, ""),
                    version=str(metadata.get("version", "0.0.0") or "0.0.0"),
                    description=str(metadata.get("description", "") or ""),
                    provides=normalize_plugin_provides(metadata.get("provides", [])),
                    dependencies=tuple(self.plugin_dependencies.get(plugin_id, [])),
                    protected=plugin_id in self.protected_plugins,
                    activation_context=str(
                        metadata.get("activation_context", "legacy_ui") or "legacy_ui"
                    ),
                    activation_context_explicit=bool(
                        metadata.get("activation_context_explicit", False)
                    ),
                    declared_name=str(
                        metadata.get("declared_name", plugin_id) or plugin_id
                    ),
                    editor_contributions=tuple(
                        deepcopy(metadata.get("editor_contributions", []))
                    ),
                )
            )
        return entries

    def _command_batch(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> tuple[tuple[str, CommandSpec], ...]:
        """Validate and canonicalize one provider batch before registry mutation."""

        provides = normalize_plugin_provides(plugin_info.get("provides", []))
        if "command" not in provides or not isinstance(plugin, ICommandProvider):
            return ()

        raw_specs = plugin.get_command_specs()
        try:
            specs = tuple(raw_specs)
        except TypeError as exc:
            raise TypeError(
                f"command provider {plugin_id} must return an iterable of CommandSpec"
            ) from exc

        records: list[tuple[str, CommandSpec]] = []
        seen_ids: set[str] = set()
        for index, spec in enumerate(specs):
            if not isinstance(spec, CommandSpec):
                raise TypeError(
                    f"command provider {plugin_id} returned non-CommandSpec at index {index}"
                )
            command_id = str(spec.id).strip()
            if not command_id:
                raise ValueError(f"command provider {plugin_id} returned an empty command id")
            if command_id in seen_ids:
                raise ValueError(
                    f"command provider {plugin_id} returned duplicate command: {command_id}"
                )
            seen_ids.add(command_id)
            owned_spec = (
                spec if spec.owner == plugin_id else replace(spec, owner=plugin_id)
            )
            records.append((command_id, owned_spec))

        registry = get_command_registry()
        missing = object()
        for command_id, _spec in records:
            if registry.get(command_id, missing) is not missing:
                raise ValueError(f"command already registered: {command_id}")
        return tuple(records)

    @staticmethod
    def _release_command_records(
        records: tuple[tuple[str, CommandSpec], ...],
    ) -> None:
        """Remove only specs still identical to one Host-owned publication."""

        registry = get_command_registry()
        missing = object()
        failures: list[tuple[str, BaseException]] = []
        for command_id, spec in records:
            if registry.get(command_id, missing) is not spec:
                continue
            try:
                registry.unregister(command_id)
            except BaseException as exc:
                failures.append((command_id, exc))
        if failures:
            details = ", ".join(
                f"{command_id}: {type(exc).__name__}: {exc}"
                for command_id, exc in failures
            )
            raise RuntimeError(f"command unpublication failed: {details}") from failures[0][1]

    def _publish_plugin_commands(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
    ) -> None:
        """Publish one complete provider batch and retain exact release facts."""

        if plugin_id in self._command_publications:
            raise RuntimeError(f"plugin commands are already active: {plugin_id}")
        records = self._command_batch(plugin, plugin_id, plugin_info)
        if not records:
            return

        registry = get_command_registry()
        attempted: list[tuple[str, CommandSpec]] = []
        try:
            for command_id, spec in records:
                attempted.append((command_id, spec))
                registry.register(spec)
        except BaseException as registration_error:
            attempted_records = tuple(attempted)
            try:
                self._release_command_records(attempted_records)
            except BaseException as rollback_error:
                self._command_publications[plugin_id] = attempted_records
                raise RuntimeError(
                    f"command registration rollback failed for {plugin_id}: {rollback_error}"
                ) from registration_error
            raise
        self._command_publications[plugin_id] = records

    def _release_plugin_commands(self, plugin_id: str) -> None:
        """Release the exact command batch owned by one successful activation."""

        records = self._command_publications.get(plugin_id)
        if records is None:
            return
        self._release_command_records(records)
        self._command_publications.pop(plugin_id, None)

    def _rollback_failed_activation(
        self,
        plugin: IRuntimePlugin,
        plugin_id: str,
        plugin_info: Mapping[str, Any],
        *,
        cleanup_adapter: bool,
    ) -> None:
        """Undo completed activation stages in strict reverse lifecycle order."""

        failures: list[tuple[str, BaseException]] = []
        if cleanup_adapter:
            try:
                self.adapter.before_plugin_unload(
                    plugin, plugin_id, deepcopy(dict(plugin_info))
                )
            except BaseException as exc:
                failures.append(("adapter_cleanup", exc))
        try:
            plugin.on_unload()
        except BaseException as exc:
            failures.append(("plugin_on_unload", exc))
        try:
            self._release_plugin_commands(plugin_id)
        except BaseException as exc:
            failures.append(("command_owner_release", exc))

        if failures:
            details = ", ".join(
                f"{stage}: {type(exc).__name__}: {exc}" for stage, exc in failures
            )
            raise RuntimeError(
                f"activation rollback failed for {plugin_id}: {details}"
            ) from failures[0][1]

    def load_plugin(
        self,
        plugin: IRuntimePlugin,
        *,
        plugin_id: str | None = None,
    ) -> str:
        """Execute runtime load, publish commands, then project concrete Host UI.

        Lifecycle planners pass their already-resolved canonical identity so every
        activation stage observes one Host-owned metadata snapshot.  The legacy
        direct-call path remains available and obtains that identity from the
        live plugin object before using the same activation sequence.
        """

        if plugin_id is None:
            live_info = plugin.get_plugin_info()
            raw_name = live_info.get("name")
            if not raw_name:
                raise ValueError(f"plugin {type(plugin).__name__} is missing name")
            plugin_id = canonical_plugin_id(str(raw_name), type(plugin).__name__)
            info = self._plugin_metadata_snapshot(
                plugin_id,
                fallback=lambda: live_info,
            )
        else:
            plugin_id = canonical_plugin_id(str(plugin_id), type(plugin).__name__)
            info = self._plugin_metadata_snapshot(
                plugin_id,
                fallback=plugin.get_plugin_info,
            )

        parse_plugin_activation_metadata(
            info,
            plugin_id=plugin_id,
            source=self.plugin_files.get(plugin_id, ""),
        )
        plugin.on_load(self._activation_context_resolver(info))
        try:
            self._publish_plugin_commands(plugin, plugin_id, info)
        except BaseException as activation_error:
            try:
                self._rollback_failed_activation(
                    plugin,
                    plugin_id,
                    info,
                    cleanup_adapter=False,
                )
            except BaseException as rollback_error:
                raise RuntimeError(
                    f"command activation failed and rollback was incomplete for "
                    f"{plugin_id}: {rollback_error}"
                ) from activation_error
            raise
        try:
            self.adapter.after_plugin_load(plugin, plugin_id, deepcopy(info))
        except BaseException as activation_error:
            try:
                self._rollback_failed_activation(
                    plugin,
                    plugin_id,
                    info,
                    cleanup_adapter=True,
                )
            except BaseException as rollback_error:
                raise RuntimeError(
                    f"adapter activation failed and rollback was incomplete for "
                    f"{plugin_id}: {rollback_error}"
                ) from activation_error
            raise
        return plugin_id

    def _deactivate_plugin(
        self,
        plugin_id: str,
        *,
        allow_protected: bool,
        shutdown_mode: bool,
    ) -> _PluginDeactivationResult:
        """Execute one staged deactivation and retain exact failure facts."""

        if plugin_id not in self.loaded_plugins:
            return _PluginDeactivationResult(
                False,
                failed_action={
                    "action": "deactivate",
                    "plugin_id": plugin_id,
                    "stage": "registry_lookup",
                    "error": "plugin_not_active",
                },
            )
        if plugin_id in self.protected_plugins and not allow_protected:
            return _PluginDeactivationResult(
                False,
                failed_action={
                    "action": "deactivate",
                    "plugin_id": plugin_id,
                    "stage": "protected_plugin",
                    "error": "protected_plugin",
                },
            )

        plugin = self.loaded_plugins[plugin_id]

        def failed(stage: str, exc: Exception, *, deactivated: bool = False):
            logger.exception(
                "plugin deactivation failed: plugin=%s stage=%s",
                plugin_id,
                stage,
                exc_info=exc,
            )
            return _PluginDeactivationResult(
                False,
                deactivated=deactivated,
                failed_action={
                    "action": "deactivate",
                    "plugin_id": plugin_id,
                    "stage": stage,
                    "error": type(exc).__name__,
                },
            )

        try:
            info = self._plugin_metadata_snapshot(
                plugin_id,
                fallback=plugin.get_plugin_info,
            )
        except Exception as exc:
            return failed("plugin_info", exc)

        progress = self._deactivation_progress.setdefault(
            plugin_id, _PluginDeactivationProgress()
        )
        if not progress.host_teardown_prepared:
            if isinstance(plugin, IRuntimePluginTeardown):
                try:
                    plugin.prepare_host_teardown()
                except Exception as exc:
                    return failed("plugin_prepare_host_teardown", exc)
            progress.host_teardown_prepared = True

        if not progress.adapter_cleanup_completed:
            cleanup = self.adapter.before_plugin_unload
            if shutdown_mode:
                strict_cleanup = getattr(self.adapter, "before_plugin_shutdown", None)
                if callable(strict_cleanup):
                    cleanup = strict_cleanup
            try:
                cleanup(plugin, plugin_id, deepcopy(info))
            except Exception as exc:
                return failed("adapter_cleanup", exc)
            progress.adapter_cleanup_completed = True

        if not progress.plugin_unload_completed:
            try:
                plugin.on_unload()
            except Exception as exc:
                return failed("plugin_on_unload", exc)
            progress.plugin_unload_completed = True

        if not progress.command_release_completed:
            try:
                self._release_plugin_commands(plugin_id)
            except Exception as exc:
                return failed("command_owner_release", exc)
            progress.command_release_completed = True

        try:
            del self.loaded_plugins[plugin_id]
        except Exception as exc:
            return failed("registry_removal", exc)
        self._deactivation_progress.pop(plugin_id, None)

        try:
            self.adapter.after_plugin_deactivated(plugin, plugin_id, deepcopy(info))
        except Exception as exc:
            return failed("unload_signal", exc, deactivated=True)
        return _PluginDeactivationResult(True, deactivated=True)

    def unload_plugin(self, plugin_id: str) -> bool:
        """Deactivate one non-protected plugin through the compatibility Interface."""

        if plugin_id not in self.loaded_plugins:
            logger.warning("plugin is not active: %s", plugin_id)
            return False
        if plugin_id in self.protected_plugins:
            logger.warning("protected plugin cannot be unloaded: %s", plugin_id)
            return False
        return self._deactivate_plugin(
            plugin_id, allow_protected=False, shutdown_mode=False
        ).ok

    def shutdown_plugins(self) -> Dict[str, Any]:
        """Fail closed while deactivating every active nested plugin in plan order."""

        plan = build_plugin_lifecycle_plan(
            self.catalog_entries(),
            active_plugin_ids=set(self.loaded_plugins),
            requested_plugin_ids=set(),
            retain_protected=False,
        )
        report = plan.to_dict()
        report["source"] = "shutdown"
        report["completed"] = {"deactivated": [], "activated": []}
        report["failed_action"] = None
        report["remaining_active_plugin_ids"] = sorted(self.loaded_plugins)
        report["transition_attempted"] = bool(plan.deactivate_plugin_ids)

        if not plan.ok:
            report["status"] = "blocked"
            self.last_lifecycle_report = report
            return report
        if not plan.deactivate_plugin_ids:
            report["status"] = "noop"
            self.last_lifecycle_report = report
            return report

        for plugin_id in plan.deactivate_plugin_ids:
            result = self._deactivate_plugin(
                plugin_id, allow_protected=True, shutdown_mode=True
            )
            if result.deactivated:
                report["completed"]["deactivated"].append(plugin_id)
            if not result.ok:
                report["status"] = "failed"
                report["failed_action"] = result.failed_action
                report["remaining_active_plugin_ids"] = sorted(self.loaded_plugins)
                self.last_lifecycle_report = report
                return report

        report["status"] = "settled"
        report["remaining_active_plugin_ids"] = sorted(self.loaded_plugins)
        self.last_lifecycle_report = report
        return report

    def execute_lifecycle_target(
        self,
        target: set[str],
        *,
        source: str,
        allow_deactivate: bool,
    ) -> Dict[str, Any]:
        """Execute the E5 authority plan and report exact completed actions."""

        active_for_plan = set(self.loaded_plugins)
        if not allow_deactivate:
            active_for_plan.intersection_update(target)
        plan = build_plugin_lifecycle_plan(
            self.catalog_entries(),
            active_plugin_ids=active_for_plan,
            requested_plugin_ids=target,
        )
        report = plan.to_dict()
        report["source"] = source
        report["completed"] = {"deactivated": [], "activated": []}
        report["failed_action"] = None
        if not plan.ok:
            report["status"] = "blocked"
            self.last_lifecycle_report = report
            return report

        if allow_deactivate:
            for plugin_id in plan.deactivate_plugin_ids:
                if not self.unload_plugin(plugin_id):
                    report["status"] = "failed"
                    report["failed_action"] = {
                        "action": "deactivate",
                        "plugin_id": plugin_id,
                    }
                    self.last_lifecycle_report = report
                    return report
                report["completed"]["deactivated"].append(plugin_id)

        failed_activation: set[str] = set()
        skipped_activation: set[str] = set()
        report["skipped"] = {"activation": []}
        for plugin_id in plan.activate_plugin_ids:
            dependencies = set(self.plugin_dependencies.get(plugin_id, []))
            blocked_by = sorted(dependencies & (failed_activation | skipped_activation))
            if blocked_by:
                skipped_activation.add(plugin_id)
                report["skipped"]["activation"].append(
                    {"plugin_id": plugin_id, "blocked_by": blocked_by}
                )
                continue
            plugin = self.plugin_registry.get(plugin_id)
            if plugin is None:
                failed_activation.add(plugin_id)
                if report["failed_action"] is None:
                    report["failed_action"] = {
                        "action": "activate",
                        "plugin_id": plugin_id,
                        "error": "plugin_registry_missing",
                    }
                continue
            try:
                self.load_plugin(plugin, plugin_id=plugin_id)
                self.loaded_plugins[plugin_id] = plugin
                self.failed_plugins.pop(plugin_id, None)
                report["completed"]["activated"].append(plugin_id)
            except Exception as exc:
                logger.exception("plugin activation failed: %s", plugin_id)
                self.loaded_plugins.pop(plugin_id, None)
                self.failed_plugins[plugin_id] = str(exc)
                failed_activation.add(plugin_id)
                if report["failed_action"] is None:
                    report["failed_action"] = {
                        "action": "activate",
                        "plugin_id": plugin_id,
                        "error": type(exc).__name__,
                    }

        report["status"] = "failed" if failed_activation else "settled"
        self.last_lifecycle_report = report
        return report

    def instantiate_plugin_from_file(self, file_path: Path) -> tuple[str, IRuntimePlugin]:
        """Import one hot-reload candidate and return its canonical identity."""

        module = self._import_plugin_module(
            file_path,
            prefix="vitaloom_plugin",
            invalidate_bytecode=True,
        )
        for class_name, plugin_class in self._plugin_classes(module):
            plugin = plugin_class()
            info = plugin.get_plugin_info()
            raw_name = info.get("name")
            if not raw_name:
                raise ValueError(f"plugin class {class_name} is missing name")
            plugin_id = canonical_plugin_id(str(raw_name), class_name)
            parse_plugin_activation_metadata(
                info,
                plugin_id=plugin_id,
                source=str(file_path),
            )
            return plugin_id, plugin
        raise RuntimeError(f"no IRuntimePlugin implementation found in {file_path}")

    def invalidate_plugin_bytecode(self, file_path: Path) -> None:
        """Remove source-adjacent bytecode so hot reload observes current source."""

        cache_dir = file_path.parent / "__pycache__"
        if cache_dir.is_dir():
            for pyc in cache_dir.glob(f"{file_path.stem}*.pyc"):
                try:
                    pyc.unlink()
                except OSError:
                    pass
        importlib.invalidate_caches()

    def _import_plugin_module(
        self,
        file_path: Path,
        *,
        prefix: str,
        invalidate_bytecode: bool,
    ):
        if invalidate_bytecode:
            self.invalidate_plugin_bytecode(file_path)
        module_name = f"{prefix}_{file_path.stem}_{time.time_ns()}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise RuntimeError(f"cannot load plugin module: {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _plugin_classes(module) -> list[tuple[str, type[IRuntimePlugin]]]:
        return [
            (name, candidate)
            for name, candidate in inspect.getmembers(module)
            if inspect.isclass(candidate)
            and issubclass(candidate, IRuntimePlugin)
            and candidate is not IRuntimePlugin
            and not inspect.isabstract(candidate)
        ]


__all__ = [
    "NullRuntimePluginHostAdapter",
    "RuntimePluginHost",
    "RuntimePluginHostAdapter",
]



