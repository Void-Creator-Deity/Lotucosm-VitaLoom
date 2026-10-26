# -*- coding: utf-8 -*-
"""E52 proofs for Host-owned Qt-free command-provider lifecycle."""
from __future__ import annotations

from dataclasses import replace

import pytest


@pytest.fixture(autouse=True)
def _fresh_command_registry():
    from core.VitaLoom.commands.registry import reset_command_registry

    registry = reset_command_registry()
    yield registry
    reset_command_registry()


def _command_spec(command_id: str, *, owner: str = "declared-owner"):
    from core.VitaLoom.commands.registry import CommandSpec, command_ok

    return CommandSpec(
        id=command_id,
        title=command_id,
        owner=owner,
        handler=lambda _payload, _context: command_ok({"command_id": command_id}),
    )


def _provider_plugin(
    plugin_id: str,
    specs,
    events: list[str],
    *,
    fail_load: bool = False,
):
    from core.VitaLoom.core.runtime_plugin_contract import (
        ICommandProvider,
        IRuntimePlugin,
    )

    class Plugin(IRuntimePlugin, ICommandProvider):
        def get_plugin_info(self):
            return {
                "name": plugin_id,
                "version": "1.0.0",
                "dependencies": [],
                "provides": ("command",),
                "activation_context": "runtime",
            }

        def get_command_specs(self):
            events.append(f"commands:{plugin_id}")
            return list(specs)

        def on_load(self, _context):
            events.append(f"load:{plugin_id}")
            if fail_load:
                raise RuntimeError("load failed")

        def on_unload(self):
            events.append(f"unload:{plugin_id}")

    return Plugin()


def test_headless_host_publishes_commands_after_on_load_with_canonical_owner() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    plugin = _provider_plugin(
        "HeadlessCommandPlugin",
        [_command_spec("headless.echo")],
        events,
    )
    host = RuntimePluginHost()
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"HeadlessCommandPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert events == ["load:HeadlessCommandPlugin", "commands:HeadlessCommandPlugin"]
    assert get_command_registry().describe("headless.echo")["owner"] == (
        "HeadlessCommandPlugin"
    )
    assert host.loaded_plugins == {"HeadlessCommandPlugin": plugin}


def test_provider_batch_failure_rolls_back_every_command_without_partial_state() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    plugin = _provider_plugin(
        "DuplicateCommandPlugin",
        [_command_spec("duplicate.command"), _command_spec("duplicate.command")],
        events,
    )
    host = RuntimePluginHost()
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"DuplicateCommandPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"] == {
        "action": "activate",
        "plugin_id": "DuplicateCommandPlugin",
        "error": "ValueError",
    }
    with pytest.raises(KeyError):
        get_command_registry().describe("duplicate.command")
    assert host.loaded_plugins == {}
    assert events == [
        "load:DuplicateCommandPlugin",
        "commands:DuplicateCommandPlugin",
        "unload:DuplicateCommandPlugin",
    ]


def test_partial_registry_failure_releases_the_exact_registered_prefix(
    monkeypatch,
) -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    plugin = _provider_plugin(
        "PartialCommandPlugin",
        [_command_spec("partial.one"), _command_spec("partial.two")],
        events,
    )
    registry = get_command_registry()
    original_register = registry.register

    def fail_second(spec) -> None:
        if spec.id == "partial.two":
            raise RuntimeError("second registration failed")
        original_register(spec)

    monkeypatch.setattr(registry, "register", fail_second)
    host = RuntimePluginHost()
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"PartialCommandPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert report["failed_action"]["error"] == "RuntimeError"
    with pytest.raises(KeyError):
        registry.describe("partial.one")
    with pytest.raises(KeyError):
        registry.describe("partial.two")
    assert host.loaded_plugins == {}
    assert events == [
        "load:PartialCommandPlugin",
        "commands:PartialCommandPlugin",
        "unload:PartialCommandPlugin",
    ]


