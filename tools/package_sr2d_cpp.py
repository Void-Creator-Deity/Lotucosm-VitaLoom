# -*- coding: utf-8 -*-
"""Build and verify the optional Lotucosm-VitaLoom SR2D C++ wheel.

This is a release-evidence tool, not a runtime package manager.  It keeps the
native implementation behind the existing SR2D Adapter seam and verifies that
Python remains the mandatory no-native fallback.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
NATIVE_PROJECT = ROOT / "native" / "sr2d_cpp"
RUNTIME_ROOT = (
    ROOT
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)
DISTRIBUTION_NAME = "lotucosm-vitaloom-sr2d-cpp"
DISTRIBUTION_VERSION = "1.0.0"
REQUIRES_PYTHON = ">=3.11"
MODULE_NAME = "_vitalloom_sr2d_cpp"
KERNEL_SYMBOL = "step_pvaec_circles"
ABI_VERSION = 1
VISUAL_STUDIO_VERSION_RANGE = "[17.0,19.0)"


def _canonicalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _python_literal(value: str | os.PathLike[str]) -> str:
    return json.dumps(os.fspath(value), ensure_ascii=True)


def _is_windows() -> bool:
    return os.name == "nt"


def _environment_value(environment: Mapping[str, str], name: str) -> str:
    expected = name.casefold()
    for key, value in environment.items():
        if key.casefold() == expected:
            return value
    return ""


def _find_vswhere(environment: Mapping[str, str]) -> Path:
    path_value = _environment_value(environment, "PATH")
    discovered = shutil.which("vswhere", path=path_value or None)
    if discovered:
        return Path(discovered)

    candidates: list[Path] = []
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        root = _environment_value(environment, variable)
        if root:
            candidates.append(
                Path(root) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
            )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "MSVC is required for the Windows SR2D wheel, but vswhere.exe was not found"
    )


def _capture_visual_studio_environment(
    vsdevcmd: Path,
    base_environment: Mapping[str, str],
) -> dict[str, str]:
    comspec = (
        _environment_value(base_environment, "COMSPEC")
        or os.environ.get("COMSPEC")
        or "cmd.exe"
    )
    encoding = locale.getpreferredencoding(False)
    with tempfile.TemporaryDirectory(prefix="vitalloom-vs-env-") as temp_dir:
        script = Path(temp_dir) / "capture.cmd"
        script.write_text(
            "\r\n".join(
                (
                    f'@call "{vsdevcmd}" -no_logo -arch=x64 -host_arch=x64 >nul',
                    "@if errorlevel 1 exit /b %errorlevel%",
                    "@set",
                    "",
                )
            ),
            encoding=encoding,
        )
        proc = subprocess.run(
            [comspec, "/d", "/c", str(script)],
            env=dict(base_environment),
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            check=True,
        )
    environment = dict(base_environment)
    for line in proc.stdout.splitlines():
        if "=" not in line or line.startswith("="):
            continue
        key, value = line.split("=", 1)
        environment[key] = value

    captured_path = _environment_value(environment, "PATH")
    if captured_path:
        environment["PATH"] = captured_path
    return environment


def _discover_visual_studio_environment(
    base_environment: Mapping[str, str],
) -> dict[str, str]:
    vswhere = _find_vswhere(base_environment)
    proc = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-version",
            VISUAL_STUDIO_VERSION_RANGE,
            "-property",
            "installationPath",
        ],
        env=dict(base_environment),
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        errors="replace",
        check=True,
    )
    installations = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not installations:
        raise RuntimeError(
            "MSVC is required for the Windows SR2D wheel, but no compatible "
            "Visual Studio installation was discovered"
        )
    vsdevcmd = Path(installations[-1]) / "Common7" / "Tools" / "VsDevCmd.bat"
    if not vsdevcmd.is_file():
        raise RuntimeError(f"Visual Studio developer environment is missing: {vsdevcmd}")
    return _capture_visual_studio_environment(vsdevcmd, base_environment)


def _wheel_build_environment(
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = dict(os.environ if base_environment is None else base_environment)
    environment["CMAKE_GENERATOR"] = "Ninja"
    if not _is_windows():
        return environment

    path_value = _environment_value(environment, "PATH")
    if shutil.which("cl", path=path_value or None) is None:
        environment = _discover_visual_studio_environment(environment)
        environment["CMAKE_GENERATOR"] = "Ninja"

    compiler = shutil.which(
        "cl",
        path=_environment_value(environment, "PATH") or None,
    )
    if compiler is None:
        raise RuntimeError(
            "Visual Studio was discovered, but cl.exe is unavailable in the "
            "captured x64 developer environment"
        )
    interpreter_scripts = str(Path(sys.executable).resolve().parent)
    current_path = _environment_value(environment, "PATH")
    environment["PATH"] = (
        interpreter_scripts + os.pathsep + current_path
        if current_path
        else interpreter_scripts
    )
    return environment


def _wheel_build_argv(output_dir: Path, build_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(output_dir.resolve()),
        "--config-settings",
        f"build-dir={build_dir.resolve()}",
        str(NATIVE_PROJECT.resolve()),
    ]


def _wheel_install_argv(wheel: Path, target: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--target",
        str(target.resolve()),
        str(wheel.resolve()),
    ]


def _isolated_import_argv(target: Path) -> list[str]:
    target_literal = 'r"' + str(target.resolve()).replace('"', '\"') + '"'
    code = "; ".join(
        (
            "import importlib, sys",
            "from pathlib import Path",
            f"expected = Path({target_literal}).resolve()",
            "sys.path.insert(0, str(expected))",
            f"module = importlib.import_module({MODULE_NAME!r})",
            "module_path = Path(module.__file__).resolve()",
            "assert module_path.is_relative_to(expected), (module_path, expected)",
            f"assert callable(getattr(module, {KERNEL_SYMBOL!r}, None))",
            f"assert getattr(module, 'VITALLOOM_SR2D_ABI_VERSION', None) == {ABI_VERSION}",
            "print(module_path)",
        )
    )
    return [sys.executable, "-S", "-c", code]


def _clean_fallback_argv() -> list[str]:
    runtime_literal = _python_literal(str(RUNTIME_ROOT.resolve()))
    code = "\n".join(
        (
            "import os, sys",
            f"sys.path.insert(0, {runtime_literal})",
            "os.environ['VITALOOM_SR2D_ADAPTER'] = 'auto'",
            "from core.Lotucosm.sr_physics2d import (",
            "    CppSrPhysics2DAdapter, PythonSrPhysics2DAdapter,",
            "    is_cpp_sr2d_available, make_default_adapter,",
            ")",
            "assert is_cpp_sr2d_available() is False",
            "assert isinstance(make_default_adapter(), PythonSrPhysics2DAdapter)",
            "failed_loudly = False",
            "try:",
            "    CppSrPhysics2DAdapter()",
            "except RuntimeError:",
            "    failed_loudly = True",
            "assert failed_loudly",
            "print('clean Python fallback OK')",
        )
    )
    return [sys.executable, "-S", "-c", code]

def _packaged_parity_command(target: Path) -> tuple[list[str], dict[str, str]]:
    target_path = str(target.resolve())
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    pythonpath = [target_path, str(RUNTIME_ROOT.resolve()), str(ROOT.resolve())]
    if existing_pythonpath:
        pythonpath.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)
    env["PYTHONNOUSERSITE"] = "1"
    env["VITALOOM_SR2D_EXPECT_MODULE_ROOT"] = target_path
    env["VITALOOM_SR2D_ADAPTER"] = "cpp"
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "tests/test_sr2d_packaged_artifact_parity.py",
    ]
    return argv, env


def _single_member(names: Sequence[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError(
            f"wheel must contain exactly one {suffix} member; found {len(matches)}"
        )
    return matches[0]


def _read_metadata(archive: zipfile.ZipFile, member: str) -> Mapping[str, str]:
    return BytesParser(policy=email_policy).parsebytes(archive.read(member))


def _parse_wheel_filename(path: Path) -> tuple[str, str, str, str, str]:
    if path.suffix != ".whl":
        raise RuntimeError(f"not a wheel artifact: {path.name}")
    parts = path.name[:-4].split("-")
    if len(parts) != 5:
        raise RuntimeError(
            "wheel filename must use distribution-version-python-abi-platform tags"
        )
    distribution, version, python_tag, abi_tag, platform_tag = parts
    return distribution, version, python_tag, abi_tag, platform_tag


def _inspect_wheel(wheel: Path) -> dict[str, Any]:
    wheel = wheel.resolve()
    if not wheel.is_file():
        raise RuntimeError(f"wheel artifact does not exist: {wheel}")

    filename_distribution, filename_version, python_tag, abi_tag, platform_tag = (
        _parse_wheel_filename(wheel)
    )
    if _canonicalize_name(filename_distribution) != _canonicalize_name(
        DISTRIBUTION_NAME
    ):
        raise RuntimeError(
            f"wheel distribution mismatch: {filename_distribution!r} != "
            f"{DISTRIBUTION_NAME!r}"
        )
    if filename_version != DISTRIBUTION_VERSION:
        raise RuntimeError(
            f"wheel version mismatch: {filename_version!r} != {DISTRIBUTION_VERSION!r}"
        )
    if platform_tag == "any" or abi_tag == "none":
        raise RuntimeError("SR2D artifact must be a non-pure platform wheel")

    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_member = _single_member(names, ".dist-info/METADATA")
        wheel_member = _single_member(names, ".dist-info/WHEEL")
        record_member = _single_member(names, ".dist-info/RECORD")
        extension_members = [
            name
            for name in names
            if Path(name).name.startswith(MODULE_NAME)
            and Path(name).suffix.lower() in {".pyd", ".so"}
        ]
        if len(extension_members) != 1:
            raise RuntimeError(
                f"wheel must contain exactly one {MODULE_NAME} native extension; "
                f"found {len(extension_members)}"
            )
        extension_member = extension_members[0]

        metadata = _read_metadata(archive, metadata_member)
        distribution = str(metadata.get("Name", "")).strip()
        version = str(metadata.get("Version", "")).strip()
        requires_python = str(metadata.get("Requires-Python", "")).strip()
        if _canonicalize_name(distribution) != _canonicalize_name(DISTRIBUTION_NAME):
            raise RuntimeError(
                f"METADATA distribution mismatch: {distribution!r} != "
                f"{DISTRIBUTION_NAME!r}"
            )
        if version != DISTRIBUTION_VERSION:
            raise RuntimeError(
                f"METADATA version mismatch: {version!r} != {DISTRIBUTION_VERSION!r}"
            )
        if requires_python != REQUIRES_PYTHON:
            raise RuntimeError(
                f"Requires-Python mismatch: {requires_python!r} != {REQUIRES_PYTHON!r}"
            )

        wheel_metadata = _read_metadata(archive, wheel_member)
        root_is_purelib = str(wheel_metadata.get("Root-Is-Purelib", "")).lower()
        if root_is_purelib != "false":
            raise RuntimeError("SR2D artifact must be a non-pure platform wheel")

        record_rows = list(
            csv.reader(io.StringIO(archive.read(record_member).decode("utf-8")))
        )
        record_names = {row[0] for row in record_rows if row}
        record_contains_extension = extension_member in record_names
        if not record_contains_extension:
            raise RuntimeError("wheel RECORD does not contain the native extension")

    return {
        "wheel": str(wheel),
        "distribution": distribution,
        "version": version,
        "requires_python": requires_python,
        "python_tag": python_tag,
        "abi_tag": abi_tag,
        "platform_tag": platform_tag,
        "root_is_purelib": False,
        "extension_member": extension_member,
        "record_contains_extension": record_contains_extension,
    }


def _display_command(argv: Sequence[str]) -> str:
    return subprocess.list2cmdline([str(item) for item in argv])


def _run_checked(
    argv: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> None:
    command = [str(item) for item in argv]
    print(f"+ {_display_command(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _artifact_fingerprint(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


def _select_built_wheel(
    wheel_dir: Path,
    before: Mapping[Path, tuple[int, int]],
) -> Path:
    wheels = sorted(wheel_dir.glob("*.whl"))
    changed = [
        wheel
        for wheel in wheels
        if before.get(wheel.resolve()) != _artifact_fingerprint(wheel)
    ]
    if len(changed) == 1:
        return changed[0]

    expected_prefix = _canonicalize_name(DISTRIBUTION_NAME).replace("-", "_")
    matching = [
        wheel
        for wheel in wheels
        if wheel.name.startswith(f"{expected_prefix}-{DISTRIBUTION_VERSION}-")
    ]
    if len(matching) == 1:
        return matching[0]
    raise RuntimeError(
        "expected exactly one newly built SR2D wheel; "
        f"changed={len(changed)}, matching={len(matching)}"
    )


def build_and_verify(wheel_dir: Path) -> dict[str, Any]:
    wheel_dir = wheel_dir.resolve()
    wheel_dir.mkdir(parents=True, exist_ok=True)
    before = {
        wheel.resolve(): _artifact_fingerprint(wheel)
        for wheel in wheel_dir.glob("*.whl")
    }

    with tempfile.TemporaryDirectory(prefix="vitalloom-sr2d-package-") as temp_dir:
        scratch = Path(temp_dir)
        build_dir = scratch / "build"
        target = scratch / "installed"
        target.mkdir(parents=True, exist_ok=True)

        _run_checked(
            _wheel_build_argv(wheel_dir, build_dir),
            env=_wheel_build_environment(),
        )
        wheel = _select_built_wheel(wheel_dir, before)
        inspection = _inspect_wheel(wheel)
        _run_checked(_wheel_install_argv(wheel, target))
        _run_checked(_isolated_import_argv(target))
        _run_checked(_clean_fallback_argv())
        parity_argv, parity_env = _packaged_parity_command(target)
        _run_checked(parity_argv, env=parity_env)

    return {
        "schema_version": 1,
        "python_executable": sys.executable,
        "native_project": str(NATIVE_PROJECT.resolve()),
        "wheel_dir": str(wheel_dir),
        "inspection": inspection,
        "isolated_import_verified": True,
        "clean_fallback_verified": True,
        "packaged_parity_verified": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheel-dir",
        type=Path,
        default=ROOT / "dist" / "sr2d_cpp",
        help="directory that receives the built wheel artifact",
    )
    parser.add_argument(
        "--inspect-only",
        type=Path,
        metavar="WHEEL",
        help="inspect one existing wheel without building or installing it",
    )
    args = parser.parse_args(argv)

    if args.inspect_only is not None:
        report: dict[str, Any] = {
            "schema_version": 1,
            "inspection": _inspect_wheel(args.inspect_only),
        }
    else:
        report = build_and_verify(args.wheel_dir)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
