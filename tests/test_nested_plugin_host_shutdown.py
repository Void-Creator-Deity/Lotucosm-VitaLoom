# -*- coding: utf-8 -*-
"""E25 red proofs for composition-root shutdown publication."""
from __future__ import annotations


class _Plugin:
    def get_plugin_info(self):
        return {
            "name": "RuntimePlugin",
            "version": "1.0.0",
            "dependencies": [],
            "provides": [],
            "activation_context": "runtime",
        }

    def on_load(self, _context):
        return None

    def on_unload(self):
        return None


def test_nested_shutdown_publishes_exact_report_once_and_skips_noop_observer() -> None:
    from core.VitaLoom.core.nested_plugin_host import NestedPluginHost

    observed: list[dict] = []
    host = NestedPluginHost(
        repo_root_resolver=lambda: ".",
        eager_mode_resolver=lambda: False,
        player_mode_resolver=lambda: False,
        bootstrap_plugin_ids_resolver=lambda _root: set(),
        after_lifecycle_transition=observed.append,
    )
    runtime = host.runtime_plugin_host
    plugin = _Plugin()
    runtime.register_plugin(plugin, scope=runtime.SCOPE_CORE, source="RuntimePlugin.py")
    runtime.loaded_plugins["RuntimePlugin"] = plugin
    runtime.resolve_dependencies()

    published: list[dict] = []
    original_publish = host._publish_lifecycle_report

    def publish(report):
        published.append(report)
        original_publish(report)

    host._publish_lifecycle_report = publish

    report = host.shutdown_plugins()

    assert published == [report]
    assert observed == [report]
    assert host.last_lifecycle_report is report
    assert runtime.last_lifecycle_report is report

    noop = host.shutdown_plugins()

    assert published == [report, noop]
    assert observed == [report]
    assert noop["status"] == "noop"
    assert host.last_lifecycle_report is noop
    assert runtime.last_lifecycle_report is noop