def test_adapter_failure_after_publication_rolls_back_exact_command_batch() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class FailingAdapter:
        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            assert get_command_registry().describe("adapter.visible")["owner"] == plugin_id
            raise RuntimeError("projection failed")

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            events.append(f"adapter_cleanup:{plugin_id}")

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            return None

    events: list[str] = []
    plugin = _provider_plugin(
        "AdapterFailurePlugin", [_command_spec("adapter.visible")], events
    )
    host = RuntimePluginHost(adapter=FailingAdapter())
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"AdapterFailurePlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    with pytest.raises(KeyError):
        get_command_registry().describe("adapter.visible")
    assert host.loaded_plugins == {}
    assert events == [
        "load:AdapterFailurePlugin",
        "commands:AdapterFailurePlugin",
        "adapter_cleanup:AdapterFailurePlugin",
        "unload:AdapterFailurePlugin",
    ]


def test_unload_releases_only_the_exact_specs_published_by_that_activation() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    original = _command_spec("replacement.safe")
    plugin = _provider_plugin("ExactOwnerPlugin", [original], events)
    host = RuntimePluginHost()
    host.register_plugin(plugin)
    host.execute_lifecycle_target(
        {"ExactOwnerPlugin"}, source="test", allow_deactivate=True
    )

    registry = get_command_registry()
    registry.unregister("replacement.safe")
    replacement = replace(
        original,
        title="replacement",
        owner="ExactOwnerPlugin",
    )
    registry.register(replacement)

    assert host.unload_plugin("ExactOwnerPlugin") is True
    assert registry.describe("replacement.safe")["title"] == "replacement"
    assert events[-1] == "unload:ExactOwnerPlugin"



def test_post_registry_observer_failure_preserves_converged_removal() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []

    class FailingObserverAdapter:
        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            return None

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            events.append(f"adapter_cleanup:{plugin_id}")

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            events.append(f"after_deactivated:{plugin_id}")
            raise RuntimeError("simulated post-registry observer failure")

    plugin = _provider_plugin(
        "PostRegistryObserverPlugin",
        [_command_spec("post.registry.observer")],
        events,
    )
    host = RuntimePluginHost(adapter=FailingObserverAdapter())
    host.register_plugin(plugin)
    host.execute_lifecycle_target(
        {"PostRegistryObserverPlugin"}, source="test", allow_deactivate=True
    )

    assert host.unload_plugin("PostRegistryObserverPlugin") is False
    assert events == [
        "load:PostRegistryObserverPlugin",
        "commands:PostRegistryObserverPlugin",
        "adapter_cleanup:PostRegistryObserverPlugin",
        "unload:PostRegistryObserverPlugin",
        "after_deactivated:PostRegistryObserverPlugin",
    ]
    assert host.loaded_plugins == {}
    assert host._deactivation_progress == {}
    with pytest.raises(KeyError):
        get_command_registry().describe("post.registry.observer")

    # The plugin has already been removed; retry cannot and must not replay
    # the final observer or resurrect lifecycle ownership.
    assert host.unload_plugin("PostRegistryObserverPlugin") is False
    assert events.count("after_deactivated:PostRegistryObserverPlugin") == 1


