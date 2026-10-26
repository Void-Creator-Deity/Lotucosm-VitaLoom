# -*- coding: utf-8 -*-
"""PluginLoader Adapter execution for candidate-first L3 hot reload."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


class _SignalStub:
    def __init__(self) -> None:
        self.events: list[str] = []

    def emit(self, name: str) -> None:
        self.events.append(name)


class _KernelStub:
    def __init__(self, root: Path) -> None:
        self.plugin_loaded = _SignalStub()
        self.plugin_unloaded = _SignalStub()
        self.layout_manager = None
        self._context = type("Context", (), {"repo_root": str(root), "project_root": str(root)})()

    def get_context(self):
        return self._context


class _Plugin:
    def __init__(
        self,
        plugin_id: str,
        events: list[str],
        *,
        version: str = "1.0.0",
        dependencies: tuple[str, ...] = (),
        fail_load: bool = False,
        fail_unload: bool = False,
    ) -> None:
        self.plugin_id = plugin_id
        self.version = version
        self.dependencies = dependencies
        self.events = events
        self.fail_load = fail_load
        self.fail_unload = fail_unload

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": self.version,
            "dependencies": list(self.dependencies),
            "provides": [],
        }

    def on_load(self, _context):
        self.events.append(f"load:{self.plugin_id}:{self.version}")
        if self.fail_load:
            raise RuntimeError(f"load failed: {self.plugin_id}")

    def on_editor_ready(self):
        pass

    def on_unload(self):
        self.events.append(f"unload:{self.plugin_id}:{self.version}")
        if self.fail_unload:
            raise RuntimeError(f"unload failed: {self.plugin_id}")


def _loader(tmp_path: Path):
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    return PluginLoader(_KernelStub(tmp_path))


def _install(
    loader,
    tmp_path: Path,
    plugins: dict[str, _Plugin],
    *,
    active: set[str],
    scopes: dict[str, str] | None = None,
) -> Path:
    target_file = tmp_path / "TargetPlugin_plugin.py"
    target_file.write_text("# candidate source\n", encoding="utf-8")
    for plugin_id, plugin in plugins.items():
        loader.plugin_registry[plugin_id] = plugin
        loader.plugin_dependencies[plugin_id] = list(plugin.dependencies)
        loader.plugin_scopes[plugin_id] = (scopes or {}).get(plugin_id, loader.SCOPE_USER)
        loader.plugin_files[plugin_id] = (
            str(target_file) if plugin_id == "TargetPlugin" else str(tmp_path / f"{plugin_id}.py")
        )
        if plugin_id in active:
            loader.loaded_plugins[plugin_id] = plugin
    return target_file


def test_candidate_import_failure_preserves_old_active_instance(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(loader, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})

    with patch.object(loader, "_instantiate_plugin_from_file", side_effect=SyntaxError("broken")):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert report["diagnostics"][0]["code"] == "reload_candidate_import_failed"
    assert loader.plugin_registry["TargetPlugin"] is old
    assert loader.loaded_plugins["TargetPlugin"] is old
    assert events == []


def test_candidate_id_mismatch_preserves_old_active_instance(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    old = _Plugin("TargetPlugin", events)
    wrong = _Plugin("WrongPlugin", events, version="2.0.0")
    _install(loader, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})

    with patch.object(loader, "_instantiate_plugin_from_file", return_value=("WrongPlugin", wrong)):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert report["diagnostics"][0]["code"] == "reload_candidate_id_mismatch"
    assert loader.loaded_plugins["TargetPlugin"] is old
    assert events == []


def test_active_reload_deactivates_dependents_then_reactivates_dependency_first(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    plugins = {
        "BasePlugin": _Plugin("BasePlugin", events),
        "TargetPlugin": _Plugin("TargetPlugin", events, dependencies=("BasePlugin",)),
        "MiddlePlugin": _Plugin("MiddlePlugin", events, dependencies=("TargetPlugin",)),
        "LeafPlugin": _Plugin("LeafPlugin", events, dependencies=("MiddlePlugin",)),
        "NewDependencyPlugin": _Plugin("NewDependencyPlugin", events),
    }
    _install(
        loader,
        tmp_path,
        plugins,
        active={"BasePlugin", "TargetPlugin", "MiddlePlugin", "LeafPlugin"},
    )
    candidate = _Plugin(
        "TargetPlugin",
        events,
        version="2.0.0",
        dependencies=("BasePlugin", "NewDependencyPlugin"),
    )

    with patch.object(
        loader,
        "_instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    assert report["completed"]["deactivated"] == [
        "LeafPlugin",
        "MiddlePlugin",
        "TargetPlugin",
    ]
    assert report["completed"]["activated"] == [
        "NewDependencyPlugin",
        "TargetPlugin",
        "MiddlePlugin",
        "LeafPlugin",
    ]
    assert events == [
        "unload:LeafPlugin:1.0.0",
        "unload:MiddlePlugin:1.0.0",
        "unload:TargetPlugin:1.0.0",
        "load:NewDependencyPlugin:1.0.0",
        "load:TargetPlugin:2.0.0",
        "load:MiddlePlugin:1.0.0",
        "load:LeafPlugin:1.0.0",
    ]
    assert loader.loaded_plugins["TargetPlugin"] is candidate
    assert loader.last_reload_report == report
    assert loader.last_lifecycle_report["source"] == "hot_reload"


def test_missing_candidate_dependency_blocks_before_callbacks(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    old = _Plugin("TargetPlugin", events)
    candidate = _Plugin("TargetPlugin", events, version="2.0.0", dependencies=("MissingPlugin",))
    _install(loader, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})

    with patch.object(loader, "_instantiate_plugin_from_file", return_value=("TargetPlugin", candidate)):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert "plugin_dependency_missing" in {item["code"] for item in report["diagnostics"]}
    assert loader.loaded_plugins["TargetPlugin"] is old
    assert events == []


def test_inactive_target_replacement_has_no_callbacks(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    old = _Plugin("TargetPlugin", events)
    candidate = _Plugin("TargetPlugin", events, version="2.0.0")
    _install(loader, tmp_path, {"TargetPlugin": old}, active=set())

    with patch.object(loader, "_instantiate_plugin_from_file", return_value=("TargetPlugin", candidate)):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    assert report["completed"] == {
        "deactivated": [],
        "activated": [],
        "registry_replaced": True,
    }
    assert loader.plugin_registry["TargetPlugin"] is candidate
    assert "TargetPlugin" not in loader.loaded_plugins
    assert events == []


def test_target_activation_failure_is_partial_and_skips_dependents(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    target = _Plugin("TargetPlugin", events)
    dependent = _Plugin("DependentPlugin", events, dependencies=("TargetPlugin",))
    _install(
        loader,
        tmp_path,
        {"TargetPlugin": target, "DependentPlugin": dependent},
        active={"TargetPlugin", "DependentPlugin"},
    )
    candidate = _Plugin("TargetPlugin", events, version="2.0.0", fail_load=True)

    with patch.object(loader, "_instantiate_plugin_from_file", return_value=("TargetPlugin", candidate)):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "partial"
    assert report["failed_action"]["plugin_id"] == "TargetPlugin"
    assert report["skipped"]["activation"] == [
        {"plugin_id": "DependentPlugin", "blocked_by": ["TargetPlugin"]}
    ]
    assert report["rollback"]["status"] == "not_available"
    assert "TargetPlugin" not in loader.loaded_plugins
    assert "DependentPlugin" not in loader.loaded_plugins


def test_first_unload_failure_keeps_candidate_uninstalled(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    target = _Plugin("TargetPlugin", events)
    dependent = _Plugin(
        "DependentPlugin",
        events,
        dependencies=("TargetPlugin",),
        fail_unload=True,
    )
    _install(
        loader,
        tmp_path,
        {"TargetPlugin": target, "DependentPlugin": dependent},
        active={"TargetPlugin", "DependentPlugin"},
    )
    candidate = _Plugin("TargetPlugin", events, version="2.0.0")

    with patch.object(loader, "_instantiate_plugin_from_file", return_value=("TargetPlugin", candidate)):
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "failed"
    assert report["failed_action"] == {
        "action": "deactivate",
        "plugin_id": "DependentPlugin",
    }
    assert report["completed"]["registry_replaced"] is False
    assert loader.plugin_registry["TargetPlugin"] is target
    assert loader.loaded_plugins["TargetPlugin"] is target
    assert loader.loaded_plugins["DependentPlugin"] is dependent
    assert report["rollback"]["status"] == "not_available"


def test_l4_reload_is_rejected_before_candidate_import(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(
        loader,
        tmp_path,
        {"TargetPlugin": old},
        active={"TargetPlugin"},
        scopes={"TargetPlugin": loader.SCOPE_EMBEDDED},
    )

    with patch.object(loader, "_instantiate_plugin_from_file") as instantiate:
        report = loader.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert report["diagnostics"][0]["code"] == "reload_scope_forbidden"
    instantiate.assert_not_called()
    assert loader.loaded_plugins["TargetPlugin"] is old


def test_reloadable_listing_excludes_l4_core_unknown_and_protected(tmp_path: Path) -> None:
    events: list[str] = []
    loader = _loader(tmp_path)
    plugins = {
        "UserPlugin": _Plugin("UserPlugin", events),
        "OfficialPlugin": _Plugin("OfficialPlugin", events),
        "EmbeddedPlugin": _Plugin("EmbeddedPlugin", events),
        "CorePlugin": _Plugin("CorePlugin", events),
        "UnknownPlugin": _Plugin("UnknownPlugin", events),
        "ProtectedPlugin": _Plugin("ProtectedPlugin", events),
    }
    scopes = {
        "UserPlugin": loader.SCOPE_USER,
        "OfficialPlugin": loader.SCOPE_OFFICIAL,
        "EmbeddedPlugin": loader.SCOPE_EMBEDDED,
        "CorePlugin": loader.SCOPE_CORE,
        "UnknownPlugin": loader.SCOPE_UNKNOWN,
        "ProtectedPlugin": loader.SCOPE_USER,
    }
    _install(loader, tmp_path, plugins, active=set(plugins), scopes=scopes)
    for plugin_id in plugins:
        source = tmp_path / f"{plugin_id}.py"
        source.write_text("# source\n", encoding="utf-8")
        loader.plugin_files[plugin_id] = str(source)
    loader.protected_plugins.add("ProtectedPlugin")

    assert loader.list_reloadable_plugins() == ["OfficialPlugin", "UserPlugin"]


def test_project_disable_source_uses_lifecycle_sync_not_direct_unload() -> None:
    runtime = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    source = (
        runtime
        / "builtin"
        / "editor_extensions"
        / "plugin_runtime_ops.py"
    ).read_text(encoding="utf-8")
    disable_block = source.split("def disable_plugin_in_project", 1)[1].split(
        "def enable_plugin_in_project", 1
    )[0]

    assert "unload_plugin(" not in disable_block
    assert "_sync_plugins_for_current_project()" in disable_block


def test_hot_reload_ui_consumes_plugin_host_capability_reports() -> None:
    runtime = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    source = (
        runtime
        / "builtin"
        / "editor_extensions"
        / "hot_reload_plugin.py"
    ).read_text(encoding="utf-8")

    assert "host = resolve_plugin_host(self.context)" in source
    assert "host.observe_plugins()" in source
    assert 'snapshot.get("reloadable_plugin_ids", [])' in source
    assert "host.reload_plugin(plugin_id)" in source
    assert 'report.get("status")' in source
    assert "kernel.plugin_loader" not in source
