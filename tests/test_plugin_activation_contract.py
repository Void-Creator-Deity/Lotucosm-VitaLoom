# -*- coding: utf-8 -*-
"""E17 proofs for the shared plugin activation contract and manifest authority."""
from __future__ import annotations

import builtins
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


MODULE_NAME = "core.VitaLoom.core.plugin_activation_contract"


def _module():
    return importlib.import_module(MODULE_NAME)


def test_activation_contract_module_is_qt_free(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    importlib.invalidate_caches()
    module = importlib.import_module(MODULE_NAME)
    assert module.DEFAULT_ACTIVATION_CONTEXT == "legacy_ui"
    assert module.RUNTIME_ACTIVATION_CONTEXT == "runtime"


def test_missing_activation_context_defaults_to_legacy_ui_with_explicit_fact() -> None:
    module = _module()

    metadata = module.parse_plugin_activation_metadata(
        {"name": "LegacyPlugin"}, plugin_id="LegacyPlugin", source="legacy.py"
    )

    assert metadata.kind == "legacy_ui"
    assert metadata.explicit is False
    assert metadata.to_dict() == {
        "activation_context": "legacy_ui",
        "activation_context_explicit": False,
        "activation_context_source": "default",
    }


def test_activation_context_accepts_only_explicit_known_string_kinds() -> None:
    module = _module()

    runtime = module.parse_plugin_activation_metadata(
        {"activation_context": "runtime"}, plugin_id="RuntimePlugin"
    )
    assert runtime.kind == "runtime"
    assert runtime.explicit is True

    for value, code in ((None, "activation_context_invalid_type"), (True, "activation_context_invalid_type"), ("mystery", "activation_context_unknown"), (1, "activation_context_invalid_type")):
        with pytest.raises(module.PluginActivationContractError) as caught:
            module.parse_plugin_activation_metadata(
                {"activation_context": value}, plugin_id="BadPlugin"
            )
        assert caught.value.code == code
        assert caught.value.details["plugin_id"] == "BadPlugin"


def test_manifest_and_code_context_kinds_must_match() -> None:
    module = _module()

    manifest = module.parse_plugin_activation_metadata(
        {"activation_context": "runtime"}, plugin_id="ExamplePlugin", source="plugin.json"
    )
    code = module.parse_plugin_activation_metadata(
        {"activation_context": "legacy_ui"}, plugin_id="ExamplePlugin", source="entry.py"
    )

    with pytest.raises(module.PluginActivationContractError, match="manifest/code"):
        module.validate_plugin_activation_context_pair(manifest, code)


def test_catalog_entry_and_operator_facts_include_context_kind() -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import PluginHostCatalogEntry
    from core.VitaLoom.project.plugin_host_operator import build_plugin_host_inspection

    entry = PluginHostCatalogEntry(
        plugin_id="RuntimePlugin",
        scope="official_mod",
        source="runtime.py",
        version="1.0.0",
        activation_context="runtime",
        activation_context_explicit=True,
    )
    inspection = build_plugin_host_inspection(
        project_path="C:/world",
        embedded_catalog_project_path="",
        catalog_entries=[entry],
        active_plugin_ids={"RuntimePlugin"},
        failed_plugins={},
        discovery_report={"status": "ready", "diagnostics": []},
        lifecycle_report={"status": "settled", "diagnostics": []},
    )

    assert inspection["catalog"][0]["activation_context"] == "runtime"
    assert inspection["catalog"][0]["activation_context_explicit"] is True


def test_l4_manifest_missing_context_is_backward_compatible(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    addon = project / "addons" / "legacy"
    addon.mkdir(parents=True)
    (addon / "legacy_plugin.py").write_text("raise AssertionError('must not import')\n", encoding="utf-8")
    (addon / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "LegacyPlugin",
                "version": "1.0.0",
                "entry": "legacy_plugin.py",
                "runtime": {"plugin_id": "lotucosm-vitaloom", "version": "1.0.0"},
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )

    result = discover_project_addons(project, runtime_version="1.0.0")
    assert result.ok is True
    source = result.sources[0]
    assert source.activation_context == "legacy_ui"
    assert source.activation_context_explicit is False
    assert source.to_dict()["activation_context_source"] == "default"


def test_l4_manifest_invalid_context_fails_before_entry_import(tmp_path: Path) -> None:
    from core.VitaLoom.project.plugin_host_lifecycle import discover_project_addons

    project = tmp_path / "world"
    addon = project / "addons" / "invalid"
    addon.mkdir(parents=True)
    (addon / "invalid_plugin.py").write_text("raise AssertionError('must not import')\n", encoding="utf-8")
    (addon / "plugin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "InvalidPlugin",
                "version": "1.0.0",
                "entry": "invalid_plugin.py",
                "activation_context": "mystery",
                "runtime": {"plugin_id": "lotucosm-vitaloom", "version": "1.0.0"},
                "dependencies": [],
            }
        ),
        encoding="utf-8",
    )

    result = discover_project_addons(project, runtime_version="1.0.0")
    assert result.ok is False
    assert [item.code for item in result.diagnostics] == ["activation_context_unknown"]


def test_plugin_loader_discovery_rejects_invalid_code_metadata(tmp_path: Path) -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader
    from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin

    class Kernel:
        def get_context(self):
            return SimpleNamespace()

    source = tmp_path / "invalid_plugin.py"
    source.write_text(
        "from core.VitaLoom.kernel.plugin_interfaces import IEditorPlugin\n"
        "class InvalidPlugin(IEditorPlugin):\n"
        "    def get_plugin_info(self):\n"
        "        return {'name': 'InvalidPlugin', 'activation_context': 'mystery'}\n"
        "    def on_load(self, context): pass\n"
        "    def on_unload(self): pass\n",
        encoding="utf-8",
    )

    loader = PluginLoader(Kernel())
    loader._discover_plugin(source, loader.SCOPE_USER)
    assert "InvalidPlugin" not in loader.plugin_registry
    assert "activation_context_unknown" in next(iter(loader.discovery_errors.values()))
