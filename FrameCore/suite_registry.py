# -*- coding: utf-8 -*-
"""FrameCore plugin manifest loading.

The public function names keep the historical ``suite`` wording for callers,
but the physical model is now simpler: FrameCore loads one app plugin package,
``lotucosm-vitaloom``. That plugin owns Hub and all versioned runtimes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SUITE_PLUGIN_ID = "lotucosm-vitaloom"


@dataclass(frozen=True)
class SuiteManifest:
    schema_version: int
    frame_plugin_id: str
    suite_id: str
    version: str
    entry: str
    products: tuple[str, ...]
    display_name: str = ""
    display_name_zh: str = ""
    capability_catalog: str = ""
    suite_root: Path | None = None

    @property
    def plugin_id(self) -> str:
        return self.frame_plugin_id

    @property
    def product_id(self) -> str:
        return self.products[0] if self.products else self.suite_id


def resolve_application_root(path: str | Path) -> Path:
    """Resolve app, FrameCore, or versioned-runtime paths to one app root."""
    candidate = Path(path).resolve()
    starts = [candidate.parent] if candidate.is_file() else [candidate]
    for item in (*starts, *candidate.parents):
        manifest = (
            item
            / "FrameCore"
            / "plugins"
            / DEFAULT_SUITE_PLUGIN_ID
            / "plugin_manifest.json"
        )
        if manifest.is_file():
            return item
    return candidate


def framecore_root(app_root: str | Path) -> Path:
    return resolve_application_root(app_root) / "FrameCore"


def suite_plugin_root(
    app_root: str | Path,
    suite_plugin_id: str = DEFAULT_SUITE_PLUGIN_ID,
) -> Path:
    return framecore_root(app_root) / "plugins" / suite_plugin_id


def _manifest_path(root: Path) -> Path:
    return root / "plugin_manifest.json"


def _require_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = str(data.get(key, "") or "").strip()
    if not value:
        raise ValueError(f"{label} missing {key}")
    return value


def load_suite_manifest(suite_root: str | Path) -> SuiteManifest:
    """Read a FrameCore app plugin package manifest."""
    root = Path(suite_root).resolve()
    path = _manifest_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"missing plugin_manifest.json: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} root must be an object")
    schema = int(data.get("schema_version", 0) or 0)
    if schema < 1:
        raise ValueError(f"{path.name} schema_version must be >= 1")
    plugin_id = _require_string(data, "plugin_id", label=path.name)
    suite_id = str(data.get("suite_id", "") or plugin_id).strip()
    product_id = str(data.get("product_id", "") or plugin_id).strip()
    raw_versions = data.get("versions", [])
    if not isinstance(raw_versions, list) or not raw_versions:
        raise ValueError(f"{path.name} versions must be a non-empty list")
    entry = _require_string(data, "entry", label=path.name)
    if not (root / entry.split(" ", 1)[0]).exists():
        raise ValueError(f"plugin entry does not exist: {entry}")
    return SuiteManifest(
        schema_version=schema,
        frame_plugin_id=plugin_id,
        suite_id=suite_id,
        version=_require_string(data, "default_version", label=path.name),
        entry=entry,
        products=(product_id,),
        display_name=str(data.get("display_name", "") or ""),
        display_name_zh=str(data.get("display_name_zh", "") or ""),
        capability_catalog=str(data.get("capability_catalog", "") or ""),
        suite_root=root,
    )


def load_default_suite_manifest(app_root: str | Path) -> SuiteManifest:
    return load_suite_manifest(suite_plugin_root(app_root))
