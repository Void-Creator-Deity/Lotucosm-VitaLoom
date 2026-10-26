# -*- coding: utf-8 -*-
"""E51 proofs for metadata-only declarative Editor contribution refresh."""
from __future__ import annotations

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


class _EventBus:
    def __init__(self, events: list[object]) -> None:
        self.events = events

    def publish(self, event_name: str, payload: object) -> None:
        self.events.append(("event", event_name, payload))


class _Layout:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(f"remove:{plugin_id}")

    def add_menu_items(self, items, plugin_id: str) -> None:
        self.events.append(f"menu:{plugin_id}:{len(items)}")

    def add_toolbar_items(self, items, plugin_id: str) -> None:
        self.events.append(f"toolbar:{plugin_id}:{len(items)}")


class _Signal:
    def emit(self, _plugin_id: str) -> None:
        pass


def _kernel(events: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        layout_manager=_Layout(events),
        get_context=lambda: SimpleNamespace(
            marker="legacy",
            event_bus=None,
            i18n_tr=lambda _key, default: default,
        ),
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )


def _metadata(plugin_id: str, *contributions: dict[str, object]) -> dict[str, object]:
    return {
        "name": plugin_id,
        "version": "1.0.0",
        "provides": ["editor_contribution"],
        "editor_contributions": [
            {"owner_plugin_id": plugin_id, **item} for item in contributions
        ],
    }


def _menu_separator(contribution_id: str) -> dict[str, object]:
    return {
        "id": contribution_id,
        "kind": "menu_separator",
        "menu_path": [
            {
                "id": "file",
                "label_key": "menu.file",
                "default_label": "File",
            }
        ],
        "order": 10,
    }


def _toolbar_separator(contribution_id: str) -> dict[str, object]:
    return {
        "id": contribution_id,
        "kind": "toolbar_separator",
        "group": "main",
        "order": 10,
    }


def test_language_change_publishes_then_invokes_declarative_refresh_seam(
    monkeypatch,
) -> None:
    from builtin.editor_extensions.localization_plugin import LocalizationPlugin

    events: list[object] = []
    kernel = SimpleNamespace(
        refresh_editor_contributions=lambda: events.append(("refresh",))
    )
    context = SimpleNamespace(kernel=kernel, event_bus=_EventBus(events))
    plugin = LocalizationPlugin()
    monkeypatch.setattr(plugin, "_load_locale", lambda language: {"language": language})

    plugin.on_load(context)
    plugin.set_language("en_US")

    assert events == [
        ("event", "language_changed", {"language": "en_US"}),
        ("refresh",),
    ]


def test_localization_source_has_no_loader_live_provider_or_layout_mechanics() -> None:
    source = (
        RUNTIME / "builtin" / "editor_extensions" / "localization_plugin.py"
    ).read_text(encoding="utf-8-sig")

    for forbidden in (
        "IMenuProvider",
        "plugin_loader",
        "loaded_plugins",
        "get_plugin_info()",
        "get_menu_items()",
        "get_toolbar_items()",
        "remove_plugin_ui",
        "add_menu_items",
        "add_toolbar_items",
        "refresh_legacy_menu_contributions",
    ):
        assert forbidden not in source
    assert "refresh_editor_contributions" in source


def test_runtime_has_no_live_menu_provider_interface_or_getters() -> None:
    sources = {
        path: path.read_text(encoding="utf-8-sig")
        for path in RUNTIME.rglob("*.py")
    }

    for forbidden in (
        "IMenuProvider",
        "get_menu_items",
        "get_toolbar_items",
    ):
        offenders = [str(path.relative_to(RUNTIME)) for path, source in sources.items() if forbidden in source]
        assert offenders == [], f"{forbidden} remains in: {offenders}"


def test_adapter_refreshes_copied_contributions_in_metadata_host_order() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[str] = []
    adapter = LegacyEditorPluginAdapter(_kernel(events))
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (
            ("CanonicalFirst", _metadata("CanonicalFirst", _menu_separator("first"))),
            ("Ignored", _metadata("Ignored")),
            (
                "CanonicalSecond",
                _metadata("CanonicalSecond", _toolbar_separator("second")),
            ),
        )
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("CanonicalSecond", object()), ("CanonicalFirst", object()))
    )

    adapter.refresh_editor_contributions()

    assert events == [
        "remove:CanonicalFirst",
        "menu:CanonicalFirst:1",
        "remove:CanonicalSecond",
        "toolbar:CanonicalSecond:1",
    ]


def test_adapter_declarative_refresh_failure_is_local_to_one_owner() -> None:
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[str] = []
    adapter = LegacyEditorPluginAdapter(_kernel(events))
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (
            (
                "Broken",
                _metadata(
                    "Broken",
                    {"id": "broken", "kind": "unknown_editor_fact", "order": 1},
                ),
            ),
            ("Healthy", _metadata("Healthy", _menu_separator("healthy"))),
        )
    )

    adapter.refresh_editor_contributions()

    assert events == [
        "remove:Broken",
        "remove:Healthy",
        "menu:Healthy:1",
    ]


def test_loader_binds_adapter_to_exact_nested_host_metadata_mapping() -> None:
    from core.VitaLoom.kernel.plugin_loader import PluginLoader

    events: list[str] = []
    loader = PluginLoader(_kernel(events))
    loader.nested_plugin_host.loaded_plugins["CanonicalPlugin"] = object()
    loader.runtime_plugin_host.plugin_metadata["CanonicalPlugin"] = _metadata(
        "CanonicalPlugin",
        _menu_separator("canonical"),
    )

    loader.legacy_editor_plugin_adapter.refresh_editor_contributions()

    assert events == [
        "remove:CanonicalPlugin",
        "menu:CanonicalPlugin:1",
    ]


def test_editor_kernel_exposes_only_narrow_declarative_refresh_delegation() -> None:
    source = (
        RUNTIME / "core" / "VitaLoom" / "kernel" / "editor_kernel.py"
    ).read_text(encoding="utf-8-sig")

    assert "def refresh_editor_contributions(self)" in source
    assert "legacy_editor_plugin_adapter.refresh_editor_contributions()" in source
    assert "refresh_legacy_menu_contributions" not in source
    assert "refresh_menu_providers" not in source


def test_adapter_source_has_no_live_or_hybrid_menu_provider_path() -> None:
    source = (
        RUNTIME
        / "core"
        / "VitaLoom"
        / "kernel"
        / "legacy_editor_plugin_adapter.py"
    ).read_text(encoding="utf-8-sig")

    for forbidden in (
        "IMenuProvider",
        "def register_menu(",
        "def _apply_menu_contributions(",
        "refresh_menu_providers",
        '"menu" in provides',
        "has_legacy",
    ):
        assert forbidden not in source