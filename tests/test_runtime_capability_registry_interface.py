# -*- coding: utf-8 -*-
"""E14 proofs for the Qt-free L1 runtime capability registry seam."""
from __future__ import annotations

import builtins
import logging
import os
import importlib
import inspect
import sys
from pathlib import Path

import pytest


MODULE_NAME = "core.VitaLoom.core.runtime_capability_registry"


def _registry_module():
    return importlib.import_module(MODULE_NAME)


def test_runtime_registry_module_import_is_qt_free(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    parent = importlib.import_module("core.VitaLoom.core")
    parent_attribute = "runtime_capability_registry"
    missing = object()
    previous_parent_attribute = vars(parent).get(parent_attribute, missing)
    previous = sys.modules.pop(MODULE_NAME, None)
    try:
        module = importlib.import_module(MODULE_NAME)
        assert module.InMemoryRuntimeCapabilityRegistry.__name__ == (
            "InMemoryRuntimeCapabilityRegistry"
        )
    finally:
        sys.modules.pop(MODULE_NAME, None)
        if previous is not None:
            sys.modules[MODULE_NAME] = previous
        if previous_parent_attribute is missing:
            vars(parent).pop(parent_attribute, None)
        else:
            setattr(parent, parent_attribute, previous_parent_attribute)

def test_in_memory_registry_has_strict_key_contract_and_basic_operations() -> None:
    module = _registry_module()
    registry = module.InMemoryRuntimeCapabilityRegistry()
    capability = object()

    registry.register("  runtime.example  ", capability)
    assert registry.has("runtime.example") is True
    assert registry.get(" runtime.example ") is capability

    registry.unregister(" runtime.example ")
    assert registry.has("runtime.example") is False
    assert registry.get("runtime.example", "missing") == "missing"

    for invalid in (None, 1, object()):
        with pytest.raises(TypeError, match="must be a string"):
            registry.register(invalid, object())
    with pytest.raises(ValueError, match="must not be empty"):
        registry.register("   ", object())
    with pytest.raises(ValueError, match="must not be None"):
        registry.register("runtime.none", None)


def test_registry_is_compatible_with_e13_publication_lease() -> None:
    module = _registry_module()
    from core.VitaLoom.core.capability_publication import publish_capabilities

    registry = module.InMemoryRuntimeCapabilityRegistry()
    capability = object()
    lease = publish_capabilities(
        registry,
        owner="tests.e14",
        capabilities={"runtime.capability": capability},
    )

    assert registry.get("runtime.capability") is capability
    release = lease.release()
    assert release.removed_keys == ("runtime.capability",)
    assert registry.has("runtime.capability") is False


def test_l0_and_l1_registries_are_structurally_and_state_isolated() -> None:
    module = _registry_module()
    from FrameCore.service_registry import ServiceRegistry as FrameServiceRegistry

    l0_registry = FrameServiceRegistry()
    l1_registry = module.InMemoryRuntimeCapabilityRegistry()
    l0_capability = object()
    l1_capability = object()

    l0_registry.register("shared.spelling", l0_capability)
    l1_registry.register("shared.spelling", l1_capability)

    assert l0_registry.get("shared.spelling") is l0_capability
    assert l1_registry.get("shared.spelling") is l1_capability
    assert not isinstance(l0_registry, module.RuntimeCapabilityRegistry)
    assert isinstance(l1_registry, module.RuntimeCapabilityRegistry)


def test_legacy_editor_context_service_registry_name_remains_compatible() -> None:
    module = _registry_module()
    from core.VitaLoom.core.editor_context import ServiceRegistry

    assert ServiceRegistry is module.InMemoryRuntimeCapabilityRegistry


def test_editor_context_binds_explicit_registry_once() -> None:
    module = _registry_module()
    from core.VitaLoom.core.editor_context import EditorContext, get_editor_context

    previous = EditorContext._instance
    EditorContext._instance = None
    first = module.InMemoryRuntimeCapabilityRegistry()
    second = module.InMemoryRuntimeCapabilityRegistry()
    try:
        context = get_editor_context(first)
        assert context.services is first
        assert get_editor_context(first) is context
        with pytest.raises(RuntimeError, match="already bound"):
            get_editor_context(second)
    finally:
        EditorContext._instance = previous


def test_editor_kernel_binds_explicit_registry_before_first_translation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _registry_module()
    from core.VitaLoom.core.editor_context import (
        EditorContext,
        get_existing_editor_context,
    )
    from core.VitaLoom.kernel import editor_kernel

    class StopAfterWindowSetup(RuntimeError):
        pass

    registry = module.InMemoryRuntimeCapabilityRegistry()
    previous = EditorContext._instance
    EditorContext._instance = None

    def translated_title(self, key: str, default: str = "") -> str:
        context = get_existing_editor_context()
        assert context is not None
        assert context.services is registry
        return default or key

    def stop_before_runtime_managers(_kernel) -> None:
        raise StopAfterWindowSetup("window setup completed")

    monkeypatch.setattr(editor_kernel, "PluginLoader", stop_before_runtime_managers)
    monkeypatch.setattr(editor_kernel.EditorKernel, "_t", translated_title)
    try:
        with pytest.raises(StopAfterWindowSetup, match="window setup completed"):
            editor_kernel.EditorKernel(capability_registry=registry)
    finally:
        EditorContext._instance = previous


def test_resolver_accepts_registry_explicit_command_context_and_legacy_context() -> None:
    module = _registry_module()
    registry = module.InMemoryRuntimeCapabilityRegistry()
    legacy_context = type("LegacyContext", (), {"services": registry})()

    assert module.resolve_runtime_capability_registry(registry) is registry
    assert module.resolve_runtime_capability_registry(
        {module.RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: registry}
    ) is registry
    assert module.resolve_runtime_capability_registry(
        {"editor_context": legacy_context}
    ) is registry
    assert module.resolve_runtime_capability_registry(legacy_context) is registry


def test_headless_runtime_command_resolves_explicit_registry_without_editor_context() -> None:
    module = _registry_module()
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.service_keys import PS_RUNTIME_SNAPSHOT_HOST

    class Host:
        def discover_ps_runtime_organisms(self):
            return {
                "schema_version": 1,
                "status": "ok",
                "scope": "ps_runtime_organism_discovery",
                "authority": "test",
                "track": "ps",
                "read_only": True,
                "identity_relation": "explicit",
                "run_id": "run-e14",
                "identities": [],
            }

        def query_ps_runtime_organism_snapshot(self, identity):
            return {"status": "ok", "identity": identity}

    registry = module.InMemoryRuntimeCapabilityRegistry()
    registry.register(PS_RUNTIME_SNAPSHOT_HOST, Host())

    result = get_command_registry().run(
        "runtime.ps.organism_discovery",
        {},
        context={module.RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: registry},
    )

    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
    assert result["result"]["run_id"] == "run-e14"


def test_project_world_consumer_resolves_explicit_registry_and_command_context() -> None:
    module = _registry_module()
    from core.VitaLoom.core.service_keys import PROJECT_WORLD_READ_MODEL
    from core.VitaLoom.project.project_world_capabilities import (
        get_project_world_read_model,
    )

    class ReadModel:
        def current_project_world_path(self) -> str:
            return "project-e14"

        def current_project_world_config(self) -> dict[str, object]:
            return {"name": "E14"}

    registry = module.InMemoryRuntimeCapabilityRegistry()
    read_model = ReadModel()
    registry.register(PROJECT_WORLD_READ_MODEL, read_model)

    assert get_project_world_read_model(registry) is read_model
    assert get_project_world_read_model(
        {module.RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: registry}
    ) is read_model


def test_ps_service_consumer_resolves_explicit_registry_and_command_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _registry_module()
    from core.VitaLoom.simulation import ps_experiment_service as ps_module

    class FakePsExperimentService:
        pass

    service = FakePsExperimentService()
    registry = module.InMemoryRuntimeCapabilityRegistry()
    registry.register(ps_module.SERVICE_KEY, service)
    monkeypatch.setattr(ps_module, "PsExperimentService", FakePsExperimentService)

    assert ps_module.get_ps_experiment_service(registry) is service
    assert ps_module.get_ps_experiment_service(
        {module.RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: registry}
    ) is service


def test_editor_player_and_cli_expose_explicit_registry_composition_seams() -> None:
    from core.VitaLoom.commands import cli
    from core.VitaLoom.editor_launcher import launch_editor
    from core.VitaLoom.kernel.editor_kernel import EditorKernel
    from core.VitaLoom.player.player_shell import (
        PlayerShell,
        run_player_shell,
        run_player_smoke,
    )

    for callable_object in (
        EditorKernel,
        launch_editor,
        PlayerShell,
        run_player_shell,
        run_player_smoke,
    ):
        assert "capability_registry" in inspect.signature(callable_object).parameters
    assert "capability_registry" in inspect.signature(cli.main).parameters


def test_cli_run_composes_and_forwards_runtime_registry(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _registry_module()
    from core.VitaLoom.commands import cli

    runtime_registry = module.InMemoryRuntimeCapabilityRegistry()
    captured: dict[str, object] = {}

    class Commands:
        def run(self, command_id, payload, *, context=None):
            captured.update(
                command_id=command_id,
                payload=payload,
                context=context,
            )
            return {"ok": True, "result": {}, "events": [], "warnings": [], "error": None}

    monkeypatch.setattr(cli, "get_command_registry", lambda: Commands())

    assert cli.main(
        ["run", "runtime.ps.organism_discovery"],
        capability_registry=runtime_registry,
    ) == 0
    assert captured["context"] == {
        module.RUNTIME_CAPABILITY_REGISTRY_CONTEXT_KEY: runtime_registry
    }
    assert '"ok": true' in capsys.readouterr().out


def test_launch_editor_forwards_the_exact_registry_to_editor_kernel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _registry_module()
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    runtime_registry = module.InMemoryRuntimeCapabilityRegistry()
    captured: dict[str, object] = {}

    class App:
        def exec(self) -> int:
            return 41

    class Kernel:
        def __init__(self, *, capability_registry):
            captured["registry"] = capability_registry

        def load_plugins_layered(self, layers) -> None:
            captured["layers"] = layers

        def show(self) -> None:
            captured["shown"] = True

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    assert editor_launcher.launch_editor(
        App(),
        "repo-e14",
        use_splash=False,
        capability_registry=runtime_registry,
    ) == 41
    assert captured == {
        "registry": runtime_registry,
        "layers": {"l1": []},
        "shown": True,
    }


def test_launch_editor_project_path_does_not_leak_skip_auto_open_to_a_later_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    monkeypatch.delenv("VITALOOM_SKIP_AUTO_OPEN", raising=False)
    observed_environment: list[str | None] = []
    startup_projects: list[str] = []

    class App:
        def exec(self) -> int:
            return 0

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            observed_environment.append(os.environ.get("VITALOOM_SKIP_AUTO_OPEN"))

        def set_startup_project(self, project_path: str) -> None:
            startup_projects.append(project_path)

        def load_plugins_layered(self, _layers: object) -> None:
            return None

        def show(self) -> None:
            return None

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    assert editor_launcher.launch_editor(
        App(), "repo-e96", project_path="project-e96", use_splash=False
    ) == 0
    assert os.environ.get("VITALOOM_SKIP_AUTO_OPEN") is None
    assert editor_launcher.launch_editor(App(), "repo-e96", use_splash=False) == 0

    assert observed_environment == [None, None]
    assert startup_projects == [os.path.abspath("project-e96")]


def test_launch_editor_project_path_preserves_skip_auto_open_on_constructor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    original_error = RuntimeError("constructor failure")
    monkeypatch.delenv("VITALOOM_SKIP_AUTO_OPEN", raising=False)

    class App:
        def exec(self) -> int:
            pytest.fail("constructor failure must not enter the event loop")

    def fail_kernel_construction(**_kwargs: object) -> object:
        assert os.environ.get("VITALOOM_SKIP_AUTO_OPEN") is None
        raise original_error

    monkeypatch.setattr(kernel_package, "EditorKernel", fail_kernel_construction)

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(
            App(), "repo-e96", project_path="project-e96", use_splash=False
        )

    assert captured.value is original_error
    assert "VITALOOM_SKIP_AUTO_OPEN" not in os.environ


def test_launch_editor_project_path_preserves_callers_auto_open_setting_on_plugin_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    original_error = RuntimeError("plugin failure")
    monkeypatch.setenv("VITALOOM_SKIP_AUTO_OPEN", "caller-managed")

    class App:
        def exec(self) -> int:
            pytest.fail("plugin failure must not enter the event loop")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            assert os.environ.get("VITALOOM_SKIP_AUTO_OPEN") == "caller-managed"

        def set_startup_project(self, _project_path: str) -> None:
            return None

        def load_plugins_layered(self, _layers: object) -> None:
            raise original_error

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(
            App(), "repo-e96", project_path="project-e96", use_splash=False
        )

    assert captured.value is original_error
    assert os.environ.get("VITALOOM_SKIP_AUTO_OPEN") == "caller-managed"


def test_launch_editor_normalizes_string_and_pathlike_project_paths_before_kernel_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VITALOOM_SKIP_AUTO_OPEN", raising=False)
    startup_projects: list[str] = []

    class App:
        def exec(self) -> int:
            return 0

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            return None

        def set_startup_project(self, project_path: str) -> None:
            startup_projects.append(project_path)

        def load_plugins_layered(self, _layers: object) -> None:
            return None

        def show(self) -> None:
            return None

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    assert editor_launcher.launch_editor(
        App(), "repo-e99", project_path="relative-string-project", use_splash=False
    ) == 0
    assert editor_launcher.launch_editor(
        App(), "repo-e99", project_path=Path("relative-pathlike-project"), use_splash=False
    ) == 0

    assert startup_projects == [
        str(tmp_path / "relative-string-project"),
        str(tmp_path / "relative-pathlike-project"),
    ]
    assert os.environ.get("VITALOOM_SKIP_AUTO_OPEN") is None


@pytest.mark.parametrize("project_path", [None, ""])
def test_launch_editor_treats_none_and_empty_project_path_as_no_explicit_request(
    monkeypatch: pytest.MonkeyPatch,
    project_path: str | None,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    calls: list[str] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 0

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def set_startup_project(self, _project_path: str) -> None:
            pytest.fail("empty project path must not become an explicit request")

        def load_plugins_layered(self, _layers: object) -> None:
            calls.append("kernel.load")

        def show(self) -> None:
            calls.append("kernel.show")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(editor_launcher, "default_plugin_layers", lambda _root: {"l1": []})

    assert editor_launcher.launch_editor(
        App(), "repo-e99", project_path=project_path, use_splash=False
    ) == 0
    assert calls == ["kernel.construct", "kernel.load", "kernel.show", "app.exec"]


class _BytesProjectPath:
    def __fspath__(self) -> bytes:
        return b"unsupported-by-public-contract"


@pytest.mark.parametrize("project_path", [object(), _BytesProjectPath()])
def test_launch_editor_rejects_unsupported_project_path_before_startup_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    project_path: object,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("invalid project path must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("invalid project path must not show a splash"),
    )

    with pytest.raises(TypeError, match="project_path"):
        editor_launcher.launch_editor(object(), "repo-e99", project_path=project_path)


class _ExplodingProjectPath:
    def __init__(self, error: BaseException) -> None:
        self._error = error

    def __fspath__(self) -> str:
        raise self._error


def test_launch_editor_preserves_pathlike_normalization_error_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    normalization_error = RuntimeError("PathLike normalization failed")
    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("normalization failure must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("normalization failure must not show a splash"),
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(
            object(), "repo-e99", project_path=_ExplodingProjectPath(normalization_error)
        )

    assert captured.value is normalization_error

def test_launch_editor_normalizes_repo_root_before_plugin_layer_handoff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    monkeypatch.chdir(tmp_path)
    received_roots: list[str] = []
    loaded_layers: list[object] = []

    class App:
        def exec(self) -> int:
            return 0

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            return None

        def load_plugins_layered(self, layers: object) -> None:
            loaded_layers.append(layers)

        def show(self) -> None:
            return None

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda root: received_roots.append(root) or {"official_mod": [root]},
    )

    assert editor_launcher.launch_editor(
        App(), "relative-string-root", use_splash=False
    ) == 0
    assert editor_launcher.launch_editor(
        App(), Path("relative-pathlike-root"), use_splash=False
    ) == 0

    assert received_roots == [
        str(tmp_path / "relative-string-root"),
        str(tmp_path / "relative-pathlike-root"),
    ]
    assert loaded_layers == [
        {"official_mod": [str(tmp_path / "relative-string-root")]},
        {"official_mod": [str(tmp_path / "relative-pathlike-root")]},
    ]


@pytest.mark.parametrize("repo_root", [object(), _BytesProjectPath()])
def test_launch_editor_rejects_invalid_repo_root_before_startup_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    repo_root: object,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("invalid repo root must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("invalid repo root must not show a splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("invalid repo root must not resolve plugin layers"),
    )

    with pytest.raises(TypeError, match="repo_root"):
        editor_launcher.launch_editor(object(), repo_root)


def test_launch_editor_preserves_repo_root_pathlike_normalization_error_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    normalization_error = RuntimeError("repo root normalization failed")
    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("normalization failure must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("normalization failure must not show a splash"),
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(
            object(), _ExplodingProjectPath(normalization_error)
        )

    assert captured.value is normalization_error
def test_launch_editor_preserves_incomplete_kernel_rollback_without_entering_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.kernel.editor_kernel import (
        EditorKernelInitializationRollbackError,
    )

    startup_error = RuntimeError("startup failed")
    rollback_error = EditorKernelInitializationRollbackError(startup_error)
    constructor_calls: list[dict[str, object]] = []
    lifecycle_calls: list[str] = []

    class App:
        def exec(self) -> int:
            lifecycle_calls.append("exec")
            return 0

    def raise_unsettled_rollback(**kwargs: object) -> object:
        constructor_calls.append(kwargs)
        raise rollback_error from startup_error

    monkeypatch.setattr(kernel_package, "EditorKernel", raise_unsettled_rollback)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: lifecycle_calls.append("plugin_layers") or {"l1": []},
    )

    with pytest.raises(EditorKernelInitializationRollbackError) as captured:
        editor_launcher.launch_editor(App(), "repo-e94", use_splash=False)

    assert captured.value is rollback_error
    assert captured.value.__cause__ is startup_error
    assert constructor_calls and "capability_registry" in constructor_calls[0]
    assert lifecycle_calls == []



def test_dismiss_splash_hides_and_schedules_the_failed_presentation() -> None:
    from core.VitaLoom.ui.splash_screen import dismiss_splash

    calls: list[str] = []

    class Splash:
        def hide(self) -> None:
            calls.append("hide")

        def deleteLater(self) -> None:
            calls.append("deleteLater")

    dismiss_splash(Splash())
    dismiss_splash(None)

    assert calls == ["hide", "deleteLater"]



def test_launch_editor_finishes_splash_only_after_kernel_is_shown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    splash = object()
    calls: list[str] = []
    kernels: list[object] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 95

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")
            kernels.append(self)

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    def finish(received_splash: object, received_kernel: object) -> None:
        assert received_splash is splash
        assert received_kernel is kernels[0]
        calls.append("splash.finish")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "finish_splash", finish)
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda _splash: pytest.fail("successful startup must not dismiss the splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    assert editor_launcher.launch_editor(App(), "repo-e95") == 95
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.message",
        "kernel.show",
        "splash.finish",
        "app.exec",
    ]


def test_launch_editor_dismisses_splash_when_kernel_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    startup_error = RuntimeError("kernel construction failed")
    splash = object()
    calls: list[str] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("event loop must not start after construction failure")

    def raise_startup_error(**_kwargs: object) -> object:
        calls.append("kernel.construct")
        raise startup_error

    monkeypatch.setattr(kernel_package, "EditorKernel", raise_startup_error)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append("splash.dismiss") if received is splash else None,
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("plugin layers must not be requested"),
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(App(), "repo-e95")

    assert captured.value is startup_error
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.dismiss",
    ]


def test_launch_editor_dismisses_splash_when_plugin_loading_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    plugin_error = RuntimeError("plugin layer failed")
    splash = object()
    calls: list[str] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("event loop must not start after plugin failure")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")
            raise plugin_error

        def show(self) -> None:
            raise AssertionError("partial kernel must not be shown")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        splash_screen,
        "dismiss_splash",
        lambda received: calls.append("splash.dismiss") if received is splash else None,
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(App(), "repo-e95")

    assert captured.value is plugin_error
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.dismiss",
    ]


