from __future__ import annotations

import builtins
import importlib
import sys

import pytest

from core.VitaLoom.core.capability_publication import publish_capabilities


_MISSING = object()


class _Registry:
    def __init__(self, values=None, *, fail_key=None, mutate_before_failure=False):
        self.values = dict(values or {})
        self.fail_key = fail_key
        self.mutate_before_failure = mutate_before_failure

    def register(self, key, value):
        if key == self.fail_key:
            if self.mutate_before_failure:
                self.values[key] = value
            raise RuntimeError(f"register failed: {key}")
        self.values[key] = value

    def get(self, key, default=None):
        return self.values.get(key, default)

    def unregister(self, key):
        self.values.pop(key, None)


def test_publication_records_owner_keys_and_replacement_evidence() -> None:
    previous = object()
    first = object()
    second = object()
    registry = _Registry({"cap.first": previous})

    lease = publish_capabilities(
        registry,
        owner=" adapter.game-viewport ",
        capabilities={"cap.first": first, "cap.second": second},
    )

    assert registry.values == {"cap.first": first, "cap.second": second}
    assert lease.owner == "adapter.game-viewport"
    assert lease.keys == ("cap.first", "cap.second")
    assert lease.active is True
    assert [(item.owner, item.key, item.replaced_existing) for item in lease.records] == [
        ("adapter.game-viewport", "cap.first", True),
        ("adapter.game-viewport", "cap.second", False),
    ]


@pytest.mark.parametrize(
    ("registry", "owner", "capabilities", "error"),
    [
        (None, "owner", {"key": object()}, TypeError),
        (object(), "owner", {"key": object()}, TypeError),
        (_Registry(), " ", {"key": object()}, ValueError),
        (_Registry(), "owner", {}, ValueError),
        (_Registry(), "owner", {" ": object()}, ValueError),
        (_Registry(), "owner", {1: object()}, TypeError),
        (_Registry(), "owner", {"key": None}, ValueError),
    ],
)
def test_publication_validation_fails_before_registry_mutation(
    registry, owner, capabilities, error
) -> None:
    before = dict(getattr(registry, "values", {}))
    with pytest.raises(error):
        publish_capabilities(
            registry,
            owner=owner,
            capabilities=capabilities,
        )
    assert getattr(registry, "values", {}) == before


def test_mid_batch_failure_restores_all_previous_registry_state() -> None:
    previous_first = object()
    previous_second = object()
    registry = _Registry(
        {"cap.first": previous_first, "cap.second": previous_second},
        fail_key="cap.second",
        mutate_before_failure=True,
    )

    with pytest.raises(RuntimeError, match="register failed: cap.second"):
        publish_capabilities(
            registry,
            owner="adapter.ps",
            capabilities={"cap.first": object(), "cap.second": object()},
        )

    assert registry.values == {
        "cap.first": previous_first,
        "cap.second": previous_second,
    }


def test_mid_batch_failure_removes_newly_created_keys() -> None:
    registry = _Registry(fail_key="cap.second", mutate_before_failure=True)

    with pytest.raises(RuntimeError):
        publish_capabilities(
            registry,
            owner="adapter.ps",
            capabilities={"cap.first": object(), "cap.second": object()},
        )

    assert registry.values == {}


def test_release_removes_only_exact_objects_and_preserves_later_replacements() -> None:
    first = object()
    second = object()
    replacement = object()
    registry = _Registry()
    lease = publish_capabilities(
        registry,
        owner="adapter.package-manager",
        capabilities={"cap.first": first, "cap.second": second},
    )
    registry.register("cap.second", replacement)

    report = lease.release()

    assert registry.values == {"cap.second": replacement}
    assert report.owner == "adapter.package-manager"
    assert report.removed_keys == ("cap.first",)
    assert report.retained_replacement_keys == ("cap.second",)
    assert report.already_absent_keys == ()
    assert report.already_released is False
    assert lease.active is False


def test_release_reports_external_absence_without_recreating_prior_values() -> None:
    prior = object()
    published = object()
    registry = _Registry({"cap": prior})
    lease = publish_capabilities(
        registry,
        owner="adapter.console",
        capabilities={"cap": published},
    )
    registry.unregister("cap")

    report = lease.release()

    assert registry.get("cap", _MISSING) is _MISSING
    assert report.already_absent_keys == ("cap",)


def test_double_release_is_deterministic_and_has_no_side_effects() -> None:
    capability = object()
    registry = _Registry()
    lease = publish_capabilities(
        registry,
        owner="adapter.downloader",
        capabilities={"cap": capability},
    )

    first = lease.release()
    registry.register("cap", object())
    second = lease.release()

    assert first.removed_keys == ("cap",)
    assert second.already_released is True
    assert second.removed_keys == ()
    assert "cap" in registry.values


def test_module_import_is_qt_free(monkeypatch) -> None:
    module_name = "core.VitaLoom.core.capability_publication"
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise AssertionError(f"unexpected PyQt import: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop(module_name, None)
    module = importlib.import_module(module_name)

    assert callable(module.publish_capabilities)