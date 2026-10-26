# -*- coding: utf-8 -*-
"""Launch product-version Editor processes from the Suite Hub."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PyQt6.QtCore import QProcess, QProcessEnvironment
    from PyQt6.QtWidgets import QWidget

from FrameCore.product_registry import ProductVersion, load_product_registry
from FrameCore.project_lock import resolve_project_runtime


DEFAULT_PRODUCT_ID = "lotucosm-vitaloom"
MAX_FAILURE_OUTPUT_CHARS = 4000


def _app_root() -> Path:
    raw = os.environ.get("VITALOOM_APP_ROOT")
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[4]


def _suite_root() -> Path:
    raw = os.environ.get("VITALOOM_SUITE_ROOT")
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[1]


def _select_product_version(
    product_id: str = DEFAULT_PRODUCT_ID,
    product_version: str = "",
) -> ProductVersion:
    """Select an explicit product version; a lock may not silently fall back."""
    registry = load_product_registry(_suite_root())
    version = (
        registry.get_version(product_id, product_version)
        if product_version
        else registry.get_default_version(product_id)
    )
    if version is None:
        requested = f" {product_version}" if product_version else " default"
        raise RuntimeError(f"missing product version: {product_id}{requested}")
    return version


def _editor_env(version: ProductVersion) -> "QProcessEnvironment":
    from PyQt6.QtCore import QProcessEnvironment

    env = QProcessEnvironment.systemEnvironment()
    app_root = str(_app_root())
    resource_root = app_root
    env.insert("FRAMECORE_ROOT", str(_app_root() / "FrameCore"))
    env.insert("VITALOOM_SUITE_ROOT", str(_suite_root()))
    env.insert("VITALOOM_PRODUCT_VERSION_ROOT", str(version.version_root))
    env.insert("VITALOOM_APP_ROOT", app_root)
    runtime = str(version.runtime_root)
    current_pythonpath = env.value("PYTHONPATH")
    pythonpath_entries = [runtime, app_root, resource_root]
    if current_pythonpath:
        pythonpath_entries.append(current_pythonpath)
    env.insert(
        "PYTHONPATH",
        os.pathsep.join(pythonpath_entries),
    )
    return env


def editor_subprocess_command(project_path: str) -> tuple[str, list[str], ProductVersion]:
    """Build an Editor subprocess command from the Project World lock resolution."""
    abspath = os.path.abspath(project_path)
    resolved = resolve_project_runtime(abspath, repo_root=_app_root())
    if resolved.has_blocking_issues:
        raise RuntimeError(
            resolved.blocking_issue_summary
            or f"project runtime is not launchable: {resolved.lock_status_text}"
        )
    version = _select_product_version(resolved.product_id, resolved.product_version)
    command = version.entrypoints.get("editor", "runtime/main.py --editor")
    parts = command.split()
    script = version.version_root / parts[0]
    return sys.executable, [str(script), *parts[1:], "--project", abspath], version


def start_editor_subprocess(
    project_path: str,
    *,
    parent: Optional["QWidget"] = None,
) -> "QProcess":
    from PyQt6.QtCore import QProcess

    program, args, version = editor_subprocess_command(project_path)
    proc = QProcess(parent)
    proc.setWorkingDirectory(str(version.runtime_root))
    proc.setProgram(program)
    proc.setArguments([str(a) for a in args])
    proc.setProcessEnvironment(_editor_env(version))
    # The Hub must be able to explain startup failures. Editor diagnostics are
    # useful whether they are written to stdout or stderr, so keep one stream.
    proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
    proc.start()
    if proc.error() == QProcess.ProcessError.FailedToStart:
        detail = proc.errorString() or "FailedToStart"
        raise RuntimeError(f"cannot start editor: {detail}\n{program} {' '.join(args)}")
    return proc


def editor_launch_log_path() -> Path:
    """Return the single durable location for Editor launch diagnostics."""
    return _app_root() / "workspace" / "state" / "logs" / "editor-launch.log"


def decode_process_output(raw: bytes) -> str:
    if not raw:
        return ""
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding).replace("\r\n", "\n").strip()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n").strip()


def failure_output_excerpt(output: str, limit: int = MAX_FAILURE_OUTPUT_CHARS) -> str:
    """Keep the end of the output, where Python and Qt expose the real error."""
    text = (output or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return "…（仅显示最后一部分）\n" + text[-limit:].lstrip()


def write_editor_launch_log(
    *,
    project_path: str,
    exit_code: int,
    output: str,
) -> Path:
    path = editor_launch_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = (
        f"[{timestamp}] project={project_path}\n"
        f"exit_code={exit_code}\n"
        f"output:\n{output or '(no process output)'}\n"
        f"{'-' * 72}\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(body)
    return path


def launch_editor_subprocess_blocking(
    project_path: str,
    *,
    parent: Optional["QWidget"] = None,
) -> int:
    import subprocess

    program, args, version = editor_subprocess_command(project_path)
    env = os.environ.copy()
    env.update(
        {
            "FRAMECORE_ROOT": str(_app_root() / "FrameCore"),
            "VITALOOM_SUITE_ROOT": str(_suite_root()),
            "VITALOOM_PRODUCT_VERSION_ROOT": str(version.version_root),
            "VITALOOM_APP_ROOT": str(_app_root()),
            "PYTHONPATH": str(version.runtime_root)
            + os.pathsep
            + str(_app_root())
            + os.pathsep
            + env.get("PYTHONPATH", ""),
        }
    )
    result = subprocess.run(
        [program, *args],
        cwd=str(version.runtime_root),
        env=env,
        check=False,
    )
    if result.returncode != 0 and parent is not None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(
            parent,
            "编辑器退出",
            f"织机编辑器异常退出，代码 {result.returncode}",
        )
    return int(result.returncode)