def test_launch_editor_preserves_unsettled_rollback_when_splash_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.kernel.editor_kernel import (
        EditorKernelInitializationRollbackError,
    )
    from core.VitaLoom.ui import splash_screen

    startup_error = RuntimeError("startup failed")
    rollback_error = EditorKernelInitializationRollbackError(startup_error)
    splash = object()
    calls: list[str] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("event loop must not start after rollback failure")

    def raise_unsettled_rollback(**_kwargs: object) -> object:
        calls.append("kernel.construct")
        raise rollback_error from startup_error

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")
        raise RuntimeError("splash cleanup failed")

    monkeypatch.setattr(kernel_package, "EditorKernel", raise_unsettled_rollback)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("plugin layers must not be requested"),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(EditorKernelInitializationRollbackError) as captured:
            editor_launcher.launch_editor(App(), "repo-e95")

    assert captured.value is rollback_error
    assert captured.value.__cause__ is startup_error
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.dismiss",
    ]


def test_run_player_shell_forwards_the_exact_registry_to_player_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _registry_module()
    from core.VitaLoom.player import player_shell as player_module

    runtime_registry = module.InMemoryRuntimeCapabilityRegistry()
    captured: dict[str, object] = {}

    class App:
        def exec(self) -> int:
            return 42

    class Shell:
        def __init__(self, repo_root, project_path, *, capability_registry):
            captured.update(
                repo_root=repo_root,
                project_path=project_path,
                registry=capability_registry,
            )

        def show(self) -> None:
            captured["shown"] = True

    monkeypatch.setattr(player_module, "PlayerShell", Shell)

    assert player_module.run_player_shell(
        App(),
        "repo-e14",
        "project-e14",
        capability_registry=runtime_registry,
    ) == 42
    assert captured == {
        "repo_root": "repo-e14",
        "project_path": "project-e14",
        "registry": runtime_registry,
        "shown": True,
    }

