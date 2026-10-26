# -*- coding: utf-8 -*-
"""E66 timing proofs for the legacy Editor layout-restoration projection."""
from __future__ import annotations

import logging
from types import SimpleNamespace

from core.VitaLoom.kernel.editor_kernel import EditorKernel


class _SynchronousLayeredLoader:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    def load_from_layered_directories(self, _layers):
        self._calls.append("host-finalized")
        return {"status": "settled"}


def test_layered_discovery_finishes_before_layout_restore_is_scheduled() -> None:
    calls: list[str] = []
    fake_kernel = SimpleNamespace(
        plugin_loader=_SynchronousLayeredLoader(calls),
        _schedule_post_plugin_init=lambda: calls.append("restore-scheduled"),
    )

    EditorKernel.load_plugins_layered(fake_kernel, {"official_mod": []})

    assert calls == ["host-finalized", "restore-scheduled"]


def test_post_plugin_callback_restores_before_opening_project(monkeypatch) -> None:
    calls: list[str] = []
    scheduled: list[tuple[int, object]] = []
    fake_kernel = SimpleNamespace(
        layout_manager=SimpleNamespace(
            restore_layout=lambda: calls.append("restore") or False,
            apply_default_workspace_layout=lambda: calls.append("default"),
        ),
        _try_open_last_project_on_startup=lambda: calls.append("project"),
    )

    from PyQt6.QtCore import QTimer

    monkeypatch.setattr(
        QTimer,
        "singleShot",
        lambda delay, callback: scheduled.append((delay, callback)),
    )
    EditorKernel._schedule_post_plugin_init(fake_kernel, delay_ms=0)

    assert calls == []
    assert len(scheduled) == 1
    assert scheduled[0][0] == 0
    scheduled[0][1]()

    assert calls == ["restore", "default", "project"]


def test_explicit_startup_project_precedes_last_project_fallback(tmp_path) -> None:
    pending = tmp_path / "explicit-project"
    pending.mkdir()
    (pending / "project.json").write_text("{}", encoding="utf-8")
    calls: list[tuple[str, str]] = []

    class Host:
        def open_project(self, project_path: str) -> None:
            calls.append(("explicit", project_path))

        def open_last_project_on_startup(self) -> None:
            calls.append(("fallback", ""))

    fake_kernel = SimpleNamespace(
        project_world_session_host=Host(),
        _startup_project_path=str(pending),
    )

    EditorKernel._try_open_last_project_on_startup(fake_kernel)

    assert calls == [("explicit", str(pending))]


def test_absent_or_invalid_startup_project_uses_existing_host_fallback(tmp_path) -> None:
    invalid = tmp_path / "missing-project-metadata"
    invalid.mkdir()

    for pending in (None, str(invalid)):
        calls: list[str] = []

        class Host:
            def open_project(self, _project_path: str) -> None:
                calls.append("explicit")

            def open_last_project_on_startup(self) -> None:
                calls.append("fallback")

        fake_kernel = SimpleNamespace(
            project_world_session_host=Host(),
            _startup_project_path=pending,
        )

        EditorKernel._try_open_last_project_on_startup(fake_kernel)

        assert calls == ["fallback"]


def test_explicit_project_host_failure_is_contained_without_fallback(caplog, tmp_path) -> None:
    pending = tmp_path / "failing-explicit-project"
    pending.mkdir()
    (pending / "project.json").write_text("{}", encoding="utf-8")
    calls: list[str] = []

    class Host:
        def open_project(self, _project_path: str) -> None:
            calls.append("explicit")
            raise RuntimeError("explicit project open failed")

        def open_last_project_on_startup(self) -> None:
            calls.append("fallback")

    fake_kernel = SimpleNamespace(
        project_world_session_host=Host(),
        _startup_project_path=str(pending),
    )

    with caplog.at_level(logging.WARNING):
        EditorKernel._try_open_last_project_on_startup(fake_kernel)

    assert calls == ["explicit"]
    assert "explicit project open failed" in caplog.text



def test_successful_explicit_startup_project_is_consumed_after_first_open(tmp_path) -> None:
    pending = tmp_path / "one-shot-explicit-project"
    pending.mkdir()
    (pending / "project.json").write_text("{}", encoding="utf-8")
    calls: list[str] = []

    class Host:
        def open_project(self, _project_path: str) -> None:
            calls.append("explicit")

        def open_last_project_on_startup(self) -> None:
            calls.append("fallback")

    fake_kernel = SimpleNamespace(
        project_world_session_host=Host(),
        _startup_project_path=str(pending),
    )

    EditorKernel._try_open_last_project_on_startup(fake_kernel)
    EditorKernel._try_open_last_project_on_startup(fake_kernel)

    assert calls == ["explicit", "fallback"]
    assert fake_kernel._startup_project_path is None


def test_failed_explicit_startup_project_remains_available_for_retry(caplog, tmp_path) -> None:
    pending = tmp_path / "retry-explicit-project"
    pending.mkdir()
    (pending / "project.json").write_text("{}", encoding="utf-8")
    calls: list[str] = []

    class Host:
        def open_project(self, _project_path: str) -> None:
            calls.append("explicit")
            if len(calls) == 1:
                raise RuntimeError("first explicit open failed")

        def open_last_project_on_startup(self) -> None:
            calls.append("fallback")

    fake_kernel = SimpleNamespace(
        project_world_session_host=Host(),
        _startup_project_path=str(pending),
    )

    with caplog.at_level(logging.WARNING):
        EditorKernel._try_open_last_project_on_startup(fake_kernel)
    assert fake_kernel._startup_project_path == str(pending)

    EditorKernel._try_open_last_project_on_startup(fake_kernel)
    EditorKernel._try_open_last_project_on_startup(fake_kernel)

    assert calls == ["explicit", "explicit", "fallback"]
    assert fake_kernel._startup_project_path is None
    assert "first explicit open failed" in caplog.text


def test_later_valid_startup_project_replaces_an_invalid_pending_path(tmp_path) -> None:
    invalid = tmp_path / "invalid-project"
    invalid.mkdir()
    valid = tmp_path / "valid-project"
    valid.mkdir()
    (valid / "project.json").write_text("{}", encoding="utf-8")
    calls: list[tuple[str, str]] = []

    class Host:
        def open_project(self, project_path: str) -> None:
            calls.append(("explicit", project_path))

        def open_last_project_on_startup(self) -> None:
            calls.append(("fallback", ""))

    fake_kernel = SimpleNamespace(
        project_world_session_host=Host(),
        _startup_project_path=str(invalid),
    )

    EditorKernel._try_open_last_project_on_startup(fake_kernel)
    EditorKernel.set_startup_project(fake_kernel, str(valid))
    EditorKernel._try_open_last_project_on_startup(fake_kernel)

    assert calls == [("fallback", ""), ("explicit", str(valid))]
    assert fake_kernel._startup_project_path is None
