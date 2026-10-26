# -*- coding: utf-8 -*-
"""Path resolution for the product-version runtime."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def is_frozen_bundle() -> bool:
    return bool(getattr(sys, "frozen", False))


def _this_runtime_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _dev_repo_root() -> Path:
    return application_root()


def product_version_root() -> Path:
    raw = os.environ.get("VITALOOM_PRODUCT_VERSION_ROOT")
    if raw:
        return Path(raw).resolve()
    return _this_runtime_root().parent


def runtime_root() -> Path:
    return product_version_root() / "runtime"


def suite_root() -> Path:
    raw = os.environ.get("VITALOOM_SUITE_ROOT")
    if raw:
        return Path(raw).resolve()
    return product_version_root().parents[1]


def framecore_root() -> Path:
    raw = os.environ.get("FRAMECORE_ROOT")
    if raw:
        return Path(raw).resolve()
    return suite_root().parents[1]


def application_root() -> Path:
    raw = os.environ.get("VITALOOM_APP_ROOT")
    if raw:
        return Path(raw).resolve()
    if is_frozen_bundle():
        return Path(sys.executable).resolve().parent
    return framecore_root().parent


def resource_root() -> Path:
    export_root = os.environ.get("VITALOOM_EXPORT_ROOT")
    if export_root:
        return Path(export_root).resolve() / "runtime"
    current_runtime = runtime_root()
    if current_runtime.exists():
        return current_runtime
    if is_frozen_bundle():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return runtime_root()


def repo_root() -> Path:
    return resource_root()


def projects_root() -> Path:
    root = application_root() / "workspace" / "projects"
    root.mkdir(parents=True, exist_ok=True)
    return root


def samples_projects_root() -> Path:
    root = projects_root() / "samples"
    root.mkdir(parents=True, exist_ok=True)
    return root


def user_projects_root() -> Path:
    root = projects_root() / "user"
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_sample_projects_for_clone() -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    samples = samples_projects_root()
    if not samples.is_dir():
        return out
    for child in sorted(samples.iterdir()):
        if not child.is_dir() or not (child / "project.json").is_file():
            continue
        label = child.name
        try:
            data = json.loads((child / "project.json").read_text(encoding="utf-8"))
            name = str(data.get("name", "") or "").strip()
            if name:
                label = name
        except (OSError, json.JSONDecodeError):
            pass
        out.append((label, child.name))
    return out


def user_plugins_root() -> Path:
    root = application_root() / "workspace" / "extensions" / "user"
    root.mkdir(parents=True, exist_ok=True)
    return root


def include_legacy_project_roots() -> bool:
    raw = os.environ.get("VITALOOM_INCLUDE_LEGACY_PROJECT_ROOTS", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def include_legacy_plugin_roots() -> bool:
    raw = os.environ.get("VITALOOM_INCLUDE_LEGACY_PLUGIN_ROOTS", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def iter_project_containers(
    *, include_legacy_flat: bool | None = None
) -> List[Path]:
    base = projects_root()
    out: List[Path] = []
    for name in ("samples", "user"):
        sub = base / name
        if sub.is_dir():
            out.append(sub)
    if include_legacy_flat is None:
        include_legacy_flat = include_legacy_project_roots()
    if include_legacy_flat:
        out.append(base)
    return out


def iter_discovered_project_dirs(
    *, include_legacy_flat: bool | None = None
) -> List[Path]:
    base = projects_root()
    skip_at_root = {"samples", "user", "__pycache__"}
    found: List[Path] = []
    seen: set[str] = set()
    for container in iter_project_containers(include_legacy_flat=include_legacy_flat):
        if not container.is_dir():
            continue
        for child in sorted(container.iterdir()):
            if not child.is_dir():
                continue
            if container == base and child.name in skip_at_root:
                continue
            if not (child / "project.json").is_file():
                continue
            key = os.path.normcase(str(child.resolve()))
            if key in seen:
                continue
            seen.add(key)
            found.append(child)
    return found


def system_config_dir() -> Path:
    app_cfg = application_root() / "workspace" / "state" / "system"
    app_cfg.mkdir(parents=True, exist_ok=True)
    if is_frozen_bundle():
        _seed_system_config(app_cfg)
    return app_cfg


def _seed_system_config(target: Path) -> None:
    bundled = resource_root() / "workspace" / "state" / "system"
    if not bundled.is_dir():
        return
    for name in ("editor_config.json", "package_registries.json", "package_policy.json"):
        src = bundled / name
        if not src.is_file() and name == "editor_config.json":
            src = bundled / "editor_config.json.example"
        dst = target / name
        if src.is_file() and not dst.is_file():
            try:
                dst.write_bytes(src.read_bytes())
            except OSError:
                pass


def physical_root_exists(rel: str | Path, *, repo_root: Path | None = None) -> bool:
    rel_norm = str(rel).replace("\\", "/").strip("/")
    if not rel_norm:
        return True
    roots = []
    if repo_root is not None:
        roots.append(Path(repo_root))
    roots.extend([product_version_root(), resource_root(), application_root()])
    for root in roots:
        if (root / rel_norm).exists():
            return True
    if rel_norm.startswith("core/"):
        return importlib.util.find_spec("core") is not None
    return False


def _dedupe_paths(paths: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in paths:
        key = os.path.normcase(os.path.normpath(raw))
        if key in seen:
            continue
        seen.add(key)
        out.append(raw)
    return out


def _collect_user_plugin_dirs(
    base: Path,
    *,
    include_legacy_flat: bool | None = None,
) -> List[str]:
    out: List[str] = []
    if not os.environ.get("VITALOOM_ENABLE_WORKSPACE_EXTENSIONS"):
        return out
    extensions_root = base / "workspace" / "extensions"
    if not extensions_root.is_dir():
        return out
    for name in ("user", "community"):
        sub = extensions_root / name
        if sub.is_dir():
            out.append(str(sub))
    if include_legacy_flat is None:
        include_legacy_flat = include_legacy_plugin_roots()
    if include_legacy_flat:
        for child in sorted(extensions_root.iterdir()):
            if child.is_dir() and child.name not in {"user", "community", "__pycache__"}:
                out.append(str(child))
    return out


def default_plugin_layer_dirs() -> Dict[str, List[str]]:
    app = application_root()
    res = resource_root()
    official = [str(res / "builtin" / "editor_extensions")]
    user_dirs: List[str] = []
    for base in (app, res):
        user_dirs.extend(_collect_user_plugin_dirs(base))
    return {
        "official_mod": _dedupe_paths(official),
        "user_mod": _dedupe_paths(user_dirs),
    }


def editor_version() -> str:
    for base in (application_root(), product_version_root(), resource_root()):
        version_file = base / "VERSION.txt"
        if version_file.is_file():
            try:
                text = version_file.read_text(encoding="utf-8").strip()
                if text:
                    return text.splitlines()[0].strip()
            except OSError:
                pass
    try:
        from core.VitaLoom.project.project_manifest import (
            get_loom_editor_version_from_pyproject,
        )

        return get_loom_editor_version_from_pyproject(application_root())
    except Exception:
        return "1.0.0"


def project_data_root(project_path: str | Path) -> Path:
    return Path(project_path).resolve()


def ensure_cwd_application_root() -> None:
    if is_frozen_bundle():
        try:
            os.chdir(application_root())
        except OSError:
            pass


def is_under_application_root(path: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(application_root().resolve())
        return True
    except ValueError:
        return False
