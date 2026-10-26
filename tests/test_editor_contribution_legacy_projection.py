# -*- coding: utf-8 -*-
"""Qt-free Editor contribution ownership and legacy projection proofs."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self._events = events
        self._name = name

    def emit(self, plugin_id: str) -> None:
        self._events.append((self._name, plugin_id))


class _EventBus:
    def __init__(self, events: list[object]) -> None:
        self._events = events

    def publish(self, topic: str, payload: object) -> None:
        self._events.append(("event", topic, payload))


class _Layout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.menu_batches: list[tuple[str, list[dict[str, object]]]] = []

    def add_menu_items(self, items, plugin_id: str) -> None:
        copied = list(items)
        self.menu_batches.append((plugin_id, copied))
        self.events.append(("menu", plugin_id, [item.get("path") for item in copied]))

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        self.events.append(("toolbar", plugin_id, len(items)))

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove", plugin_id))


class _PassivePlugin:
    def get_plugin_info(self):
        return {"name": "PassivePlugin", "version": "1.0.0"}

    def on_load(self, _context) -> None:
        return None

    def on_unload(self) -> None:
        return None


def _kernel(events: list[object], context: object):
    return SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: context,
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )


def _normalized_localization_ui_info() -> dict[str, object]:
    from builtin.editor_extensions.localization_ui_plugin import LocalizationUIPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = LocalizationUIPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "LocalizationUIPlugin", info["editor_contributions"]
            )
        ],
    }


def test_runtime_host_caches_copied_contribution_observations() -> None:
    from builtin.editor_extensions.localization_ui_plugin import LocalizationUIPlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    plugin = LocalizationUIPlugin()
    declaration = plugin.get_plugin_info()
    host = RuntimePluginHost()
    plugin_id = host.register_plugin(plugin)

    declaration["editor_contributions"][0]["command_payload"]["language"] = "xx"
    observed = host.plugin_metadata[plugin_id]["editor_contributions"]

    assert observed[0]["owner_plugin_id"] == "LocalizationUIPlugin"
    assert observed[0]["command_payload"] == {"language": "zh_CN"}
    json.dumps(observed, ensure_ascii=False)


def test_localization_ui_metadata_is_observable_without_importing_pyqt() -> None:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(RUNTIME), existing] if existing else [str(RUNTIME)]
    )
    code = (
        "import json, sys; "
        "from builtin.editor_extensions.localization_ui_plugin import LocalizationUIPlugin; "
        "payload=LocalizationUIPlugin().get_plugin_info(); "
        "json.dumps(payload, ensure_ascii=False); "
        "assert not any(name.startswith('PyQt6') for name in sys.modules); "
        "print(len(payload['editor_contributions']))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "2"


def test_runtime_host_passes_copied_normalized_facts_to_adapter() -> None:
    from builtin.editor_extensions.localization_ui_plugin import LocalizationUIPlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class CaptureAdapter:
        def __init__(self) -> None:
            self.loaded: list[tuple[str, dict[str, object]]] = []

        def after_plugin_load(self, _plugin, plugin_id, plugin_info) -> None:
            self.loaded.append((plugin_id, plugin_info))

        def before_plugin_unload(self, _plugin, _plugin_id, _plugin_info) -> None:
            return None

        def after_plugin_unload_callback(self, _plugin, _plugin_id, _plugin_info) -> None:
            return None

        def after_plugin_deactivated(self, _plugin, _plugin_id, _plugin_info) -> None:
            return None

    plugin = LocalizationUIPlugin()
    declaration = plugin.get_plugin_info()
    adapter = CaptureAdapter()
    host = RuntimePluginHost(adapter=adapter)
    plugin_id = host.register_plugin(plugin)
    declaration["editor_contributions"][0]["command_payload"]["language"] = "xx"

    host.load_plugin(plugin)

    observed_id, observed_info = adapter.loaded[-1]
    assert observed_id == plugin_id == "LocalizationUIPlugin"
    assert observed_info == host.plugin_metadata[plugin_id]
    assert observed_info is not host.plugin_metadata[plugin_id]
    assert observed_info["editor_contributions"][0]["owner_plugin_id"] == plugin_id
    assert observed_info["editor_contributions"][0]["command_payload"] == {
        "language": "zh_CN"
    }


def test_localization_ui_declares_no_live_provider_or_layout_mechanics() -> None:
    from builtin.editor_extensions.localization_ui_plugin import LocalizationUIPlugin

    info = LocalizationUIPlugin().get_plugin_info()
    assert "editor_contribution" in info["provides"]
    assert len(info["editor_contributions"]) == 2
    json.dumps(info, ensure_ascii=False)

    source = (
        RUNTIME / "builtin" / "editor_extensions" / "localization_ui_plugin.py"
    ).read_text(encoding="utf-8-sig")
    for forbidden in (
        "IMenuProvider",
        "get_menu_items",
        "get_toolbar_items",
        "layout_manager",
        "remove_plugin_ui",
        "add_menu_items",
        '"action"',
    ):
        assert forbidden not in source


def test_legacy_adapter_projects_localized_command_actions() -> None:
    from builtin.editor_extensions.localization_plugin import LocalizationPlugin
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    registry = reset_command_registry()
    events: list[object] = []
    context = SimpleNamespace(event_bus=_EventBus(events))
    kernel = _kernel(events, context)
    context.kernel = kernel
    kernel.refresh_editor_contributions = lambda: events.append(("refresh",))

    localization = LocalizationPlugin()
    localization._load_locale = lambda language: {
        "menu.tools": "Tools",
        "menu.language": "Language",
        "menu.language.zh": "Simplified Chinese",
        "menu.language.en": "English",
    }
    adapter = LegacyEditorPluginAdapter(kernel)
    host = RuntimePluginHost(
        activation_context_resolver=lambda _info: context,
        adapter=adapter,
    )
    host.register_plugin(localization)
    report = host.execute_lifecycle_target(
        {"LocalizationPlugin"}, source="test", allow_deactivate=True
    )
    assert report["status"] == "settled"

    adapter.after_plugin_load(
        _PassivePlugin(),
        "LocalizationUIPlugin",
        _normalized_localization_ui_info(),
    )

    plugin_id, menu_items = kernel.layout_manager.menu_batches[-1]
    assert plugin_id == "LocalizationUIPlugin"
    assert [item["path"] for item in menu_items] == [
        "Tools/Language/Simplified Chinese",
        "Tools/Language/English",
    ]
    assert all(callable(item["action"]) for item in menu_items)

    result = menu_items[1]["action"]()
    assert result["ok"] is True
    assert result["result"]["language"] == "en_US"
    assert ("event", "language_changed", {"language": "en_US"}) in events
    assert ("refresh",) in events
    assert registry.describe("editor.language.set")["owner"] == "LocalizationPlugin"

def test_declarative_refresh_uses_copied_host_metadata_order() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    context = SimpleNamespace(i18n_tr=lambda key, default: f"tr:{key}" if key else default)
    kernel = _kernel(events, context)
    adapter = LegacyEditorPluginAdapter(kernel)
    first = _normalized_localization_ui_info()
    second = {
        **first,
        "name": "SecondPlugin",
        "editor_contributions": [
            {
                **first["editor_contributions"][0],
                "owner_plugin_id": "SecondPlugin",
                "id": "second.command",
            }
        ],
    }
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("LocalizationUIPlugin", first), ("SecondPlugin", second))
    )
    adapter.bind_active_plugin_items_resolver(lambda: ())

    adapter.refresh_editor_contributions()

    removes = [event for event in events if event[0] == "remove"]
    menus = [event for event in events if event[0] == "menu"]
    assert removes == [
        ("remove", "LocalizationUIPlugin"),
        ("remove", "SecondPlugin"),
    ]
    assert [event[1] for event in menus] == [
        "LocalizationUIPlugin",
        "SecondPlugin",
    ]


def test_declarative_contribution_cleanup_remains_plugin_owned() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    context = SimpleNamespace(i18n_tr=lambda _key, default: default)
    adapter = LegacyEditorPluginAdapter(_kernel(events, context))

    adapter.before_plugin_unload(
        _PassivePlugin(),
        "LocalizationUIPlugin",
        _normalized_localization_ui_info(),
    )

    assert events == [("remove", "LocalizationUIPlugin")]


def test_language_command_is_registry_visible_and_validates_payload() -> None:
    from builtin.editor_extensions.localization_plugin import LocalizationPlugin
    from core.VitaLoom.commands.registry import reset_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    registry = reset_command_registry()
    events: list[object] = []
    context = SimpleNamespace(event_bus=_EventBus(events))
    kernel = _kernel(events, context)
    context.kernel = kernel
    kernel.refresh_editor_contributions = lambda: None

    plugin = LocalizationPlugin()
    plugin._load_locale = lambda _language: {}
    host = RuntimePluginHost(activation_context_resolver=lambda _info: context)
    host.register_plugin(plugin)
    report = host.execute_lifecycle_target(
        {"LocalizationPlugin"}, source="test", allow_deactivate=True
    )
    assert report["status"] == "settled"

    described = registry.describe("editor.language.set")
    assert described["owner"] == "LocalizationPlugin"
    assert described["capability"] == "vitalloom.editor_essentials"
    assert registry.run("editor.language.set", {})["error"]["code"] == "schema_validation_failed"

    invalid = registry.run("editor.language.set", {"language": "xx"})
    assert invalid["ok"] is False
    assert invalid["error"]["code"] in {
        "invalid_payload",
        "unsupported_language",
    }

