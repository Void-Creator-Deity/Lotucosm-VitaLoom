#!/usr/bin/env python3
# -*- coding: utf-8
"""使用 PyInstaller 打包 VitaLoom Hub + 编辑器为 Windows exe。

用法:
  python tools/build_exe.py              # 目录版 dist/FrameCore/FrameCore.exe（推荐）
  python tools/build_exe.py --onefile    # 单文件 exe（启动较慢）
  python tools/build_exe.py --console    # 保留控制台便于排错

依赖: pip install pyinstaller
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "FrameCore" / "plugins" / "lotucosm-vitaloom"
VERSION_ROOT = SUITE_ROOT / "versions" / "1.0.0"
RUNTIME_ROOT = VERSION_ROOT / "runtime"
APP_NAME = "FrameCore"
APP_EXE = f"{APP_NAME}.exe"
DIST_APP = ROOT / "dist" / APP_NAME
BUILD = ROOT / "build" / "pyinstaller"
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 打包后必须能在产品 runtime 中找到的官方插件数量。
EXPECTED_OFFICIAL_PLUGINS = 21


def _data_sep() -> str:
    return ";" if os.name == "nt" else ":"


def _add_data(src: Path, dest: str) -> str:
    if not src.exists():
        return ""
    return f"{src.resolve()}{_data_sep()}{dest}"


def _read_project_version() -> str:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return "1.0.0"
    try:
        text = pyproject.read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return "1.0.0"


def _try_release_locked_exe() -> None:
    """Windows：若 dist 内 exe 正在运行会导致 PyInstaller 无法覆盖。"""
    exe = DIST_APP / APP_EXE
    if not exe.is_file():
        return
    try:
        subprocess.run(
            ["taskkill", "/IM", APP_EXE, "/F"],
            check=False,
            capture_output=True,
        )
    except Exception:
        pass


def build(*, onefile: bool, console: bool) -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("请先安装 PyInstaller: pip install pyinstaller")
        return 1

    if os.name == "nt":
        _try_release_locked_exe()

    datas: list[str] = []
    for item in (
        ("FrameCore", "FrameCore"),
        ("main.py", "."),
        ("player.py", "."),
        ("workspace", "workspace"),
    ):
        spec = _add_data(ROOT / item[0], item[1])
        if spec:
            datas.append(spec)

    hidden = [
        "numpy",
        "pygame",
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "uuid",
    ]

    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(ROOT / "main.py"),
        "--name",
        APP_NAME,
        "--noconfirm",
        "--clean",
        f"--distpath={ROOT / 'dist'}",
        f"--workpath={BUILD}",
        f"--specpath={BUILD}",
        f"--paths={RUNTIME_ROOT}",
        "--collect-all",
        "PyQt6",
        "--collect-submodules",
        "FrameCore",
        "--collect-submodules",
        "core",
        "--collect-submodules",
        "builtin",
        "--exclude-module",
        "tkinter",
    ]
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    if not console:
        cmd.append("--windowed")
    else:
        cmd.append("--console")

    for d in datas:
        cmd.extend(["--add-data", d])
    for h in hidden:
        cmd.extend(["--hidden-import", h])

    print(">>> PyInstaller 命令:")
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        return rc

    dest_root = ROOT / "dist" if onefile else DIST_APP
    _post_stage_writable_runtime(dest_root)
    _post_copy_projects(onefile)
    _ensure_dist_project_layout(dest_root)
    _create_dist_user_aliases(dest_root)
    _write_version_file(dest_root)
    _write_dist_readme(onefile)

    ok, issues = verify_dist(dest_root, onefile=onefile)
    if not ok:
        print("\n[WARN] 打包校验未完全通过:")
        for item in issues:
            print(f"  - {item}")
        return 2

    out = dest_root / APP_EXE
    _write_build_folder_warning()
    print(f"\n[OK] 打包完成: {out}")
    print(f"[!!] 请运行 dist\\{APP_NAME}\\{APP_EXE} ，不要运行 build\\pyinstaller\\ 下的 exe")
    return 0


def _write_build_folder_warning() -> None:
    """build/ 仅为 PyInstaller 中间目录，缺少 _internal 无法单独运行。"""
    note = BUILD / APP_NAME / "请勿在此运行.txt"
    try:
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            f"此目录是 PyInstaller 编译中间产物，不能单独运行 {APP_EXE}。\n"
            "缺少完整的 _internal 运行时，会报错 Failed to load Python DLL。\n\n"
            "请使用打包输出目录：\n"
            f"  {DIST_APP / APP_EXE}\n\n"
            "重新打包：在项目根目录运行 python tools/build_exe.py\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _post_stage_writable_runtime(dest_root: Path) -> None:
    """在 exe 旁布置可写运行时目录（用户插件、配置、社区扩展位）。"""
    import json

    plugins_dest = dest_root / "workspace" / "extensions"
    (plugins_dest / "user").mkdir(parents=True, exist_ok=True)
    community_dest = plugins_dest / "community"
    community_dest.mkdir(parents=True, exist_ok=True)

    src_plugins = ROOT / "workspace" / "extensions"
    if src_plugins.is_dir():
        for item in src_plugins.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            target = plugins_dest / item.name
            if target.exists():
                continue
            if item.is_dir():
                shutil.copytree(
                    item,
                    target,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
                )
            else:
                shutil.copy2(item, target)
        print(f"已布置 workspace/extensions/ -> {plugins_dest}")

    sys_dest = dest_root / "workspace" / "state" / "system"
    sys_dest.mkdir(parents=True, exist_ok=True)
    src_sys = ROOT / "workspace" / "state" / "system"
    for name in ("package_registries.json", "package_policy.json"):
        src = src_sys / name
        if src.is_file():
            shutil.copy2(src, sys_dest / name)
    editor_cfg = sys_dest / "editor_config.json"
    editor_cfg.write_text(
        json.dumps(
            {
                "recent_projects": [],
                "last_opened_project": None,
                "editor_installs": [],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已布置 workspace/state/system/ -> {sys_dest}")


def _post_copy_projects(onefile: bool) -> None:
    """复制示范工程到 exe 旁（可写）。"""
    src = ROOT / "workspace" / "projects"
    if not src.is_dir():
        return
    if onefile:
        dest_root = ROOT / "dist"
    else:
        dest_root = DIST_APP
    dest = dest_root / "workspace" / "projects"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
    )
    print(f"已复制 workspace/projects/ -> {dest}")


def _ensure_dist_project_layout(dest_root: Path) -> None:
    """确保发行版含 workspace/projects/samples 与 workspace/projects/user。"""
    for sub in ("samples", "user"):
        (dest_root / "workspace" / "projects" / sub).mkdir(parents=True, exist_ok=True)
    readme = dest_root / "workspace" / "projects" / "user" / "README.txt"
    if not readme.is_file():
        readme.write_text(
            "在此目录新建或导入你的工程（Hub 默认保存位置）。\n",
            encoding="utf-8",
        )


def _link_or_copy_alias(dest_root: Path, alias_name: str, target_rel: str) -> None:
    """创建用户友好别名目录；Windows 优先 junction，失败则拷贝。"""
    alias = dest_root / alias_name
    target = dest_root / target_rel
    if not target.is_dir():
        return
    if alias.exists():
        if alias.is_symlink() or alias.is_dir():
            try:
                is_junction = getattr(os.path, "isjunction", lambda _p: False)
                if alias.is_symlink() or is_junction(str(alias)):
                    alias.unlink()
                elif alias.is_dir():
                    shutil.rmtree(alias)
            except OSError:
                pass
    if os.name == "nt":
        try:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(target.resolve())],
                check=True,
                capture_output=True,
            )
            print(f"已创建别名 {alias_name}/ -> {target_rel}")
            return
        except (OSError, subprocess.CalledProcessError):
            pass
    if not alias.exists():
        shutil.copytree(
            target,
            alias,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        print(f"已复制别名 {alias_name}/ <- {target_rel}")


def _create_dist_user_aliases(dest_root: Path) -> None:
    """Samples/、Extensions/ 为用户可见的通俗目录名。"""
    _link_or_copy_alias(dest_root, "Samples", "workspace/projects/samples")
    _link_or_copy_alias(dest_root, "Extensions", "workspace/extensions/user")


def _write_version_file(dest_root: Path) -> None:
    version = _read_project_version()
    (dest_root / "VERSION.txt").write_text(version + "\n", encoding="utf-8")


def verify_dist(dest_root: Path, *, onefile: bool) -> tuple[bool, list[str]]:
    """校验 dist 是否包含插件、包索引与 Qt 运行时。"""
    issues: list[str] = []
    exe = dest_root / APP_EXE
    if not exe.is_file():
        issues.append(f"缺少主程序: {exe}")

    internal = dest_root / "_internal"
    if not onefile and not internal.is_dir():
        issues.append(f"缺少 _internal 目录: {internal}")

    search_roots = [dest_root]
    if internal.is_dir():
        search_roots.insert(0, internal)

    plugin_count = 0
    has_index = False
    has_data_system = False
    has_plugin_manifest = False
    has_main_entry = False
    has_player_entry = False
    qt_dll_count = 0
    for base in search_roots:
        suite_root = base / "FrameCore" / "plugins" / "lotucosm-vitaloom"
        version_root = suite_root / "versions" / "1.0.0"
        runtime_root = version_root / "runtime"
        ext_dir = runtime_root / "builtin" / "editor_extensions"
        if ext_dir.is_dir():
            plugin_count = max(plugin_count, len(list(ext_dir.glob("*_plugin.py"))))
        index = runtime_root / "builtin" / "package_index.json"
        if index.is_file():
            has_index = True
        if (base / "workspace" / "state" / "system").is_dir():
            has_data_system = True
        if (suite_root / "plugin_manifest.json").is_file():
            has_plugin_manifest = True
        if (base / "main.py").is_file():
            has_main_entry = True
        if (base / "player.py").is_file():
            has_player_entry = True
        qt_dll_count += len(list(base.glob("PyQt6/**/*.dll")))

    if plugin_count < EXPECTED_OFFICIAL_PLUGINS:
        issues.append(
            f"官方插件不足: 期望>={EXPECTED_OFFICIAL_PLUGINS}, 实际={plugin_count}"
        )
    if not has_index:
        issues.append("缺少 product runtime builtin/package_index.json")
    if not has_data_system:
        issues.append("缺少 workspace/state/system 配置目录")
    if qt_dll_count < 10:
        issues.append(f"PyQt6 DLL 过少: {qt_dll_count}")

    if not has_plugin_manifest:
        issues.append("missing FrameCore plugin_manifest.json")
    if not has_main_entry:
        issues.append("missing main.py Suite entrypoint file")
    if not has_player_entry:
        issues.append("missing player.py Suite entrypoint file")
    _check_dist_suite_registry(search_roots, issues)

    side_plugins = dest_root / "workspace" / "extensions"
    if not side_plugins.is_dir():
        issues.append(f"exe 旁缺少可写 workspace/extensions/ 目录: {side_plugins}")
    elif not (side_plugins / "community").is_dir():
        issues.append("exe 旁缺少 workspace/extensions/community/（用户扩展安装位）")

    if not (dest_root / "workspace" / "projects").is_dir():
        issues.append("缺少工程目录 workspace/projects/")
    if not (dest_root / "workspace" / "projects" / "samples").is_dir():
        issues.append("缺少示范工程目录 workspace/projects/samples/")
    if not (dest_root / "workspace" / "projects" / "user").is_dir():
        issues.append("缺少用户工程目录 workspace/projects/user/")
    if not (dest_root / "workspace" / "extensions" / "user").is_dir():
        issues.append("缺少用户扩展目录 workspace/extensions/user/")
    if not (dest_root / "Samples").exists():
        issues.append("缺少用户别名目录 Samples/")
    if not (dest_root / "Extensions").exists():
        issues.append("缺少用户别名目录 Extensions/")
    if not (dest_root / "VERSION.txt").is_file():
        issues.append("缺少 VERSION.txt")

    editor_cfg = dest_root / "workspace" / "state" / "system" / "editor_config.json"
    if editor_cfg.is_file():
        try:
            import json

            cfg = json.loads(editor_cfg.read_text(encoding="utf-8"))
            recent = cfg.get("recent_projects", [])
            if recent:
                issues.append(
                    f"editor_config.json 应无预填 recent_projects，实际 {len(recent)} 条"
                )
        except Exception as exc:
            issues.append(f"无法解析 editor_config.json: {exc}")
    else:
        issues.append("缺少 workspace/state/system/editor_config.json")

    return len(issues) == 0, issues


def _check_dist_suite_registry(search_roots: list[Path], issues: list[str]) -> None:
    """Validate FrameCore plugin registry files copied into dist."""
    registry_root = None
    for base in search_roots:
        candidate = base / "FrameCore" / "plugins" / "lotucosm-vitaloom"
        if (candidate / "plugin_manifest.json").is_file() and (candidate / "versions").is_dir():
            registry_root = candidate
            break
    if registry_root is None:
        return
    try:
        plugin = json.loads((registry_root / "plugin_manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"无法解析 dist plugin_manifest.json: {exc}")
        return
    if not isinstance(plugin, dict):
        issues.append("dist plugin_manifest.json root must be object")
        return
    product_id = str(plugin.get("product_id", "") or plugin.get("plugin_id", "") or "").strip()
    if not product_id:
        issues.append("dist plugin_manifest.json missing product_id/plugin_id")
        product_id = "lotucosm-vitaloom"
    suite_entry = str(plugin.get("entry", "") or "").split(" ", 1)[0]
    if suite_entry and not (registry_root / suite_entry).exists():
        issues.append(f"dist plugin entry missing: {suite_entry}")
    catalog = str(plugin.get("capability_catalog", "") or "")
    if catalog and not (registry_root / catalog).is_file():
        issues.append(f"dist capability catalog missing: {catalog}")

    versions = plugin.get("versions", [])
    if not isinstance(versions, list) or not versions:
        issues.append(f"dist plugin {product_id} versions must be non-empty")
        return
    default_version = str(plugin.get("default_version", "") or versions[0]).strip()
    if default_version not in {str(v).strip() for v in versions}:
        issues.append(f"dist plugin {product_id} default_version not in versions")
    for version in [str(v or "").strip() for v in versions if str(v or "").strip()]:
            version_path = registry_root / "versions" / version / "version_manifest.json"
            dist_version_root = registry_root / "versions" / version
            if not version_path.is_file():
                issues.append(f"dist version manifest missing: {product_id}@{version}")
                continue
            try:
                vdata = json.loads(version_path.read_text(encoding="utf-8"))
            except Exception as exc:
                issues.append(f"无法解析 dist version manifest {product_id}@{version}: {exc}")
                continue
            if str(vdata.get("version", "") or "") != version:
                issues.append(f"dist version manifest mismatch: {product_id}@{version}")
            entrypoints = vdata.get("entrypoints", {})
            if not isinstance(entrypoints, dict) or not entrypoints:
                issues.append(f"dist version {product_id}@{version} entrypoints missing")
            else:
                for name, command in sorted(entrypoints.items()):
                    entry_file = str(command or "").split(" ", 1)[0]
                    if not entry_file or not (dist_version_root / entry_file).exists():
                        issues.append(
                            f"dist version {product_id}@{version} entrypoint {name} missing: {command}"
                        )
            index = str(vdata.get("builtin_capability_index", "") or "")
            if index and not (dist_version_root / index).is_file():
                issues.append(
                    f"dist version {product_id}@{version} capability index missing: {index}"
                )
            roots = vdata.get("physical_roots", [])
            if isinstance(roots, list):
                for rel in [str(r or "").replace("\\", "/").strip("/") for r in roots]:
                    if not rel:
                        continue
                    if not (dist_version_root / rel).exists():
                        issues.append(
                            f"dist version {product_id}@{version} physical root missing: {rel}"
                        )
            else:
                issues.append(f"dist version {product_id}@{version} physical_roots must be list")


def _write_dist_readme(onefile: bool) -> None:
    dest_root = ROOT / "dist" if onefile else DIST_APP
    version = _read_project_version()
    readme = dest_root / "README.txt"
    readme.write_text(
        f"""FrameCore 启动器 · 打包版 v{version}

