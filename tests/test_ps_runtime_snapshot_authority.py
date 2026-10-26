# -*- coding: utf-8 -*-
"""Qt-free PS run/organism runtime snapshot Authority contract."""
from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path

import pytest

from core.Lotucosm.runtime.ps_runtime_snapshot_authority import (
    PsRuntimeSnapshotAuthority,
)


def _identity(run_id: str, organism_id: str = "exp_1") -> dict[str, str]:
    return {
        "track": "ps_batch",
        "run_id": run_id,
        "organism_id": organism_id,
    }


def _snapshot(organism_id: str = "exp_1", **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "organism_id": organism_id,
        "entity_type": "organism",
        "position": [12.5, 20.0],
        "energy": 100.0,
    }
    value.update(extra)
    return value


def test_begin_creates_unique_opaque_run_ids() -> None:
    authority = PsRuntimeSnapshotAuthority()

    first = authority.begin()
    second = authority.begin()

    assert first.startswith("ps_")
    assert second.startswith("ps_")
    assert first != second
    assert authority.current_run_id() == second


def test_query_before_begin_is_not_running() -> None:
    result = PsRuntimeSnapshotAuthority().query(_identity("ps_old"))

    assert result["status"] == "not_running"
    assert result["scope"] == "ps_runtime_organism"
    assert result["authority"] == "ps_runtime_snapshot_authority"
    assert result["track"] == "ps_batch"
    assert result["identity_relation"] == "run_scoped_not_cross_track"
    json.dumps(result, allow_nan=False)


def test_query_validates_identity_and_track() -> None:
    authority = PsRuntimeSnapshotAuthority()
    run_id = authority.begin()

    missing = _identity(run_id)
    missing.pop("organism_id")
    assert authority.query(missing)["status"] == "invalid_identity"
    assert authority.query({**_identity(run_id), "track": "sr_play"})["status"] == "unsupported_track"
    assert authority.query(object())["status"] == "invalid_identity"


def test_publish_query_and_copy_isolation() -> None:
    authority = PsRuntimeSnapshotAuthority()
    run_id = authority.begin()
    source = _snapshot(metadata={"tags": ["seed"]})

    assert authority.publish(run_id, [source]) == 1
    source["position"][0] = 999.0  # type: ignore[index]
    source["metadata"]["tags"].append("mutated")  # type: ignore[index,union-attr]

    first = authority.query(_identity(run_id))
    assert first["status"] == "ok"
    assert first["revision"] == 1
    assert first["snapshot"] == {
        "source": "read_only_json_snapshot",
        "organism_id": "exp_1",
        "entity_type": "organism",
        "position": [12.5, 20.0],
        "energy": 100.0,
        "metadata": {"tags": ["seed"]},
    }

    first["snapshot"]["position"][0] = -100.0
    first["snapshot"]["metadata"]["tags"].append("query_mutation")
    second = authority.query(_identity(run_id))
    assert second["snapshot"]["position"] == [12.5, 20.0]
    assert second["snapshot"]["metadata"] == {"tags": ["seed"]}


def test_publish_completely_replaces_population_and_empty_clears_it() -> None:
    authority = PsRuntimeSnapshotAuthority()
    run_id = authority.begin()

    assert authority.publish(run_id, [_snapshot("exp_1"), _snapshot("exp_2")]) == 1
    assert authority.publish(run_id, [_snapshot("exp_2", energy=55.0)]) == 2
    assert authority.query(_identity(run_id, "exp_1"))["status"] == "missing"
    assert authority.query(_identity(run_id, "exp_2"))["snapshot"]["energy"] == 55.0

    assert authority.publish(run_id, []) == 3
    cleared = authority.query(_identity(run_id, "exp_2"))
    assert cleared["status"] == "missing"
    assert cleared["revision"] == 3


def test_stale_is_resolved_before_missing_across_reused_organism_id() -> None:
    authority = PsRuntimeSnapshotAuthority()
    old_run = authority.begin()
    authority.publish(old_run, [_snapshot("same_id")])
    new_run = authority.begin()
    authority.publish(new_run, [_snapshot("same_id")])

    assert authority.query(_identity(old_run, "does_not_exist"))["status"] == "stale"
    assert authority.query(_identity(new_run, "does_not_exist"))["status"] == "missing"


