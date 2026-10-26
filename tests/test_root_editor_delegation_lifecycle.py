# -*- coding: utf-8 -*-
"""E115 root-entry delegation and lifecycle-unload regressions."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT_MAIN = Path(__file__).resolve().parents[1] / "main.py"


def test_root_editor_delegation_preserves_exit_and_unloads_frame_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E115: root keeps versioned Qt ownership below FrameCore delegation."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 77
    expected_suite = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0")

    class Plugin:
        pass

    plugin = Plugin()

    class FakeLifecycleRunner:
        def __init__(self) -> None:
            calls.append("lifecycle.construct")

        def load(self, received_plugin: object, received_api: object) -> None:
            assert received_plugin is plugin
            assert isinstance(received_api, FakeFrameApi)
            calls.append("lifecycle.load")

        def unload_all(self) -> None:
            calls.append("lifecycle.unload_all")

    class FakeFrameApi:
        def __init__(self, *, app_root: Path, resource_root: Path, suite: object) -> None:
            assert app_root == ROOT_MAIN.parent
            assert resource_root == ROOT_MAIN.parent
            assert suite is expected_suite
            calls.append("frame_api.construct")

        def create_lifecycle_plugin(self) -> Plugin:
            calls.append("frame_api.create_plugin")
            return plugin

        def select_product_version(self, product_id: str) -> object:
            assert product_id == "lotucosm-vitaloom"
            calls.append("frame_api.select_product")
            return version

        def run_product_entry(
            self,
            received_version: object,
            entry: str,
            extra_args: list[str] | None,
        ) -> None:
            assert received_version is version
            assert entry == "editor"
            assert extra_args == ["--editor"]
            calls.append("frame_api.run_product_entry")
            raise SystemExit(exit_code)

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or expected_suite,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", FakeFrameApi)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", FakeLifecycleRunner)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "--editor"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_editor_delegation_preserves_failure_identity_and_unloads_frame_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E116: root finally unloads Frame lifecycle without translating entry errors."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    expected_error = RuntimeError("controlled delegated editor failure")
    expected_suite = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0")

    class Plugin:
        pass

    plugin = Plugin()

    class FakeLifecycleRunner:
        def __init__(self) -> None:
            calls.append("lifecycle.construct")

        def load(self, received_plugin: object, received_api: object) -> None:
            assert received_plugin is plugin
            assert isinstance(received_api, FakeFrameApi)
            calls.append("lifecycle.load")

        def unload_all(self) -> None:
            calls.append("lifecycle.unload_all")

    class FakeFrameApi:
        def __init__(self, *, app_root: Path, resource_root: Path, suite: object) -> None:
            assert app_root == ROOT_MAIN.parent
            assert resource_root == ROOT_MAIN.parent
            assert suite is expected_suite
            calls.append("frame_api.construct")

        def create_lifecycle_plugin(self) -> Plugin:
            calls.append("frame_api.create_plugin")
            return plugin

        def select_product_version(self, product_id: str) -> object:
            assert product_id == "lotucosm-vitaloom"
            calls.append("frame_api.select_product")
            return version

        def run_product_entry(
            self,
            received_version: object,
            entry: str,
            extra_args: list[str] | None,
        ) -> None:
            assert received_version is version
            assert entry == "editor"
            assert extra_args == ["--editor"]
            calls.append("frame_api.run_product_entry")
            raise expected_error

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or expected_suite,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", FakeFrameApi)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", FakeLifecycleRunner)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "--editor"])

    with pytest.raises(RuntimeError) as error_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert error_info.value is expected_error
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def _run_root_with_raising_lifecycle_unload(
    monkeypatch: pytest.MonkeyPatch,
    *,
    entry_error: BaseException | None,
) -> tuple[list[str], RuntimeError]:
    """Configure root __main__ doubles with a transparent cleanup failure."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    cleanup_error = RuntimeError("controlled root lifecycle-unload failure")
    suite = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = object()
    plugin = object()

    def create_plugin() -> object:
        calls.append("frame_api.create_plugin")
        return plugin

    def select_product_version(product_id: str) -> object:
        assert product_id == "lotucosm-vitaloom"
        calls.append("frame_api.select_product")
        return version

    def run_product_entry(
        received_version: object,
        entry: str,
        extra_args: list[str] | None,
    ) -> None:
        assert received_version is version
        assert entry == "editor"
        assert extra_args == ["--editor"]
        calls.append("frame_api.run_product_entry")
        if entry_error is not None:
            raise entry_error

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=create_plugin,
        select_product_version=select_product_version,
        run_product_entry=run_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    def load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def unload_all() -> None:
        calls.append("lifecycle.unload_all")
        raise cleanup_error

    suite_manifest = suite
    runner = SimpleNamespace(load=load, unload_all=unload_all)
    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(
        lifecycle,
        "LifecycleRunner",
        lambda: calls.append("lifecycle.construct") or runner,
    )
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "--editor"])
    return calls, cleanup_error


