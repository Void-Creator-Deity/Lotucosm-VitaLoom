# -*- coding: utf-8 -*-
"""Headless Interface and architecture tests for E22 manual plugin reload."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class _Plugin:
    def __init__(
        self,
        plugin_id: str,
        events: list[str],
        *,
        version: str = "1.0.0",
        dependencies: tuple[str, ...] = (),
        description: str = "",
        provides=(),
        fail_load: bool = False,
        fail_unload: bool = False,
    ) -> None:
        self.plugin_id = plugin_id
        self.events = events
        self.version = version
        self.dependencies = dependencies
        self.description = description
        self.provides = provides
        self.fail_load = fail_load
        self.fail_unload = fail_unload

    def get_plugin_info(self):
        return {
            "name": self.plugin_id,
            "version": self.version,
            "dependencies": list(self.dependencies),
            "description": self.description,
            "provides": self.provides,
        }

    def on_load(self, _context):
        self.events.append(f"load:{self.plugin_id}:{self.version}")
        if self.fail_load:
            raise RuntimeError(f"load failed: {self.plugin_id}")

    def on_unload(self):
        self.events.append(f"unload:{self.plugin_id}:{self.version}")
        if self.fail_unload:
            raise RuntimeError(f"unload failed: {self.plugin_id}")


def _authorities(tmp_path: Path):
    from core.VitaLoom.core.manual_plugin_reload_host import ManualPluginReloadHost
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    runtime_host = RuntimePluginHost()
    reload_host = ManualPluginReloadHost(runtime_host)
    return runtime_host, reload_host


def _install(
    runtime_host,
    tmp_path: Path,
    plugins: dict[str, _Plugin],
    *,
    active: set[str],
    scopes: dict[str, str] | None = None,
    protected: set[str] | None = None,
) -> Path:
    target_file = tmp_path / "TargetPlugin_plugin.py"
    target_file.write_text("# candidate source\n", encoding="utf-8")
    for plugin_id, plugin in plugins.items():
        source = target_file if plugin_id == "TargetPlugin" else tmp_path / f"{plugin_id}.py"
        if plugin_id != "TargetPlugin":
            source.write_text("# plugin source\n", encoding="utf-8")
        runtime_host.plugin_registry[plugin_id] = plugin
        runtime_host.plugin_dependencies[plugin_id] = list(plugin.dependencies)
        runtime_host.plugin_scopes[plugin_id] = (scopes or {}).get(
            plugin_id, runtime_host.SCOPE_USER
        )
        runtime_host.plugin_files[plugin_id] = str(source)
        if plugin_id in active:
            runtime_host.loaded_plugins[plugin_id] = plugin
    runtime_host.protected_plugins.update(protected or set())
    runtime_host.resolve_dependencies()
    return target_file


def test_candidate_import_failure_preserves_old_active_instance(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        side_effect=SyntaxError("broken"),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert report["diagnostics"][0]["code"] == "reload_candidate_import_failed"
    assert runtime_host.plugin_registry["TargetPlugin"] is old
    assert runtime_host.loaded_plugins["TargetPlugin"] is old
    assert runtime_host.last_lifecycle_report == report
    assert reload_host.last_reload_report == report
    assert events == []


def test_active_reload_orders_reverse_dependents_then_dependencies(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    plugins = {
        "BasePlugin": _Plugin("BasePlugin", events),
        "TargetPlugin": _Plugin("TargetPlugin", events, dependencies=("BasePlugin",)),
        "LeafPlugin": _Plugin("LeafPlugin", events, dependencies=("TargetPlugin",)),
        "NewDependencyPlugin": _Plugin("NewDependencyPlugin", events),
    }
    _install(
        runtime_host,
        tmp_path,
        plugins,
        active={"BasePlugin", "TargetPlugin", "LeafPlugin"},
    )
    candidate = _Plugin(
        "TargetPlugin",
        events,
        version="2.0.0",
        dependencies=("BasePlugin", "NewDependencyPlugin"),
    )

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    assert report["completed"] == {
        "deactivated": ["LeafPlugin", "TargetPlugin"],
        "activated": ["NewDependencyPlugin", "TargetPlugin", "LeafPlugin"],
        "registry_replaced": True,
    }
    assert events == [
        "unload:LeafPlugin:1.0.0",
        "unload:TargetPlugin:1.0.0",
        "load:NewDependencyPlugin:1.0.0",
        "load:TargetPlugin:2.0.0",
        "load:LeafPlugin:1.0.0",
    ]
    assert runtime_host.plugin_registry["TargetPlugin"] is candidate
    assert runtime_host.loaded_plugins["TargetPlugin"] is candidate


def test_inactive_target_replacement_has_no_callbacks(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active=set())
    candidate = _Plugin("TargetPlugin", events, version="2.0.0")

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    assert report["target_was_active"] is False
    assert report["completed"]["registry_replaced"] is True
    assert runtime_host.plugin_registry["TargetPlugin"] is candidate
    assert runtime_host.loaded_plugins == {}
    assert events == []


def test_reload_replaces_copied_catalog_metadata_with_normalized_candidate_facts(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin(
        "TargetPlugin",
        events,
        description="old description",
        provides=["old"],
    )
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active=set())
    candidate = _Plugin(
        "TargetPlugin",
        events,
        version="2.0.0",
        description="new description",
        provides="dock",
    )

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    row = next(
        item
        for item in runtime_host.catalog_entries()
        if item.plugin_id == "TargetPlugin"
    ).to_dict()
    assert row["version"] == "2.0.0"
    assert row["description"] == "new description"
    assert row["provides"] == ["dock"]


def test_missing_candidate_dependency_blocks_before_callbacks(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})
    candidate = _Plugin("TargetPlugin", events, version="2.0.0", dependencies=("Missing",))

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert "plugin_dependency_missing" in {item["code"] for item in report["diagnostics"]}
    assert runtime_host.plugin_registry["TargetPlugin"] is old
    assert runtime_host.loaded_plugins["TargetPlugin"] is old
    assert events == []


def test_target_activation_failure_is_partial_and_skips_dependents(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    leaf = _Plugin("LeafPlugin", events, dependencies=("TargetPlugin",))
    _install(
        runtime_host,
        tmp_path,
        {"TargetPlugin": old, "LeafPlugin": leaf},
        active={"TargetPlugin", "LeafPlugin"},
    )
    candidate = _Plugin("TargetPlugin", events, version="2.0.0", fail_load=True)

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "partial"
    assert report["failed_action"] == {
        "action": "activate",
        "plugin_id": "TargetPlugin",
        "error": "RuntimeError",
    }
    assert report["skipped"]["activation"] == [
        {"plugin_id": "LeafPlugin", "blocked_by": ["TargetPlugin"]}
    ]
    assert runtime_host.failed_plugins["TargetPlugin"] == "load failed: TargetPlugin"
    assert "TargetPlugin" not in runtime_host.loaded_plugins
    assert "LeafPlugin" not in runtime_host.loaded_plugins
    assert report["rollback"]["status"] == "not_available"


def test_first_unload_failure_keeps_candidate_uninstalled(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events, fail_unload=True)
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})
    candidate = _Plugin("TargetPlugin", events, version="2.0.0")

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "failed"
    assert report["failed_action"] == {"action": "deactivate", "plugin_id": "TargetPlugin"}
    assert report["completed"]["registry_replaced"] is False
    assert runtime_host.plugin_registry["TargetPlugin"] is old
    assert runtime_host.loaded_plugins["TargetPlugin"] is old
    assert report["rollback"]["status"] == "not_available"


@pytest.mark.parametrize(
    ("scope", "protected", "code"),
    [
        ("core_mod", False, "reload_scope_forbidden"),
        ("embedded_mod", False, "reload_scope_forbidden"),
        ("unknown", False, "reload_scope_forbidden"),
        ("user_mod", True, "reload_protected_plugin"),
    ],
)
def test_forbidden_target_is_rejected_before_candidate_import(
    tmp_path: Path,
    scope: str,
    protected: bool,
    code: str,
) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(
        runtime_host,
        tmp_path,
        {"TargetPlugin": old},
        active={"TargetPlugin"},
        scopes={"TargetPlugin": scope},
        protected={"TargetPlugin"} if protected else set(),
    )

    with patch.object(runtime_host, "instantiate_plugin_from_file") as candidate_import:
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "blocked"
    assert report["diagnostics"][0]["code"] == code
    candidate_import.assert_not_called()
    assert runtime_host.plugin_registry["TargetPlugin"] is old
    assert events == []


def test_reloadable_listing_accepts_only_active_regular_l3_sources(tmp_path: Path) -> None:
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    plugins = {
        "Official": _Plugin("Official", events),
        "User": _Plugin("User", events),
        "Inactive": _Plugin("Inactive", events),
        "Embedded": _Plugin("Embedded", events),
        "Core": _Plugin("Core", events),
        "Protected": _Plugin("Protected", events),
        "MissingSource": _Plugin("MissingSource", events),
    }
    _install(
        runtime_host,
        tmp_path,
        plugins,
        active={"Official", "User", "Embedded", "Core", "Protected", "MissingSource"},
        scopes={
            "Official": "official_mod",
            "User": "user_mod",
            "Inactive": "user_mod",
            "Embedded": "embedded_mod",
            "Core": "core_mod",
            "Protected": "user_mod",
            "MissingSource": "user_mod",
        },
        protected={"Protected"},
    )
    runtime_host.plugin_files["MissingSource"] = str(tmp_path / "absent.py")

    assert reload_host.list_reloadable_plugins() == ["Official", "User"]


def test_manual_reload_module_and_loader_authority_shape() -> None:
    runtime = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
    )
    module_source = (
        runtime / "core" / "VitaLoom" / "core" / "manual_plugin_reload_host.py"
    ).read_text(encoding="utf-8")
    nested_source = (
        runtime / "core" / "VitaLoom" / "core" / "nested_plugin_host.py"
    ).read_text(encoding="utf-8-sig")
    loader_source = (
        runtime / "core" / "VitaLoom" / "kernel" / "plugin_loader.py"
    ).read_text(encoding="utf-8")
    editor_adapter_source = (
        runtime
        / "core"
        / "VitaLoom"
        / "kernel"
        / "legacy_editor_plugin_adapter.py"
    ).read_text(encoding="utf-8-sig")

    assert "class ManualPluginReloadHost" in module_source
    assert "build_plugin_reload_plan(" in module_source
    assert "instantiate_plugin_from_file" in module_source
    for forbidden in (
        "PyQt6",
        "EditorKernel",
        "LayoutManager",
        "kernel.plugin_loader",
        "kernel.plugin_interfaces",
    ):
        assert forbidden not in module_source

    assert "ManualPluginReloadHost(" in nested_source
    assert "ManualPluginReloadHost(" not in loader_source
    assert "NestedPluginHost(" in loader_source
    assert "return self.nested_plugin_host.list_reloadable_plugins()" in loader_source
    assert "return self.nested_plugin_host.reload_plugin(plugin_name)" in loader_source
    assert "build_plugin_reload_plan(" not in loader_source
    assert "parse_plugin_activation_metadata(" not in loader_source
    assert editor_adapter_source.count("parse_plugin_activation_metadata(") == 1
    assert "PluginActivationContractError" not in loader_source


def test_active_reload_reuses_candidate_preflight_metadata_snapshot(tmp_path: Path) -> None:
    """Candidate metadata is read once before old active closure is removed."""
    events: list[str] = []
    runtime_host, reload_host = _authorities(tmp_path)
    old = _Plugin("TargetPlugin", events)
    _install(runtime_host, tmp_path, {"TargetPlugin": old}, active={"TargetPlugin"})

    class OneShotMetadataCandidate(_Plugin):
        def __init__(self) -> None:
            super().__init__("TargetPlugin", events, version="2.0.0")
            self.info_calls = 0

        def get_plugin_info(self):
            self.info_calls += 1
            if self.info_calls > 1:
                raise RuntimeError("reload must reuse candidate preflight metadata")
            return super().get_plugin_info()

    candidate = OneShotMetadataCandidate()

    with patch.object(
        runtime_host,
        "instantiate_plugin_from_file",
        return_value=("TargetPlugin", candidate),
    ):
        report = reload_host.reload_plugin("TargetPlugin")

    assert report["status"] == "settled"
    assert report["completed"] == {
        "deactivated": ["TargetPlugin"],
        "activated": ["TargetPlugin"],
        "registry_replaced": True,
    }
    assert candidate.info_calls == 1
    assert events == [
        "unload:TargetPlugin:1.0.0",
        "load:TargetPlugin:2.0.0",
    ]
    assert runtime_host.plugin_registry["TargetPlugin"] is candidate
    assert runtime_host.loaded_plugins["TargetPlugin"] is candidate
    assert runtime_host.plugin_metadata["TargetPlugin"]["version"] == "2.0.0"