def test_deactivation_retries_use_fresh_host_metadata_snapshots() -> None:
    """Adapter-side metadata mutation must not alter Host lifecycle facts or retries."""
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_contract import ICommandProvider, IRuntimePlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class SnapshotPlugin(IRuntimePlugin, ICommandProvider):
        def __init__(self) -> None:
            self.raise_info = False
            self.fail_on_unload = True
            self.info_calls = 0
            self.unload_calls = 0

        def get_plugin_info(self):
            self.info_calls += 1
            if self.raise_info:
                raise RuntimeError("live metadata must not be read during retry")
            return {
                "name": "MetadataSnapshotPlugin",
                "version": "1.0.0",
                "description": "registered snapshot",
                "dependencies": [],
                "provides": ("command",),
                "activation_context": "runtime",
            }

        def get_command_specs(self):
            return [_command_spec("metadata.snapshot.command")]

        def on_load(self, _context) -> None:
            return None

        def on_unload(self) -> None:
            self.unload_calls += 1
            if self.fail_on_unload:
                raise RuntimeError("simulated unload failure after cleanup")

    class MutatingAdapter:
        def __init__(self) -> None:
            self.cleanup_calls = 0
            self.observed_descriptions: list[str] = []

        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            self.observed_descriptions.append(plugin_info["description"])
            plugin_info["description"] = "after-load mutation"

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            self.cleanup_calls += 1
            self.observed_descriptions.append(plugin_info["description"])
            plugin_info["description"] = "cleanup mutation"

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            self.observed_descriptions.append(plugin_info["description"])

    plugin = SnapshotPlugin()
    adapter = MutatingAdapter()
    host = RuntimePluginHost(adapter=adapter)
    host.register_plugin(plugin)
    host.execute_lifecycle_target(
        {"MetadataSnapshotPlugin"}, source="test", allow_deactivate=True
    )

    assert host.plugin_metadata["MetadataSnapshotPlugin"]["description"] == (
        "registered snapshot"
    )
    assert adapter.observed_descriptions == ["registered snapshot"]
    assert plugin.info_calls == 1  # registration only; activation uses Host metadata

    assert host.unload_plugin("MetadataSnapshotPlugin") is False
    assert adapter.cleanup_calls == 1
    assert plugin.unload_calls == 1
    assert adapter.observed_descriptions == [
        "registered snapshot",
        "registered snapshot",
    ]
    assert host.plugin_metadata["MetadataSnapshotPlugin"]["description"] == (
        "registered snapshot"
    )

    plugin.raise_info = True
    plugin.fail_on_unload = False
    assert host.unload_plugin("MetadataSnapshotPlugin") is True

    assert plugin.info_calls == 1
    assert adapter.cleanup_calls == 1
    assert plugin.unload_calls == 2
    assert adapter.observed_descriptions == [
        "registered snapshot",
        "registered snapshot",
        "registered snapshot",
    ]
    assert host.plugin_metadata["MetadataSnapshotPlugin"]["description"] == (
        "registered snapshot"
    )
    assert host.loaded_plugins == {}
    assert host._deactivation_progress == {}
    with pytest.raises(KeyError):
        get_command_registry().describe("metadata.snapshot.command")

def test_deactivation_does_not_fall_back_from_present_empty_host_metadata() -> None:
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class EmptySnapshotPlugin(IRuntimePlugin):
        def __init__(self) -> None:
            self.info_calls = 0
            self.raise_info = False

        def get_plugin_info(self):
            self.info_calls += 1
            if self.raise_info:
                raise RuntimeError("present Host metadata must prevent live fallback")
            return {
                "name": "EmptyMetadataSnapshotPlugin",
                "version": "1.0.0",
                "dependencies": [],
                "activation_context": "runtime",
            }

        def on_load(self, _context) -> None:
            return None

        def on_unload(self) -> None:
            return None

    class RecordingAdapter:
        def __init__(self) -> None:
            self.metadata: list[dict[str, object]] = []

        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            return None

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            self.metadata.append(dict(plugin_info))

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            self.metadata.append(dict(plugin_info))

    plugin = EmptySnapshotPlugin()
    adapter = RecordingAdapter()
    host = RuntimePluginHost(adapter=adapter)
    host.register_plugin(plugin)
    host.execute_lifecycle_target(
        {"EmptyMetadataSnapshotPlugin"}, source="test", allow_deactivate=True
    )

    # Direct registry-replacement paths may leave a deliberately sparse cache;
    # its presence is still a Host fact, never a reason to query the live object.
    host.plugin_metadata["EmptyMetadataSnapshotPlugin"] = {}
    plugin.raise_info = True

    assert host.unload_plugin("EmptyMetadataSnapshotPlugin") is True
    assert plugin.info_calls == 1  # registration only; activation uses Host metadata
    assert adapter.metadata == [{}, {}]
    assert host.loaded_plugins == {}

