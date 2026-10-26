# -*- coding: utf-8 -*-
"""E46 Qt-free theme facts and exact legacy Qt style lifecycle."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


RUNTIME = (
    Path(__file__).resolve().parents[1]
    / "FrameCore"
    / "plugins"
    / "lotucosm-vitaloom"
    / "versions"
    / "1.0.0"
    / "runtime"
)


def _theme_profile(**overrides):
    item = {
        "id": "unity_dark.profile",
        "kind": "theme_profile",
        "theme_id": "unity.dark",
        "name_key": "theme.unity_dark.name",
        "default_name": "Unity Dark",
        "appearance": "dark",
        "palette": {
            "background": "#282828",
            "border": "#202020",
            "highlight": "#2a5a8a",
            "hover": "#4a4a4a",
            "menubar": "#3c3c3c",
            "text": "#d0d0d0",
        },
        "order": 100,
    }
    item.update(overrides)
    return item


def _normalized_info(owner: str, item: dict, *, provides=None) -> dict:
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    return {
        "name": owner,
        "version": "1.0.0",
        "provides": list(provides or ["theme", "editor_contribution"]),
        "editor_contributions": [
            contribution.to_dict()
            for contribution in parse_editor_contributions(owner, [item])
        ],
    }


class _Signal:
    def __init__(self, events: list[object], name: str) -> None:
        self.events = events
        self.name = name

    def emit(self, plugin_id: str) -> None:
        self.events.append((self.name, plugin_id))


class _ThemeLayout:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.theme_state = {
            "application": "APP-BASELINE",
            "main_window": "WINDOW-BASELINE",
        }
        self.capture_calls = 0
        self.apply_calls: list[tuple[str, str]] = []
        self.restore_calls: list[dict[str, str]] = []
        self.fail_apply_count = 0
        self.fail_restore_count = 0

    def capture_theme_style_state(self):
        self.capture_calls += 1
        return dict(self.theme_state)

    def register_theme(self, theme_name: str, stylesheet: str) -> None:
        if self.fail_apply_count:
            self.fail_apply_count -= 1
            raise RuntimeError("theme apply failed")
        self.apply_calls.append((theme_name, stylesheet))
        self.theme_state = {
            "application": stylesheet,
            "main_window": stylesheet,
        }
        self.events.append(("apply_theme", theme_name, stylesheet))

    def restore_theme_style_state(self, state) -> None:
        if self.fail_restore_count:
            self.fail_restore_count -= 1
            raise RuntimeError("theme restore failed")
        copied = {
            "application": state["application"],
            "main_window": state["main_window"],
        }
        self.restore_calls.append(copied)
        self.theme_state = copied
        self.events.append(("restore_theme", copied))

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        pass

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        pass

    def remove_plugin_ui(self, plugin_id: str) -> None:
        self.events.append(("remove_ui", plugin_id))

    def process_pending_dock_tabify(self) -> None:
        pass


class _ThemePluginBase:
    def __init__(
        self,
        info: dict,
        stylesheet: str,
        *,
        legacy_name: str = "Legacy Theme",
        forbid_profile_getters: bool = True,
    ) -> None:
        self.info = info
        self.stylesheet = stylesheet
        self.legacy_name = legacy_name
        self.forbid_profile_getters = forbid_profile_getters
        self.stylesheet_calls = 0
        self.name_calls = 0
        self.color_scheme_calls = 0
        self.ready_calls = 0

    def get_plugin_info(self):
        return self.info

    def on_load(self, _context):
        pass

    def on_unload(self):
        pass

    def on_editor_ready(self):
        self.ready_calls += 1

    def get_theme_name(self):
        self.name_calls += 1
        if self.forbid_profile_getters:
            raise AssertionError("declarative theme identity must come from copied facts")
        return self.legacy_name

    def get_stylesheet(self):
        self.stylesheet_calls += 1
        return self.stylesheet

    def get_color_scheme(self):
        self.color_scheme_calls += 1
        if self.forbid_profile_getters:
            raise AssertionError("declarative palette must come from copied facts")
        return {"text": "#ffffff"}


def _theme_plugin(info: dict, stylesheet: str, **kwargs):
    from core.VitaLoom.kernel.plugin_interfaces import IThemeProvider

    class ThemePlugin(_ThemePluginBase, IThemeProvider):
        pass

    return ThemePlugin(info, stylesheet, **kwargs)


def _adapter_fixture():
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    events: list[object] = []
    layout = _ThemeLayout(events)
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: SimpleNamespace(),
        plugin_loaded=_Signal(events, "loaded"),
        plugin_unloaded=_Signal(events, "unloaded"),
    )
    return LegacyEditorPluginAdapter(kernel), layout, events


def _style_dependencies():
    return (
        patch(
            "core.VitaLoom.ui.theme_manager.get_theme_manager",
            return_value=SimpleNamespace(DARK_THEME="DARK", LIGHT_THEME="LIGHT"),
        ),
        patch(
            "core.VitaLoom.ui.design_tokens.modern_editor_overlay",
            return_value="OVERLAY",
        ),
    )


def test_theme_profile_is_immutable_host_owned_and_json_safe() -> None:
    from core.VitaLoom.core import editor_contribution_contract as contract

    profile = contract.parse_editor_contributions(
        "UnityDarkTheme", [_theme_profile()]
    )[0]

    assert isinstance(profile, contract.EditorThemeProfileContribution)
    assert profile.owner_plugin_id == "UnityDarkThemePlugin"
    assert profile.kind == contract.THEME_PROFILE_KIND
    assert profile.theme_id == "unity.dark"
    assert profile.name_key == "theme.unity_dark.name"
    assert profile.default_name == "Unity Dark"
    assert profile.appearance == "dark"
    assert list(profile.palette) == sorted(profile.palette)
    assert profile.palette["background"] == "#282828"
    with pytest.raises(dataclasses.FrozenInstanceError):
        profile.order = 5
    with pytest.raises(TypeError):
        profile.palette["text"] = "#ffffff"

    observed = profile.to_dict()
    assert json.loads(json.dumps(observed)) == observed
    assert "stylesheet" not in observed
    assert "qss" not in json.dumps(observed).lower()


def test_theme_profiles_are_deterministic_and_theme_ids_are_unique_per_owner() -> None:
    from core.VitaLoom.core import editor_contribution_contract as contract

    profiles = contract.parse_editor_contributions(
        "ThemePackPlugin",
        [
            _theme_profile(
                id="light.profile",
                theme_id="pack.light",
                default_name="Light",
                appearance="light",
                order=20,
            ),
            _theme_profile(
                id="dark.z",
                theme_id="pack.dark.z",
                default_name="Dark Z",
                order=10,
            ),
            _theme_profile(
                id="dark.a",
                theme_id="pack.dark.a",
                default_name="Dark A",
                order=10,
            ),
        ],
    )
    assert [profile.id for profile in profiles] == [
        "dark.a",
        "dark.z",
        "light.profile",
    ]

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "ThemePackPlugin",
            [
                _theme_profile(),
                _theme_profile(id="duplicate.profile", order=200),
            ],
        )
    assert captured.value.code == "contribution_duplicate_theme_id"


@pytest.mark.parametrize(
    ("override", "code"),
    [
        ({"owner_plugin_id": "OtherPlugin"}, "contribution_owner_forbidden"),
        ({"stylesheet": "QWidget { color: red; }"}, "contribution_theme_field_unknown"),
        ({"qss": "QWidget {}"}, "contribution_theme_field_unknown"),
        ({"appearance": "qt-dark"}, "contribution_theme_appearance_invalid"),
        ({"palette": {"QWidget": "#ffffff"}}, "contribution_theme_palette_token_invalid"),
        ({"palette": {"text": "white"}}, "contribution_theme_palette_color_invalid"),
        ({"palette": {"text": object()}}, "contribution_value_not_json_safe"),
        ({"palette": {"text": lambda: "#ffffff"}}, "contribution_live_value_forbidden"),
    ],
)
def test_theme_profile_rejects_qt_qss_live_and_invalid_palette_values(
    override: dict, code: str
) -> None:
    from core.VitaLoom.core import editor_contribution_contract as contract

    with pytest.raises(contract.EditorContributionContractError) as captured:
        contract.parse_editor_contributions(
            "UnityDarkThemePlugin", [_theme_profile(**override)]
        )
    assert captured.value.code == code


def test_contract_stays_qt_free_and_has_no_theme_registry_or_host() -> None:
    from core.VitaLoom.core import editor_contribution_contract as contract

    source = Path(contract.__file__).read_text(encoding="utf-8-sig")
    for forbidden in (
        "from PyQt6",
        "import PyQt6",
        "IThemeProvider",
        "ThemeManager",
        "LayoutManager",
        "class ThemeRegistry",
        "class ThemeHost",
    ):
        assert forbidden not in source


def test_builtin_unity_dark_publishes_one_portable_profile_without_qss() -> None:
    from builtin.editor_extensions.unity_dark_theme_plugin import UnityDarkThemePlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        EditorThemeProfileContribution,
        parse_editor_contributions,
    )

    info = UnityDarkThemePlugin().get_plugin_info()
    profiles = parse_editor_contributions(
        "UnityDarkThemePlugin", info["editor_contributions"]
    )

    assert len(profiles) == 1
    profile = profiles[0]
    assert isinstance(profile, EditorThemeProfileContribution)
    assert profile.theme_id == "unity.dark"
    assert profile.default_name == "Unity Dark"
    assert profile.appearance == "dark"
    assert profile.palette == UnityDarkThemePlugin().get_color_scheme()
    assert "QWidget" not in json.dumps(profile.to_dict())


def test_adapter_uses_copied_profile_identity_and_only_live_qss_payload() -> None:
    adapter, layout, _events = _adapter_fixture()
    info = _normalized_info("CopiedThemePlugin", _theme_profile())
    plugin = _theme_plugin(info, "PLUGIN-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(plugin, "CopiedThemePlugin", info)

    assert plugin.name_calls == 0
    assert plugin.color_scheme_calls == 0
    assert plugin.stylesheet_calls == 1
    assert layout.capture_calls == 1
    assert layout.apply_calls == [
        ("Unity Dark", "DARK\nOVERLAY\nPLUGIN-QSS")
    ]
    assert adapter._theme_owner_by_id == {"unity.dark": "CopiedThemePlugin"}
    assert list(adapter._theme_projection_by_owner) == ["CopiedThemePlugin"]


def test_theme_id_collision_is_rejected_before_any_style_mutation() -> None:
    adapter, layout, _events = _adapter_fixture()
    first_info = _normalized_info("FirstThemePlugin", _theme_profile(order=10))
    second_info = _normalized_info(
        "SecondThemePlugin",
        _theme_profile(id="other.profile", default_name="Other", order=20),
    )
    first = _theme_plugin(first_info, "FIRST-QSS")
    second = _theme_plugin(second_info, "SECOND-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(first, "FirstThemePlugin", first_info)
        before_state = dict(layout.theme_state)
        before_calls = list(layout.apply_calls)
        with pytest.raises(RuntimeError, match="theme id .* already owned"):
            adapter.after_plugin_load(second, "SecondThemePlugin", second_info)

    assert layout.theme_state == before_state
    assert layout.apply_calls == before_calls
    assert second.stylesheet_calls == 0
    assert adapter._theme_owner_by_id == {"unity.dark": "FirstThemePlugin"}


def test_theme_priority_is_deterministic_and_unload_reprojects_previous_layer() -> None:
    adapter, layout, _events = _adapter_fixture()
    high_info = _normalized_info(
        "HighThemePlugin",
        _theme_profile(
            id="high.profile",
            theme_id="theme.high",
            default_name="High",
            order=200,
        ),
    )
    low_info = _normalized_info(
        "LowThemePlugin",
        _theme_profile(
            id="low.profile",
            theme_id="theme.low",
            default_name="Low",
            appearance="light",
            order=10,
        ),
    )
    high = _theme_plugin(high_info, "HIGH-QSS")
    low = _theme_plugin(low_info, "LOW-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(high, "HighThemePlugin", high_info)
        adapter.after_plugin_load(low, "LowThemePlugin", low_info)
        assert layout.apply_calls == [("High", "DARK\nOVERLAY\nHIGH-QSS")]
        adapter.before_plugin_unload(high, "HighThemePlugin", high_info)

    assert layout.apply_calls[-1] == ("Low", "LIGHT\nOVERLAY\nLOW-QSS")
    assert adapter._theme_owner_by_id == {"theme.low": "LowThemePlugin"}
    assert list(adapter._theme_projection_by_owner) == ["LowThemePlugin"]


def test_last_theme_unload_restores_exact_application_and_window_baseline() -> None:
    adapter, layout, _events = _adapter_fixture()
    info = _normalized_info("ThemePlugin", _theme_profile())
    plugin = _theme_plugin(info, "ACTIVE-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(plugin, "ThemePlugin", info)
        adapter.before_plugin_unload(plugin, "ThemePlugin", info)

    assert layout.restore_calls == [
        {"application": "APP-BASELINE", "main_window": "WINDOW-BASELINE"}
    ]
    assert layout.theme_state == {
        "application": "APP-BASELINE",
        "main_window": "WINDOW-BASELINE",
    }
    assert adapter._theme_owner_by_id == {}
    assert adapter._theme_projection_by_owner == {}
    assert adapter._theme_baseline_state is None


def test_theme_cleanup_failure_retains_projection_and_can_retry() -> None:
    adapter, layout, _events = _adapter_fixture()
    info = _normalized_info("RetryThemePlugin", _theme_profile())
    plugin = _theme_plugin(info, "ACTIVE-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(plugin, "RetryThemePlugin", info)
        active_state = dict(layout.theme_state)
        layout.fail_restore_count = 1
        with pytest.raises(RuntimeError, match="theme restore failed"):
            adapter.before_plugin_unload(plugin, "RetryThemePlugin", info)

        assert layout.theme_state == active_state
        assert adapter._theme_owner_by_id == {
            "unity.dark": "RetryThemePlugin"
        }
        assert "RetryThemePlugin" in adapter._theme_projection_by_owner

        adapter.before_plugin_unload(plugin, "RetryThemePlugin", info)

    assert layout.theme_state == {
        "application": "APP-BASELINE",
        "main_window": "WINDOW-BASELINE",
    }
    assert adapter._theme_owner_by_id == {}
    assert adapter._theme_projection_by_owner == {}


def test_reload_reuses_owner_without_stale_stylesheet() -> None:
    adapter, layout, _events = _adapter_fixture()
    info = _normalized_info("ReloadThemePlugin", _theme_profile())
    first = _theme_plugin(info, "OLD-QSS")
    replacement = _theme_plugin(info, "NEW-QSS")
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(first, "ReloadThemePlugin", info)
        adapter.before_plugin_unload(first, "ReloadThemePlugin", info)
        adapter.after_plugin_load(replacement, "ReloadThemePlugin", info)

    assert layout.apply_calls[-1] == (
        "Unity Dark",
        "DARK\nOVERLAY\nNEW-QSS",
    )
    assert "OLD-QSS" not in layout.theme_state["application"]
    assert adapter._theme_owner_by_id == {
        "unity.dark": "ReloadThemePlugin"
    }


def test_unmigrated_community_theme_keeps_legacy_payload_fallback_and_restores() -> None:
    adapter, layout, _events = _adapter_fixture()
    info = {
        "name": "CommunityThemePlugin",
        "version": "1.0.0",
        "provides": ["theme"],
        "editor_contributions": [],
    }
    plugin = _theme_plugin(
        info,
        "COMMUNITY-QSS",
        legacy_name="Community Theme",
        forbid_profile_getters=False,
    )
    dark_patch, overlay_patch = _style_dependencies()

    with dark_patch, overlay_patch:
        adapter.after_plugin_load(plugin, "CommunityThemePlugin", info)
        adapter.before_plugin_unload(plugin, "CommunityThemePlugin", info)

    assert plugin.name_calls == 1
    assert plugin.stylesheet_calls == 1
    assert plugin.color_scheme_calls == 0
    assert layout.apply_calls == [
        ("Community Theme", "DARK\nCOMMUNITY-QSS")
    ]
    assert layout.theme_state == {
        "application": "APP-BASELINE",
        "main_window": "WINDOW-BASELINE",
    }


def test_layout_manager_theme_state_apply_restore_is_exact_and_transactional() -> None:
    from core.VitaLoom.kernel import layout_manager as layout_module

    class StyleTarget:
        def __init__(self, value: str, *, fail_value: str | None = None) -> None:
            self.value = value
            self.fail_value = fail_value

        def styleSheet(self) -> str:
            return self.value

        def setStyleSheet(self, value: str) -> None:
            if value == self.fail_value:
                raise RuntimeError("style mutation failed")
            self.value = value

    app = StyleTarget("APP-ORIGINAL")
    window = StyleTarget("WINDOW-ORIGINAL", fail_value="BROKEN")
    manager = layout_module.LayoutManager.__new__(layout_module.LayoutManager)
    manager.main_window = window

    with patch.object(
        layout_module,
        "QApplication",
        SimpleNamespace(instance=lambda: app),
    ):
        baseline = manager.capture_theme_style_state()
        manager.register_theme("Working", "WORKING")
        assert app.value == "WORKING"
        assert window.value == "WORKING"
        manager.restore_theme_style_state(baseline)
        assert app.value == "APP-ORIGINAL"
        assert window.value == "WINDOW-ORIGINAL"

        with pytest.raises(RuntimeError, match="style mutation failed"):
            manager.register_theme("Broken", "BROKEN")

    assert app.value == "APP-ORIGINAL"
    assert window.value == "WINDOW-ORIGINAL"