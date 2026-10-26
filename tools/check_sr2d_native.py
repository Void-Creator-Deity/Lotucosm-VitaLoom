#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report SR2D native backend import/build readiness without requiring native builds."""
from __future__ import annotations

import importlib
import importlib.util
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._runtime_bootstrap import install_runtime_paths

install_runtime_paths(ROOT)


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def _module_status(name: str) -> dict[str, Any]:
    status: dict[str, Any] = {
        "module": name,
        "available": False,
        "has_kernel": False,
        "import_error": None,
    }
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on local native builds
        status["import_error"] = f"{exc.__class__.__name__}: {exc}"
        return status
    status["available"] = True
    status["has_kernel"] = callable(getattr(module, "step_pvaec_circles", None))
    module_path = getattr(module, "__file__", None)
    status["artifact_sha256"] = None
    status["artifact_provenance"] = "unavailable"
    if isinstance(module_path, str):
        try:
            status["artifact_sha256"] = hashlib.sha256(Path(module_path).read_bytes()).hexdigest()
            status["artifact_provenance"] = "hashed"
        except OSError:
            status["artifact_provenance"] = "unreadable"
    abi_version = getattr(module, "VITALLOOM_SR2D_ABI_VERSION", None)
    status["abi_version_exported"] = (
        abi_version if isinstance(abi_version, int) and not isinstance(abi_version, bool) else None
    )
    return status


def _backend_status(names: list[str]) -> dict[str, Any]:
    modules = [_module_status(name) for name in names]
    loaded = next((item for item in modules if item["available"]), None)
    return {
        "available": any(item["available"] for item in modules),
        "has_kernel": any(item["has_kernel"] for item in modules),
        "artifact_sha256": loaded.get("artifact_sha256") if loaded else None,
        "artifact_provenance": loaded.get("artifact_provenance") if loaded else "unavailable",
        "abi_version_exported": loaded.get("abi_version_exported") if loaded else None,
        "modules": modules,
    }


def _toolchain_status() -> dict[str, bool]:
    names = ("cl", "cmake", "ninja", "g++", "clang++", "nmake", "cargo", "rustc", "maturin")
    scripts = Path(sys.executable).resolve().parent
    status: dict[str, bool] = {}
    for name in names:
        status[name] = shutil.which(name) is not None or any(
            (scripts / f"{name}{suffix}").is_file()
            for suffix in ("", ".exe", ".cmd", ".bat")
        )
    if sys.platform == "win32":
        from tools.build_sr2d_native import _discover_windows_toolchain

        discovered = _discover_windows_toolchain().get("discovered_paths", {})
        for name in ("cl", "cmake", "ninja"):
            if discovered.get(name):
                status[name] = True
    return status


def _package_status() -> dict[str, bool]:
    names = ("pybind11", "skbuild", "scikit_build_core", "cibuildwheel")
    return {name: importlib.util.find_spec(name) is not None for name in names}


def collect_status() -> dict[str, Any]:
    from core.Lotucosm.sr_physics2d import (
        SR2D_ABI_VERSION,
        SR2D_INPUT_CONTRACT,
        build_sr2d_runtime_provenance,
        is_cpp_sr2d_available,
        is_native_sr2d_available,
        is_rust_sr2d_available,
    )

    return {
        "schema_version": 1,
        "abi_version_required": SR2D_ABI_VERSION,
        "input_contract": SR2D_INPUT_CONTRACT,
        "runtime_provenance": build_sr2d_runtime_provenance(),
        "root": str(ROOT),
        "native_available": is_native_sr2d_available(),
        "cpp": {
            **_backend_status(["_vitalloom_sr2d_cpp"]),
            "adapter_available": is_cpp_sr2d_available(),
        },
        "rust": {
            **_backend_status(["_vitalloom_sr2d_rust", "_vitalloom_sr2d"]),
            "adapter_available": is_rust_sr2d_available(),
        },
        "toolchain": _toolchain_status(),
        "python_packages": _package_status(),
    }


def main() -> int:
    _configure_stdout()
    print(json.dumps(collect_status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
