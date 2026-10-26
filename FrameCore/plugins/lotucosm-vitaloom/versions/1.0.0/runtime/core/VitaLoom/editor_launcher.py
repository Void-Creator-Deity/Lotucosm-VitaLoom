# -*- coding: utf-8 -*-
"""Launch the product-version Editor kernel."""
from __future__ import annotations

import logging
import os

from PyQt6.QtWidgets import QApplication


logger = logging.getLogger(__name__)


def default_plugin_layers(_repo_root: str) -> dict[str, list[str]]:
    from core.VitaLoom.core.bundle_paths import default_plugin_layer_dirs

    return default_plugin_layer_dirs()


def _require_application_event_loop(app: object) -> None:
    """Require the minimal event-loop capability Launcher always consumes."""
    if not callable(getattr(app, "exec", None)):
        raise TypeError("app must provide a callable exec() event loop method")


def _normalize_pathlike_text(
    value: str | os.PathLike[str],
    *,
    parameter_name: str,
) -> str:
    """Normalize one public path-like input to an absolute text path."""
    if isinstance(value, str):
        return os.path.abspath(value)
    if not isinstance(value, os.PathLike):
        raise TypeError(
            f"{parameter_name} must be str or os.PathLike[str]; "
            f"got {type(value).__name__}"
        )

    normalized_path = os.fspath(value)
    if not isinstance(normalized_path, str):
        raise TypeError(
            f"{parameter_name} os.PathLike value must resolve to str; "
            f"got {type(normalized_path).__name__}"
        )
    return os.path.abspath(normalized_path)


def _normalize_startup_project_path(
    project_path: str | os.PathLike[str] | None,
) -> str | None:
    """Normalize the public explicit-project request without inspecting the project."""
    if project_path is None or project_path == "":
        return None
    return _normalize_pathlike_text(project_path, parameter_name="project_path")


def launch_editor(
    app: QApplication,
    repo_root: str | os.PathLike[str],
    *,
    project_path: str | os.PathLike[str] | None = None,
    use_splash: bool = True,
    capability_registry: object | None = None,
    event_bus: object | None = None,
) -> int:
    normalized_repo_root = _normalize_pathlike_text(
        repo_root,
        parameter_name="repo_root",
    )
    startup_project_path = _normalize_startup_project_path(project_path)

    from core.VitaLoom.core.runtime_capability_registry import (
        InMemoryRuntimeCapabilityRegistry,
        require_runtime_capability_registry,
    )
    from core.VitaLoom.core.runtime_event_bus import require_runtime_event_bus
    from core.VitaLoom.kernel import EditorKernel
    from core.VitaLoom.ui.splash_screen import (
        dismiss_splash,
        finish_splash,
        show_vitaloom_splash,
        splash_message,
    )

    runtime_registry = (
        InMemoryRuntimeCapabilityRegistry()
        if capability_registry is None
        else require_runtime_capability_registry(capability_registry)
    )
    runtime_event_bus = (
        None if event_bus is None else require_runtime_event_bus(event_bus)
    )
    _require_application_event_loop(app)

    splash = None
    try:
        if use_splash:
            splash = show_vitaloom_splash(app)
            splash_message(splash, "初始化织机内核...", app)


        kernel_kwargs: dict[str, object] = {
            "capability_registry": runtime_registry,
        }
        if runtime_event_bus is not None:
            kernel_kwargs["event_bus"] = runtime_event_bus
        kernel = EditorKernel(**kernel_kwargs)
        if startup_project_path is not None:
            kernel.set_startup_project(startup_project_path)

        if splash is not None:
            splash_message(splash, "加载官方能力包与用户扩展...", app)

        kernel.load_plugins_layered(default_plugin_layers(normalized_repo_root))

        if splash is not None:
            splash_message(splash, "恢复布局与项目...", app)

        kernel.show()
        if splash is not None:
            finish_splash(splash, kernel)
    except (Exception, SystemExit):
        try:
            dismiss_splash(splash)
        except (Exception, SystemExit):
            logger.warning("Failed to dismiss splash after editor startup failure", exc_info=True)
        raise

    return app.exec()
