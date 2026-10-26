# -*- coding: utf-8 -*-
"""PS runner Adapter contract for run-scoped organism runtime identity."""
from __future__ import annotations

from typing import Any

import pytest

from builtin.systems.ps_experiment_runner import PsExperimentRunner
from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.runtime.ps_runtime_snapshot_authority import (
    PsRuntimeSnapshotAuthority,
)
from core.Lotucosm.runtime.deterministic_identity import DeterministicIdentitySource


def _config(*, ticks: int = 2, initial_organisms: int = 1) -> PsExperimentConfig:
    return PsExperimentConfig(
        name="runtime_identity_test",
        ticks=ticks,
        seed=7,
        initial_organisms=initial_organisms,
        initial_components=0,
        snapshot_interval=1,
        enable_pvaec_cycle_per_tick=False,
        enable_generation_orchestrator=False,
        evolution_generation_interval=0,
    )


def _identity(run_id: str, organism_id: str = "exp_1") -> dict[str, str]:
    return {
        "track": "ps_batch",
        "run_id": run_id,
        "organism_id": organism_id,
    }


def test_initial_population_is_published_before_first_tick() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    pond = runner.build_pond()
    original_update = pond.update
    observed: dict[str, Any] = {}

    def checked_update() -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        observed.update(authority.query(_identity(run_id)))
        original_update()

    pond.update = checked_update  # type: ignore[method-assign]
    runner.run(pond)

    assert observed["status"] == "ok"
    assert observed["revision"] == 1
    assert authority.current_run_id() is None


def test_runner_composition_can_use_caller_owned_deterministic_identity():
    source = DeterministicIdentitySource("runner-e417")
    runner = PsExperimentRunner(_config(ticks=1), identity_source=source)
    run_id = runner._snapshot_authority.begin()
    assert run_id == "ps_" + run_id.removeprefix("ps_")
    assert run_id == PsRuntimeSnapshotAuthority(
        identity_source=DeterministicIdentitySource("runner-e417")
    ).begin()
    runner._snapshot_authority.end(run_id)


def test_progress_callback_can_query_current_whitelisted_snapshot() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    observed: dict[str, Any] = {}

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = runner.current_runtime_run_id()
        assert run_id is not None
        observed.update(runner.query_runtime_organism_snapshot(_identity(run_id)))

    runner.run(progress_callback=progress)

    assert observed["status"] == "ok"
    assert observed["revision"] == 2
    snapshot = observed["snapshot"]
    assert set(snapshot) == {
        "source",
        "organism_id",
        "entity_type",
        "position",
        "energy",
        "max_energy",
        "health",
        "max_health",
        "age",
        "generation",
        "developmental_stage",
        "dead",
        "component_facts",
    }
    assert snapshot["organism_id"] == "exp_1"
    assert isinstance(snapshot["position"], list)
    assert isinstance(snapshot["component_facts"], list)
    assert snapshot["component_facts"]
    for component in snapshot["component_facts"]:
        assert set(component) == {
            "source",
            "identity_relation",
            "component_id",
            "component_type",
            "location",
            "acquired",
            "congenital",
            "attach_point",
            "connection_count",
            "inspectable_properties",
            "component_fields",
        }
    for forbidden in ("components", "memory", "memory_system", "scripts", "pond", "organism"):
        assert forbidden not in snapshot
    assert authority.current_run_id() is None


def test_each_completed_tick_publishes_a_new_revision() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=2), snapshot_authority=authority)
    revisions: list[int] = []

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        result = authority.query(_identity(run_id))
        revisions.append(result["revision"])

    runner.run(progress_callback=progress)

    assert revisions == [2, 3]


def test_extinction_publishes_empty_population_instead_of_stale_snapshot() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    pond = runner.build_pond()
    observed: dict[str, Any] = {}

    def extinction_update() -> None:
        pond.time += 1
        pond.organisms.clear()

    pond.update = extinction_update  # type: ignore[method-assign]

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        observed.update(authority.query(_identity(run_id)))

    runner.run(pond, progress_callback=progress)

    assert observed["status"] == "missing"
    assert observed["revision"] == 2
    assert authority.current_run_id() is None


