#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check or build optional SR2D native backends with interpreter-exact proof."""
from __future__ import annotations

import argparse
import importlib.util
import json
import hashlib
import platform
import re
import struct
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
ABI_VERSION = 1
ABI_SYMBOL = "VITALLOOM_SR2D_ABI_VERSION"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _discover_windows_toolchain() -> dict[str, Any]:
    """Report installed Windows tools without changing the active environment."""
    result: dict[str, Any] = {
        "platform": sys.platform,
        "vswhere": None,
        "visual_studio_installations": [],
        "discovered_paths": {},
    }
    if sys.platform != "win32":
        return result

    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"),
        Path(r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"),
    ]
    vswhere = next((path for path in candidates if path.is_file()), None)
    if vswhere is None:
        return result
    result["vswhere"] = str(vswhere)
    try:
        completed = subprocess.run(
            [str(vswhere), "-latest", "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
             "-property", "installationPath"],
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            errors="replace",
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return result

    installations = [Path(line.strip()) for line in completed.stdout.splitlines() if line.strip()]
    result["visual_studio_installations"] = [str(path) for path in installations]
    for installation in installations:
        tool_candidates = {
            "cl": installation / "VC" / "Tools" / "MSVC",
            "cmake": installation / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "CMake" / "bin" / "cmake.exe",
            "ninja": installation / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "Ninja" / "ninja.exe",
        }
        for name, path in tool_candidates.items():
            if name in result["discovered_paths"]:
                continue
            if name == "cl":
                matches = sorted(path.glob("*/bin/Hostx64/x64/cl.exe"))
                if matches:
                    result["discovered_paths"][name] = str(matches[-1])
            elif path.is_file():
                result["discovered_paths"][name] = str(path)
    return result


def _configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def _tool_available(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    scripts = Path(sys.executable).resolve().parent
    for suffix in ("", ".exe", ".cmd", ".bat"):
        if (scripts / f"{name}{suffix}").is_file():
            return True
    return False


def _package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _package_status(names: tuple[str, ...]) -> dict[str, bool]:
    return {name: _package_available(name) for name in names}


def _build_argv(project: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        f"./{project}",
    ]


def _import_check_argv(module_name: str, kernel_symbol: str) -> list[str]:
    code = (
        f"import hashlib, json, platform, struct; import {module_name} as module; "
        f"assert callable(getattr(module, {kernel_symbol!r}, None)); "
        f"assert getattr(module, {ABI_SYMBOL!r}, None) == {ABI_VERSION}; "
        "print(json.dumps({"
        "'module': module.__name__, "
        "'artifact': str(module.__file__), "
        "'artifact_sha256': hashlib.sha256(open(module.__file__, 'rb').read()).hexdigest(), "
        f"'abi_version': getattr(module, {ABI_SYMBOL!r}), "
        "'python_version': platform.python_version(), "
        "'platform': platform.platform(), "
        "'pointer_bits': struct.calcsize('P') * 8"
        "}, sort_keys=True))"
    )
    return [sys.executable, "-c", code]


def _display_command(argv: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(argv))


def _cpp_status() -> dict[str, Any]:
    discovery = _discover_windows_toolchain()
    tools = {
        name: _tool_available(name)
        for name in ("cl", "cmake", "ninja", "g++", "clang++", "nmake")
    }
    for name in ("cl", "cmake", "ninja"):
        if discovery.get("discovered_paths", {}).get(name):
            tools[name] = True
    packages = _package_status(("pybind11", "scikit_build_core"))
    has_compiler = tools["cl"] or tools["g++"] or tools["clang++"]
    toolchain_ready = tools["cmake"] and has_compiler
    python_packages_ready = all(packages.values())
    project = "native/sr2d_cpp"
    module_name = "_vitalloom_sr2d_cpp"
    kernel_symbol = "step_pvaec_circles"
    build_argv = _build_argv(project)
    import_check_argv = _import_check_argv(module_name, kernel_symbol)
    return {
        "backend": "cpp",
        "project": project,
        "source_project": project,
        "module_name": module_name,
        "kernel_symbol": kernel_symbol,
        "abi_version_required": ABI_VERSION,
        "abi_symbol": ABI_SYMBOL,
        "python_executable": sys.executable,
        "ready": toolchain_ready and python_packages_ready,
        "toolchain_ready": toolchain_ready,
        "python_packages_ready": python_packages_ready,
        "toolchain": tools,
        "missing": [name for name, ok in tools.items() if not ok],
        "missing_tools": [name for name, ok in tools.items() if not ok],
        "python_packages": packages,
        "missing_python_packages": [name for name, ok in packages.items() if not ok],
        "environment_discovery": discovery,
        "build_argv": build_argv,
        "build_command": _display_command(build_argv),
        "import_check_argv": import_check_argv,
        "import_check": _display_command(import_check_argv),
    }


def _rust_status() -> dict[str, Any]:
    tools = {name: _tool_available(name) for name in ("cargo", "rustc", "maturin")}
    packages = _package_status(("maturin",))
    # pip invokes the installed maturin build backend; only cargo/rustc are external tools.
    toolchain_ready = tools["cargo"] and tools["rustc"]
    python_packages_ready = all(packages.values())
    project = "native/sr2d_kernel"
    module_name = "_vitalloom_sr2d_rust"
    kernel_symbol = "step_pvaec_circles"
    build_argv = _build_argv(project)
    import_check_argv = _import_check_argv(module_name, kernel_symbol)
    return {
        "backend": "rust",
        "project": project,
        "source_project": project,
        "module_name": module_name,
        "legacy_module_name": "_vitalloom_sr2d",
        "kernel_symbol": kernel_symbol,
        "abi_version_required": ABI_VERSION,
        "abi_symbol": ABI_SYMBOL,
        "python_executable": sys.executable,
        "ready": toolchain_ready and python_packages_ready,
        "toolchain_ready": toolchain_ready,
        "python_packages_ready": python_packages_ready,
        "toolchain": tools,
        "missing": [name for name, ok in tools.items() if not ok],
        "missing_tools": [name for name, ok in tools.items() if not ok],
        "python_packages": packages,
        "missing_python_packages": [name for name, ok in packages.items() if not ok],
        "environment_discovery": {"platform": sys.platform},
        "build_argv": build_argv,
        "build_command": _display_command(build_argv),
        "import_check_argv": import_check_argv,
        "import_check": _display_command(import_check_argv),
    }


def collect_status(backend: str) -> dict[str, Any]:
    selected = ("cpp", "rust") if backend == "all" else (backend,)
    statuses = {"cpp": _cpp_status(), "rust": _rust_status()}
    return {name: statuses[name] for name in selected}


def _run_command(argv: Sequence[str]) -> dict[str, Any]:
    command = list(argv)
    try:
        proc = subprocess.run(
            command,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": command,
            "command": _display_command(command),
            "returncode": 124,
            "stdout_tail": str(exc.stdout or "")[-4000:],
            "stderr_tail": f"command timed out after {exc.timeout} seconds",
        }
    except OSError as exc:
        return {
            "argv": command,
            "command": _display_command(command),
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": f"{type(exc).__name__}: {exc}",
        }
    return {
        "argv": command,
        "command": _display_command(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def _validate_import_provenance(
    provenance: object,
    *,
    expected_module: str,
) -> tuple[bool, str]:
    if not isinstance(provenance, dict):
        return False, "JSON ABI provenance must be an object"
    required = (
        "module",
        "artifact",
        "artifact_sha256",
        "abi_version",
        "python_version",
        "platform",
        "pointer_bits",
    )
    missing = [key for key in required if key not in provenance]
    if missing:
        return False, f"incomplete JSON ABI provenance: missing {', '.join(missing)}"
    if provenance["module"] != expected_module:
        return False, "unexpected imported module"
    if not isinstance(provenance["artifact"], str) or not provenance["artifact"]:
        return False, "missing native artifact path"
    if not isinstance(provenance["artifact_sha256"], str) or not _SHA256_RE.fullmatch(
        provenance["artifact_sha256"]
    ):
        return False, "invalid native artifact SHA-256"
    if provenance["abi_version"] != ABI_VERSION or isinstance(
        provenance["abi_version"], bool
    ):
        return False, "unexpected ABI version"
    if not isinstance(provenance["python_version"], str) or not provenance[
        "python_version"
    ]:
        return False, "missing Python runtime provenance"
    if not isinstance(provenance["platform"], str) or not provenance["platform"]:
        return False, "missing platform provenance"
    pointer_bits = provenance["pointer_bits"]
    if isinstance(pointer_bits, bool) or not isinstance(pointer_bits, int) or pointer_bits <= 0:
        return False, "invalid pointer-width provenance"
    return True, ""


def _run_backend_build(status: dict[str, Any]) -> bool:
    status["build_result"] = _run_command(status["build_argv"])
    status["import_check_result"] = None
    status["build_import_verified"] = False
    if status["build_result"]["returncode"] != 0:
        return False

    status["import_check_result"] = _run_command(status["import_check_argv"])
    status["build_import_verified"] = status["import_check_result"]["returncode"] == 0
    status["artifact_provenance"] = None
    if status["build_import_verified"]:
        stdout = str(status["import_check_result"].get("stdout_tail") or "").strip()
        try:
            provenance = json.loads(stdout.splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            status["build_import_verified"] = False
            status["import_check_result"]["stderr_tail"] += "\nmissing JSON ABI provenance"
        else:
            valid, reason = _validate_import_provenance(
                provenance,
                expected_module=str(status["module_name"]),
            )
            if not valid:
                status["build_import_verified"] = False
                status["import_check_result"]["stderr_tail"] += f"\n{reason}"
            else:
                status["artifact_provenance"] = provenance
    return bool(status["build_import_verified"])


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("cpp", "rust", "all"), default="all")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    backends = collect_status(args.backend)
    result: dict[str, Any] = {
        "schema_version": 1,
        "root": str(ROOT),
        "python_executable": sys.executable,
        "check_only": bool(args.check_only),
        "backends": backends,
    }
    if args.check_only:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    exit_code = 0
    for status in backends.values():
        if not status["ready"]:
            status["build_skipped"] = True
            status["skip_reason"] = "missing native toolchain or Python build packages"
            status["build_import_verified"] = False
            exit_code = 2
            continue
        status["build_skipped"] = False
        if not _run_backend_build(status):
            build_result = status.get("build_result") or {}
            import_result = status.get("import_check_result") or {}
            exit_code = int(import_result.get("returncode") or build_result.get("returncode") or 1)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