def test_runtime_registry_module_lives_inside_versioned_engine_plugin_runtime() -> None:
    module = _registry_module()
    path = Path(module.__file__).resolve()
    normalized = path.as_posix()

    assert "/FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/" in normalized
    assert "/FrameCore/service_registry.py" not in normalized

@pytest.mark.parametrize(
    ("parameter_name", "invalid_value", "error_match"),
    [
        ("capability_registry", object(), "runtime capability registry"),
        ("event_bus", object(), "runtime event bus"),
    ],
)
def test_launch_editor_rejects_invalid_injected_runtime_services_before_startup_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    parameter_name: str,
    invalid_value: object,
    error_match: str,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("invalid service must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("invalid service must not show a splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("invalid service must not resolve plugin layers"),
    )

    with pytest.raises(TypeError, match=error_match):
        editor_launcher.launch_editor(
            object(),
            "repo-e101",
            **{parameter_name: invalid_value},
        )

@pytest.mark.parametrize("use_splash", [False, True])
def test_launch_editor_rejects_application_without_callable_event_loop_before_startup_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    use_splash: bool,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("invalid app must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: pytest.fail("invalid app must not show a splash"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("invalid app must not resolve plugin layers"),
    )

    with pytest.raises(TypeError, match="app must provide a callable exec"):
        editor_launcher.launch_editor(
            object(),
            "repo-e102",
            use_splash=use_splash,
        )


