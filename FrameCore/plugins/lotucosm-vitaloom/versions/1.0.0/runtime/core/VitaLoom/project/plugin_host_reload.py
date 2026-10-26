# -*- coding: utf-8 -*-
"""Qt-free planning authority for manual L3 engine-extension hot reload.

This Module decides whether a candidate may replace one engine extension and
which lifecycle order the concrete Host Adapter must execute.  It never imports
plugin source, invokes callbacks, or depends on a GUI Host.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id
from core.VitaLoom.project.plugin_host_lifecycle import (
    PluginHostCatalogEntry,
    PluginHostDiagnostic,
)

_ALLOWED_RELOAD_SCOPES = frozenset({"official_mod", "user_mod"})


@dataclass(frozen=True)
class PluginReloadPlan:
    """One deterministic, fail-closed hot-reload plan."""

    ok: bool
    target_plugin_id: str
    target_was_active: bool
    candidate: PluginHostCatalogEntry
    catalog: tuple[PluginHostCatalogEntry, ...]
    affected_plugin_ids: tuple[str, ...]
    deactivate_plugin_ids: tuple[str, ...]
    activate_plugin_ids: tuple[str, ...]
    diagnostics: tuple[PluginHostDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "ready" if self.ok else "blocked",
            "target_plugin_id": self.target_plugin_id,
            "target_was_active": self.target_was_active,
            "candidate": self.candidate.to_dict(),
            "catalog": [entry.to_dict() for entry in self.catalog],
            "affected_plugin_ids": list(self.affected_plugin_ids),
            "deactivate_plugin_ids": list(self.deactivate_plugin_ids),
            "activate_plugin_ids": list(self.activate_plugin_ids),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _diagnostic(
    code: str,
    message: str,
    *,
    plugin_id: str = "",
    source: str = "",
    level: str = "error",
) -> PluginHostDiagnostic:
    return PluginHostDiagnostic(
        code=code,
        message=message,
        level=level,
        plugin_id=plugin_id,
        source=source,
    )


def _normalise_catalog(
    entries: Sequence[PluginHostCatalogEntry],
) -> tuple[dict[str, PluginHostCatalogEntry], list[PluginHostDiagnostic]]:
    catalog: dict[str, PluginHostCatalogEntry] = {}
    diagnostics: list[PluginHostDiagnostic] = []
    for entry in sorted(
        (item.normalized() for item in entries),
        key=lambda item: (item.plugin_id, item.scope, item.source),
    ):
        if entry.plugin_id in catalog:
            diagnostics.append(
                _diagnostic(
                    "reload_catalog_duplicate",
                    f"reload catalog contains duplicate plugin {entry.plugin_id}",
                    plugin_id=entry.plugin_id,
                    source=entry.source,
                )
            )
            continue
        catalog[entry.plugin_id] = entry
    return catalog, diagnostics


def _dependency_closure(
    requested: Iterable[str],
    catalog: Mapping[str, PluginHostCatalogEntry],
    diagnostics: list[PluginHostDiagnostic],
) -> set[str]:
    closure: set[str] = set()
    pending = sorted({canonical_plugin_id(str(item)) for item in requested if str(item)}, reverse=True)
    seen_missing: set[tuple[str, str]] = set()
    while pending:
        plugin_id = pending.pop()
        if plugin_id in closure:
            continue
        entry = catalog.get(plugin_id)
        if entry is None:
            key = (plugin_id, "")
            if key not in seen_missing:
                diagnostics.append(
                    _diagnostic(
                        "requested_plugin_not_found",
                        f"requested plugin {plugin_id} is not present in the reload catalog",
                        plugin_id=plugin_id,
                    )
                )
                seen_missing.add(key)
            continue
        closure.add(plugin_id)
        for dependency in reversed(entry.dependencies):
            if dependency not in catalog:
                key = (plugin_id, dependency)
                if key not in seen_missing:
                    diagnostics.append(
                        _diagnostic(
                            "plugin_dependency_missing",
                            f"plugin {plugin_id} requires missing plugin {dependency}",
                            plugin_id=plugin_id,
                            source=entry.source,
                        )
                    )
                    seen_missing.add(key)
                continue
            if dependency not in closure:
                pending.append(dependency)
    return closure


def _topological_order(
    plugin_ids: set[str],
    catalog: Mapping[str, PluginHostCatalogEntry],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    in_degree = {plugin_id: 0 for plugin_id in plugin_ids}
    dependents = {plugin_id: [] for plugin_id in plugin_ids}
    for plugin_id in sorted(plugin_ids):
        for dependency in catalog[plugin_id].dependencies:
            if dependency not in plugin_ids:
                continue
            dependents[dependency].append(plugin_id)
            in_degree[plugin_id] += 1
    ready = sorted(plugin_id for plugin_id, degree in in_degree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for dependent in sorted(dependents[current]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    unresolved = tuple(sorted(plugin_ids.difference(ordered)))
    return tuple(ordered), unresolved


def _active_dependents(
    target_plugin_id: str,
    active_plugin_ids: set[str],
    catalog: Mapping[str, PluginHostCatalogEntry],
) -> set[str]:
    affected = {target_plugin_id}
    changed = True
    while changed:
        changed = False
        for plugin_id in sorted(active_plugin_ids.difference(affected)):
            entry = catalog.get(plugin_id)
            if entry is not None and set(entry.dependencies).intersection(affected):
                affected.add(plugin_id)
                changed = True
    return affected


def build_plugin_reload_plan(
    catalog_entries: Sequence[PluginHostCatalogEntry],
    *,
    target_plugin_id: str,
    candidate: PluginHostCatalogEntry,
    active_plugin_ids: Iterable[str],
) -> PluginReloadPlan:
    """Validate a candidate and compute exact L3 reload callback order."""

    target = canonical_plugin_id(str(target_plugin_id))
    candidate_entry = candidate.normalized()
    catalog, diagnostics = _normalise_catalog(catalog_entries)
    current = catalog.get(target)
    active = {canonical_plugin_id(str(item)) for item in active_plugin_ids if str(item)}
    target_was_active = target in active

    if current is None:
        diagnostics.append(
            _diagnostic(
                "reload_target_not_found",
                f"reload target {target} is not present in the catalog",
                plugin_id=target,
            )
        )
    if candidate_entry.plugin_id != target:
        diagnostics.append(
            _diagnostic(
                "reload_candidate_id_mismatch",
                f"candidate id {candidate_entry.plugin_id} does not match target {target}",
                plugin_id=target,
                source=candidate_entry.source,
            )
        )

    if current is not None:
        if current.scope not in _ALLOWED_RELOAD_SCOPES:
            diagnostics.append(
                _diagnostic(
                    "reload_scope_forbidden",
                    f"scope {current.scope} cannot use direct L3 hot reload",
                    plugin_id=target,
                    source=current.source,
                )
            )
        if current.protected:
            diagnostics.append(
                _diagnostic(
                    "reload_protected_plugin",
                    f"protected plugin {target} cannot be hot reloaded",
                    plugin_id=target,
                    source=current.source,
                )
            )
        if not current.source:
            diagnostics.append(
                _diagnostic(
                    "reload_source_missing",
                    f"plugin {target} has no source continuity fact",
                    plugin_id=target,
                )
            )
        if candidate_entry.scope != current.scope:
            diagnostics.append(
                _diagnostic(
                    "reload_scope_changed",
                    f"candidate scope {candidate_entry.scope} does not match {current.scope}",
                    plugin_id=target,
                    source=candidate_entry.source,
                )
            )
        if candidate_entry.source != current.source:
            diagnostics.append(
                _diagnostic(
                    "reload_source_changed",
                    "candidate source does not match the registered L3 source",
                    plugin_id=target,
                    source=candidate_entry.source,
                )
            )
    if candidate_entry.scope not in _ALLOWED_RELOAD_SCOPES:
        diagnostics.append(
            _diagnostic(
                "reload_scope_forbidden",
                f"candidate scope {candidate_entry.scope} cannot use direct L3 hot reload",
                plugin_id=target,
                source=candidate_entry.source,
            )
        )
    if candidate_entry.protected:
        diagnostics.append(
            _diagnostic(
                "reload_protected_candidate",
                f"candidate {target} declares itself protected",
                plugin_id=target,
                source=candidate_entry.source,
            )
        )

    updated_catalog = dict(catalog)
    if candidate_entry.plugin_id == target:
        updated_catalog[target] = candidate_entry

    candidate_closure: set[str] = set()
    if target in updated_catalog:
        candidate_closure = _dependency_closure({target}, updated_catalog, diagnostics)
        _, candidate_cycle = _topological_order(candidate_closure, updated_catalog)
        if candidate_cycle:
            diagnostics.append(
                _diagnostic(
                    "plugin_dependency_cycle",
                    "candidate dependency cycle blocks hot reload: " + ", ".join(candidate_cycle),
                    plugin_id=candidate_cycle[0],
                )
            )

    affected: set[str] = set()
    deactivate_order: tuple[str, ...] = ()
    activate_order: tuple[str, ...] = ()
    if target_was_active and current is not None:
        affected = _active_dependents(target, active, catalog)
        protected_affected = sorted(
            plugin_id
            for plugin_id in affected
            if catalog.get(plugin_id) is not None and catalog[plugin_id].protected
        )
        for plugin_id in protected_affected:
            diagnostics.append(
                _diagnostic(
                    "reload_protected_dependent",
                    f"protected active plugin {plugin_id} would need deactivation",
                    plugin_id=plugin_id,
                    source=catalog[plugin_id].source,
                )
            )

        current_order, current_cycle = _topological_order(affected, catalog)
        if current_cycle:
            diagnostics.append(
                _diagnostic(
                    "active_plugin_dependency_cycle",
                    "active reload closure has a dependency cycle: " + ", ".join(current_cycle),
                    plugin_id=current_cycle[0],
                )
            )
        else:
            deactivate_order = tuple(reversed(current_order))

        reload_closure = _dependency_closure(affected, updated_catalog, diagnostics)
        reload_order, reload_cycle = _topological_order(reload_closure, updated_catalog)
        if reload_cycle:
            diagnostics.append(
                _diagnostic(
                    "plugin_dependency_cycle",
                    "reload activation closure has a dependency cycle: " + ", ".join(reload_cycle),
                    plugin_id=reload_cycle[0],
                )
            )
        else:
            active_remaining = active.difference(affected)
            activate_order = tuple(
                plugin_id for plugin_id in reload_order if plugin_id not in active_remaining
            )

    blocked = any(item.level == "error" for item in diagnostics)
    catalog_tuple = tuple(updated_catalog[key] for key in sorted(updated_catalog))
    if blocked:
        deactivate_order = ()
        activate_order = ()

    affected_order: tuple[str, ...] = ()
    if affected:
        ordered, unresolved = _topological_order(affected, catalog)
        affected_order = ordered + unresolved

    return PluginReloadPlan(
        ok=not blocked,
        target_plugin_id=target,
        target_was_active=target_was_active,
        candidate=candidate_entry,
        catalog=catalog_tuple,
        affected_plugin_ids=affected_order,
        deactivate_plugin_ids=deactivate_order,
        activate_plugin_ids=activate_order,
        diagnostics=tuple(diagnostics),
    )
