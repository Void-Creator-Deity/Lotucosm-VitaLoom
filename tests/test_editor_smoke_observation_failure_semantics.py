# -*- coding: utf-8 -*-
"""E83 regressions for the editor-smoke public plugin observation read-model."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


RUNTIME_MAIN = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
    / "main.py"
)


def _load_editor_main() -> ModuleType:
    spec = importlib.util.spec_from_file_location("editor_smoke_main_under_test", RUNTIME_MAIN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def editor_main() -> ModuleType:
    return _load_editor_main()


def _ready_observation() -> dict[str, object]:
    return {
        "status": "ready",
        "discovery_errors": {},
        "failed_plugins": {},
        "counts": {"active": 3, "catalog": 5},
    }


@pytest.mark.parametrize(
    ("observation", "expected"),
    (
        (None, "plugin observation is unavailable or malformed"),
        (
            {
                "status": "unavailable",
                "discovery_errors": {},
                "failed_plugins": {},
                "counts": {"active": 0, "catalog": 0},
            },
            "plugin host is unavailable",
        ),
        (
            {
                "status": "ready",
                "discovery_errors": None,
                "failed_plugins": {},
                "counts": {"active": 3, "catalog": 5},
            },
            "plugin observation discovery_errors is malformed",
        ),
        (
            {
                "status": "ready",
                "discovery_errors": {},
                "failed_plugins": "plugin-a: failed",
                "counts": {"active": 3, "catalog": 5},
            },
            "plugin observation failed_plugins is malformed",
        ),
        (
            {
                "status": "ready",
                "discovery_errors": {},
                "failed_plugins": {},
            },
            "plugin observation counts is malformed",
        ),
        (
            {
                "status": "ready",
                "discovery_errors": {},
                "failed_plugins": {},
                "counts": {"active": "3", "catalog": 5},
            },
            "plugin observation counts.active is malformed",
        ),
        (
            {
                "status": "ready",
                "discovery_errors": {},
                "failed_plugins": {},
                "counts": {"active": 3},
            },
            "plugin observation counts.catalog is malformed",
        ),
    ),
)
def test_editor_smoke_malformed_public_observation_has_deterministic_failure(
    editor_main: ModuleType,
    observation: object,
    expected: str,
) -> None:
    assert editor_main._editor_smoke_observation_failure(observation) == expected


def test_editor_smoke_valid_public_observation_keeps_ready_and_degraded_facts(
    editor_main: ModuleType,
) -> None:
    assert editor_main._editor_smoke_observation_failure(_ready_observation()) is None

    degraded = _ready_observation()
    degraded["status"] = "degraded"
    degraded["failed_plugins"] = {"plugin-a": "load failed"}
    assert editor_main._editor_smoke_observation_failure(degraded) is None

@pytest.mark.parametrize(
    "observation",
    (
        None,
        {
            "status": "ready",
            "discovery_errors": {},
            "failed_plugins": {},
            "counts": {"active": "3", "catalog": 5},
        },
    ),
)
def test_editor_smoke_reports_malformed_public_observation_without_false_success(
    editor_main: ModuleType,
    observation: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from types import SimpleNamespace

    runtime = SimpleNamespace(
        suite=SimpleNamespace(suite_id="lotucosm"),
        product_version=SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0"),
    )

    assert editor_main._report_editor_smoke_observation(observation, runtime) == 1
    captured = capsys.readouterr()
    assert "Editor smoke FAILED:" in captured.out
    assert "Editor smoke OK:" not in captured.out


def test_editor_smoke_reports_valid_observation_counts(
    editor_main: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from types import SimpleNamespace

    runtime = SimpleNamespace(
        suite=SimpleNamespace(suite_id="lotucosm"),
        product_version=SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0"),
    )

    assert editor_main._report_editor_smoke_observation(_ready_observation(), runtime) == 0
    assert "Editor smoke OK: suite=lotucosm product=lotucosm-vitaloom@1.0.0 plugins=3/5" in capsys.readouterr().out

class _RaisingObservationHost:
    def observe_plugins(self) -> object:
        raise RuntimeError("public observation unavailable")


def test_editor_smoke_converts_public_observation_call_failure_to_exit_one(
    editor_main: ModuleType,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from types import SimpleNamespace

    runtime = SimpleNamespace(
        suite=SimpleNamespace(suite_id="lotucosm"),
        product_version=SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0"),
    )

    assert editor_main._report_editor_smoke_host_observation(_RaisingObservationHost(), runtime) == 1
    captured = capsys.readouterr()
    assert "Editor smoke FAILED: plugin observation is unavailable or malformed" in captured.out
    assert "public observation unavailable" not in captured.out
    assert "Editor smoke OK:" not in captured.out

@pytest.mark.parametrize(
    ("expected_detail", "expects_rollback_marker"),
    (
        ("plain startup failure", False),
        ("Project World rollback did not settle", True),
    ),
)
def test_product_main_distinguishes_unsettled_kernel_rollback_in_startup_diagnostics(
    editor_main: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    expected_detail: str,
    expects_rollback_marker: bool,
) -> None:
    import sys
    from types import SimpleNamespace

    from core.VitaLoom import editor_launcher
    from core.VitaLoom.kernel.editor_kernel import (
        EditorKernelInitializationRollbackError,
    )
    from core.VitaLoom.ui import design_tokens

    runtime = SimpleNamespace(
        product_version=SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0")
    )
    fake_app = object()
    fake_qtwidgets = SimpleNamespace(
        QApplication=SimpleNamespace(instance=lambda: fake_app)
    )
    root_cause = RuntimeError("startup failed")
    startup_exception: Exception = (
        EditorKernelInitializationRollbackError(root_cause)
        if expects_rollback_marker
        else RuntimeError("plain startup failure")
    )

    def raise_startup_failure(*_args: object, **_kwargs: object) -> int:
        if expects_rollback_marker:
            raise startup_exception from root_cause
        raise startup_exception

    monkeypatch.setattr(editor_main, "ensure_cwd_application_root", lambda: None)
    monkeypatch.setattr(editor_main, "bootstrap_suite_runtime", lambda _root: runtime)
    monkeypatch.setattr(editor_main, "resource_root", lambda: Path("repo-e94"))
    monkeypatch.setattr(design_tokens, "apply_app_baseline", lambda _app: None)
    monkeypatch.setattr(editor_launcher, "launch_editor", raise_startup_failure)
    monkeypatch.setitem(sys.modules, "PyQt6", SimpleNamespace(QtWidgets=fake_qtwidgets))
    monkeypatch.setattr(editor_main.sys, "argv", ["main.py"])

    with pytest.raises(SystemExit) as exit_info:
        editor_main.main()

    assert exit_info.value.code == 1
    output = capsys.readouterr().out
    assert "ERROR: failed to start VitaLoom product runtime:" in output
    assert expected_detail in output
    assert ("Project World rollback did not settle" in output) is expects_rollback_marker
def test_product_main_preserves_normal_launcher_exit_code_without_shutdown(
    editor_main: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """E114: product main preserves launcher exit while keeping shutdown ownership out."""
    import os
    import sys
    from types import SimpleNamespace

    from core.VitaLoom import editor_launcher
    from core.VitaLoom.ui import design_tokens

    calls: list[str] = []
    exit_code = 76
    fake_app = object()
    runtime = SimpleNamespace(
        product_version=SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0")
    )
    fake_qapplication = SimpleNamespace(
        instance=lambda: fake_app,
        quit=lambda: calls.append("app.quit"),
        close=lambda: calls.append("app.close"),
        shutdown=lambda: calls.append("app.shutdown"),
        deleteLater=lambda: calls.append("app.deleteLater"),
    )
    fake_qtwidgets = SimpleNamespace(QApplication=fake_qapplication)

    def return_launcher_exit(
        received_app: object,
        repo_root: str,
        *,
        project_path: str | None,
        use_splash: bool,
    ) -> int:
        assert received_app is fake_app
        assert repo_root == "repo-e114"
        assert project_path == os.path.abspath("project-e114.pond")
        assert use_splash is True
        calls.append("launch_editor")
        return exit_code

    monkeypatch.setattr(editor_main, "ensure_cwd_application_root", lambda: calls.append("cwd"))
    monkeypatch.setattr(editor_main, "bootstrap_suite_runtime", lambda _root: runtime)
    monkeypatch.setattr(editor_main, "resource_root", lambda: Path("repo-e114"))
    monkeypatch.setattr(
        design_tokens,
        "apply_app_baseline",
        lambda received_app: calls.append("baseline") if received_app is fake_app else None,
    )
    monkeypatch.setattr(editor_launcher, "launch_editor", return_launcher_exit)
    monkeypatch.setitem(sys.modules, "PyQt6", SimpleNamespace(QtWidgets=fake_qtwidgets))
    monkeypatch.setattr(
        editor_main.sys,
        "argv",
        ["runtime-main.py", "--project", "project-e114.pond"],
    )

    with pytest.raises(SystemExit) as exit_info:
        editor_main.main()

    assert exit_info.value.code == exit_code
    assert calls == ["cwd", "baseline", "launch_editor"]
    assert capsys.readouterr().out == "VitaLoom Editor starting: lotucosm-vitaloom@1.0.0\n"
