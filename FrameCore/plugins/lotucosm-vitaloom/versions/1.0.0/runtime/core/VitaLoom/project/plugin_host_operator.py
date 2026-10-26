# -*- coding: utf-8 -*-
"""Qt-free operator authority for the L1 engine plugin's downstream Host.

The Module derives deterministic inspection/recovery facts. Concrete Host
Adapters execute only a validated normal lifecycle retry; this module never
imports UI code or invokes plugin callbacks itself.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import weakref
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence


SCHEMA_VERSION = 1
RETRY_PROJECT_LIFECYCLE = "retry_project_lifecycle"
_ATTENTION_STATUSES = {"blocked", "failed", "partial"}


class PluginHostOperatorError(RuntimeError):
    """Fail-closed operator Interface error with a stable code and facts."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)
        self.details = _json_safe(details or {})


class PluginHostOperatorAdapter(Protocol):
    """Concrete live Host Adapter consumed by shared command transports."""

    def inspect_plugin_host(self, project_path: str = "") -> dict[str, Any]: ...

    def list_plugin_host_recoveries(self, project_path: str = "") -> dict[str, Any]: ...

    def resolve_plugin_host_recovery(
        self,
        *,
        project_path: str,
        report_id: str,
        action: str,
        operator_confirmation: str,
    ) -> dict[str, Any]: ...


_BOUND_ADAPTER: Callable[[], PluginHostOperatorAdapter | None] | None = None


def bind_plugin_host_operator_adapter(adapter: PluginHostOperatorAdapter) -> None:
    """Bind the current same-process Host without retaining it unnecessarily."""

    global _BOUND_ADAPTER
    try:
        reference = weakref.ref(adapter)
        _BOUND_ADAPTER = reference
    except TypeError:
        _BOUND_ADAPTER = lambda: adapter


def unbind_plugin_host_operator_adapter(
    adapter: PluginHostOperatorAdapter | None = None,
) -> None:
    """Clear the live binding, optionally only when it matches one Adapter."""

    global _BOUND_ADAPTER
    current = _BOUND_ADAPTER() if _BOUND_ADAPTER is not None else None
    if adapter is None or current is adapter:
        _BOUND_ADAPTER = None


def get_plugin_host_operator_adapter(
    context: Mapping[str, Any] | None = None,
) -> PluginHostOperatorAdapter | None:
    """Prefer an explicit command context, then the current Qt-free binding."""

    if isinstance(context, Mapping):
        explicit = context.get("plugin_host_operator")
        if explicit is not None:
            return explicit
    return _BOUND_ADAPTER() if _BOUND_ADAPTER is not None else None


def canonical_project_path(value: str | Path | None) -> str:
    """Return one stable absolute spelling without requiring the path to exist."""

    text = str(value or "").strip()
    if not text:
        return ""
    return os.path.normcase(os.path.abspath(os.path.expanduser(text)))


