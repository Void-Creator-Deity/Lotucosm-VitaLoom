# -*- coding: utf-8 -*-
"""Lotucosm-VitaLoom product-version Editor entrypoint."""
from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path


if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


RUNTIME_ROOT = Path(__file__).resolve().parent
VERSION_ROOT = Path(
    os.environ.get("VITALOOM_PRODUCT_VERSION_ROOT") or RUNTIME_ROOT.parent
).resolve()
SUITE_ROOT = Path(
    os.environ.get("VITALOOM_SUITE_ROOT") or VERSION_ROOT.parents[1]
).resolve()
APP_ROOT = Path(
    os.environ.get("VITALOOM_APP_ROOT") or SUITE_ROOT.parents[2]
).resolve()

os.environ.setdefault("VITALOOM_PRODUCT_VERSION_ROOT", str(VERSION_ROOT))
os.environ.setdefault("VITALOOM_SUITE_ROOT", str(SUITE_ROOT))
os.environ.setdefault("FRAMECORE_ROOT", str(APP_ROOT / "FrameCore"))
os.environ.setdefault("VITALOOM_APP_ROOT", str(APP_ROOT))

for path in (str(RUNTIME_ROOT), str(APP_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


from core.VitaLoom.core.bundle_paths import ensure_cwd_application_root, resource_root
from core.VitaLoom.suite.runtime_bootstrap import bootstrap_suite_runtime


def _parse_cli_project_path() -> str | None:
    argv = sys.argv[1:]
    if "--project" in argv:
        idx = argv.index("--project")
        if idx + 1 < len(argv):
            return os.path.abspath(argv[idx + 1])
    return None


def _format_runtime_version() -> str:
    runtime = bootstrap_suite_runtime(resource_root())
    return (
        f"{runtime.suite.display_name or runtime.suite.suite_id} "
        f"{runtime.suite.version} / "
        f"{runtime.product_version.product_id} "
        f"{runtime.product_version.version}"
    )


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def _editor_smoke_observation_failure(observation: object) -> str | None:
    """Return a deterministic read-model failure for an unusable Host snapshot."""

    if not isinstance(observation, Mapping):
        return "plugin observation is unavailable or malformed"

    status = observation.get("status")
    if status == "unavailable":
        return "plugin host is unavailable"
    if status not in {"ready", "degraded"}:
        return "plugin observation status is malformed"

    for field in ("discovery_errors", "failed_plugins"):
        if not isinstance(observation.get(field), Mapping):
            return f"plugin observation {field} is malformed"

    counts = observation.get("counts")
    if not isinstance(counts, Mapping):
        return "plugin observation counts is malformed"
    for field in ("active", "catalog"):
        value = counts.get(field)
        if type(value) is not int or value < 0:
            return f"plugin observation counts.{field} is malformed"
    return None

def _report_editor_smoke_observation(observation: object, runtime: object) -> int:
    """Print the smoke-only public Host read-model and return its exit status."""

    observation_failure = _editor_smoke_observation_failure(observation)
    if observation_failure:
        print(f"Editor smoke FAILED: {observation_failure}")
        return 1

    discovery_errors = observation["discovery_errors"]
    failed_plugins = observation["failed_plugins"]
    if discovery_errors or failed_plugins:
        print("Editor smoke FAILED:")
        for path, error in sorted(discovery_errors.items(), key=lambda item: str(item[0])):
            print(f"  discovery {path}: {error}")
        for plugin, error in sorted(failed_plugins.items(), key=lambda item: str(item[0])):
            print(f"  load {plugin}: {error}")
        return 1

    counts = observation["counts"]
    print(
        "Editor smoke OK: "
        f"suite={runtime.suite.suite_id} "
        f"product={runtime.product_version.product_id}@{runtime.product_version.version} "
        f"plugins={counts['active']}/{counts['catalog']}"
    )
    return 0

def _report_editor_smoke_host_observation(host: object, runtime: object) -> int:
    """Convert a public Host observation outage into a smoke failure."""

    try:
        observation = host.observe_plugins()
    except Exception:
        print("Editor smoke FAILED: plugin observation is unavailable or malformed")
        return 1
    return _report_editor_smoke_observation(observation, runtime)

def _run_editor_smoke() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    runtime = bootstrap_suite_runtime(resource_root())
    old_state_home = os.environ.get("VITALOOM_STATE_HOME")
    old_skip_auto_open = os.environ.get("VITALOOM_SKIP_AUTO_OPEN")
    with tempfile.TemporaryDirectory(prefix="vitaloom_editor_smoke_") as tmp:
        from core.VitaLoom.core import bundle_paths
        from core.VitaLoom.project.project_world_host_composition import (
            dispose_project_world_host_if_idle,
        )

        tmp_path = Path(tmp)
        os.environ["VITALOOM_STATE_HOME"] = str(tmp_path / "state")
        os.environ["VITALOOM_SKIP_AUTO_OPEN"] = "1"
        original_system_config_dir = bundle_paths.system_config_dir
        bundle_paths.system_config_dir = lambda: tmp_path / "workspace" / "state" / "system"
        if not dispose_project_world_host_if_idle():
            raise RuntimeError("Editor smoke requires an idle Project World Host")
        kernel = None
        try:
            from PyQt6 import QtWidgets
            from core.VitaLoom.editor_launcher import default_plugin_layers
            from core.VitaLoom.kernel import EditorKernel
            from core.VitaLoom.ui.design_tokens import apply_app_baseline

            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
            apply_app_baseline(app)
            kernel = EditorKernel()
            kernel.load_plugins_layered(default_plugin_layers(str(resource_root())))
            app.processEvents()
            from core.VitaLoom.core.plugin_host_capabilities import resolve_plugin_host

            host = resolve_plugin_host(kernel.editor_context)
            return _report_editor_smoke_host_observation(host, runtime)
        finally:
            if kernel is not None:
                try:
                    kernel.close()
                    app = QtWidgets.QApplication.instance()
                    if app is not None:
                        app.processEvents()
                except Exception:
                    __import__("logging").getLogger(__name__).debug("Ignored recoverable exception.", exc_info=True)
            if not dispose_project_world_host_if_idle():
                raise RuntimeError(
                    "Editor smoke leaked an active Project World Host lease"
                )
            bundle_paths.system_config_dir = original_system_config_dir
            _restore_env("VITALOOM_STATE_HOME", old_state_home)
            _restore_env("VITALOOM_SKIP_AUTO_OPEN", old_skip_auto_open)


def main() -> None:
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "command":
            from core.VitaLoom.commands.cli import main as command_main

            raise SystemExit(command_main(sys.argv[2:]))
        if "--version" in sys.argv[1:]:
            print(_format_runtime_version())
            return
        if "--smoke-editor" in sys.argv[1:]:
            raise SystemExit(_run_editor_smoke())

        ensure_cwd_application_root()
        runtime = bootstrap_suite_runtime(resource_root())
        from PyQt6 import QtWidgets
        from core.VitaLoom.editor_launcher import launch_editor
        from core.VitaLoom.ui.design_tokens import apply_app_baseline

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        apply_app_baseline(app)
        print(
            "VitaLoom Editor starting: "
            f"{runtime.product_version.product_id}@{runtime.product_version.version}"
        )
        raise SystemExit(
            launch_editor(
                app,
                str(resource_root()),
                project_path=_parse_cli_project_path(),
                use_splash=True,
            )
        )
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: failed to start VitaLoom product runtime: {exc}")
        __import__("logging").getLogger(__name__).exception(
            "Failed to start VitaLoom product runtime"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