@pytest.mark.parametrize("invalid_process_events", [None, "not-callable"])
def test_launch_editor_rejects_invalid_splash_event_processing_before_creating_a_presentation(
    monkeypatch: pytest.MonkeyPatch,
    invalid_process_events: object,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    calls: list[str] = []

    class App:
        processEvents = invalid_process_events

        def exec(self) -> int:
            calls.append("app.exec")
            raise AssertionError("event loop must not start after splash protocol failure")

    monkeypatch.setattr(
        splash_screen,
        "create_vitaloom_splash",
        lambda: pytest.fail("invalid splash protocol must not create a presentation"),
    )
    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("invalid splash protocol must not construct a Kernel"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("invalid splash protocol must not resolve plugin layers"),
    )

    with pytest.raises(TypeError) as captured:
        editor_launcher.launch_editor(App(), "repo-e103")

    assert str(captured.value) == (
        "app must provide a callable processEvents() event-processing method"
    )
    assert calls == []


def test_show_vitaloom_splash_cleans_up_and_preserves_event_processing_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    event_processing_error = RuntimeError("event processing failed")
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            raise event_processing_error

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)

    with pytest.raises(RuntimeError) as captured:
        splash_screen.show_vitaloom_splash(App())

    assert captured.value is event_processing_error
    assert calls == [
        "splash.show",
        "app.processEvents",
        "splash.hide",
        "splash.deleteLater",
    ]