def build_plugin_host_inspection(
    *,
    project_path: str | Path | None,
    embedded_catalog_project_path: str | Path | None,
    catalog_entries: Sequence[Any],
    active_plugin_ids: Sequence[str] | set[str] | tuple[str, ...],
    failed_plugins: Mapping[str, Any],
    discovery_report: Mapping[str, Any],
    lifecycle_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one deterministic JSON-safe live Host inspection snapshot."""

    facts = {
        "schema_version": SCHEMA_VERSION,
        "project_path": canonical_project_path(project_path),
        "embedded_catalog_project_path": canonical_project_path(
            embedded_catalog_project_path
        ),
        "catalog": _normalise_catalog(catalog_entries),
        "active_plugin_ids": sorted(
            {str(item) for item in active_plugin_ids if str(item)}
        ),
        "failed_plugins": {
            str(key): str(value)
            for key, value in sorted(failed_plugins.items(), key=lambda item: str(item[0]))
        },
        "discovery": _json_safe(discovery_report),
        "lifecycle": _json_safe(lifecycle_report),
    }
    status = _derive_status(facts["discovery"], facts["lifecycle"])
    diagnostics = _collect_diagnostics(facts["discovery"], facts["lifecycle"])
    report_id = _digest(facts)
    inspection = {
        **facts,
        "status": status,
        "diagnostics": diagnostics,
        "report_id": report_id,
    }
    inspection["recoveries"] = _build_recoveries(inspection)
    return inspection


def list_plugin_host_recoveries(inspection: Mapping[str, Any]) -> dict[str, Any]:
    """Return a read-only recovery list tied to one exact inspection report."""

    return {
        "schema_version": SCHEMA_VERSION,
        "status": str(inspection.get("status") or "not_run"),
        "project_path": str(inspection.get("project_path") or ""),
        "embedded_catalog_project_path": str(
            inspection.get("embedded_catalog_project_path") or ""
        ),
        "report_id": str(inspection.get("report_id") or ""),
        "records": _json_safe(inspection.get("recoveries") or []),
    }


def validate_plugin_host_recovery(
    inspection: Mapping[str, Any],
    *,
    project_path: str,
    report_id: str,
    action: str,
    operator_confirmation: str,
) -> dict[str, Any]:
    """Validate project/report/action/confirmation before any Host mutation."""

    current_project = canonical_project_path(inspection.get("project_path"))
    supplied_project = canonical_project_path(project_path)
    if not current_project or supplied_project != current_project:
        raise PluginHostOperatorError(
            "plugin_host_project_mismatch",
            "Recovery must target the exact current Project World",
            details={"current_project_path": current_project, "project_path": supplied_project},
        )
    current_report_id = str(inspection.get("report_id") or "")
    if not report_id or str(report_id) != current_report_id:
        raise PluginHostOperatorError(
            "plugin_host_report_stale",
            "Plugin Host inspection changed; inspect again before recovery",
            details={"current_report_id": current_report_id, "report_id": str(report_id)},
        )
    records = inspection.get("recoveries")
    if not isinstance(records, list):
        records = []
    record = next(
        (item for item in records if isinstance(item, Mapping) and item.get("action") == action),
        None,
    )
    if record is None:
        raise PluginHostOperatorError(
            "plugin_host_recovery_action_unavailable",
            "The requested recovery action is not offered by the current report",
            details={
                "action": str(action),
                "available_actions": [
                    str(item.get("action"))
                    for item in records
                    if isinstance(item, Mapping)
                ],
            },
        )
    expected = str(record.get("operator_confirmation_required") or "")
    if not expected or str(operator_confirmation) != expected:
        raise PluginHostOperatorError(
            "plugin_host_recovery_confirmation_required",
            "Exact operator confirmation must bind project, report, and action",
            details={
                "project_path": current_project,
                "report_id": current_report_id,
                "action": str(action),
                "expected_confirmation": expected,
            },
        )
    return _json_safe(record)


def read_project_lifecycle_input(project_path: str | Path) -> tuple[str, dict[str, Any]]:
    """Freshly read one Project World's lifecycle input for a validated retry."""

    raw = Path(project_path)
    try:
        project = raw.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PluginHostOperatorError(
            "plugin_host_project_unavailable",
            "Project World is unavailable for lifecycle recovery",
            details={"project_path": str(raw), "error": str(exc)},
        ) from exc
    if not project.is_dir():
        raise PluginHostOperatorError(
            "plugin_host_project_unavailable",
            "Project World path must be a directory",
            details={"project_path": str(project)},
        )
    project_file = project / "project.json"
    if not project_file.is_file() or project_file.is_symlink():
        raise PluginHostOperatorError(
            "plugin_host_project_manifest_unavailable",
            "Lifecycle recovery requires a regular project.json",
            details={"project_path": str(project), "project_file": str(project_file)},
        )
    try:
        data = json.loads(project_file.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PluginHostOperatorError(
            "plugin_host_project_manifest_invalid",
            "project.json could not be read as JSON",
            details={"project_file": str(project_file), "error": str(exc)},
        ) from exc
    if not isinstance(data, dict):
        raise PluginHostOperatorError(
            "plugin_host_project_manifest_invalid",
            "project.json root must be an object",
            details={"project_file": str(project_file)},
        )
    return canonical_project_path(project), data


def _normalise_catalog(entries: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if hasattr(entry, "to_dict") and callable(entry.to_dict):
            value = entry.to_dict()
        elif isinstance(entry, Mapping):
            value = dict(entry)
        else:
            value = {"plugin_id": str(entry)}
        row = _json_safe(value)
        if not isinstance(row, dict):
            row = {"plugin_id": str(row)}
        rows.append(row)
    return sorted(
        rows,
        key=lambda item: (
            str(item.get("plugin_id") or ""),
            str(item.get("scope") or ""),
            str(item.get("source") or ""),
        ),
    )


def _derive_status(discovery: Mapping[str, Any], lifecycle: Mapping[str, Any]) -> str:
    discovery_status = str(discovery.get("status") or "not_run")
    lifecycle_status = str(lifecycle.get("status") or "not_run")
    if discovery_status in {"blocked", "failed"}:
        return discovery_status
    if lifecycle_status == "blocked":
        return "blocked"
    if lifecycle_status in {"failed", "partial"}:
        completed = lifecycle.get("completed")
        skipped = lifecycle.get("skipped")
        has_completed = isinstance(completed, Mapping) and any(
            bool(value) for value in completed.values()
        )
        has_skipped = isinstance(skipped, Mapping) and any(
            bool(value) for value in skipped.values()
        )
        return "partial" if has_completed or has_skipped else "failed"
    if lifecycle_status in {"settled", "skipped_eager_mode"}:
        return "settled"
    if discovery_status == "ready" and lifecycle_status == "not_run":
        return "not_run"
    return lifecycle_status if lifecycle_status else "not_run"


def _collect_diagnostics(
    discovery: Mapping[str, Any], lifecycle: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for origin, report in (("discovery", discovery), ("lifecycle", lifecycle)):
        diagnostics = report.get("diagnostics")
        if not isinstance(diagnostics, list):
            continue
        for item in diagnostics:
            row = _json_safe(item)
            if isinstance(row, dict):
                row = {"origin": origin, **row}
            else:
                row = {"origin": origin, "message": str(row)}
            rows.append(row)
    return sorted(
        rows,
        key=lambda item: (
            str(item.get("origin") or ""),
            str(item.get("code") or ""),
            str(item.get("plugin_id") or ""),
            str(item.get("source") or ""),
            str(item.get("message") or ""),
        ),
    )


def _build_recoveries(inspection: Mapping[str, Any]) -> list[dict[str, Any]]:
    status = str(inspection.get("status") or "not_run")
    project_path = str(inspection.get("project_path") or "")
    lifecycle = inspection.get("lifecycle")
    if isinstance(lifecycle, Mapping) and lifecycle.get("source") == "hot_reload":
        # E6 recovery re-runs Project World discovery/lifecycle only.  It must
        # not pretend to repair a failed L3 candidate replacement.
        return []
    if status not in _ATTENTION_STATUSES or not project_path:
        return []
    report_id = str(inspection.get("report_id") or "")
    project_binding = hashlib.sha256(project_path.encode("utf-8")).hexdigest()[:16]
    confirmation = (
        f"resolve_plugin_lifecycle:{project_binding}:{report_id}:"
        f"{RETRY_PROJECT_LIFECYCLE}"
    )
    manual_review = status in {"failed", "partial"}
    return [
        {
            "action": RETRY_PROJECT_LIFECYCLE,
            "project_path": project_path,
            "report_id": report_id,
            "requires_manual_review": manual_review,
            "risk": (
                "third-party callback side effects may require manual repair or process restart"
                if manual_review
                else "normal authoritative discovery and lifecycle planning will be re-run"
            ),
            "operator_confirmation_required": confirmation,
        }
    ]


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (set, frozenset)):
        items = [_json_safe(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(
                item, ensure_ascii=False, sort_keys=True, allow_nan=False
            ),
        )
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)