def test_cancel_ends_lifetime_at_next_tick_boundary() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=5), snapshot_authority=authority)
    seen_run_ids: list[str] = []

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        seen_run_ids.append(run_id)
        runner.request_cancel()

    summary = runner.run(progress_callback=progress)

    assert summary["cancelled"] is True
    assert len(seen_run_ids) == 1
    assert authority.current_run_id() is None
    assert authority.query(_identity(seen_run_ids[0]))["status"] == "not_running"


@pytest.mark.parametrize("failure_site", ["callback", "update"])
def test_failure_always_ends_runtime_lifetime(failure_site: str) -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    pond = runner.build_pond()
    captured_run_id: list[str] = []

    if failure_site == "update":
        def failing_update() -> None:
            run_id = authority.current_run_id()
            assert run_id is not None
            captured_run_id.append(run_id)
            raise RuntimeError("update failed")

        pond.update = failing_update  # type: ignore[method-assign]
        callback = None
    else:
        def failing_callback(_metrics: dict[str, Any]) -> None:
            run_id = authority.current_run_id()
            assert run_id is not None
            captured_run_id.append(run_id)
            raise RuntimeError("callback failed")

        callback = failing_callback

    with pytest.raises(RuntimeError, match="failed"):
        runner.run(pond, progress_callback=callback)

    assert captured_run_id
    assert authority.current_run_id() is None
    assert authority.query(_identity(captured_run_id[0]))["status"] == "not_running"


def test_unified_bridge_uses_same_authority_lifecycle() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    observed: dict[str, Any] = {}

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        observed.update(authority.query(_identity(run_id, "bridge_hub_1")))

    summary = runner.run_unified_bridge(progress_callback=progress)

    assert summary["mode"] == "unified_bridge"
    assert observed["status"] == "ok"
    assert observed["revision"] == 2
    assert authority.current_run_id() is None


def test_second_run_makes_old_identity_stale_while_new_run_is_active() -> None:
    authority = PsRuntimeSnapshotAuthority()
    runner = PsExperimentRunner(_config(ticks=1), snapshot_authority=authority)
    first_run_ids: list[str] = []

    def first_progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        first_run_ids.append(run_id)

    runner.run(progress_callback=first_progress)
    stale_statuses: list[str] = []

    def second_progress(_metrics: dict[str, Any]) -> None:
        stale_statuses.append(authority.query(_identity(first_run_ids[0]))["status"])

    runner.run(progress_callback=second_progress)

    assert stale_statuses == ["stale"]
    assert authority.current_run_id() is None


def test_ps_snapshot_adapter_projects_component_facts_without_behavior_calls() -> None:
    class ExplodingComponent:
        id = "sensor_1"
        component_type = "touch_sensor"
        location = "external"
        acquired = False
        congenital = True
        attach_point = "north"
        signal_threshold = 0.25
        sensing_range = 42.0
        connections = [object(), object()]

        def get_inspectable_properties(self):
            raise AssertionError("Adapter must not call component methods")

        def update(self):
            raise AssertionError("Adapter must not call component behavior")

    class Organism:
        organism_id = "org_component"
        entity_type = "Organism"
        position = (1.0, 2.0)
        energy = 10.0
        max_energy = 20.0
        health = 8.0
        max_health = 10.0
        age = 3
        generation = 2
        developmental_stage = 1
        dead = False
        components = {"registry_sensor": ExplodingComponent()}

    snapshot = PsExperimentRunner._organism_runtime_snapshot(
        "registry_org",
        Organism(),
    )

    assert snapshot["component_facts"] == [
        {
            "source": "ps_component_registry",
            "identity_relation": "ps_component_registry_member",
            "component_id": "sensor_1",
            "component_type": "touch_sensor",
            "location": "external",
            "acquired": False,
            "congenital": True,
            "attach_point": "north",
            "connection_count": 2,
            "inspectable_properties": {
                "sensing_range": 42.0,
                "signal_threshold": 0.25,
            },
            "component_fields": {
                "sensing_range": 42.0,
                "signal_threshold": 0.25,
            },
        }
    ]
    assert "components" not in snapshot