def test_command_release_failure_resumes_without_replaying_cleanup_or_on_unload(
    monkeypatch,
) -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class RecordingAdapter:
        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            return None

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            events.append(f"adapter_cleanup:{plugin_id}")

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            events.append(f"after_deactivated:{plugin_id}")

    events: list[str] = []
    plugin = _provider_plugin(
        "RetryCommandReleasePlugin",
        [_command_spec("retry.command.release")],
        events,
    )
    host = RuntimePluginHost(adapter=RecordingAdapter())
    host.register_plugin(plugin)
    host.execute_lifecycle_target(
        {"RetryCommandReleasePlugin"}, source="test", allow_deactivate=True
    )

    original_release = host._release_plugin_commands
    release_attempts = 0

    def fail_once(plugin_id: str) -> None:
        nonlocal release_attempts
        release_attempts += 1
        if release_attempts == 1:
            raise RuntimeError("simulated command release failure")
        original_release(plugin_id)

    monkeypatch.setattr(host, "_release_plugin_commands", fail_once)

    assert host.unload_plugin("RetryCommandReleasePlugin") is False
    assert host.loaded_plugins == {"RetryCommandReleasePlugin": plugin}
    assert events == [
        "load:RetryCommandReleasePlugin",
        "commands:RetryCommandReleasePlugin",
        "adapter_cleanup:RetryCommandReleasePlugin",
        "unload:RetryCommandReleasePlugin",
    ]
    assert get_command_registry().describe("retry.command.release")["owner"] == (
        "RetryCommandReleasePlugin"
    )

    assert host.unload_plugin("RetryCommandReleasePlugin") is True
    assert release_attempts == 2
    assert events == [
        "load:RetryCommandReleasePlugin",
        "commands:RetryCommandReleasePlugin",
        "adapter_cleanup:RetryCommandReleasePlugin",
        "unload:RetryCommandReleasePlugin",
        "after_deactivated:RetryCommandReleasePlugin",
    ]
    with pytest.raises(KeyError):
        get_command_registry().describe("retry.command.release")
    assert host.loaded_plugins == {}
    assert host._deactivation_progress == {}

def test_shutdown_releases_headless_provider_commands_after_on_unload() -> None:
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    events: list[str] = []
    plugin = _provider_plugin(
        "ShutdownCommandPlugin", [_command_spec("shutdown.command")], events
    )
    host = RuntimePluginHost()
    host.register_plugin(plugin, protected=True)
    host.execute_lifecycle_target(
        {"ShutdownCommandPlugin"}, source="test", allow_deactivate=True
    )

    report = host.shutdown_plugins()

    assert report["status"] == "settled"
    assert events == [
        "load:ShutdownCommandPlugin",
        "commands:ShutdownCommandPlugin",
        "unload:ShutdownCommandPlugin",
    ]
    with pytest.raises(KeyError):
        get_command_registry().describe("shutdown.command")
    assert host.loaded_plugins == {}




