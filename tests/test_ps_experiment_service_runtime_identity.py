# -*- coding: utf-8 -*-
"""PS service/worker Adapter contract for the shared runtime Authority."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtCore import Qt

from core.Lotucosm.experiment_config import PsExperimentConfig
from core.Lotucosm.runtime.ps_runtime_snapshot_authority import PsRuntimeSnapshotAuthority
from core.VitaLoom.simulation import ps_experiment_service as service_module
from core.VitaLoom.simulation.ps_experiment_service import (
    PsExperimentService,
    _PsExperimentWorker,
)
from core.VitaLoom.simulation import simulation_coordinator as coordinator_module


def _config(*, ticks: int = 2) -> PsExperimentConfig:
    return PsExperimentConfig(
        name="service_runtime_identity",
        ticks=ticks,
        seed=11,
        initial_organisms=1,
        initial_components=0,
        snapshot_interval=1,
        enable_pvaec_cycle_per_tick=False,
        enable_generation_orchestrator=False,
        evolution_generation_interval=0,
    )


def _identity(run_id: str, organism_id: str = "exp_1") -> dict[str, str]:
    return {"track": "ps_batch", "run_id": run_id, "organism_id": organism_id}


class _Coordinator:
    def __init__(self) -> None:
        self.starts = 0
        self.stops = 0

    def register_lane_start(self, _lane: object) -> bool:
        self.starts += 1
        return True

    def register_lane_stop(self, _lane: object) -> None:
        self.stops += 1


class _Signal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback: object, *_args: object, **_kwargs: object) -> None:
        self.callback = callback

    def emit(self, *args: object) -> None:
        assert self.callback is not None
        self.callback(*args)


def test_sync_progress_queries_shared_authority_and_finish_invalidates_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coord = _Coordinator()
    monkeypatch.setattr(coordinator_module, "_coordinator", coord)
    service = PsExperimentService(tmp_path)
    observed: list[dict[str, Any]] = []
    discoveries: list[dict[str, Any]] = []

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = service.current_runtime_run_id()
        assert run_id is not None
        discovery = service.discover_runtime_organisms()
        discoveries.append(discovery)
        assert discovery["run_id"] == run_id
        assert discovery["organism_count"] == 1
        observed.append(
            service.query_runtime_organism_snapshot(discovery["identities"][0])
        )

    summary, out_dir = service.run_sync(_config(ticks=1), export=False, progress_callback=progress)

    assert summary["cancelled"] is False
    assert out_dir is None
    assert discoveries and discoveries[0]["status"] == "ok"
    assert observed and observed[0]["status"] == "ok"
    assert service.current_runtime_run_id() is None
    assert service.discover_runtime_organisms()["status"] == "not_running"
    assert service.query_runtime_organism_snapshot(observed[0]["identity"])["status"] == "not_running"
    assert service.is_running is False
    assert coord.starts == 1
    assert coord.stops == 1


def test_sync_callback_failure_clears_state_lane_and_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coord = _Coordinator()
    monkeypatch.setattr(coordinator_module, "_coordinator", coord)
    service = PsExperimentService(tmp_path)
    states: list[str] = []
    original_emit_state = service._emit_state

    def record_state(state=None) -> None:
        original_emit_state(state)
        states.append(service.state.phase)

    monkeypatch.setattr(service, "_emit_state", record_state)
    captured: list[dict[str, str]] = []

    def fail(_metrics: dict[str, Any]) -> None:
        run_id = service.current_runtime_run_id()
        assert run_id is not None
        captured.append(_identity(run_id))
        raise RuntimeError("sync callback failed")

    with pytest.raises(RuntimeError, match="sync callback failed"):
        service.run_sync(_config(ticks=1), export=False, progress_callback=fail)

    assert service.is_running is False
    assert service.current_runtime_run_id() is None
    assert service.query_runtime_organism_snapshot(captured[0])["status"] == "not_running"
    assert "error" in states
    assert states[-1] == "idle"
    assert coord.starts == 1
    assert coord.stops == 1


def test_worker_thread_publishes_to_authority_queryable_from_calling_thread() -> None:
    authority = PsRuntimeSnapshotAuthority()
    worker = _PsExperimentWorker(
        _config(ticks=1),
        export_results=False,
        snapshot_authority=authority,
    )
    entered = threading.Event()
    release = threading.Event()
    worker_identity: list[dict[str, str]] = []

    def block_progress(_metrics: dict[str, Any]) -> None:
        run_id = authority.current_run_id()
        assert run_id is not None
        worker_identity.append(_identity(run_id))
        entered.set()
        assert release.wait(5.0)

    worker.progress.connect(block_progress, Qt.ConnectionType.DirectConnection)
    worker.start()
    assert entered.wait(5.0)
    queried = authority.query(worker_identity[0])
    release.set()
    assert worker.wait(5000)

    assert queried["status"] == "ok"
    assert queried["revision"] == 2
    assert authority.current_run_id() is None


@pytest.mark.parametrize(
    ("terminal", "expected_phase"),
    [("finished", "finished"), ("cancelled", "cancelled"), ("failed", "error")],
)
def test_async_adapters_share_authority_and_close_terminal_lifecycle(
    terminal: str,
    expected_phase: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coord = _Coordinator()
    monkeypatch.setattr(coordinator_module, "_coordinator", coord)
    service = PsExperimentService(tmp_path)
    states: list[str] = []
    original_emit_state = service._emit_state

    def record_state(state=None) -> None:
        original_emit_state(state)
        states.append(service.state.phase)

    monkeypatch.setattr(service, "_emit_state", record_state)
    observed: list[dict[str, Any]] = []
    errors: list[str] = []

    class _FakeWorker:
        def __init__(
            self,
            config: PsExperimentConfig,
            *,
            export_results: bool,
            snapshot_authority: PsRuntimeSnapshotAuthority,
        ) -> None:
            assert snapshot_authority is service._runtime_snapshot_authority
            self.authority = snapshot_authority
            self.progress = _Signal()
            self.finished_ok = _Signal()
            self.failed = _Signal()

        def request_cancel(self) -> None:
            pass

        def start(self) -> None:
            run_id = self.authority.begin()
            self.authority.publish(run_id, [{
                "organism_id": "exp_1",
                "entity_type": "organism",
                "position": [1.0, 2.0],
            }])
            self.progress.emit({"tick": 1, "population": 1})
            self.authority.end(run_id)
            if terminal == "failed":
                self.failed.emit("worker failed")
                return
            summary = {
                "cancelled": terminal == "cancelled",
                "final": {"tick": 1, "population": 1},
                "snapshots": [],
            }
            self.finished_ok.emit(summary, None)

    monkeypatch.setattr(service_module, "_PsExperimentWorker", _FakeWorker)

    def progress(_metrics: dict[str, Any]) -> None:
        run_id = service.current_runtime_run_id()
        assert run_id is not None
        observed.append(service.query_runtime_organism_snapshot(_identity(run_id)))

    started = service.run_async(
        _config(ticks=1),
        export=False,
        on_progress=progress,
        on_error=errors.append,
    )

    assert started is True
    assert observed and observed[0]["status"] == "ok"
    assert service.is_running is False
    assert service.current_runtime_run_id() is None
    assert expected_phase in states
    assert states[-1] == "idle"
    assert coord.starts == 1
    assert coord.stops == 1
    assert bool(errors) is (terminal == "failed")


def test_async_worker_start_failure_rolls_back_state_lane_and_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coord = _Coordinator()
    monkeypatch.setattr(coordinator_module, "_coordinator", coord)
    service = PsExperimentService(tmp_path)
    states: list[str] = []
    original_emit_state = service._emit_state

    def record_state(state=None) -> None:
        original_emit_state(state)
        states.append(service.state.phase)

    monkeypatch.setattr(service, "_emit_state", record_state)
    errors: list[str] = []

    class _StartFailureWorker:
        def __init__(
            self,
            config: PsExperimentConfig,
            *,
            export_results: bool,
            snapshot_authority: PsRuntimeSnapshotAuthority,
        ) -> None:
            self.authority = snapshot_authority
            self.progress = _Signal()
            self.finished_ok = _Signal()
            self.failed = _Signal()

        def start(self) -> None:
            run_id = self.authority.begin()
            self.authority.publish(run_id, [])
            raise RuntimeError("start failed")

    monkeypatch.setattr(service_module, "_PsExperimentWorker", _StartFailureWorker)

    assert service.run_async(_config(ticks=1), export=False, on_error=errors.append) is False
    assert errors == ["start failed"]
    assert service.is_running is False
    assert service._worker is None
    assert service.current_runtime_run_id() is None
    assert "error" in states
    assert states[-1] == "idle"
    assert coord.starts == 1
    assert coord.stops == 1