def test_show_vitaloom_splash_preserves_event_processing_failure_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from core.VitaLoom.ui import splash_screen

    monkeypatch.delenv("VITALOOM_NO_SPLASH", raising=False)
    event_processing_error = RuntimeError("event processing failed")
    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[str] = []

    class Splash:
        def show(self) -> None:
            calls.append("splash.show")

    class App:
        def processEvents(self) -> None:
            calls.append("app.processEvents")
            raise event_processing_error

    def fail_to_dismiss(received: object) -> None:
        assert isinstance(received, Splash)
        calls.append("splash.dismiss")
        raise cleanup_error

    monkeypatch.setattr(splash_screen, "create_vitaloom_splash", Splash)
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            splash_screen.show_vitaloom_splash(App())

    assert captured.value is event_processing_error
    assert "Failed to dismiss splash after splash presentation failure" in caplog.text
    assert calls == ["splash.show", "app.processEvents", "splash.dismiss"]

def test_launch_editor_keeps_no_splash_mode_independent_of_event_processing_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package

    monkeypatch.setenv("VITALOOM_NO_SPLASH", "1")
    calls: list[str] = []

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 103

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    assert editor_launcher.launch_editor(App(), "repo-e103") == 103
    assert calls == [
        "kernel.construct",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "kernel.show",
        "app.exec",
    ]


