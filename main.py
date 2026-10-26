# -*- coding: utf-8 -*-
"""FrameCore application entrypoint.

L0 discovers the ``lotucosm-vitaloom`` app plugin and delegates Hub entries to
its lifecycle Adapter. Product-version Editor/Player commands remain delegated
to the selected runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

from FrameCore.lifecycle import FrameApi, FrameAppPlugin, LifecycleRunner
from FrameCore.product_registry import ProductVersion
from FrameCore.suite_registry import load_default_suite_manifest


DEFAULT_PRODUCT_ID = "lotucosm-vitaloom"
_LIFECYCLE = LifecycleRunner()
_FRAME_API: FrameApi | None = None
_FRAME_PLUGIN: FrameAppPlugin | None = None


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return Path(__file__).resolve().parent


def _bootstrap_frame_plugin() -> tuple[FrameApi, FrameAppPlugin]:
    global _FRAME_API, _FRAME_PLUGIN
    if _FRAME_API is not None and _FRAME_PLUGIN is not None:
        return _FRAME_API, _FRAME_PLUGIN

    suite = load_default_suite_manifest(_resource_root())
    frame_api = FrameApi(
        app_root=_app_root(),
        resource_root=_resource_root(),
        suite=suite,
    )
    plugin = frame_api.create_lifecycle_plugin()
    _LIFECYCLE.load(plugin, frame_api)
    _FRAME_API = frame_api
    _FRAME_PLUGIN = plugin
    return frame_api, plugin


def _frame_api() -> FrameApi:
    return _bootstrap_frame_plugin()[0]


def _frame_plugin() -> FrameAppPlugin:
    return _bootstrap_frame_plugin()[1]


def _select_product_version(product_id: str = DEFAULT_PRODUCT_ID) -> ProductVersion:
    return _frame_api().select_product_version(product_id)


def _run_product_entry(entry: str, extra_args: list[str] | None = None) -> None:
    version = _select_product_version()
    _frame_api().run_product_entry(version, entry, extra_args)


def _run_frame_plugin_entry(entry: str, args: list[str] | None = None) -> int:
    return int(_frame_plugin().run_entry(entry, args))


def _format_runtime_version() -> str:
    suite = _frame_api().suite
    version = _select_product_version()
    return (
        f"{suite.display_name or suite.suite_id} {suite.version} / "
        f"{version.product_id} {version.version}"
    )


def _shutdown_frame_plugin() -> None:
    global _FRAME_API, _FRAME_PLUGIN
    _LIFECYCLE.unload_all()
    _FRAME_API = None
    _FRAME_PLUGIN = None


def main() -> None:
    args = sys.argv[1:]
    if "--version" in args:
        print(_format_runtime_version())
        return
    if args and args[0] == "command":
        _run_product_entry("command", args[1:])
        return
    if "--smoke-hub" in args:
        raise SystemExit(_run_frame_plugin_entry("hub_smoke", args))
    if "--editor" in args or "--smoke-editor" in args or "--project" in args:
        _run_product_entry("editor", args)
        return
    raise SystemExit(_run_frame_plugin_entry("hub", args))


if __name__ == "__main__":
    try:
        main()
    finally:
        _shutdown_frame_plugin()
