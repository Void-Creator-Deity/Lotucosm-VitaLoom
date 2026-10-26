# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


def test_sr2d_native_smoke_tool_reports_missing_native_without_failing() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_sr2d_native.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["schema_version"] == 1
    assert data["abi_version_required"] == 1
    assert data["input_contract"]["kernel"] == "step_pvaec_circles"
    assert data["runtime_provenance"]["schema_version"] == 1
    assert data["runtime_provenance"]["cross_platform_parity_proven"] is False
    assert "cpp" in data
    assert "rust" in data
    assert "toolchain" in data
    assert "python_packages" in data
    assert "available" in data["cpp"]
    assert "has_kernel" in data["cpp"]
    assert "artifact_sha256" in data["cpp"]
    assert "abi_version_exported" in data["cpp"]
    assert "available" in data["rust"]
    assert "has_kernel" in data["rust"]
    assert "artifact_sha256" in data["rust"]
    assert "abi_version_exported" in data["rust"]


def test_sr2d_native_build_tool_check_only_reports_commands() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/build_sr2d_native.py", "--backend", "all", "--check-only"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["schema_version"] == 1
    assert data["check_only"] is True
    assert "cpp" in data["backends"]
    assert "rust" in data["backends"]
    assert data["backends"]["cpp"]["project"] == "native/sr2d_cpp"
    assert data["backends"]["rust"]["project"] == "native/sr2d_kernel"
    assert data["backends"]["cpp"]["build_argv"][-1] == "./native/sr2d_cpp"
    assert data["backends"]["rust"]["build_argv"][-1] == "./native/sr2d_kernel"
    assert "--no-build-isolation" in data["backends"]["cpp"]["build_argv"]
    assert "--no-build-isolation" in data["backends"]["rust"]["build_argv"]
    assert data["backends"]["cpp"]["module_name"] == "_vitalloom_sr2d_cpp"
    assert data["backends"]["cpp"]["kernel_symbol"] == "step_pvaec_circles"
    assert "import _vitalloom_sr2d_cpp" in data["backends"]["cpp"]["import_check"]
    assert "VITALLOOM_SR2D_ABI_VERSION" in data["backends"]["cpp"]["import_check"]
    assert "missing_tools" in data["backends"]["cpp"]
    assert "python_packages" in data["backends"]["cpp"]
    assert "missing_python_packages" in data["backends"]["cpp"]
    assert data["backends"]["rust"]["module_name"] == "_vitalloom_sr2d_rust"
    assert data["backends"]["rust"]["legacy_module_name"] == "_vitalloom_sr2d"
    assert data["backends"]["rust"]["kernel_symbol"] == "step_pvaec_circles"
    assert "import _vitalloom_sr2d_rust" in data["backends"]["rust"]["import_check"]
    assert "missing_tools" in data["backends"]["rust"]
    assert "python_packages" in data["backends"]["rust"]
    assert "missing_python_packages" in data["backends"]["rust"]
    assert "VITALLOOM_SR2D_ABI_VERSION" in data["backends"]["rust"]["import_check"]


