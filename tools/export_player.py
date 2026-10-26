#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出可运行 Player 目录（含 runtime 包闭包 + project 数据）。"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = SUITE_ROOT / "versions" / "1.0.0"
RUNTIME_ROOT = VERSION_ROOT / "runtime"
for path in (ROOT, RUNTIME_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
os.environ.setdefault("FRAMECORE_ROOT", str(ROOT / "FrameCore"))
os.environ.setdefault("VITALOOM_SUITE_ROOT", str(SUITE_ROOT))
os.environ.setdefault("VITALOOM_PRODUCT_VERSION_ROOT", str(VERSION_ROOT))
os.environ.setdefault("VITALOOM_APP_ROOT", str(ROOT))
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PLAYER_MAIN_TEMPLATE = textwrap.dedent(
    '''\
    """导出包内 Player 入口。"""
    import os
    import sys

    _DIST_ROOT = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("VITALOOM_PLAYER_MODE", "1")
    os.environ.setdefault("VITALOOM_SKIP_HUB", "1")
    os.environ["VITALOOM_EXPORT_ROOT"] = _DIST_ROOT
    os.environ.setdefault("VITALOOM_APP_ROOT", _DIST_ROOT)
    _runtime = os.path.join(_DIST_ROOT, "runtime")
    if _runtime not in sys.path:
        sys.path.insert(0, _runtime)

    if __name__ == "__main__":
        import argparse
        from core.VitaLoom.player.player_shell import run_player_shell, run_player_smoke
        from PyQt6.QtWidgets import QApplication

        parser = argparse.ArgumentParser()
        parser.add_argument("--project", default=os.path.join(_DIST_ROOT, "project"))
        parser.add_argument("--smoke", action="store_true")
        args = parser.parse_args()
        app = QApplication(sys.argv)
        if args.smoke:
            sys.exit(run_player_smoke(app, _runtime, os.path.abspath(args.project)))
        sys.exit(run_player_shell(app, _runtime, os.path.abspath(args.project)))
    '''
)


def _load_presets(project_path: Path) -> List[Dict[str, Any]]:
    preset_file = project_path / "export_presets.json"
    if not preset_file.is_file():
        return [
            {
                "name": "default",
                "platform": "desktop",
                "data_dirs": ["assets", "scenes", "scripts"],
                "output_dir": "dist/export",
            }
        ]
    data = json.loads(preset_file.read_text(encoding="utf-8"))
    presets = data.get("presets", [])
    return presets if isinstance(presets, list) else []


def _copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    elif src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def _copy_runtime_bundle(
    repo_root: Path,
    runtime_out: Path,
    package_ids: List[str],
    catalog: List[Dict[str, Any]],
) -> None:
    _ = (repo_root, package_ids, catalog)
    def _ignore(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if name == "__pycache__" or name.endswith(".pyc")}

    shutil.copytree(RUNTIME_ROOT, runtime_out, dirs_exist_ok=True, ignore=_ignore)
    framecore_out = runtime_out / "FrameCore"
    framecore_out.mkdir(parents=True, exist_ok=True)
    for src in (ROOT / "FrameCore").glob("*.py"):
        shutil.copy2(src, framecore_out / src.name)


def export_project(
    project_path: Path,
    *,
    preset_name: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    repo_root = repo_root or ROOT
    project_path = project_path.resolve()
    pj = project_path / "project.json"
    if not pj.is_file():
        raise FileNotFoundError(f"缺少 project.json: {project_path}")

    from core.VitaLoom.project.asset_index import build_project_asset_index

    asset_index = build_project_asset_index(project_path)
    if not asset_index["export"]["ready"]:
        dependencies = asset_index["dependencies"]
        raise RuntimeError(
            "asset index is not export-ready: "
            f"missing={dependencies['missing_total']}, "
            f"outside_project={dependencies['outside_project_total']}, "
            f"invalid={dependencies['invalid_total']}, "
            f"malformed_scenes={len(dependencies['malformed_scenes'])}"
        )

    from core.VitaLoom.project.project_manifest import (
        get_loom_editor_version_from_pyproject,
        load_package_catalog,
    )
    from core.VitaLoom.project.runtime_packages import collect_runtime_package_ids
    from core.VitaLoom.suite.project_lock import (
        build_project_lock,
        resolve_project_runtime,
    )
    from core.Lotucosm.script_trust_policy import validate_project_script_trust_sources
    from FrameCore.project_lock import (
        load_project_lock,
        project_lock_schema_error,
        project_script_trust_lock_matches,
    )

    project_data = json.loads(pj.read_text(encoding="utf-8"))
    source_lock_path = project_path / "project.lock.json"
    source_lock_data_for_manifest = load_project_lock(project_path)
    if not source_lock_path.is_file():
        lock_source_admission = "missing"
    elif source_lock_data_for_manifest is None:
        lock_source_admission = "invalid"
    elif project_lock_schema_error(source_lock_data_for_manifest):
        lock_source_admission = "unsupported_schema"
    elif "schema_version" not in source_lock_data_for_manifest:
        lock_source_admission = "legacy"
    else:
        lock_source_admission = "current"
    if isinstance(project_data, dict) and "script_trust" in project_data:
        source_validation = validate_project_script_trust_sources(project_path)
        if not source_validation.get("trusted"):
            raise RuntimeError(
                "project script trust source validation failed: "
                + str(source_validation.get("reason", "unknown"))
            )
    runtime_resolution = resolve_project_runtime(project_path, repo_root=repo_root)
    if runtime_resolution.has_blocking_issues:
        raise RuntimeError(
            "project runtime is not exportable: "
            + (
                runtime_resolution.blocking_issue_summary
                or runtime_resolution.lock_status_text
            )
        )
    catalog = load_package_catalog(repo_root)
    runtime_pkg_ids = collect_runtime_package_ids(
        project_data, catalog, repo_root=str(repo_root)
    )
    if preset_name is None:
        presets_list = _load_presets(project_path)
        if presets_list and presets_list[0].get("packages"):
            preset_pkg = presets_list[0].get("packages")
            if isinstance(preset_pkg, list):
                runtime_pkg_ids = list(dict.fromkeys([*preset_pkg, *runtime_pkg_ids]))

    game_name = str(project_data.get("name") or project_path.name)
    presets = _load_presets(project_path)
    preset = presets[0]
    if preset_name:
        for p in presets:
            if str(p.get("name")) == preset_name:
                preset = p
                break

    out_rel = str(preset.get("output_dir") or "dist/export")
    out_root = (project_path / out_rel).resolve() if not os.path.isabs(out_rel) else Path(out_rel)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in game_name)[:48]
    dist_dir = out_root / safe_name
    project_out = dist_dir / "project"
    runtime_out = dist_dir / "runtime"

    # Validate and prepare the lock before replacing an existing export.
    source_lock = project_path / "project.lock.json"
    source_lock_data: dict[str, Any] | None = None
    if source_lock.is_file():
        source_lock_data = json.loads(source_lock.read_text(encoding="utf-8"))
        if "script_trust" in project_data and not project_script_trust_lock_matches(
            project_path, source_lock_data, repo_root=repo_root
        ):
            raise RuntimeError("project.lock.json script trust digest is stale or missing")
    else:
        source_lock_data = build_project_lock(project_data, repo_root=repo_root)

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    project_out.mkdir(parents=True)
    runtime_out.mkdir(parents=True)

    shutil.copy2(pj, project_out / "project.json")
    entry_scene = preset.get("entry_scene")
    if entry_scene and isinstance(project_data, dict):
        project_data = dict(project_data)
        project_data["active_scene"] = str(entry_scene)
        (project_out / "project.json").write_text(
            json.dumps(project_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if source_lock.is_file():
        shutil.copy2(source_lock, project_out / "project.lock.json")
    else:
        (project_out / "project.lock.json").write_text(
            json.dumps(source_lock_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    data_dirs = preset.get("data_dirs") or ["assets", "scenes", "scripts"]
    if not isinstance(data_dirs, list):
        data_dirs = ["assets", "scenes", "scripts"]
    for sub in data_dirs:
        src = project_path / str(sub)
        if src.is_dir():
            shutil.copytree(src, project_out / str(sub))

    _copy_runtime_bundle(repo_root, runtime_out, runtime_pkg_ids, catalog)

    (dist_dir / "player_main.py").write_text(PLAYER_MAIN_TEMPLATE, encoding="utf-8")

    launch_bat = dist_dir / "launch.bat"
    launch_bat.write_text(
        "@echo off\nchcp 65001 >nul\ncd /d \"%~dp0\"\n"
        "set PYTHONPATH=%~dp0runtime\n"
        f"python \"%~dp0player_main.py\" --project \"%~dp0project\"\n"
        "pause\n",
        encoding="utf-8",
    )
    launch_sh = dist_dir / "launch.sh"
    launch_sh.write_text(
        "#!/bin/sh\n"
        "cd \"$(dirname \"$0\")\"\n"
        "export PYTHONPATH=\"$(pwd)/runtime\"\n"
        "exec python \"$(pwd)/player_main.py\" --project \"$(pwd)/project\"\n",
        encoding="utf-8",
    )

    editor_ver = get_loom_editor_version_from_pyproject(repo_root)
    meta = {
        "project_name": game_name,
        "source_project": str(project_path),
        "preset": preset.get("name"),
        "loom_editor_version": editor_ver,
        "suite": {
            "id": runtime_resolution.suite_id,
            "version": runtime_resolution.suite_version,
        },
        "product": {
            "id": runtime_resolution.product_id,
            "version": runtime_resolution.product_version,
            "lock_status": runtime_resolution.lock_status_text,
        },
        "lock": {
            "source_admission": lock_source_admission,
            "runtime_status": runtime_resolution.lock_status_text,
            "runtime_admission": runtime_resolution.lock_admission_code,
        },
        "resolved_capabilities": runtime_resolution.resolved_capabilities,
        "runtime_packages": runtime_pkg_ids,
        "asset_index": {
            "schema_version": asset_index["schema_version"],
            "index_revision": asset_index["index_revision"],
            "asset_count": asset_index["asset_count"],
            "file_count": asset_index["file_count"],
            "dependency_edges": asset_index["dependencies"]["total_edges"],
            "warnings": asset_index["export"]["warnings"],
        },
        "packages": project_data.get("required_packages", []),
    }
    (dist_dir / "export_manifest.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return dist_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="导出 VitaLoom Player 运行目录")
    parser.add_argument("project", help="工程路径（含 project.json）")
    parser.add_argument("--preset", default=None, help="export_presets.json 中的预设名")
    args = parser.parse_args()
    try:
        out = export_project(Path(args.project), preset_name=args.preset)
    except Exception as exc:
        print(f"导出失败: {exc}", file=sys.stderr)
        return 1
    print(f"导出完成: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
