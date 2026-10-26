# -*- coding: utf-8 -*-
"""Qt-free lifecycle authority for extensions hosted by the L1 engine plugin.

The Module decides *what* may be discovered and *which order* transitions must
use.  The Qt-free `RuntimePluginHost` imports plugin code and executes runtime
callbacks; concrete Editor/UI Host Adapters only publish UI contributions and
legacy Host signals around those callbacks.
"""
from __future__ import annotations

import json
import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from core.VitaLoom.kernel.plugin_ids import canonical_plugin_id, normalize_dependency_ids
from core.VitaLoom.core.plugin_activation_contract import (
    PluginActivationContractError,
    parse_plugin_activation_metadata,
)
from core.VitaLoom.project.project_manifest import version_matches_constraint

ENGINE_PLUGIN_ID = "lotucosm-vitaloom"
PROJECT_ADDON_SCOPE = "embedded_mod"

_SCOPE_PRIORITY: Mapping[str, int] = {
    "unknown": 0,
    "embedded_mod": 1,
    "user_mod": 2,
    "official_mod": 3,
    "core_mod": 4,
}
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _json_safe_copy(value: Any) -> Any:
    """Copy declarative plugin metadata without leaking live objects."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_copy(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe_copy(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_json_safe_copy(item) for item in sorted(value, key=lambda item: str(item))]
    return str(value)


def normalize_plugin_provides(value: Any) -> tuple[Any, ...]:
    """Return one deterministic JSON-safe capability declaration tuple.

    Plugin metadata in the legacy ecosystem is not perfectly uniform: a
    provider may declare one string, a mapping, or a sequence. Normalizing at
    the canonical catalog seam prevents reload and discovery paths from
    accidentally splitting strings into characters or mappings into keys.
    """

    safe = _json_safe_copy(value)
    if safe is None:
        return ()
    if isinstance(safe, list):
        return tuple(safe)
    return (safe,)


@dataclass(frozen=True)
class PluginHostDiagnostic:
    code: str
    message: str
    level: str = "error"
    plugin_id: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "plugin_id": self.plugin_id,
            "source": self.source,
        }


@dataclass(frozen=True)
class PluginHostCatalogEntry:
    plugin_id: str
    scope: str
    source: str
    version: str = "0.0.0"
    description: str = ""
    provides: tuple[Any, ...] = ()
    dependencies: tuple[str, ...] = ()
    protected: bool = False
    activation_context: str = "legacy_ui"
    activation_context_explicit: bool = False
    declared_name: str = ""
    editor_contributions: tuple[Any, ...] = ()

    def normalized(self) -> "PluginHostCatalogEntry":
        plugin_id = canonical_plugin_id(str(self.plugin_id))
        scope = str(self.scope) if str(self.scope) in _SCOPE_PRIORITY else "unknown"
        dependencies = tuple(normalize_dependency_ids(self.dependencies))
        return PluginHostCatalogEntry(
            plugin_id=plugin_id,
            scope=scope,
            source=str(self.source),
            version=str(self.version or "0.0.0"),
            description=str(self.description or ""),
            provides=normalize_plugin_provides(self.provides),
            dependencies=dependencies,
            protected=bool(self.protected),
            activation_context=str(self.activation_context or "legacy_ui"),
            activation_context_explicit=bool(self.activation_context_explicit),
            declared_name=str(self.declared_name or plugin_id),
            editor_contributions=tuple(_json_safe_copy(self.editor_contributions)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "scope": self.scope,
            "source": self.source,
            "version": self.version,
            "description": self.description,
            "provides": _json_safe_copy(list(self.provides)),
            "dependencies": list(self.dependencies),
            "protected": self.protected,
            "activation_context": self.activation_context,
            "activation_context_explicit": self.activation_context_explicit,
            "declared_name": self.declared_name or self.plugin_id,
            "editor_contributions": _json_safe_copy(list(self.editor_contributions)),
            "activation_context_source": (
                "declared" if self.activation_context_explicit else "default"
            ),
        }


@dataclass(frozen=True)
class PluginLifecyclePlan:
    ok: bool
    catalog: tuple[PluginHostCatalogEntry, ...]
    requested_plugin_ids: tuple[str, ...]
    target_plugin_ids: tuple[str, ...]
    retained_plugin_ids: tuple[str, ...]
    deactivate_plugin_ids: tuple[str, ...]
    activate_plugin_ids: tuple[str, ...]
    diagnostics: tuple[PluginHostDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "ready" if self.ok else "blocked",
            "catalog": [item.to_dict() for item in self.catalog],
            "requested_plugin_ids": list(self.requested_plugin_ids),
            "target_plugin_ids": list(self.target_plugin_ids),
            "retained_plugin_ids": list(self.retained_plugin_ids),
            "deactivate_plugin_ids": list(self.deactivate_plugin_ids),
            "activate_plugin_ids": list(self.activate_plugin_ids),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _normalise_catalog(
    entries: Iterable[PluginHostCatalogEntry],
) -> tuple[dict[str, PluginHostCatalogEntry], list[PluginHostDiagnostic]]:
    selected: dict[str, PluginHostCatalogEntry] = {}
    diagnostics: list[PluginHostDiagnostic] = []
    ordered = sorted(
        (entry.normalized() for entry in entries),
        key=lambda item: (item.plugin_id, item.scope, item.source),
    )
    for candidate in ordered:
        existing = selected.get(candidate.plugin_id)
        if existing is None:
            selected[candidate.plugin_id] = candidate
            continue
        existing_priority = _SCOPE_PRIORITY.get(existing.scope, 0)
        candidate_priority = _SCOPE_PRIORITY.get(candidate.scope, 0)
        if candidate_priority == existing_priority:
            if candidate.source != existing.source:
                diagnostics.append(
                    PluginHostDiagnostic(
                        code="plugin_source_collision",
                        message=(
                            f"plugin {candidate.plugin_id} has multiple sources at scope "
                            f"{candidate.scope}"
                        ),
                        plugin_id=candidate.plugin_id,
                        source=f"{existing.source}|{candidate.source}",
                    )
                )
            continue
        if candidate_priority > existing_priority:
            winner, ignored = candidate, existing
            selected[candidate.plugin_id] = candidate
        else:
            winner, ignored = existing, candidate
        diagnostics.append(
            PluginHostDiagnostic(
                level="warning",
                code="lower_priority_source_ignored",
                message=(
                    f"plugin {candidate.plugin_id} uses {winner.scope}; "
                    f"ignored lower-priority {ignored.scope} source"
                ),
                plugin_id=candidate.plugin_id,
                source=ignored.source,
            )
        )
    return selected, diagnostics


def _dependency_closure(
    requested: set[str],
    catalog: Mapping[str, PluginHostCatalogEntry],
    diagnostics: list[PluginHostDiagnostic],
) -> set[str]:
    target: set[str] = set()
    pending = sorted(requested, reverse=True)
    seen_missing: set[tuple[str, str]] = set()
    while pending:
        plugin_id = pending.pop()
        if plugin_id in target:
            continue
        entry = catalog.get(plugin_id)
        if entry is None:
            key = (plugin_id, "")
            if key not in seen_missing:
                diagnostics.append(
                    PluginHostDiagnostic(
                        code="requested_plugin_not_found",
                        message=f"requested plugin {plugin_id} is not present in the catalog",
                        plugin_id=plugin_id,
                    )
                )
                seen_missing.add(key)
            continue
        target.add(plugin_id)
        for dependency in reversed(entry.dependencies):
            if dependency not in catalog:
                key = (plugin_id, dependency)
                if key not in seen_missing:
                    diagnostics.append(
                        PluginHostDiagnostic(
                            code="plugin_dependency_missing",
                            message=f"plugin {plugin_id} requires missing plugin {dependency}",
                            plugin_id=plugin_id,
                            source=entry.source,
                        )
                    )
                    seen_missing.add(key)
                continue
            if dependency not in target:
                pending.append(dependency)
    return target


def _topological_order(
    plugin_ids: set[str], catalog: Mapping[str, PluginHostCatalogEntry]
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


def build_plugin_lifecycle_plan(
    catalog_entries: Sequence[PluginHostCatalogEntry],
    *,
    active_plugin_ids: Iterable[str],
    requested_plugin_ids: Iterable[str],
    retain_protected: bool = True,
) -> PluginLifecyclePlan:
    """Return one deterministic, fail-closed downstream-extension transition plan."""

    catalog, diagnostics = _normalise_catalog(catalog_entries)
    requested = {canonical_plugin_id(str(item)) for item in requested_plugin_ids if str(item)}
    active = {canonical_plugin_id(str(item)) for item in active_plugin_ids if str(item)}

    target = _dependency_closure(requested, catalog, diagnostics)
    retained: set[str] = set()
    if retain_protected:
        for plugin_id in sorted(active):
            entry = catalog.get(plugin_id)
            if entry is not None and entry.protected and plugin_id not in target:
                target.add(plugin_id)
                retained.add(plugin_id)
                diagnostics.append(
                    PluginHostDiagnostic(
                        level="warning",
                        code="protected_plugin_retained",
                        message=f"protected plugin {plugin_id} remains active",
                        plugin_id=plugin_id,
                        source=entry.source,
                    )
                )

    target_order, target_cycle = _topological_order(target, catalog) if target else ((), ())
    if target_cycle:
        diagnostics.append(
            PluginHostDiagnostic(
                code="plugin_dependency_cycle",
                message="dependency cycle blocks lifecycle transition: " + ", ".join(target_cycle),
                plugin_id=target_cycle[0],
            )
        )

    active_known = {plugin_id for plugin_id in active if plugin_id in catalog}
    active_order, active_cycle = (
        _topological_order(active_known, catalog) if active_known else ((), ())
    )
    if active_cycle and not target_cycle:
        diagnostics.append(
            PluginHostDiagnostic(
                code="active_plugin_dependency_cycle",
                message="active dependency cycle blocks lifecycle transition: "
                + ", ".join(active_cycle),
                plugin_id=active_cycle[0],
            )
        )

    blocked = any(item.level == "error" for item in diagnostics)
    catalog_tuple = tuple(catalog[key] for key in sorted(catalog))
    if blocked:
        return PluginLifecyclePlan(
            ok=False,
            catalog=catalog_tuple,
            requested_plugin_ids=tuple(sorted(requested)),
            target_plugin_ids=target_order,
            retained_plugin_ids=tuple(sorted(retained)),
            deactivate_plugin_ids=(),
            activate_plugin_ids=(),
            diagnostics=tuple(diagnostics),
        )

    deactivate = tuple(
        plugin_id
        for plugin_id in reversed(active_order)
        if plugin_id not in target and plugin_id not in retained
    )
    activate = tuple(plugin_id for plugin_id in target_order if plugin_id not in active)
    return PluginLifecyclePlan(
        ok=True,
        catalog=catalog_tuple,
        requested_plugin_ids=tuple(sorted(requested)),
        target_plugin_ids=target_order,
        retained_plugin_ids=tuple(sorted(retained)),
        deactivate_plugin_ids=deactivate,
        activate_plugin_ids=activate,
        diagnostics=tuple(diagnostics),
    )


@dataclass(frozen=True)
class ProjectAddonSource:
    plugin_id: str
    version: str
    dependencies: tuple[str, ...]
    addon_root: Path
    manifest_path: Path
    entry_path: Path
    scope: str = PROJECT_ADDON_SCOPE
    activation_context: str = "legacy_ui"
    activation_context_explicit: bool = False
    manifest_sha256: str = ""
    entry_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "version": self.version,
            "dependencies": list(self.dependencies),
            "scope": self.scope,
            "addon_root": str(self.addon_root),
            "manifest_path": str(self.manifest_path),
            "entry_path": str(self.entry_path),
            "activation_context": self.activation_context,
            "activation_context_explicit": self.activation_context_explicit,
            "activation_context_source": (
                "declared" if self.activation_context_explicit else "default"
            ),
            "manifest_sha256": self.manifest_sha256,
            "entry_sha256": self.entry_sha256,
        }


@dataclass(frozen=True)
class ProjectAddonDiscoveryResult:
    ok: bool
    project_path: Path | None
    addons_root: Path | None
    sources: tuple[ProjectAddonSource, ...]
    diagnostics: tuple[PluginHostDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "ready" if self.ok else "blocked",
            "project_path": str(self.project_path) if self.project_path else "",
            "addons_root": str(self.addons_root) if self.addons_root else "",
            "sources": [item.to_dict() for item in self.sources],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _is_contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _diagnostic(code: str, message: str, *, plugin_id: str = "", source: Path | str = "") -> PluginHostDiagnostic:
    return PluginHostDiagnostic(
        code=code,
        message=message,
        plugin_id=plugin_id,
        source=str(source),
    )


def discover_project_addons(
    project_path: str | Path | None,
    *,
    runtime_version: str,
) -> ProjectAddonDiscoveryResult:
    """Validate the complete L4 addon source catalog without importing plugin code."""

    if project_path is None or not str(project_path).strip():
        diagnostic = _diagnostic(
            "project_path_required",
            "project addon discovery requires an opened Project World path",
        )
        return ProjectAddonDiscoveryResult(False, None, None, (), (diagnostic,))
    raw_project = Path(project_path)
    try:
        if raw_project.is_symlink():
            raise ValueError("project root is a symlink")
        project = raw_project.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        diagnostic = _diagnostic(
            "project_path_invalid", f"invalid Project World path: {exc}", source=raw_project
        )
        return ProjectAddonDiscoveryResult(False, None, None, (), (diagnostic,))
    if not project.is_dir():
        diagnostic = _diagnostic(
            "project_path_invalid", "Project World path is not a directory", source=project
        )
        return ProjectAddonDiscoveryResult(False, project, None, (), (diagnostic,))

    addons_raw = project / "addons"
    if not addons_raw.exists():
        return ProjectAddonDiscoveryResult(True, project, addons_raw, (), ())
    try:
        if addons_raw.is_symlink():
            raise ValueError("addons root is a symlink")
        addons_root = addons_raw.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        diagnostic = _diagnostic(
            "addons_root_invalid", f"invalid addons root: {exc}", source=addons_raw
        )
        return ProjectAddonDiscoveryResult(False, project, None, (), (diagnostic,))
    if not addons_root.is_dir() or not _is_contained(addons_root, project):
        diagnostic = _diagnostic(
            "addons_root_invalid", "addons root escapes the Project World", source=addons_root
        )
        return ProjectAddonDiscoveryResult(False, project, addons_root, (), (diagnostic,))

    diagnostics: list[PluginHostDiagnostic] = []
    sources: list[ProjectAddonSource] = []
    seen_ids: set[str] = set()
    for addon_raw in sorted(addons_root.iterdir(), key=lambda item: item.name.casefold()):
        if not addon_raw.is_dir():
            continue
        if addon_raw.is_symlink():
            diagnostics.append(
                _diagnostic(
                    "addon_root_symlink_rejected",
                    "symlinked addon roots are not accepted",
                    source=addon_raw,
                )
            )
            continue
        try:
            addon_root = addon_raw.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            diagnostics.append(
                _diagnostic("addon_root_invalid", f"invalid addon root: {exc}", source=addon_raw)
            )
            continue
        if not _is_contained(addon_root, addons_root):
            diagnostics.append(
                _diagnostic("addon_root_invalid", "addon root escapes addons", source=addon_root)
            )
            continue

        manifest_raw = addon_root / "plugin.json"
        if not manifest_raw.is_file():
            if any(addon_root.rglob("*_plugin.py")):
                diagnostics.append(
                    _diagnostic(
                        "addon_manifest_missing",
                        "addon plugin source requires plugin.json",
                        source=manifest_raw,
                    )
                )
            continue
        if manifest_raw.is_symlink():
            diagnostics.append(
                _diagnostic(
                    "addon_manifest_symlink_rejected",
                    "symlinked addon manifests are not accepted",
                    source=manifest_raw,
                )
            )
            continue
        try:
            manifest_path = manifest_raw.resolve(strict=True)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            diagnostics.append(
                _diagnostic(
                    "addon_manifest_malformed",
                    f"cannot read addon manifest: {type(exc).__name__}",
                    source=manifest_raw,
                )
            )
            continue
        if not isinstance(payload, dict):
            diagnostics.append(
                _diagnostic(
                    "addon_manifest_malformed", "addon manifest must be an object", source=manifest_path
                )
            )
            continue
        if payload.get("schema_version") != 1:
            diagnostics.append(
                _diagnostic(
                    "addon_manifest_schema_unsupported",
                    "addon manifest schema_version must be 1",
                    source=manifest_path,
                )
            )
            continue

        raw_id = str(payload.get("id", "") or "").strip()
        plugin_id = canonical_plugin_id(raw_id)
        version = str(payload.get("version", "") or "").strip()
        raw_entry = str(payload.get("entry", "") or "").strip()
        raw_dependencies = payload.get("dependencies", [])
        runtime = payload.get("runtime")
        try:
            activation_metadata = parse_plugin_activation_metadata(
                payload,
                plugin_id=plugin_id,
                source=str(manifest_path),
            )
        except PluginActivationContractError as exc:
            diagnostics.append(
                _diagnostic(
                    exc.code,
                    exc.message,
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        if not raw_id or plugin_id != raw_id:
            diagnostics.append(
                _diagnostic(
                    "addon_plugin_id_invalid",
                    "addon id must be a canonical *Plugin id",
                    plugin_id=raw_id,
                    source=manifest_path,
                )
            )
            continue
        if not _SEMVER_RE.fullmatch(version):
            diagnostics.append(
                _diagnostic(
                    "addon_version_invalid",
                    "addon version must use x.y.z",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        if not isinstance(raw_dependencies, list) or any(
            not isinstance(item, str) or canonical_plugin_id(item) != item
            for item in raw_dependencies
        ):
            diagnostics.append(
                _diagnostic(
                    "addon_dependencies_invalid",
                    "addon dependencies must be canonical plugin id strings",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        dependencies = tuple(normalize_dependency_ids(raw_dependencies))
        if not isinstance(runtime, dict):
            diagnostics.append(
                _diagnostic(
                    "addon_runtime_invalid",
                    "addon runtime authority is required",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        runtime_plugin_id = str(runtime.get("plugin_id", "") or "").strip()
        runtime_constraint = str(runtime.get("version", "") or "").strip()
        if runtime_plugin_id != ENGINE_PLUGIN_ID or not runtime_constraint:
            diagnostics.append(
                _diagnostic(
                    "addon_runtime_invalid",
                    "addon runtime must target lotucosm-vitaloom with a version constraint",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        if not version_matches_constraint(runtime_version, runtime_constraint):
            diagnostics.append(
                _diagnostic(
                    "addon_runtime_incompatible",
                    f"runtime {runtime_version} does not satisfy {runtime_constraint}",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue

        entry_relative = Path(raw_entry)
        if (
            not raw_entry
            or entry_relative.is_absolute()
            or any(part in {"", ".", ".."} for part in entry_relative.parts)
            or not entry_relative.name.endswith("_plugin.py")
        ):
            diagnostics.append(
                _diagnostic(
                    "addon_entry_invalid",
                    "addon entry must be one contained relative *_plugin.py path",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        entry_raw = addon_root / entry_relative
        if entry_raw.is_symlink():
            diagnostics.append(
                _diagnostic(
                    "addon_entry_symlink_rejected",
                    "symlinked addon entries are not accepted",
                    plugin_id=plugin_id,
                    source=entry_raw,
                )
            )
            continue
        try:
            entry_path = entry_raw.resolve(strict=True)
        except (OSError, RuntimeError):
            diagnostics.append(
                _diagnostic(
                    "addon_entry_invalid",
                    "addon entry does not exist",
                    plugin_id=plugin_id,
                    source=entry_raw,
                )
            )
            continue
        if not entry_path.is_file() or not _is_contained(entry_path, addon_root):
            diagnostics.append(
                _diagnostic(
                    "addon_entry_invalid",
                    "addon entry escapes its addon root",
                    plugin_id=plugin_id,
                    source=entry_path,
                )
            )
            continue
        try:
            manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            entry_sha256 = hashlib.sha256(entry_path.read_bytes()).hexdigest()
        except OSError as exc:
            diagnostics.append(
                _diagnostic(
                    "addon_source_unreadable",
                    f"cannot digest addon source: {type(exc).__name__}",
                    plugin_id=plugin_id,
                    source=entry_path,
                )
            )
            continue
        if plugin_id in seen_ids:
            diagnostics.append(
                _diagnostic(
                    "addon_plugin_id_duplicate",
                    f"duplicate addon plugin id {plugin_id}",
                    plugin_id=plugin_id,
                    source=manifest_path,
                )
            )
            continue
        seen_ids.add(plugin_id)
        sources.append(
            ProjectAddonSource(
                plugin_id=plugin_id,
                version=version,
                dependencies=dependencies,
                addon_root=addon_root,
                manifest_path=manifest_path,
                entry_path=entry_path,
                activation_context=activation_metadata.kind,
                activation_context_explicit=activation_metadata.explicit,
                manifest_sha256=manifest_sha256,
                entry_sha256=entry_sha256,
            )
        )

    if diagnostics:
        return ProjectAddonDiscoveryResult(
            False,
            project,
            addons_root,
            (),
            tuple(sorted(diagnostics, key=lambda item: (item.code, item.plugin_id, item.source))),
        )
    return ProjectAddonDiscoveryResult(
        True,
        project,
        addons_root,
        tuple(sorted(sources, key=lambda item: item.plugin_id)),
        (),
    )