@pytest.mark.parametrize("failure_mode", ["show_message", "process_events"])
@pytest.mark.parametrize(
    ("message_site", "failed_message_number"),
    [("initial", 1), ("plugin_loading", 2), ("restore_status", 3)],
)
def test_launch_editor_dismisses_splash_once_and_preserves_each_message_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure_mode: str,
    message_site: str,
    failed_message_number: int,

) -> None:
    """E104: each Launcher splash-message failure keeps its primary error."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    message_error = RuntimeError(f"{message_site} {failure_mode} failed")
    calls: list[str] = []

    class Splash:
        def __init__(self) -> None:
            self.message_number = 0

        def showMessage(self, *_args: object) -> None:
            self.message_number += 1
            calls.append(f"splash.showMessage:{self.message_number}")
            if (
                failure_mode == "show_message"
                and self.message_number == failed_message_number
            ):
                raise message_error

    splash = Splash()

    class App:
        def exec(self) -> int:
            raise AssertionError("event loop must not start after splash-message failure")

        def processEvents(self) -> None:
            calls.append(f"app.processEvents:{splash.message_number}")
            if (
                failure_mode == "process_events"
                and splash.message_number == failed_message_number
            ):
                raise message_error

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            raise AssertionError("kernel must not be shown after splash-message failure")

    def dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")

    monkeypatch.setattr(kernel_package, "EditorKernel", Kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(App(), f"repo-e104-{message_site}")

    assert captured.value is message_error
    expected = ["splash.show"]
    for message_number in range(1, failed_message_number + 1):
        expected.append(f"splash.showMessage:{message_number}")
        if message_number == failed_message_number:
            if failure_mode == "process_events":
                expected.append(f"app.processEvents:{message_number}")
            break
        expected.append(f"app.processEvents:{message_number}")
        if message_number == 1:
            expected.append("kernel.construct")
        elif message_number == 2:
            expected.extend(["plugin.layers", "kernel.load:{'l1': []}"])
    expected.append("splash.dismiss")
    assert calls == expected


def test_launch_editor_preserves_splash_message_failure_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E104: cleanup logging must not replace an initial message-rendering error."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    message_error = RuntimeError("initial message rendering failed")
    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[str] = []

    class Splash:
        def showMessage(self, *_args: object) -> None:
            calls.append("splash.showMessage")
            raise message_error

    splash = Splash()

    class App:
        def exec(self) -> int:
            raise AssertionError("event loop must not start after splash-message failure")

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")
        raise cleanup_error

    monkeypatch.setattr(
        kernel_package,
        "EditorKernel",
        lambda **_kwargs: pytest.fail("initial message failure must not construct a Kernel"),
    )
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: pytest.fail("initial message failure must not resolve plugin layers"),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(App(), "repo-e104-cleanup")

    assert captured.value is message_error
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls == ["splash.show", "splash.showMessage", "splash.dismiss"]


@pytest.mark.parametrize("failure_stage", ["finish", "deferred_delete"])
def test_launch_editor_dismisses_splash_once_and_preserves_finish_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    """E105: splash completion failures retain their primary error and stop the loop."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    finish_error = RuntimeError(f"{failure_stage} failed")
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")
            if failure_stage == "finish":
                raise finish_error

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            raise AssertionError("event loop must not start after splash-finish failure")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(_milliseconds: int, _callback: object) -> None:
            calls.append("timer.singleShot")
            if failure_stage == "deferred_delete":
                raise finish_error
            pytest.fail("immediate finish failure must not schedule deferred deletion")

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with pytest.raises(RuntimeError) as captured:
        editor_launcher.launch_editor(App(), f"repo-e105-{failure_stage}")

    assert captured.value is finish_error
    expected = [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.message",
        "kernel.show",
        "splash.finish",
    ]
    if failure_stage == "deferred_delete":
        expected.append("timer.singleShot")
    expected.extend(["splash.hide", "splash.deleteLater"])
    assert calls == expected


def test_launch_editor_preserves_finish_failure_when_splash_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E105: failed cleanup must not replace the immediate finish failure."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    finish_error = RuntimeError("splash finish failed")
    cleanup_error = RuntimeError("splash cleanup failed")
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")
            raise finish_error

    splash = Splash()

    class App:
        def exec(self) -> int:
            raise AssertionError("event loop must not start after splash-finish failure")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    def fail_to_dismiss(received: object) -> None:
        assert received is splash
        calls.append("splash.dismiss")
        raise cleanup_error

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "dismiss_splash", fail_to_dismiss)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(App(), "repo-e105-cleanup")

    assert captured.value is finish_error
    assert "Failed to dismiss splash after editor startup failure" in caplog.text
    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.message",
        "kernel.show",
        "splash.finish",
        "splash.dismiss",
    ]

def test_launch_editor_observes_deferred_splash_delete_failure_after_event_loop_handoff(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E106: deferred splash cleanup failures stay observable after app.exec handoff."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    delete_error = RuntimeError("deferred splash deletion failed")
    callbacks: list[object] = []
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            raise delete_error

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 47

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(App(), "repo-e106") == 47
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
            "app.exec",
        ]
        assert len(callbacks) == 1
        callback = callbacks.pop()
        assert callable(callback)
        callback()

    assert calls[-1] == "splash.deleteLater"
    assert "Failed to delete splash after editor startup handoff" in caplog.text

def test_launch_editor_defers_successful_splash_delete_until_after_event_loop_handoff(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E107: successful deferred splash deletion is one-shot and post-handoff."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    callbacks: list[object] = []
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            return 48

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(App(), "repo-e107") == 48
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
            "app.exec",
        ]
        assert len(callbacks) == 1
        callback = callbacks.pop()
        assert callable(callback)
        callback()

    assert calls[-1] == "splash.deleteLater"
    assert calls.count("splash.deleteLater") == 1
    assert "Failed to delete splash after editor startup handoff" not in caplog.text