def _load_build_tool():
    path = Path("tools/build_sr2d_native.py").resolve()
    spec = importlib.util.spec_from_file_location("build_sr2d_native_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_check_tool():
    path = Path("tools/check_sr2d_native.py").resolve()
    spec = importlib.util.spec_from_file_location("check_sr2d_native_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sr2d_native_build_reports_windows_toolchain_discovery_without_path_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_build_tool()
    monkeypatch.setattr(tool.sys, "platform", "linux")

    discovery = tool._discover_windows_toolchain()

    assert discovery["platform"] == "linux"
    assert discovery["discovered_paths"] == {}


def test_sr2d_native_check_requires_callable_kernel(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _load_check_tool()
    fake_module = type("FakeNativeModule", (), {"step_pvaec_circles": "not-callable"})()
    monkeypatch.setattr(tool.importlib, "import_module", lambda _name: fake_module)

    status = tool._module_status("fake_native")

    assert status["available"] is True
    assert status["has_kernel"] is False


def test_sr2d_native_build_tool_uses_invoking_interpreter_for_build_and_import() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/build_sr2d_native.py", "--backend", "cpp", "--check-only"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    cpp = data["backends"]["cpp"]
    assert Path(data["python_executable"]).resolve() == Path(sys.executable).resolve()
    assert cpp["build_argv"][0] == sys.executable
    assert cpp["build_argv"][1:4] == ["-m", "pip", "install"]
    assert "--no-build-isolation" in cpp["build_argv"]
    assert cpp["import_check_argv"][0] == sys.executable
    assert "callable" in cpp["import_check_argv"][-1]
    assert cpp["abi_version_required"] == 1
    assert cpp["abi_symbol"] == "VITALLOOM_SR2D_ABI_VERSION"
    assert "artifact_sha256" in cpp["import_check_argv"][-1]
    assert "environment_discovery" in cpp


def test_sr2d_native_build_runs_import_proof_after_success(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _load_build_tool()
    status = tool._cpp_status()
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> dict[str, object]:
        calls.append(list(argv))
        if argv == status["import_check_argv"]:
            stdout = '{"abi_version": 1, "artifact": "native.pyd", "artifact_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", "module": "_vitalloom_sr2d_cpp", "platform": "test", "pointer_bits": 64, "python_version": "3.11"}'
        else:
            stdout = "build ok"
        return {"argv": list(argv), "returncode": 0, "stdout_tail": stdout, "stderr_tail": ""}

    monkeypatch.setattr(tool, "_run_command", fake_run)

    assert tool._run_backend_build(status) is True
    assert calls == [status["build_argv"], status["import_check_argv"]]
    assert status["build_result"]["returncode"] == 0
    assert status["import_check_result"]["returncode"] == 0
    assert status["build_import_verified"] is True
    assert status["artifact_provenance"]["abi_version"] == 1


def test_sr2d_native_build_rejects_incomplete_import_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_build_tool()
    status = tool._cpp_status()

    def fake_run(argv: list[str]) -> dict[str, object]:
        return {
            "argv": list(argv),
            "returncode": 0,
            "stdout_tail": '{"abi_version": 1, "module": "_vitalloom_sr2d_cpp"}',
            "stderr_tail": "",
        }

    monkeypatch.setattr(tool, "_run_command", fake_run)
    assert tool._run_backend_build(status) is False
    assert "incomplete JSON ABI provenance" in status["import_check_result"]["stderr_tail"]


def test_sr2d_native_build_rejects_mismatched_import_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_build_tool()
    status = tool._cpp_status()

    provenance = (
        '{"abi_version": 1, "artifact": "native.pyd", '
        '"artifact_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", '
        '"module": "wrong_module", "platform": "test", "pointer_bits": 64, '
        '"python_version": "3.11"}'
    )

    def fake_run(argv: list[str]) -> dict[str, object]:
        return {
            "argv": list(argv),
            "returncode": 0,
            "stdout_tail": provenance,
            "stderr_tail": "",
        }

    monkeypatch.setattr(tool, "_run_command", fake_run)
    assert tool._run_backend_build(status) is False
    assert "unexpected imported module" in status["import_check_result"]["stderr_tail"]


def test_sr2d_native_build_rejects_import_proof_without_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_build_tool()
    status = tool._cpp_status()

    def fake_run(argv: list[str]) -> dict[str, object]:
        return {
            "argv": list(argv),
            "returncode": 0,
            "stdout_tail": "ok",
            "stderr_tail": "",
        }

    monkeypatch.setattr(tool, "_run_command", fake_run)
    assert tool._run_backend_build(status) is False
    assert status["build_import_verified"] is False
    assert "JSON ABI provenance" in status["import_check_result"]["stderr_tail"]


def test_sr2d_native_build_does_not_claim_import_when_build_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _load_build_tool()
    status = tool._cpp_status()
    calls: list[list[str]] = []

    def fake_run(argv: list[str]) -> dict[str, object]:
        calls.append(list(argv))
        return {"argv": list(argv), "returncode": 7, "stdout_tail": "", "stderr_tail": "failed"}

    monkeypatch.setattr(tool, "_run_command", fake_run)

    assert tool._run_backend_build(status) is False
    assert calls == [status["build_argv"]]
    assert status["import_check_result"] is None
    assert status["build_import_verified"] is False


def test_cpp_cmake_installs_windows_extension_runtime_artifact() -> None:
    cmake = Path("native/sr2d_cpp/CMakeLists.txt").read_text(encoding="utf-8")

    assert "LIBRARY DESTINATION ." in cmake
    assert "RUNTIME DESTINATION ." in cmake

def test_cpp_cmake_supports_explicit_pybind11_header_fallback() -> None:
    cmake = Path("native/sr2d_cpp/CMakeLists.txt").read_text(encoding="utf-8")

    assert "find_package(pybind11 CONFIG QUIET)" in cmake
    assert "PYBIND11_INCLUDE_DIR" in cmake
    assert "Python_add_library" in cmake
    assert "Python::Module" in cmake
    assert "pybind11/pybind11.h" in cmake


def test_cpp_scaffold_preserves_direct_abi_safety_contracts() -> None:
    bindings = Path("native/sr2d_cpp/src/bindings.cpp").read_text(encoding="utf-8")
    kernel = Path("native/sr2d_cpp/src/kernel.cpp").read_text(encoding="utf-8")

    assert "normalize_pvaec_broadphase" in bindings
    assert "entity_count == 0 || dt <= 0.0" in kernel
    assert "SR2D spatial-hash coordinates must be finite" in kernel