def test_root_cleanup_failure_preserves_identity_after_successful_delegation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E117: successful delegation does not suppress cleanup failure identity."""
    calls, cleanup_error = _run_root_with_raising_lifecycle_unload(
        monkeypatch,
        entry_error=None,
    )

    with pytest.raises(RuntimeError) as error_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert error_info.value is cleanup_error
    assert error_info.value.__context__ is None
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_cleanup_failure_chains_delegated_editor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E117: cleanup failure retains delegated failure as Python context."""
    entry_error = RuntimeError("controlled delegated editor failure")
    calls, cleanup_error = _run_root_with_raising_lifecycle_unload(
        monkeypatch,
        entry_error=entry_error,
    )

    with pytest.raises(RuntimeError) as error_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert error_info.value is cleanup_error
    assert error_info.value.__context__ is entry_error
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_command_delegation_preserves_failure_and_unloads_frame_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E118: root command delegation stays transparent and Qt-free."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    expected_error = RuntimeError("controlled delegated command failure")
    suite = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = object()
    plugin = object()

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=lambda received_plugin, received_api: (
                assert_load(received_plugin, received_api)
            ),
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def create_plugin() -> object:
        calls.append("frame_api.create_plugin")
        return plugin

    def select_product_version(product_id: str) -> object:
        assert product_id == "lotucosm-vitaloom"
        calls.append("frame_api.select_product")
        return version

    def run_product_entry(
        received_version: object,
        entry: str,
        extra_args: list[str] | None,
    ) -> None:
        assert received_version is version
        assert entry == "command"
        assert extra_args == ["inspect", "--strict"]
        calls.append("frame_api.run_product_entry")
        raise expected_error

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=create_plugin,
        select_product_version=select_product_version,
        run_product_entry=run_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    suite_manifest = suite
    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "command", "inspect", "--strict"])

    with pytest.raises(RuntimeError) as error_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert error_info.value is expected_error
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_command_delegation_preserves_exit_and_unloads_frame_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E119: root command SystemExit remains exact through the finally path."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 73
    suite = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = object()
    plugin = object()

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=assert_load,
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    def create_plugin() -> object:
        calls.append("frame_api.create_plugin")
        return plugin

    def select_product_version(product_id: str) -> object:
        assert product_id == "lotucosm-vitaloom"
        calls.append("frame_api.select_product")
        return version

    def run_product_entry(
        received_version: object,
        entry: str,
        extra_args: list[str] | None,
    ) -> None:
        assert received_version is version
        assert entry == "command"
        assert extra_args == ["inspect", "--strict"]
        calls.append("frame_api.run_product_entry")
        raise SystemExit(exit_code)

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=create_plugin,
        select_product_version=select_product_version,
        run_product_entry=run_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    suite_manifest = suite
    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "command", "inspect", "--strict"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_version_query_formats_metadata_without_product_entry_and_unloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """E120: root version query stays in L0 and still releases lifecycle once."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    suite_manifest = SimpleNamespace(
        suite_id="lotucosm.vitaloom.suite",
        display_name="VitaLoom Suite",
        version="2026.7",
    )
    version = SimpleNamespace(product_id="lotucosm-vitaloom", version="1.0.0")
    plugin = object()

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=assert_load,
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    def create_plugin() -> object:
        calls.append("frame_api.create_plugin")
        return plugin

    def select_product_version(product_id: str) -> object:
        assert product_id == "lotucosm-vitaloom"
        calls.append("frame_api.select_product")
        return version

    def unexpected_product_entry(*args: object, **kwargs: object) -> None:
        calls.append("frame_api.run_product_entry")
        raise AssertionError("--version must not dispatch a product entry")

    frame_api = SimpleNamespace(
        suite=suite_manifest,
        create_lifecycle_plugin=create_plugin,
        select_product_version=select_product_version,
        run_product_entry=unexpected_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "--version"])

    runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert capsys.readouterr().out == "VitaLoom Suite 2026.7 / lotucosm-vitaloom 1.0.0\n"
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_hub_delegation_preserves_exit_without_product_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E121: default Hub routing remains a Frame-only L0 operation."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 19
    suite_manifest = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")

    def run_hub_entry(entry: str, args: list[str] | None) -> int:
        assert entry == "hub"
        assert args == []
        calls.append("frame_plugin.run_entry")
        return exit_code

    plugin = SimpleNamespace(run_entry=run_hub_entry)

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=assert_load,
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    def create_plugin() -> object:
        calls.append("frame_api.create_plugin")
        return plugin

    def unexpected_product_selection(*args: object, **kwargs: object) -> object:
        calls.append("frame_api.select_product")
        raise AssertionError("default Hub must not select a product version")

    def unexpected_product_entry(*args: object, **kwargs: object) -> None:
        calls.append("frame_api.run_product_entry")
        raise AssertionError("default Hub must not dispatch a product entry")

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=create_plugin,
        select_product_version=unexpected_product_selection,
        run_product_entry=unexpected_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN)])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_plugin.run_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_hub_smoke_delegation_preserves_exit_without_product_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E122: Hub-smoke remains Frame-only and unloads once after exit."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 23
    suite_manifest = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")

    def run_hub_entry(entry: str, args: list[str] | None) -> int:
        assert entry == "hub_smoke"
        assert args == ["--smoke-hub"]
        calls.append("frame_plugin.run_entry")
        return exit_code

    plugin = SimpleNamespace(run_entry=run_hub_entry)

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=assert_load,
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=lambda: calls.append("frame_api.create_plugin") or plugin,
        select_product_version=lambda *args: (_ for _ in ()).throw(
            AssertionError("Hub-smoke must not select a product")
        ),
        run_product_entry=lambda *args: (_ for _ in ()).throw(
            AssertionError("Hub-smoke must not dispatch a product entry")
        ),
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), "--smoke-hub"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_plugin.run_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


def test_root_hub_forwards_non_product_arguments_without_product_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E123: default Hub receives every non-product root argument unchanged."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 29
    suite_manifest = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    expected_args = ["--safe-mode", "workspace.pond"]

    def run_hub_entry(entry: str, args: list[str] | None) -> int:
        assert entry == "hub"
        assert args == expected_args
        calls.append("frame_plugin.run_entry")
        return exit_code

    plugin = SimpleNamespace(run_entry=run_hub_entry)

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=lambda received_plugin, received_api: (
                calls.append("lifecycle.load")
                if received_plugin is plugin and received_api is frame_api
                else (_ for _ in ()).throw(AssertionError("unexpected lifecycle load"))
            ),
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=lambda: calls.append("frame_api.create_plugin") or plugin,
        select_product_version=lambda *args: (_ for _ in ()).throw(
            AssertionError("default Hub must not select a product")
        ),
        run_product_entry=lambda *args: (_ for _ in ()).throw(
            AssertionError("default Hub must not dispatch a product entry")
        ),
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), *expected_args])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_plugin.run_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1


@pytest.mark.parametrize(
    "editor_args",
    [
        ["--smoke-editor"],
        ["--project", "workspace.pond"],
    ],
)
def test_root_editor_selectors_forward_exact_args_and_unload(
    monkeypatch: pytest.MonkeyPatch,
    editor_args: list[str],
) -> None:
    """E124: every remaining root editor selector uses versioned entry routing."""
    import FrameCore.lifecycle as lifecycle
    import FrameCore.suite_registry as suite_registry

    calls: list[str] = []
    exit_code = 61
    suite_manifest = SimpleNamespace(suite_id="lotucosm.vitaloom.suite")
    version = object()
    plugin = object()

    def assert_load(received_plugin: object, received_api: object) -> None:
        assert received_plugin is plugin
        assert received_api is frame_api
        calls.append("lifecycle.load")

    def construct_lifecycle() -> object:
        calls.append("lifecycle.construct")
        return SimpleNamespace(
            load=assert_load,
            unload_all=lambda: calls.append("lifecycle.unload_all"),
        )

    def select_product_version(product_id: str) -> object:
        assert product_id == "lotucosm-vitaloom"
        calls.append("frame_api.select_product")
        return version

    def run_product_entry(
        received_version: object,
        entry: str,
        extra_args: list[str] | None,
    ) -> None:
        assert received_version is version
        assert entry == "editor"
        assert extra_args == editor_args
        calls.append("frame_api.run_product_entry")
        raise SystemExit(exit_code)

    frame_api = SimpleNamespace(
        create_lifecycle_plugin=lambda: calls.append("frame_api.create_plugin") or plugin,
        select_product_version=select_product_version,
        run_product_entry=run_product_entry,
    )

    def construct_api(*, app_root: Path, resource_root: Path, suite: object) -> object:
        assert app_root == ROOT_MAIN.parent
        assert resource_root == ROOT_MAIN.parent
        assert suite is suite_manifest
        calls.append("frame_api.construct")
        return frame_api

    monkeypatch.setattr(
        suite_registry,
        "load_default_suite_manifest",
        lambda resource_root: calls.append("suite.load") or suite_manifest,
    )
    monkeypatch.setattr(lifecycle, "FrameApi", construct_api)
    monkeypatch.setattr(lifecycle, "LifecycleRunner", construct_lifecycle)
    monkeypatch.setattr(sys, "argv", [str(ROOT_MAIN), *editor_args])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT_MAIN), run_name="__main__")

    assert exit_info.value.code == exit_code
    assert calls == [
        "lifecycle.construct",
        "suite.load",
        "frame_api.construct",
        "frame_api.create_plugin",
        "lifecycle.load",
        "frame_api.select_product",
        "frame_api.run_product_entry",
        "lifecycle.unload_all",
    ]
    assert calls.count("lifecycle.unload_all") == 1