【启动】
  双击 {APP_EXE}：进入 FrameCore，再加载 lotucosm-vitaloom 的 Hub。
  Hub 负责项目、产品版本与 lock 状态；具体编辑器由产品版本 runtime 启动。

【两种运行模式（同一 exe）】
  {APP_EXE}                          Suite Hub 项目管理器（默认）
  {APP_EXE} --editor --project PATH  织机编辑器（由 Hub 自动调用）

【用户优先看的目录】
  Samples/      示例项目，来自 workspace/projects/samples/
  Extensions/   用户扩展插件，来自 workspace/extensions/user/

【运行时目录（程序内部使用，勿删）】
  {APP_EXE}          FrameCore 主入口
  _internal/         FrameCore、Suite 插件包、产品 runtime、Qt 运行时
  workspace/projects/user/ 你的项目默认保存位置
  workspace/extensions/community/ 社区插件位置
  workspace/state/system/       用户配置

【分发】
  分发时请打包整个 FrameCore 文件夹，不要只复制单个 exe。
""",
        encoding="utf-8",
    )

def main() -> int:
    parser = argparse.ArgumentParser(description="打包 FrameCore 启动器 exe")
    parser.add_argument("--onefile", action="store_true", help="单文件 exe（较慢）")
    parser.add_argument("--console", action="store_true", help="显示控制台窗口")
    args = parser.parse_args()
    return build(onefile=args.onefile, console=args.console)


if __name__ == "__main__":
    raise SystemExit(main())
