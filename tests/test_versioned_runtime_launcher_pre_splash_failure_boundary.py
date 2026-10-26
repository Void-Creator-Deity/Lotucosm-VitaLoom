# -*- coding: utf-8 -*-
"""E133 proofs for failures before the versioned Launcher owns a splash."""
from __future__ import annotations

import pytest


class _ExplodingPath:
    def __init__(self, error: BaseException, calls: list[str], label: str) -> None:
        self._error = error
        self._calls = calls
        self._label = label

    def __fspath__(self) -> str:
        self._calls.append(f"{self._label}.fspath")
        raise self._error


def _forbid_post_validation_startup(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("pre-splash failure must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("pre-splash failure must not create a splash"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("pre-splash failure must not attempt splash cleanup"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("pre-splash failure must not resolve plugin layers"),
    )


@pytest.mark.parametrize(
    ("failure_origin", "primary_error", "expected_calls"),
    [
        ("repo_root", SystemExit(141), ["repo_root.fspath"]),
        ("project_path", SystemExit(143), ["project_path.fspath"]),
    ],
)
def test_launcher_preserves_pathlike_system_exit_before_splash_allocation(
    monkeypatch: pytest.MonkeyPatch,
    failure_origin: str,
    primary_error: SystemExit,
    expected_calls: list[str],
) -> None:
    """Path normalization exits before any Launcher-owned resource exists."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_post_validation_startup(monkeypatch, calls)

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("pre-splash SystemExit must not enter app.exec()")

    if failure_origin == "repo_root":
        repo_root: object = _ExplodingPath(primary_error, calls, "repo_root")
        project_path: object | None = None
    else:
        repo_root = "repo-e133"
        project_path = _ExplodingPath(primary_error, calls, "project_path")

    with pytest.raises(SystemExit) as captured:
        editor_launcher.launch_editor(
            App(),
            repo_root,
            project_path=project_path,
        )

    assert captured.value is primary_error
    assert captured.value.code == primary_error.code
    assert calls == expected_calls


@pytest.mark.parametrize("primary_error", [SystemExit(145), RuntimeError("exec lookup failed")])
def test_launcher_preserves_application_protocol_failure_before_splash_allocation(
    monkeypatch: pytest.MonkeyPatch,
    primary_error: BaseException,
) -> None:
    """The event-loop capability lookup fails before splash and Kernel startup."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_post_validation_startup(monkeypatch, calls)

    class App:
        @property
        def exec(self) -> object:
            calls.append("app.exec.lookup")
            raise primary_error

    with pytest.raises(type(primary_error)) as captured:
        editor_launcher.launch_editor(App(), "repo-e133-app-protocol")

    assert captured.value is primary_error
    if isinstance(primary_error, SystemExit):
        assert captured.value.code == primary_error.code
    assert calls == ["app.exec.lookup"]


@pytest.mark.parametrize(
    ("parameter_name", "invalid_value", "error_match"),
    [
        ("capability_registry", object(), "runtime capability registry"),
        ("event_bus", object(), "runtime event bus"),
    ],
)
def test_launcher_rejects_invalid_injected_service_before_event_loop_or_splash(
    monkeypatch: pytest.MonkeyPatch,
    parameter_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    """Protocol TypeError has no resource cleanup because nothing was acquired."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_post_validation_startup(monkeypatch, calls)

    class App:
        @property
        def exec(self) -> object:
            calls.append("app.exec.lookup")
            pytest.fail("invalid service must fail before app event-loop validation")

    with pytest.raises(TypeError, match=error_match):
        editor_launcher.launch_editor(
            App(),
            "repo-e133-invalid-service",
            **{parameter_name: invalid_value},
        )

    assert calls == []


def test_launcher_keeps_keyboard_interrupt_outside_pre_splash_cleanup_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KeyboardInterrupt before allocation remains unclassified and cleanup-free."""

    from core.VitaLoom import editor_launcher

    calls: list[str] = []
    _forbid_post_validation_startup(monkeypatch, calls)
    interrupt = KeyboardInterrupt()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("KeyboardInterrupt must not enter app.exec()")

    with pytest.raises(KeyboardInterrupt) as captured:
        editor_launcher.launch_editor(
            App(),
            _ExplodingPath(interrupt, calls, "repo_root"),
        )

    assert captured.value is interrupt
    assert calls == ["repo_root.fspath"]