def test_activation_uses_registered_metadata_snapshot_for_context_projection_and_rollback() -> None:
    """Known registry activation must not re-read mutable plugin metadata."""
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class SnapshotPlugin(IRuntimePlugin):
        def __init__(self) -> None:
            self.info_calls = 0
            self.events: list[str] = []

        def get_plugin_info(self):
            self.info_calls += 1
            if self.info_calls > 1:
                raise RuntimeError("activation must use registered Host metadata")
            return {
                "name": "ActivationSnapshotPlugin",
                "version": "1.0.0",
                "description": "registered activation snapshot",
                "dependencies": [],
                "activation_context": "runtime",
            }

        def on_load(self, context) -> None:
            self.events.append(f"load:{type(context).__name__}")

        def on_unload(self) -> None:
            self.events.append("unload")

    class FailingMutatingAdapter:
        def __init__(self) -> None:
            self.observed: list[tuple[str, str]] = []

        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            self.observed.append(("after_load", plugin_info["description"]))
            plugin_info["description"] = "adapter mutation"
            raise RuntimeError("projection failed")

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            self.observed.append(("rollback_cleanup", plugin_info["description"]))

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            return None

    plugin = SnapshotPlugin()
    adapter = FailingMutatingAdapter()
    host = RuntimePluginHost(adapter=adapter)
    host.register_plugin(plugin)

    report = host.execute_lifecycle_target(
        {"ActivationSnapshotPlugin"}, source="test", allow_deactivate=True
    )

    assert report["status"] == "failed"
    assert plugin.info_calls == 1
    assert plugin.events == ["load:NoneType", "unload"]
    assert adapter.observed == [
        ("after_load", "registered activation snapshot"),
        ("rollback_cleanup", "registered activation snapshot"),
    ]
    assert host.plugin_metadata["ActivationSnapshotPlugin"]["description"] == (
        "registered activation snapshot"
    )
    assert host.loaded_plugins == {}