@pytest.mark.parametrize("deletion_fails", [False, True])
def test_finish_splash_real_qt_timer_callback_has_e106_parity(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    deletion_fails: bool,
) -> None:
    """E108: the real zero-delay Qt callback preserves E106 success/failure behavior."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication

    from core.VitaLoom.ui import splash_screen

    app = QApplication.instance() or QApplication([])
    assert app is not None
    delete_error = RuntimeError("real Qt deferred splash deletion failed")
    calls: list[str] = []
    event_loop = QEventLoop()

    class Splash:
        def finish(self, _widget: object) -> None:
            calls.append("splash.finish")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            if deletion_fails:
                raise delete_error
            QTimer.singleShot(0, event_loop.quit)

    if deletion_fails:
        QTimer.singleShot(20, event_loop.quit)
    else:
        QTimer.singleShot(1000, event_loop.quit)

    with caplog.at_level(logging.WARNING):
        splash_screen.finish_splash(Splash(), object())
        assert calls == ["splash.finish"]
        event_loop.exec()

    assert calls == ["splash.finish", "splash.deleteLater"]
    warning = "Failed to delete splash after editor startup handoff"
    assert (warning in caplog.text) is deletion_fails

def test_launch_editor_preserves_event_loop_entry_failure_after_completed_splash_handoff(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E109: a post-handoff exec failure remains primary without duplicate cleanup."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    exec_error = RuntimeError("event loop entry failed")
    callbacks: list[object] = []
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            raise exec_error

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(App(), "repo-e109")

        assert captured.value is exec_error
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
            "app.exec",
        ]
        assert len(callbacks) == 1
        callback = callbacks.pop()
        assert callable(callback)
        callback()

    assert calls[-1] == "splash.deleteLater"
    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    assert "Failed to delete splash after editor startup handoff" not in caplog.text

@pytest.mark.parametrize("deletion_fails", [False, True])
def test_launch_editor_real_qt_timer_survives_event_loop_entry_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    deletion_fails: bool,
) -> None:
    """E110: real Qt timer delivery remains adapter-owned after a raising exec entry."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None
    exec_error = RuntimeError("real adapter event loop entry failed")
    delete_error = RuntimeError("real Qt deferred deletion failed")
    event_loop = QEventLoop()
    calls: list[str] = []

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            if deletion_fails:
                raise delete_error
            QTimer.singleShot(0, event_loop.quit)

    splash = Splash()

    class AppAdapter:
        def processEvents(self) -> None:
            qt_app.processEvents()

        def exec(self) -> int:
            calls.append("app.exec")
            raise exec_error

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    if deletion_fails:
        QTimer.singleShot(20, event_loop.quit)
    else:
        QTimer.singleShot(1000, event_loop.quit)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError) as captured:
            editor_launcher.launch_editor(AppAdapter(), "repo-e110")

        assert captured.value is exec_error
        assert calls == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "app.exec",
        ]
        event_loop.exec()

    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert calls[-1] == "splash.deleteLater"
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    warning = "Failed to delete splash after editor startup handoff"
    assert (warning in caplog.text) is deletion_fails
