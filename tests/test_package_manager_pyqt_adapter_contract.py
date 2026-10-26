"""Real-PyQt adapter contracts; skipped rather than faking PyQt when unavailable."""
from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PyQt6", reason="requires a real PyQt6 adapter environment")

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget

from builtin.editor_extensions.package_manager_plugin import PackageManagerPlugin
from core.VitaLoom.core.runtime_capability_registry import (
    InMemoryRuntimeCapabilityRegistry,
)
from core.VitaLoom.core.service_keys import PROJECT_WORLD_MANIFEST_VALIDATION_HOST


@pytest.fixture(scope="session", autouse=True)
def qapplication() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_queue_buttons_are_enabled_only_for_updates_tab() -> None:
    plugin = PackageManagerPlugin()
    plugin.queue_select_all_btn = QPushButton()
    plugin.queue_invert_btn = QPushButton()
    plugin.queue_clear_btn = QPushButton()
    plugin.queue_only_checked_cb = QPushButton()
    plugin.queue_stats_label = None
    plugin._get_tab_filter = lambda: "installed"  # type: ignore[method-assign]

    plugin._set_queue_buttons_enabled()
    assert not plugin.queue_select_all_btn.isEnabled()

    plugin._get_tab_filter = lambda: "updates"  # type: ignore[method-assign]
    plugin._set_queue_buttons_enabled()
    assert plugin.queue_select_all_btn.isEnabled()


def test_confirm_update_plan_without_kernel_uses_operation_service() -> None:
    plugin = PackageManagerPlugin()
    plugin.kernel = None
    plugin._packages = []
    plugin.operation_service = MagicMock()
    plugin.operation_service.create_update_plan.return_value = {"count": 1, "items": [{"id": "pkg.a"}]}

    assert plugin._confirm_update_plan({"pkg.a": "1.2.0"}) == {"count": 1, "items": [{"id": "pkg.a"}]}


def test_confirm_update_plan_renders_real_message_box_content(qapplication: QApplication) -> None:
    plugin = PackageManagerPlugin()
    plugin.kernel = QWidget()
    plugin.context = None
    plugin._packages = []
    plugin.operation_service = MagicMock()
    plugin.operation_service.create_update_plan.return_value = {
        "count": 1,
        "source_summary": {"builtin": 1},
        "items": [{"id": "pkg.a", "current_version": "1.0.0", "target_version": "1.2.0", "source": "builtin"}],
    }
    captured: dict[str, str] = {}

    def accept_active_message_box() -> None:
        box = QApplication.activeModalWidget()
        assert isinstance(box, QMessageBox)
        captured["content"] = box.text()
        button = box.button(QMessageBox.StandardButton.Yes)
        assert button is not None
        button.click()

    QTimer.singleShot(0, accept_active_message_box)
    assert plugin._confirm_update_plan({"pkg.a": "1.2.0"}) is not None
    assert "pkg.a" in captured["content"]
    assert "builtin" in captured["content"]


def test_manifest_align_requires_validation_without_remaining_missing_packages() -> None:
    plugin = PackageManagerPlugin()
    validation_report = {"missing_packages": []}
    validation_host = SimpleNamespace(
        refresh_current_project_manifest_validation=lambda: dict(validation_report)
    )
    registry = InMemoryRuntimeCapabilityRegistry()
    registry.register(PROJECT_WORLD_MANIFEST_VALIDATION_HOST, validation_host)
    plugin.context = SimpleNamespace(services=registry)
    plugin.operation_service = MagicMock()
    plugin._packages = [{"id": "pkg.alpha", "status": "builtin"}]
    plugin._load_all_packages = MagicMock(return_value=plugin._packages)
    plugin._enabled_package_ids = MagicMock(return_value=set())
    plugin._get_enable_constraint_mode = MagicMock(return_value="warn")
    plugin._run_project_plugin_command = MagicMock(return_value={"ok": True})
    plugin._handle_project_plugin_command_result = lambda result: bool(result.get("ok"))

    assert plugin._align_manifest_packages(["pkg.alpha"])

    validation_report["missing_packages"] = ["pkg.alpha"]
    assert not plugin._align_manifest_packages(["pkg.alpha"])