# -*- coding: utf-8 -*-
"""E40 PsExperiment Dock shell, retained Panel localization, and exact lifecycles."""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

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


class _EventBus:
    def __init__(
        self,
        *,
        fail_subscribe_on: str | None = None,
        fail_unsubscribe_once_on: str | None = None,
    ) -> None:
        self.fail_subscribe_on = fail_subscribe_on
        self.fail_unsubscribe_once_on = fail_unsubscribe_once_on
        self.callbacks: dict[str, list] = {}
        self.subscribe_calls: list[tuple[str, object]] = []
        self.unsubscribe_calls: list[tuple[str, object]] = []
        self.published: list[tuple[str, object]] = []

    def subscribe(self, event_name: str, callback) -> None:
        if event_name == self.fail_subscribe_on:
            raise RuntimeError(f"subscribe failed: {event_name}")
        self.subscribe_calls.append((event_name, callback))
        self.callbacks.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback) -> None:
        self.unsubscribe_calls.append((event_name, callback))
        if event_name == self.fail_unsubscribe_once_on:
            self.fail_unsubscribe_once_on = None
            raise RuntimeError(f"unsubscribe failed: {event_name}")
        callbacks = self.callbacks.get(event_name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def publish(self, event_name: str, data=None) -> None:
        self.published.append((event_name, data))
        for callback in tuple(self.callbacks.get(event_name, ())):
            callback(data)


class _Registry:
    def __init__(
        self,
        *,
        fail_register_on: str | None = None,
        fail_unregister_once_on: str | None = None,
    ) -> None:
        self.values: dict[str, object] = {}
        self.fail_register_on = fail_register_on
        self.fail_unregister_once_on = fail_unregister_once_on
        self.register_calls: list[tuple[str, object]] = []
        self.unregister_calls: list[str] = []

    def register(self, key: str, value: object) -> None:
        self.register_calls.append((key, value))
        if key == self.fail_register_on:
            raise RuntimeError(f"register failed: {key}")
        self.values[key] = value

    def unregister(self, key: str) -> None:
        self.unregister_calls.append(key)
        if key == self.fail_unregister_once_on:
            self.fail_unregister_once_on = None
            raise RuntimeError(f"unregister failed: {key}")
        self.values.pop(key, None)

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.values


class _Dock:
    def __init__(self, title: str = "", panel: object | None = None) -> None:
        self.object_name = ""
        self.window_title = title
        self.panel = panel
        self.deleted = 0

    def setObjectName(self, value: str) -> None:
        self.object_name = value

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value

    def setWidget(self, panel: object) -> None:
        self.panel = panel

    def widget(self):
        return self.panel

    def deleteLater(self) -> None:
        self.deleted += 1


class _Layout:
    def __init__(self) -> None:
        self.docks: dict[str, _Dock] = {}
        self.add_calls: list[tuple[_Dock, dict]] = []
        self.remove_calls: list[str] = []

    def add_dock(self, dock, config) -> None:
        copied = dict(config)
        self.add_calls.append((dock, copied))
        self.docks[copied["title"]] = dock

    def remove_dock(self, dock_id: str) -> None:
        self.remove_calls.append(dock_id)
        self.docks.pop(dock_id, None)

    def add_menu_items(self, _items, _plugin_id: str) -> None:
        pass

    def add_toolbar_items(self, _items, _plugin_id: str) -> None:
        pass

    def remove_plugin_ui(self, _plugin_id: str) -> None:
        pass

    def process_pending_dock_tabify(self) -> None:
        pass


class _Signal:
    def connect(self, _callback) -> None:
        pass

    def disconnect(self, _callback) -> None:
        pass

    def emit(self, *_args) -> None:
        pass


class _PsBridge:
    def __init__(self, info: dict) -> None:
        self.info = info
        self.created = 0
        self.panel = object()
        self.dock: _Dock | None = None

    def get_plugin_info(self):
        return self.info

    def create_dock_widget(self):
        self.created += 1
        self.dock = _Dock(panel=self.panel)
        return self.dock

    def get_dock_config(self):
        raise AssertionError("declarative dock config must be authoritative")

    def get_menu_items(self):
        return []

    def get_toolbar_items(self):
        return []


class _FakeService:
    fail_bind = False
    fail_unbind_once = False
    running = False
    instances: list["_FakeService"] = []

    def __init__(self, root: Path) -> None:
        self.root = root
        self.is_running = type(self).running
        self.bound_context = None
        self.bind_calls = 0
        self.unbind_calls = 0
        self.cancel_calls = 0
        type(self).instances.append(self)

    def bind_editor_context(self, context: object) -> None:
        self.bind_calls += 1
        if type(self).fail_bind:
            raise RuntimeError("service bind failed")
        self.bound_context = context

    def unbind_editor_context(self) -> None:
        self.unbind_calls += 1
        if type(self).fail_unbind_once:
            type(self).fail_unbind_once = False
            raise RuntimeError("service unbind failed")
        self.bound_context = None

    def request_cancel(self) -> None:
        self.cancel_calls += 1

    def discover_runtime_organisms(self) -> dict:
        return {}

    def query_runtime_organism_snapshot(self, identity: object) -> dict:
        return {"identity": identity}


class _FakePanel:
    def __init__(self, _context: object) -> None:
        self.project_opened = 0
        self.finished = 0
        self.config_changed = 0
        self.retranslated = 0

    def _on_project_opened(self, _data: object) -> None:
        self.project_opened += 1

    def _on_experiment_finished(self, _data: object) -> None:
        self.finished += 1

    def _on_config_changed(self, _data: object) -> None:
        self.config_changed += 1

    def retranslate_ui(self) -> None:
        self.retranslated += 1


def _normalized_info() -> dict:
    from builtin.editor_extensions.ps_experiment_plugin import PsExperimentPlugin
    from core.VitaLoom.core.editor_contribution_contract import (
        parse_editor_contributions,
    )

    info = PsExperimentPlugin().get_plugin_info()
    return {
        **info,
        "editor_contributions": [
            item.to_dict()
            for item in parse_editor_contributions(
                "PsExperimentPlugin", info["editor_contributions"]
            )
        ],
    }


def _load_plugin(
    monkeypatch,
    *,
    bus: _EventBus | None = None,
    registry: _Registry | None = None,
    fake_service: type[_FakeService] = _FakeService,
):
    import builtin.editor_extensions.ps_experiment_plugin as module

    bus = bus or _EventBus()
    registry = registry or _Registry()
    fake_service.instances.clear()
    fake_service.fail_bind = False
    fake_service.fail_unbind_once = False
    fake_service.running = False
    monkeypatch.setattr(module, "PsExperimentService", fake_service)
    context = SimpleNamespace(
        event_bus=bus,
        services=registry,
        kernel=None,
        project_root=RUNTIME,
        current_project_path=None,
        i18n_tr=lambda _key, default: default,
    )
    plugin = module.PsExperimentPlugin()
    plugin.on_load(context)
    return module, plugin, context, bus, registry, fake_service.instances[-1]


def _install_fake_panel(monkeypatch, module) -> None:
    import core.VitaLoom.docks.ps_experiment_panel as panel_module

    monkeypatch.setattr(module, "QDockWidget", _Dock)
    monkeypatch.setattr(panel_module, "PsExperimentPanel", _FakePanel)


def test_ps_experiment_declares_one_qt_free_dock_shell() -> None:
    from builtin.editor_extensions.ps_experiment_plugin import PsExperimentPlugin

    info = PsExperimentPlugin().get_plugin_info()

    assert info["provides"] == ["dock", "editor_contribution"]
    assert info["editor_contributions"] == [
        {
            "id": "ps_experiment.surface",
            "kind": "dock_surface",
            "dock_id": "PsExperiment",
            "title_key": "ps_experiment.dock_title",
            "default_title": "莲池演化实验",
            "area": "right",
            "default_visible": False,
            "can_close": True,
            "can_float": True,
            "can_move": True,
            "tabbed_with": "EcologyDashboard",
            "order": 80,
            "refresh_events": ["language_changed"],
        }
    ]


def test_ps_experiment_adapter_projects_and_refreshes_title_in_place() -> None:
    from PyQt6.QtCore import Qt
    from core.VitaLoom.kernel.legacy_editor_plugin_adapter import (
        LegacyEditorPluginAdapter,
    )

    bus = _EventBus()
    translations = {"ps_experiment.dock_title": "莲池演化实验"}
    context = SimpleNamespace(
        event_bus=bus,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    layout = _Layout()
    kernel = SimpleNamespace(
        layout_manager=layout,
        get_context=lambda: context,
        plugin_loaded=_Signal(),
        plugin_unloaded=_Signal(),
    )
    adapter = LegacyEditorPluginAdapter(kernel)
    info = _normalized_info()
    plugin = _PsBridge(info)
    adapter.bind_active_plugin_metadata_resolver(
        lambda: (("PsExperimentPlugin", info),)
    )
    adapter.bind_active_plugin_items_resolver(
        lambda: (("PsExperimentPlugin", plugin),)
    )

    adapter.after_plugin_load(plugin, "PsExperimentPlugin", info)
    dock = layout.docks["PsExperiment"]
    panel = plugin.panel
    translations["ps_experiment.dock_title"] = "Lotus Evolution Experiment"
    bus.publish("language_changed")

    assert plugin.created == 1
    assert len(layout.add_calls) == 1
    assert layout.remove_calls == []
    assert layout.docks["PsExperiment"] is dock
    assert dock.panel is panel
    assert dock.window_title == "Lotus Evolution Experiment"
    assert layout.add_calls[0][1] == {
        "title": "PsExperiment",
        "area": Qt.DockWidgetArea.RightDockWidgetArea,
        "default_visible": False,
        "can_close": True,
        "can_float": True,
        "can_move": True,
        "tabbed_with": "EcologyDashboard",
    }


def test_ps_experiment_panel_retranslates_in_place_without_self_subscription(
    monkeypatch,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    import core.VitaLoom.docks.ps_experiment_panel as panel_module

    app = QApplication.instance() or QApplication([])
    source = (RUNTIME / "core" / "VitaLoom" / "docks" / "ps_experiment_panel.py").read_text(
        encoding="utf-8-sig"
    )
    assert ".event_bus.subscribe(" not in source

    monkeypatch.setattr(panel_module, "get_ps_experiment_service", lambda _ctx: None)
    bus = _EventBus()
    translations: dict[str, str] = {}
    context = SimpleNamespace(
        event_bus=bus,
        current_project_path=None,
        i18n_tr=lambda key, default: translations.get(key, default),
    )
    panel = panel_module.PsExperimentPanel(context)
    panel.preset_combo.addItems(["alpha", "beta"])
    panel.preset_combo.setCurrentIndex(1)
    panel.history_combo.addItems(["run-a", "run-b"])
    panel.history_combo.setCurrentIndex(1)
    panel.baseline_combo.addItems(["none", "run-a", "run-b"])
    panel.baseline_combo.setCurrentIndex(2)
    panel.ticks_spin.setValue(4321)
    panel.seed_spin.setValue(77)
    panel.enable_gen_check.setChecked(False)
    panel.cancel_btn.setEnabled(True)
    panel.status_label.setText("dynamic-result")

    identities = {
        "panel": id(panel),
        "preset": id(panel.preset_combo),
        "history": id(panel.history_combo),
        "baseline": id(panel.baseline_combo),
    }
    translations.update(
        {
            "ps_experiment.title": "Evolution Lab",
            "ps_experiment.hint": "Run PVAEC in the editor.",
            "ps_experiment.preset": "Preset",
            "ps_experiment.reload": "Reload",
            "ps_experiment.project_binding": "Project Binding",
            "ps_experiment.save_preset_to_project": "Save Preset Path",
            "ps_experiment.save_evolution_defaults": "Save Evolution Defaults",
            "ps_experiment.params": "Parameters",
            "ps_experiment.ticks": "Ticks",
            "ps_experiment.seed_random": "Random",
            "ps_experiment.seed": "Seed",
            "ps_experiment.initial_organisms": "Initial Organisms",
            "ps_experiment.max_population": "Population Limit",
            "ps_experiment.generation_interval": "Generation Interval",
            "ps_experiment.mutation_rate": "Mutation Rate",
            "ps_experiment.selection_pressure": "Selection Pressure",
            "ps_experiment.elitism_rate": "Elitism Rate",
            "ps_experiment.enable_generation": "Enable Generations",
            "ps_experiment.enable_pvaec": "Run PVAEC Each Tick",
            "ps_experiment.run": "Run Experiment",
            "ps_experiment.cancel": "Cancel",
            "ps_experiment.history": "Run History",
            "ps_experiment.refresh_history": "Refresh History",
            "ps_experiment.compare_baseline": "Baseline",
            "ps_experiment.compare_none": "(No comparison)",
            "ps_experiment.open_history_dir": "Open Run Directory",
            "ps_experiment.result": "Result",
            "ps_experiment.open_output": "Open Output Directory",
        }
    )

    panel.retranslate_ui()
    app.processEvents()

    assert identities == {
        "panel": id(panel),
        "preset": id(panel.preset_combo),
        "history": id(panel.history_combo),
        "baseline": id(panel.baseline_combo),
    }
    assert panel.preset_combo.currentIndex() == 1
    assert panel.history_combo.currentIndex() == 1
    assert panel.baseline_combo.currentIndex() == 2
    assert panel.ticks_spin.value() == 4321
    assert panel.seed_spin.value() == 77
    assert panel.enable_gen_check.isChecked() is False
    assert panel.cancel_btn.isEnabled() is True
    assert panel.status_label.text() == "dynamic-result"
    assert panel._title_label.text() == "Evolution Lab"
    assert panel._hint_label.text() == "Run PVAEC in the editor."
    assert panel._preset_group.title() == "Preset"
    assert panel._reload_btn.text() == "Reload"
    assert panel._params_group.title() == "Parameters"
    assert panel._form_layout.labelForField(panel.ticks_spin).text() == "Ticks"
    assert panel.seed_spin.specialValueText() == "Random"
    assert panel.run_btn.text() == "Run Experiment"
    assert panel._history_group.title() == "Run History"
    assert panel._baseline_label.text() == "Baseline"
    assert panel.open_history_dir_btn.text() == "Open Run Directory"
    assert panel._result_group.title() == "Result"
    assert panel.open_dir_btn.text() == "Open Output Directory"
    assert bus.subscribe_calls == []


def test_plugin_owns_panel_events_once_and_releases_in_reverse(monkeypatch) -> None:
    module, plugin, _context, bus, _registry, _service = _load_plugin(monkeypatch)
    _install_fake_panel(monkeypatch, module)

    dock = plugin.create_dock_widget()
    panel = dock.panel
    assert plugin.create_dock_widget() is dock
    assert [name for name, _callback in bus.subscribe_calls] == [
        "project_opened",
        "ps_experiment_finished",
        "ps_experiment_config_changed",
        "language_changed",
    ]

    bus.publish("project_opened", {})
    bus.publish("ps_experiment_finished", {})
    bus.publish("ps_experiment_config_changed", {})
    bus.publish("language_changed", {})
    assert (panel.project_opened, panel.finished, panel.config_changed, panel.retranslated) == (
        1,
        1,
        1,
        1,
    )

    plugin.on_unload()
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "language_changed",
        "ps_experiment_config_changed",
        "ps_experiment_finished",
        "project_opened",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert dock.deleted == 1
    assert plugin.dock is None
    assert plugin._panel is None

    plugin.on_unload()
    assert len(bus.unsubscribe_calls) == 4
    assert dock.deleted == 1


def test_panel_subscription_failure_rolls_back_and_keeps_no_stale_panel(
    monkeypatch,
) -> None:
    bus = _EventBus(fail_subscribe_on="ps_experiment_config_changed")
    module, plugin, _context, _bus, _registry, _service = _load_plugin(
        monkeypatch, bus=bus
    )
    _install_fake_panel(monkeypatch, module)

    with pytest.raises(RuntimeError, match="subscribe failed: ps_experiment_config_changed"):
        plugin.create_dock_widget()

    assert [name for name, _callback in bus.subscribe_calls] == [
        "project_opened",
        "ps_experiment_finished",
    ]
    assert [name for name, _callback in bus.unsubscribe_calls] == [
        "ps_experiment_finished",
        "project_opened",
    ]
    assert all(not callbacks for callbacks in bus.callbacks.values())
    assert plugin._panel_event_subscriptions == []
    assert plugin._panel is None
    assert plugin.dock is None


def test_service_binding_failure_and_unbind_retry_preserve_exact_state(tmp_path) -> None:
    from core.VitaLoom.simulation.ps_experiment_service import PsExperimentService

    failing_bus = _EventBus(fail_subscribe_on="project_opened")
    service = PsExperimentService(tmp_path)
    context = SimpleNamespace(event_bus=failing_bus, current_project_path=None)

    with pytest.raises(RuntimeError, match="subscribe failed: project_opened"):
        service.bind_editor_context(context)

    assert service._editor_context is None
    assert service._project_open_handler is None
    assert failing_bus.callbacks == {}

    retry_bus = _EventBus(fail_unsubscribe_once_on="project_opened")
    retry_context = SimpleNamespace(event_bus=retry_bus, current_project_path=None)
    service.bind_editor_context(retry_context)

    with pytest.raises(RuntimeError, match="unsubscribe failed: project_opened"):
        service.unbind_editor_context()

    assert service._editor_context is retry_context
    assert service._project_open_handler is not None
    assert retry_bus.callbacks["project_opened"] == [service._project_open_handler]

    service.unbind_editor_context()
    assert service._editor_context is None
    assert service._project_open_handler is None
    assert retry_bus.callbacks["project_opened"] == []
    service.unbind_editor_context()
    assert len(retry_bus.unsubscribe_calls) == 2


def test_publication_failure_rolls_back_service_binding(monkeypatch) -> None:
    import builtin.editor_extensions.ps_experiment_plugin as module
    from core.VitaLoom.core.service_keys import PS_RUNTIME_SNAPSHOT_HOST

    bus = _EventBus()
    registry = _Registry(fail_register_on=PS_RUNTIME_SNAPSHOT_HOST)
    _FakeService.instances.clear()
    _FakeService.fail_bind = False
    _FakeService.fail_unbind_once = False
    monkeypatch.setattr(module, "PsExperimentService", _FakeService)
    plugin = module.PsExperimentPlugin()
    context = SimpleNamespace(
        event_bus=bus,
        services=registry,
        kernel=None,
        project_root=RUNTIME,
        current_project_path=None,
    )

    with pytest.raises(RuntimeError, match="register failed"):
        plugin.on_load(context)

    service = _FakeService.instances[-1]
    assert service.bind_calls == 1
    assert service.unbind_calls == 1
    assert service.bound_context is None
    assert registry.values == {}
    assert plugin._service is None
    assert plugin._runtime_snapshot_host is None
    assert plugin._service_publication is None


def test_primary_load_error_survives_failed_unbind_and_can_retry(monkeypatch) -> None:
    import builtin.editor_extensions.ps_experiment_plugin as module

    class _PrimaryService(_FakeService):
        pass

    _PrimaryService.instances.clear()
    _PrimaryService.fail_bind = False
    _PrimaryService.fail_unbind_once = True
    monkeypatch.setattr(module, "PsExperimentService", _PrimaryService)
    monkeypatch.setattr(
        module,
        "publish_capabilities",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("publish primary")),
    )
    plugin = module.PsExperimentPlugin()
    context = SimpleNamespace(
        event_bus=_EventBus(),
        services=_Registry(),
        kernel=None,
        project_root=RUNTIME,
        current_project_path=None,
    )

    with pytest.raises(RuntimeError, match="publish primary"):
        plugin.on_load(context)

    service = _PrimaryService.instances[-1]
    assert service.unbind_calls == 1
    assert service.bound_context is context
    assert plugin._service is service
    assert plugin._service_bound is True

    plugin.on_unload()
    assert service.unbind_calls == 2
    assert service.bound_context is None
    assert plugin._service is None


def test_unload_partial_failures_continue_and_are_retryable(monkeypatch) -> None:
    from core.VitaLoom.core.service_keys import PS_EXPERIMENT, PS_RUNTIME_SNAPSHOT_HOST

    class _RetryService(_FakeService):
        pass

    bus = _EventBus(fail_unsubscribe_once_on="ps_experiment_finished")
    registry = _Registry(fail_unregister_once_on=PS_RUNTIME_SNAPSHOT_HOST)
    module, plugin, context, _bus, _registry, service = _load_plugin(
        monkeypatch,
        bus=bus,
        registry=registry,
        fake_service=_RetryService,
    )
    _install_fake_panel(monkeypatch, module)
    dock = plugin.create_dock_widget()
    service.is_running = True
    _RetryService.fail_unbind_once = True

    replacement = object()
    registry.register(PS_EXPERIMENT, replacement)

    with pytest.raises(RuntimeError):
        plugin.on_unload()

    assert service.cancel_calls == 1
    assert len(plugin._panel_event_subscriptions) == 1
    assert plugin._service_publication is not None
    assert plugin._service_bound is True
    assert plugin._service is service
    assert registry.get(PS_EXPERIMENT) is replacement
    assert registry.get(PS_RUNTIME_SNAPSHOT_HOST) is plugin._runtime_snapshot_host
    assert plugin.dock is dock
    assert dock.deleted == 0

    plugin.on_unload()

    assert plugin._panel_event_subscriptions == []
    assert plugin._service_publication is None
    assert plugin._service_bound is False
    assert plugin._service is None
    assert plugin._runtime_snapshot_host is None
    assert registry.get(PS_EXPERIMENT) is replacement
    assert registry.has(PS_RUNTIME_SNAPSHOT_HOST) is False
    assert plugin.dock is None
    assert plugin._panel is None
    assert dock.deleted == 1
    assert service.cancel_calls == 2

    plugin.on_unload()
    assert dock.deleted == 1


def test_plugin_prefers_application_root_for_project_relative_presets(monkeypatch) -> None:
    import builtin.editor_extensions.ps_experiment_plugin as module

    _FakeService.instances.clear()
    _FakeService.fail_bind = False
    _FakeService.fail_unbind_once = False
    _FakeService.running = False
    monkeypatch.setattr(module, "PsExperimentService", _FakeService)
    application_root = Path("C:/application-root")
    repo_root = Path("C:/runtime-root")
    project_root = Path("C:/project-root")
    context = SimpleNamespace(
        event_bus=_EventBus(),
        services=_Registry(),
        kernel=None,
        application_root=application_root,
        repo_root=repo_root,
        project_root=project_root,
        current_project_path=None,
    )

    plugin = module.PsExperimentPlugin()
    plugin.on_load(context)
    try:
        assert _FakeService.instances[-1].root == application_root
    finally:
        plugin.on_unload()

def test_plugin_resolves_application_root_for_runtime_projection(monkeypatch) -> None:
    import builtin.editor_extensions.ps_experiment_plugin as module

    _FakeService.instances.clear()
    _FakeService.fail_bind = False
    _FakeService.fail_unbind_once = False
    _FakeService.running = False
    monkeypatch.setattr(module, "PsExperimentService", _FakeService)
    application_root = Path("C:/application-root")
    monkeypatch.setattr(module, "application_root", lambda: application_root)
    context = SimpleNamespace(event_bus=_EventBus(), services=_Registry())

    plugin = module.PsExperimentPlugin()
    plugin.on_load(context)
    try:
        assert _FakeService.instances[-1].root == application_root
    finally:
        plugin.on_unload()
