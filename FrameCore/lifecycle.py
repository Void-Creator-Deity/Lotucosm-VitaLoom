# -*- coding: utf-8 -*-
"""FrameCore lifecycle runner for Suite plugin packages."""
from __future__ import annotations

import importlib
import os
import runpy
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from FrameCore.product_registry import ProductVersion, load_product_registry
from FrameCore.suite_registry import SuiteManifest


class LifecyclePlugin(Protocol):
    def on_load(self, frame_api: object) -> None: ...
    def on_unload(self) -> None: ...


class FrameAppPlugin(LifecyclePlugin, Protocol):
    """L1 product plugin interface loaded from the manifest entry module."""

    def run_entry(self, entry: str, args: list[str] | None = None) -> int: ...


@dataclass(frozen=True)
class FrameApi:
    """Small L0 interface exposed to Suite lifecycle plugins."""

    app_root: Path
    resource_root: Path
    suite: SuiteManifest

    def install_plugin_env(self) -> None:
        """Expose the L1 product plugin without binding a product runtime version."""
        if self.suite.suite_root is None:
            raise RuntimeError("suite manifest did not record suite root")
        os.environ["FRAMECORE_ROOT"] = str(self.resource_root / "FrameCore")
        os.environ["VITALOOM_SUITE_ROOT"] = str(self.suite.suite_root)
        os.environ["VITALOOM_APP_ROOT"] = str(self.app_root)
        for path in (str(self.suite.suite_root), str(self.resource_root)):
            if path not in sys.path:
                sys.path.insert(0, path)

    def create_lifecycle_plugin(self) -> FrameAppPlugin:
        """Instantiate the FrameCore app plugin declared by ``manifest.entry``."""
        self.install_plugin_env()
        module = importlib.import_module(self.suite.entry)
        factory = getattr(module, "create_frame_plugin", None)
        if not callable(factory):
            raise RuntimeError(
                f"plugin entry {self.suite.entry!r} must export create_frame_plugin()"
            )
        plugin = factory()
        for method_name in ("on_load", "on_unload", "run_entry"):
            if not callable(getattr(plugin, method_name, None)):
                raise TypeError(
                    f"plugin entry {self.suite.entry!r} returned an invalid plugin: "
                    f"missing {method_name}()"
                )
        return plugin

    def load_product_registry(self):
        if self.suite.suite_root is None:
            raise RuntimeError("suite manifest did not record suite root")
        return load_product_registry(self.suite.suite_root)

    def select_product_version(self, product_id: str) -> ProductVersion:
        version = self.load_product_registry().get_default_version(product_id)
        if version is None:
            raise RuntimeError(f"missing default product version: {product_id}")
        return version

    def install_runtime_env(self, version: ProductVersion) -> None:
        self.install_plugin_env()
        os.environ["VITALOOM_PRODUCT_VERSION_ROOT"] = str(version.version_root)
        runtime_root = str(version.runtime_root)
        if runtime_root not in sys.path:
            sys.path.insert(0, runtime_root)

    def run_product_entry(
        self,
        version: ProductVersion,
        entry: str,
        extra_args: list[str] | None = None,
    ) -> None:
        self.install_runtime_env(version)
        command = version.entrypoints.get(entry)
        if not command:
            raise RuntimeError(f"missing product entrypoint: {entry}")
        parts = command.split()
        script = version.version_root / parts[0]
        if not script.is_file():
            raise FileNotFoundError(f"missing product entrypoint script: {script}")
        sys.argv = [str(script), *parts[1:], *(extra_args or [])]
        runpy.run_path(str(script), run_name="__main__")


@dataclass
class LifecycleRunner:
    """Load Suite lifecycle plugins and unload them in reverse order."""

    loaded: list[LifecyclePlugin] = field(default_factory=list)

    def load(self, plugin: LifecyclePlugin, frame_api: object) -> None:
        plugin.on_load(frame_api)
        self.loaded.append(plugin)

    def unload_all(self) -> None:
        while self.loaded:
            plugin = self.loaded.pop()
            plugin.on_unload()
