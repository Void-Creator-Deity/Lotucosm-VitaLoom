# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "package_sr2d_cpp.py"
NATIVE_PROJECT = ROOT / "native" / "sr2d_cpp"


def _load_tool():
    spec = importlib.util.spec_from_file_location("package_sr2d_cpp_under_test", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fake_wheel(
    target: Path,
    *,
    version: str = "1.0.0",
    pure: bool = False,
) -> Path:
    filename = f"lotucosm_vitaloom_sr2d_cpp-{version}-cp311-cp311-win_amd64.whl"
    wheel_path = target / filename
    dist_info = f"lotucosm_vitaloom_sr2d_cpp-{version}.dist-info"
    extension = "_vitalloom_sr2d_cpp.cp311-win_amd64.pyd"
    root_is_purelib = "true" if pure else "false"
    records = [
        extension,
        f"{dist_info}/METADATA",
        f"{dist_info}/WHEEL",
        f"{dist_info}/RECORD",
    ]
    with zipfile.ZipFile(wheel_path, "w") as archive:
        archive.writestr(extension, b"native-extension-placeholder")
        archive.writestr(
            f"{dist_info}/METADATA",
            "\n".join(
                (
                    "Metadata-Version: 2.3",
                    "Name: lotucosm-vitaloom-sr2d-cpp",
                    f"Version: {version}",
                    "Requires-Python: >=3.11",
                    "",
                )
            ),
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "\n".join(
                (
                    "Wheel-Version: 1.0",
                    "Generator: test",
                    f"Root-Is-Purelib: {root_is_purelib}",
                    "Tag: cp311-cp311-win_amd64",
                    "",
                )
            ),
        )
        archive.writestr(
            f"{dist_info}/RECORD",
            "".join(f"{name},,\n" for name in records),
        )
    return wheel_path


def test_native_pyproject_declares_product_aligned_platform_wheel_contract() -> None:
    data = tomllib.loads((NATIVE_PROJECT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "lotucosm-vitaloom-sr2d-cpp"
    assert data["project"]["version"] == "1.0.0"
    assert data["project"]["requires-python"] == ">=3.11"
    assert "scikit-build-core>=0.9" in data["build-system"]["requires"]
    assert "pybind11>=2.12" in data["build-system"]["requires"]
    assert data["build-system"]["build-backend"] == "scikit_build_core.build"
    assert data["tool"]["scikit-build"]["wheel"]["packages"] == []
    assert data["tool"]["scikit-build"]["cmake"]["version"] == ">=3.18,<4"
    assert data["tool"]["scikit-build"]["ninja"]["version"] == ">=1.11"
    assert data["tool"]["scikit-build"]["ninja"]["make-fallback"] is False
    assert "CMakeLists.txt" in data["tool"]["scikit-build"]["sdist"]["include"]
    assert "src/kernel.cpp" in data["tool"]["scikit-build"]["sdist"]["include"]
    assert "VITALLOOM_SR2D_ABI_VERSION" in (
        NATIVE_PROJECT / "src" / "bindings.cpp"
    ).read_text(encoding="utf-8")

    project_text = (NATIVE_PROJECT / "pyproject.toml").read_text(encoding="utf-8")
    assert "D:\\app" not in project_text
    assert "Microsoft Visual Studio\\2022" not in project_text


def test_wheel_build_uses_exact_interpreter_and_ephemeral_build_dir(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    build_dir = tmp_path / "build"

    argv = tool._wheel_build_argv(tmp_path, build_dir)

    assert argv[:4] == [sys.executable, "-m", "pip", "wheel"]
    assert "--no-deps" in argv
    assert argv[argv.index("--wheel-dir") + 1] == str(tmp_path.resolve())
    assert argv[argv.index("--config-settings") + 1] == (
        f"build-dir={build_dir.resolve()}"
    )
    assert argv[-1] == str(NATIVE_PROJECT.resolve())


def test_wheel_build_environment_forces_ninja_and_preserves_ready_compiler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    monkeypatch.setattr(tool, "_is_windows", lambda: True)
    monkeypatch.setattr(
        tool.shutil,
        "which",
        lambda name, path=None: r"C:\\toolchain\\cl.exe" if name == "cl" else None,
    )

    env = tool._wheel_build_environment({"PATH": r"C:\\toolchain"})

    assert env["CMAKE_GENERATOR"] == "Ninja"
    assert env["PATH"].split(tool.os.pathsep) == [
        str(Path(sys.executable).resolve().parent),
        r"C:\\toolchain",
    ]


def test_wheel_build_environment_bootstraps_msvc_without_local_path_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_tool()
    monkeypatch.setattr(tool, "_is_windows", lambda: True)
    monkeypatch.setattr(
        tool.shutil,
        "which",
        lambda name, path=None: (
            r"C:\\discovered-msvc\\cl.exe"
            if name == "cl" and path == r"C:\\discovered-msvc"
            else None
        ),
    )
    monkeypatch.setattr(
        tool,
        "_discover_visual_studio_environment",
        lambda base: {
            **base,
            "PATH": r"C:\\discovered-msvc",
            "VSCMD_ARG_TGT_ARCH": "x64",
        },
    )

    env = tool._wheel_build_environment({"PATH": ""})

    assert env["CMAKE_GENERATOR"] == "Ninja"
    assert env["PATH"].split(tool.os.pathsep) == [
        str(Path(sys.executable).resolve().parent),
        r"C:\\discovered-msvc",
    ]
    assert env["VSCMD_ARG_TGT_ARCH"] == "x64"


def test_windows_toolchain_discovery_targets_supported_visual_studio_lines() -> None:
    tool = _load_tool()

    assert tool.VISUAL_STUDIO_VERSION_RANGE == "[17.0,19.0)"


def test_wheel_install_targets_isolated_directory_without_dependencies(tmp_path: Path) -> None:
    tool = _load_tool()
    wheel = _write_fake_wheel(tmp_path)
    target = tmp_path / "installed"

    argv = tool._wheel_install_argv(wheel, target)

    assert argv[:4] == [sys.executable, "-m", "pip", "install"]
    assert "--no-deps" in argv
    assert "--target" in argv
    assert argv[argv.index("--target") + 1] == str(target.resolve())
    assert argv[-1] == str(wheel.resolve())


def test_wheel_inspection_requires_product_metadata_and_native_record(tmp_path: Path) -> None:
    tool = _load_tool()
    wheel = _write_fake_wheel(tmp_path)

    report = tool._inspect_wheel(wheel)

    assert report["distribution"] == "lotucosm-vitaloom-sr2d-cpp"
    assert report["version"] == "1.0.0"
    assert report["root_is_purelib"] is False
    assert report["extension_member"].endswith(".pyd")
    assert report["record_contains_extension"] is True


def test_wheel_inspection_rejects_pure_or_misaligned_artifacts(tmp_path: Path) -> None:
    tool = _load_tool()

    with pytest.raises(RuntimeError, match="non-pure"):
        tool._inspect_wheel(_write_fake_wheel(tmp_path, pure=True))

    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(RuntimeError, match="version"):
        tool._inspect_wheel(_write_fake_wheel(other, version="0.1.0"))


def test_isolated_import_and_clean_fallback_commands_exclude_ambient_site_packages(
    tmp_path: Path,
) -> None:
    tool = _load_tool()
    target = tmp_path / "installed"

    import_argv = tool._isolated_import_argv(target)
    fallback_argv = tool._clean_fallback_argv()

    assert import_argv[0:2] == [sys.executable, "-S"]
    assert str(target.resolve()) in import_argv[-1]
    assert "step_pvaec_circles" in import_argv[-1]
    assert "VITALLOOM_SR2D_ABI_VERSION" in import_argv[-1]
    assert "is_relative_to" in import_argv[-1]
    assert fallback_argv[0:2] == [sys.executable, "-S"]
    assert "PythonSrPhysics2DAdapter" in fallback_argv[-1]
    assert "is_cpp_sr2d_available" in fallback_argv[-1]
    assert "CppSrPhysics2DAdapter" in fallback_argv[-1]


def test_clean_fallback_command_runs_without_ambient_native_site_packages() -> None:
    tool = _load_tool()

    proc = subprocess.run(
        tool._clean_fallback_argv(),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "clean Python fallback OK" in proc.stdout


def test_cpp_and_rust_bindings_export_versioned_abi() -> None:
    cpp = (NATIVE_PROJECT / "src" / "bindings.cpp").read_text(encoding="utf-8")
    rust = (ROOT / "native" / "sr2d_kernel" / "src" / "lib.rs").read_text(encoding="utf-8")
    assert 'module.attr("VITALLOOM_SR2D_ABI_VERSION") = 1' in cpp
    assert 'module.attr("VITALLOOM_SR2D_ENTROPY_CONTRACT") = "none"' in cpp
    assert 'm.add("VITALLOOM_SR2D_ABI_VERSION", 1)' in rust
    assert 'm.add("VITALLOOM_SR2D_ENTROPY_CONTRACT", "none")' in rust


def test_rust_binding_enforces_shared_input_and_broadphase_contract() -> None:
    rust = (ROOT / "native" / "sr2d_kernel" / "src" / "lib.rs").read_text(encoding="utf-8")

    for name in ("velocities", "radii", "entity_types", "pinned", "membrane_locked"):
        assert f'("{name}",' in rust
    assert "does not match positions length" in rust
    assert 'dict_broadphase(&config_raw)?' in rust
    assert 'return Ok("bruteforce".to_owned())' in rust
    assert 'return Ok("spatial_hash".to_owned())' in rust
    assert '"bruteforce"' in rust
    assert "unsupported PVAEC broadphase" in rust
    assert "entity_count == 0 || dt <= 0.0" in rust
    assert "floor_cell_coordinate" in rust
    assert "fn is_kinematic_integrable(body: &Body) -> bool" in rust
    assert "if !is_kinematic_integrable(body)" in rust
    assert "fn clamp_dynamic_bodies(" in rust
    assert "bodies.iter_mut().filter(|b| is_dynamic(b))" in rust

def test_packaged_parity_command_binds_expected_install_root(tmp_path: Path) -> None:
    tool = _load_tool()
    target = tmp_path / "installed"

    argv, env = tool._packaged_parity_command(target)

    assert argv[:3] == [sys.executable, "-m", "pytest"]
    assert "tests/test_sr2d_packaged_artifact_parity.py" in argv
    assert env["VITALOOM_SR2D_EXPECT_MODULE_ROOT"] == str(target.resolve())
    assert str(target.resolve()) == env["PYTHONPATH"].split(tool.os.pathsep)[0]