def test_catalog_entry_cache_round_trip_preserves_known_activation_metadata() -> None:
    """Direct catalog cache must retain every Host-owned activation fact."""
    from core.VitaLoom.commands.registry import get_command_registry
    from core.VitaLoom.core.runtime_plugin_contract import (
        ICommandProvider,
        IRuntimePlugin,
    )
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class CatalogPlugin(IRuntimePlugin, ICommandProvider):
        def __init__(self) -> None:
            self.info_calls = 0
            self.contexts: list[object] = []

        def get_plugin_info(self):
            self.info_calls += 1
            if self.info_calls > 1:
                raise RuntimeError("catalog activation must use cached metadata")
            return {
                "name": "CatalogMetadataPlugin",
                "version": "3.2.1",
                "description": "catalog cache round trip",
                "dependencies": [],
                "provides": ("command",),
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "catalog.separator",
                        "kind": "toolbar_separator",
                        "group": "catalog",
                        "order": 4,
                    }
                ],
            }

        def get_command_specs(self):
            return [_command_spec("catalog.metadata")]

        def on_load(self, context) -> None:
            self.contexts.append(context)

        def on_unload(self) -> None:
            return None

    class RecordingAdapter:
        def __init__(self) -> None:
            self.after_load: list[dict[str, object]] = []

        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            self.after_load.append(dict(plugin_info))

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            return None

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            return None

    plugin = CatalogPlugin()
    source = RuntimePluginHost()
    plugin_id = source.register_plugin(plugin, source="catalog_source.py")
    entry = source.catalog_entries()[0]

    adapter = RecordingAdapter()
    destination = RuntimePluginHost(
        activation_context_resolver=lambda info: {
            "context": info["activation_context"],
            "declared_name": info["declared_name"],
        },
        adapter=adapter,
    )
    destination.plugin_registry[plugin_id] = plugin
    destination.plugin_scopes[plugin_id] = entry.scope
    destination.plugin_files[plugin_id] = entry.source
    destination.plugin_dependencies[plugin_id] = list(entry.dependencies)
    destination.cache_catalog_entry_metadata(entry)

    report = destination.execute_lifecycle_target(
        {plugin_id}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert plugin.info_calls == 1
    assert plugin.contexts == [
        {"context": "runtime", "declared_name": "CatalogMetadataPlugin"}
    ]
    assert get_command_registry().describe("catalog.metadata")["owner"] == plugin_id
    assert adapter.after_load == [
        {
            "name": plugin_id,
            "declared_name": "CatalogMetadataPlugin",
            "version": "3.2.1",
            "description": "catalog cache round trip",
            "provides": ("command",),
            "activation_context": "runtime",
            "activation_context_explicit": True,
            "editor_contributions": [
                {
                    "owner_plugin_id": plugin_id,
                    "id": "catalog.separator",
                    "kind": "toolbar_separator",
                    "group": "catalog",
                    "order": 4,
                }
            ],
        }
    ]


def test_catalog_entry_metadata_handoffs_are_mutation_isolated() -> None:
    """Catalog snapshots must never become an alias of Host metadata."""
    from core.VitaLoom.core.runtime_plugin_contract import IRuntimePlugin
    from core.VitaLoom.core.runtime_plugin_host import RuntimePluginHost

    class CatalogPlugin(IRuntimePlugin):
        def __init__(self) -> None:
            self.info_calls = 0
            self.contexts: list[object] = []

        def get_plugin_info(self):
            self.info_calls += 1
            if self.info_calls > 1:
                raise RuntimeError("catalog activation must use copied metadata")
            return {
                "name": "CatalogIsolationPlugin",
                "version": "1.0.0",
                "description": "catalog hand-off ownership proof",
                "dependencies": [],
                "provides": (),
                "activation_context": "runtime",
                "editor_contributions": [
                    {
                        "id": "catalog.isolation.separator",
                        "kind": "toolbar_separator",
                        "group": "catalog-original",
                        "order": 1,
                    }
                ],
            }

        def on_load(self, context) -> None:
            self.contexts.append(context)

        def on_unload(self) -> None:
            return None

    class RecordingAdapter:
        def __init__(self) -> None:
            self.after_load: list[dict[str, object]] = []

        def after_plugin_load(self, plugin, plugin_id, plugin_info) -> None:
            self.after_load.append(plugin_info)

        def before_plugin_unload(self, plugin, plugin_id, plugin_info) -> None:
            return None

        def after_plugin_deactivated(self, plugin, plugin_id, plugin_info) -> None:
            return None

    plugin = CatalogPlugin()
    source = RuntimePluginHost()
    plugin_id = source.register_plugin(plugin, source="catalog_source.py")
    entry = source.catalog_entries()[0]

    entry.editor_contributions[0]["group"] = "mutated-entry"
    assert source.plugin_metadata[plugin_id]["editor_contributions"][0]["group"] == (
        "catalog-original"
    )

    normalized = entry.normalized()
    normalized.editor_contributions[0]["group"] = "mutated-normalized"
    assert entry.editor_contributions[0]["group"] == "mutated-entry"

    projected = entry.to_dict()
    projected["editor_contributions"][0]["group"] = "mutated-dict"
    assert entry.editor_contributions[0]["group"] == "mutated-entry"

    adapter = RecordingAdapter()
    destination = RuntimePluginHost(adapter=adapter)
    destination.plugin_registry[plugin_id] = plugin
    destination.plugin_scopes[plugin_id] = entry.scope
    destination.plugin_files[plugin_id] = entry.source
    destination.plugin_dependencies[plugin_id] = list(entry.dependencies)
    destination.cache_catalog_entry_metadata(entry)

    entry.editor_contributions[0]["group"] = "mutated-after-cache"
    assert destination.plugin_metadata[plugin_id]["editor_contributions"][0]["group"] == (
        "mutated-entry"
    )

    report = destination.execute_lifecycle_target(
        {plugin_id}, source="test", allow_deactivate=True
    )

    assert report["status"] == "settled"
    assert plugin.info_calls == 1
    assert adapter.after_load[0]["editor_contributions"][0]["group"] == "mutated-entry"
    adapter.after_load[0]["editor_contributions"][0]["group"] = "mutated-adapter"
    assert destination.plugin_metadata[plugin_id]["editor_contributions"][0]["group"] == (
        "mutated-entry"
    )