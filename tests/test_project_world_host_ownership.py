from __future__ import annotations

import builtins
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


RUNTIME_ROOT = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


_QAPPLICATION = None


def _ensure_qapplication():
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    global _QAPPLICATION
    _QAPPLICATION = QApplication.instance() or QApplication([])
    return _QAPPLICATION


def _block_pyqt_imports(monkeypatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"Qt-free ownership imported GUI dependency: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


class _Host:
    def __init__(self, serial: int) -> None:
        self.serial = serial


class _Services:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def register(self, key: str, value: object) -> None:
        self.values[key] = value

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def unregister(self, key: str) -> None:
        self.values.pop(key, None)


def test_qt_free_ownership_reuses_host_and_disposes_on_last_release(monkeypatch) -> None:
    _block_pyqt_imports(monkeypatch)
    sys.modules.pop("core.VitaLoom.project.project_world_host_ownership", None)
    from core.VitaLoom.project.project_world_host_ownership import (
        ProjectWorldHostOwnership,
    )

    created: list[_Host] = []
    disposed: list[_Host] = []

    def factory() -> _Host:
        host = _Host(len(created) + 1)
        created.append(host)
        return host

    ownership = ProjectWorldHostOwnership(factory, lambda host: disposed.append(host) or True)
    editor = ownership.acquire("editor")
    player = ownership.acquire("player")

    assert editor.host is player.host
    assert editor.owner == "editor"
    assert player.owner == "player"
    assert ownership.active_lease_count == 2
    assert ownership.owner_labels == ("editor", "player")
    assert len(created) == 1

    assert editor.release()
    assert editor.released
    assert not disposed
    assert ownership.active_lease_count == 1
    assert not editor.release()

    assert player.release()
    assert disposed == [created[0]]
    assert ownership.active_lease_count == 0
    assert ownership.current_host is None

    fresh = ownership.acquire("fresh")
    assert fresh.host is not created[0]
    assert fresh.host.serial == 2
    assert fresh.release()


def test_factory_failure_leaves_no_host_or_lease_and_can_retry() -> None:
    from core.VitaLoom.project.project_world_host_ownership import (
        ProjectWorldHostOwnership,
    )

    calls = 0

    def factory() -> _Host:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("factory failed")
        return _Host(calls)

    ownership = ProjectWorldHostOwnership(factory, lambda _host: True)
    with pytest.raises(RuntimeError, match="factory failed"):
        ownership.acquire("failed")

    assert ownership.current_host is None
    assert ownership.active_lease_count == 0
    lease = ownership.acquire("retry")
    assert lease.host.serial == 2
    assert lease.release()


def test_disposal_failure_keeps_final_lease_active_for_retry() -> None:
    from core.VitaLoom.project.project_world_host_ownership import (
        ProjectWorldHostOwnership,
    )

    attempts = 0

    def dispose(_host: _Host) -> bool:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("dispose failed")
        return True

    ownership = ProjectWorldHostOwnership(lambda: _Host(1), dispose)
    lease = ownership.acquire("editor")

    with pytest.raises(RuntimeError, match="dispose failed"):
        lease.release()
    assert not lease.released
    assert ownership.current_host is lease.host
    assert ownership.active_lease_count == 1

    assert lease.release()
    assert lease.released
    assert attempts == 2
    assert ownership.current_host is None
    assert ownership.active_lease_count == 0


def test_capability_unregister_is_exact_and_does_not_remove_replacement() -> None:
    from core.VitaLoom.project.project_world_capabilities import (
        PROJECT_WORLD_READ_MODEL,
        register_project_world_host_capabilities,
        unregister_project_world_host_capabilities,
    )

    class ReadHost:
        def __init__(self, path: str) -> None:
            self.path = path

        def get_current_project_path(self) -> str:
            return self.path

        def get_current_project_config(self) -> dict[str, str]:
            return {"path": self.path}

    services = _Services()
    first = register_project_world_host_capabilities(services, ReadHost("first"))
    second = register_project_world_host_capabilities(services, ReadHost("second"))

    assert unregister_project_world_host_capabilities(services, first) == ()
    assert services.get(PROJECT_WORLD_READ_MODEL) is second[PROJECT_WORLD_READ_MODEL]
    assert unregister_project_world_host_capabilities(services, second) == (
        PROJECT_WORLD_READ_MODEL,
    )
    assert services.get(PROJECT_WORLD_READ_MODEL) is None


def test_legacy_composition_reuses_exact_singleton_and_creates_fresh_after_release() -> None:
    app = _ensure_qapplication()
    assert app is not None

    from core.VitaLoom.project.project_world_host_composition import (
        acquire_project_world_host,
        dispose_project_world_host_if_idle,
    )

    assert dispose_project_world_host_if_idle()
    editor = acquire_project_world_host("editor-test")
    player = acquire_project_world_host("player-test")
    first = editor.host
    assert player.host is first

    assert player.release()
    assert editor.release()

    fresh = acquire_project_world_host("fresh-test")
    assert fresh.host is not first
    assert fresh.release()
    assert dispose_project_world_host_if_idle()


def test_public_singleton_release_rejects_wrong_expected_instance() -> None:
    app = _ensure_qapplication()
    assert app is not None

    from core.VitaLoom.project.project_manager import (
        get_project_manager,
        release_project_manager_instance,
    )
    from core.VitaLoom.project.project_world_host_composition import (
        dispose_project_world_host_if_idle,
    )

    assert dispose_project_world_host_if_idle()
    current = get_project_manager()

    with pytest.raises(RuntimeError, match="different ProjectManager singleton"):
        release_project_manager_instance(expected=object())

    assert get_project_manager() is current
    assert release_project_manager_instance(expected=current)
    assert not release_project_manager_instance()


def test_borrowed_player_cleanup_does_not_invoke_legacy_disposer(monkeypatch) -> None:
    pytest.importorskip("PyQt6")
    from core.VitaLoom.player.player_shell import PlayerShell
    from core.VitaLoom.project import project_manager

    disposer_calls: list[object | None] = []

    def forbidden_disposer(expected: object | None = None) -> bool:
        disposer_calls.append(expected)
        raise AssertionError("borrowed Player Host must not use the legacy disposer")

    monkeypatch.setattr(
        project_manager,
        "release_project_manager_instance",
        forbidden_disposer,
    )
    borrowed_host = object()
    fake_shell = SimpleNamespace(
        _project_world_host=borrowed_host,
        _project_world_host_lease=None,
        project_world_capabilities={},
    )

    assert PlayerShell._release_project_world_host_lease(fake_shell)
    assert fake_shell._project_world_host is borrowed_host
    assert disposer_calls == []


def test_editor_and_player_entrypoints_use_composition_without_private_singleton_access() -> None:
    main_source = (RUNTIME_ROOT / "main.py").read_text(encoding="utf-8-sig")
    player_source = (
        RUNTIME_ROOT / "core/VitaLoom/player/player_shell.py"
    ).read_text(encoding="utf-8-sig")
    editor_source = (
        RUNTIME_ROOT / "core/VitaLoom/kernel/editor_kernel.py"
    ).read_text(encoding="utf-8-sig")

    for relative, source in {
        "main.py": main_source,
        "player_shell.py": player_source,
    }.items():
        assert "ProjectManager._instance" not in source, relative
        assert "project.project_manager import" not in source, relative

    assert "acquire_project_world_host" in player_source
    assert "acquire_project_world_host" in editor_source
    assert "unregister_project_world_host_capabilities" in player_source
    assert "unregister_project_world_host_capabilities" in editor_source