@pytest.mark.parametrize("callback_timing", ["during_exec", "after_return"])
@pytest.mark.parametrize("deletion_fails", [False, True])
def test_launch_editor_preserves_normal_event_loop_return_lifecycle_boundary(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    callback_timing: str,
    deletion_fails: bool,
) -> None:
    """E111: normal loop return does not transfer deferred-splash authority."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    callbacks: list[object] = []
    calls: list[str] = []
    exit_code = 73
    delete_error = RuntimeError("deferred deletion failed after loop return")

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            if deletion_fails:
                raise delete_error

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            if callback_timing == "during_exec":
                callback = callbacks.pop()
                assert callable(callback)
                callback()
            calls.append("app.exec.return")
            return exit_code

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(App(), "repo-e111") == exit_code
        assert calls[:11] == [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
            "app.exec",
        ]
        if callback_timing == "after_return":
            assert calls == calls[:11] + ["app.exec.return"]
            callback = callbacks.pop()
            assert callable(callback)
            callback()
        else:
            assert calls == calls[:11] + ["splash.deleteLater", "app.exec.return"]

    assert callbacks == []
    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    warning = "Failed to delete splash after editor startup handoff"
    assert (warning in caplog.text) is deletion_fails


def test_launch_editor_returns_after_real_qt_timer_delivers_within_event_loop(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E111: real Qt timer delivery during exec preserves the app return code."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None
    event_loop = QEventLoop()
    calls: list[str] = []
    exit_code = 74

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            QTimer.singleShot(0, event_loop.quit)

    splash = Splash()

    class AppAdapter:
        def processEvents(self) -> None:
            qt_app.processEvents()

        def exec(self) -> int:
            calls.append("app.exec")
            event_loop.exec()
            calls.append("app.exec.return")
            return exit_code

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )
    QTimer.singleShot(1000, event_loop.quit)

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(AppAdapter(), "repo-e111-real-qt") == exit_code

    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.message",
        "kernel.show",
        "splash.finish",
        "app.exec",
        "splash.deleteLater",
        "app.exec.return",
    ]
    assert calls.count("splash.hide") == 0
    assert calls.count("splash.deleteLater") == 1
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    assert "Failed to delete splash after editor startup handoff" not in caplog.text
@pytest.mark.parametrize("use_splash", [True, False])
def test_launch_editor_normal_return_does_not_shutdown_existing_owners(
    monkeypatch: pytest.MonkeyPatch,
    use_splash: bool,
) -> None:
    """E112: a normal event-loop return grants Launcher no shutdown authority."""
    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    callbacks: list[object] = []
    calls: list[str] = []
    exit_code = 75

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def close(self) -> None:
            calls.append("splash.close")

        def shutdown(self) -> None:
            calls.append("splash.shutdown")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")

    splash = Splash()

    class App:
        def exec(self) -> int:
            calls.append("app.exec")
            calls.append("app.exec.return")
            return exit_code

        def quit(self) -> None:
            calls.append("app.quit")

        def close(self) -> None:
            calls.append("app.close")

        def shutdown(self) -> None:
            calls.append("app.shutdown")

        def deleteLater(self) -> None:
            calls.append("app.deleteLater")

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

        def close(self) -> None:
            calls.append("kernel.close")

        def shutdown(self) -> None:
            calls.append("kernel.shutdown")

        def deleteLater(self) -> None:
            calls.append("kernel.deleteLater")

        @property
        def plugin_host(self) -> object:
            calls.append("kernel.plugin_host.read")
            return object()

        @property
        def project_world(self) -> object:
            calls.append("kernel.project_world.read")
            return object()

    kernel = Kernel.__new__(Kernel)

    class Timer:
        @staticmethod
        def singleShot(milliseconds: int, callback: object) -> None:
            assert milliseconds == 0
            calls.append("timer.singleShot")
            callbacks.append(callback)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(splash_screen, "QTimer", Timer)
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )

    assert editor_launcher.launch_editor(
        App(),
        "repo-e112",
        use_splash=use_splash,
    ) == exit_code

    expected_calls = ["kernel.construct", "plugin.layers", "kernel.load:{'l1': []}", "kernel.show"]
    if use_splash:
        expected_calls = [
            "splash.show",
            "splash.message",
            "kernel.construct",
            "splash.message",
            "plugin.layers",
            "kernel.load:{'l1': []}",
            "splash.message",
            "kernel.show",
            "splash.finish",
            "timer.singleShot",
        ]
    assert calls == expected_calls + ["app.exec", "app.exec.return"]
    assert len(callbacks) == (1 if use_splash else 0)
    assert not any(
        call in {
            "splash.hide",
            "splash.close",
            "splash.shutdown",
            "splash.deleteLater",
            "kernel.close",
            "kernel.shutdown",
            "kernel.deleteLater",
            "kernel.plugin_host.read",
            "kernel.project_world.read",
            "app.quit",
            "app.close",
            "app.shutdown",
            "app.deleteLater",
        }
        for call in calls
    )
def test_launch_editor_real_qapplication_normal_return_preserves_adapter_ownership(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E113: direct real QApplication.exec() exit leaves splash ownership adapter-side."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication

    from core.VitaLoom import editor_launcher
    from core.VitaLoom import kernel as kernel_package
    from core.VitaLoom.ui import splash_screen

    qt_app = QApplication.instance() or QApplication([])
    assert qt_app is not None
    calls: list[str] = []
    exit_requests: list[str] = []

    def quit_application(source: str) -> None:
        exit_requests.append(source)
        qt_app.quit()

    class Splash:
        def finish(self, received_widget: object) -> None:
            assert received_widget is kernel
            calls.append("splash.finish")

        def hide(self) -> None:
            calls.append("splash.hide")

        def deleteLater(self) -> None:
            calls.append("splash.deleteLater")
            QTimer.singleShot(0, lambda: quit_application("adapter.deferred_callback"))

    splash = Splash()

    class Kernel:
        def __init__(self, **_kwargs: object) -> None:
            calls.append("kernel.construct")

        def load_plugins_layered(self, layers: object) -> None:
            calls.append(f"kernel.load:{layers}")

        def show(self) -> None:
            calls.append("kernel.show")

        def shutdown(self) -> None:
            calls.append("kernel.shutdown")

    kernel = Kernel.__new__(Kernel)

    def construct_kernel(**_kwargs: object) -> Kernel:
        Kernel.__init__(kernel)
        return kernel

    monkeypatch.setattr(kernel_package, "EditorKernel", construct_kernel)
    monkeypatch.setattr(
        splash_screen,
        "show_vitaloom_splash",
        lambda _app: calls.append("splash.show") or splash,
    )
    monkeypatch.setattr(
        splash_screen,
        "splash_message",
        lambda _splash, _text, _app: calls.append("splash.message"),
    )
    monkeypatch.setattr(
        editor_launcher,
        "default_plugin_layers",
        lambda _root: calls.append("plugin.layers") or {"l1": []},
    )
    QTimer.singleShot(1000, lambda: quit_application("watchdog"))

    with caplog.at_level(logging.WARNING):
        assert editor_launcher.launch_editor(qt_app, "repo-e113") == 0
        calls.append("launcher.return")

    assert calls == [
        "splash.show",
        "splash.message",
        "kernel.construct",
        "splash.message",
        "plugin.layers",
        "kernel.load:{'l1': []}",
        "splash.message",
        "kernel.show",
        "splash.finish",
        "splash.deleteLater",
        "launcher.return",
    ]
    assert exit_requests == ["adapter.deferred_callback"]
    assert "splash.hide" not in calls
    assert "kernel.shutdown" not in calls
    assert "Failed to dismiss splash after editor startup failure" not in caplog.text
    assert "Failed to delete splash after editor startup handoff" not in caplog.text