def test_end_transitions_and_stale_end_does_not_end_current_run() -> None:
    authority = PsRuntimeSnapshotAuthority()
    old_run = authority.begin()
    current_run = authority.begin()

    assert authority.end(old_run)["status"] == "stale"
    assert authority.current_run_id() == current_run
    assert authority.end(current_run)["status"] == "ended"
    assert authority.current_run_id() is None
    assert authority.query(_identity(current_run))["status"] == "not_running"
    assert authority.end(current_run)["status"] == "not_running"


@pytest.mark.parametrize(
    "bad_value",
    [
        object(),
        lambda: None,
        (1, 2),
        {"bad_key": {1: "value"}},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_publish_rejects_non_json_snapshot_values(bad_value: object) -> None:
    authority = PsRuntimeSnapshotAuthority()
    run_id = authority.begin()

    with pytest.raises((TypeError, ValueError)):
        authority.publish(run_id, [_snapshot(extra=bad_value)])


def test_publish_rejects_duplicate_missing_or_authority_owned_fields() -> None:
    authority = PsRuntimeSnapshotAuthority()
    run_id = authority.begin()

    with pytest.raises(ValueError, match="duplicate"):
        authority.publish(run_id, [_snapshot("same"), _snapshot("same")])
    with pytest.raises(ValueError, match="organism_id"):
        authority.publish(run_id, [{"entity_type": "organism"}])
    with pytest.raises(ValueError, match="source"):
        authority.publish(run_id, [_snapshot(source="forged")])


def test_publish_rejects_not_running_and_stale_runs() -> None:
    authority = PsRuntimeSnapshotAuthority()
    with pytest.raises(RuntimeError, match="not_running"):
        authority.publish("ps_unknown", [_snapshot()])

    old_run = authority.begin()
    authority.begin()
    with pytest.raises(RuntimeError, match="stale"):
        authority.publish(old_run, [_snapshot()])


def test_authority_module_imports_when_pyqt6_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "FrameCore"
        / "plugins"
        / "lotucosm-vitaloom"
        / "versions"
        / "1.0.0"
        / "runtime"
        / "core"
        / "Lotucosm"
        / "runtime"
        / "ps_runtime_snapshot_authority.py"
    )
    real_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "PyQt6" or name.startswith("PyQt6."):
            raise ImportError("PyQt6 intentionally blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("_qt_free_ps_runtime_snapshot_authority", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.PsRuntimeSnapshotAuthority().current_run_id() is None


def test_discovery_acquires_active_run_and_current_identities_atomically() -> None:
    authority = PsRuntimeSnapshotAuthority()

    before = authority.discover()
    assert before == {
        "schema_version": 1,
        "status": "not_running",
        "scope": "ps_runtime_population",
        "authority": "ps_runtime_snapshot_authority",
        "track": "ps_batch",
        "read_only": True,
        "identity_relation": "run_scoped_not_cross_track",
        "run_id": None,
        "revision": 0,
        "organism_count": 0,
        "identities": [],
    }

    run_id = authority.begin()
    authority.publish(
        run_id,
        [
            {"organism_id": "org_b", "position": [2.0, 0.0]},
            {"organism_id": "org_a", "position": [1.0, 0.0]},
        ],
    )

    discovered = authority.discover()
    assert discovered["status"] == "ok"
    assert discovered["run_id"] == run_id
    assert discovered["revision"] == 1
    assert discovered["organism_count"] == 2
    assert discovered["identities"] == [
        {"track": "ps_batch", "run_id": run_id, "organism_id": "org_a"},
        {"track": "ps_batch", "run_id": run_id, "organism_id": "org_b"},
    ]

    discovered["identities"][0]["organism_id"] = "mutated"
    assert authority.discover()["identities"][0]["organism_id"] == "org_a"

    authority.publish(run_id, [])
    empty = authority.discover()
    assert empty["status"] == "ok"
    assert empty["run_id"] == run_id
    assert empty["revision"] == 2
    assert empty["organism_count"] == 0
    assert empty["identities"] == []

    authority.end(run_id)
    ended = authority.discover()
    assert ended["status"] == "not_running"
    assert ended["run_id"] is None
    assert ended["identities"] == []