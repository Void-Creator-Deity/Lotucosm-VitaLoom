# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

import os

import pytest

from PyQt6.QtWidgets import QApplication


_QT_APP: QApplication | None = None


@dataclass
class FakeProfiler:
    measured: list[str] = field(default_factory=list)

    @contextmanager
    def measure(self, bucket: str) -> Iterator[None]:
        self.measured.append(bucket)
        yield


class FakeSimulationContext:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self._viewport_profiler = FakeProfiler()

    def prepare_simulation_tick(self, dt: float) -> dict[str, float]:
        self.calls.append("input")
        return {"dt": dt}

    def run_script_phase(self, state: dict[str, float]) -> None:
        self.calls.append("script")

    def run_spawn_phase(self, state: dict[str, float]) -> None:
        self.calls.append("spawn")

    def run_actuator_phase(self, state: dict[str, float]) -> None:
        self.calls.append("actuator")

    def run_fluid_phase(self, state: dict[str, float]) -> None:
        self.calls.append("fluid")

    def run_physics_phase(self, state: dict[str, float]) -> None:
        self.calls.append("physics")

    def run_survival_phase(self, state: dict[str, float]) -> None:
        self.calls.append("survival")

    def run_snapshot_phase(self, state: dict[str, float]) -> None:
        self.calls.append("snapshots")


def test_simulation_driver_preserves_scene_runtime_phase_order() -> None:
    from core.VitaLoom.viewports.simulation_driver import SimulationDriver

    context = FakeSimulationContext()

    SimulationDriver().tick(context, dt=0.05)

    assert context.calls == [
        "input",
        "script",
        "spawn",
        "actuator",
        "fluid",
        "physics",
        "survival",
        "snapshots",
    ]


def test_simulation_driver_records_profiler_buckets_without_owning_widgets() -> None:
    from core.VitaLoom.viewports import simulation_driver
    from core.VitaLoom.viewports.simulation_driver import SimulationDriver

    context = FakeSimulationContext()

    SimulationDriver().tick(context, dt=0.05)

    assert context._viewport_profiler.measured == [
        "total",
        "script",
        "spawn",
        "fluid",
        "physics",
    ]

    source = inspect.getsource(simulation_driver)
    assert "PyQt6" not in source
    assert "QWidget" not in source
    assert "QPainter" not in source
    assert "GameViewport" not in source



def test_simulation_driver_propagates_phase_failure_without_tick_ownership() -> None:
    from core.VitaLoom.viewports.simulation_driver import SimulationDriver

    class FailingContext(FakeSimulationContext):
        def __init__(self) -> None:
            super().__init__()
            self.aborted = 0
            self.completed = 0

        def run_snapshot_phase(self, state: dict[str, float]) -> None:
            raise RuntimeError("snapshot transaction failed")

        def _worldbridge_abort_tick(self) -> None:
            self.aborted += 1

        def _worldbridge_complete_tick(self) -> None:
            self.completed += 1

    context = FailingContext()

    with pytest.raises(RuntimeError, match="snapshot transaction failed"):
        SimulationDriver().tick(context, dt=0.05)

    assert context.aborted == 0
    assert context.completed == 0

def test_game_viewport_owns_simulation_driver_boundary() -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    from core.VitaLoom.viewports.game_viewport import GameViewport
    from core.VitaLoom.viewports.simulation_driver import SimulationDriver

    viewport = GameViewport()

    assert isinstance(viewport._simulation_driver, SimulationDriver)


def test_game_viewport_scene_runtime_tick_delegates_to_simulation_driver() -> None:
    global _QT_APP
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _QT_APP = QApplication.instance() or QApplication([])

    from core.VitaLoom.viewports.game_viewport import GameViewport

    class FakeDriver:
        def __init__(self) -> None:
            self.calls: list[tuple[object, float]] = []

        def tick(self, context: object, dt: float) -> None:
            self.calls.append((context, dt))

    viewport = GameViewport()
    driver = FakeDriver()
    viewport._simulation_driver = driver
    viewport._sr_game_mode = False
    viewport.scene_runtime_entities = [object()]

    viewport._update_scene_runtime_entities(0.125)

    assert driver.calls == [(viewport, 0.125)]
    assert viewport._worldbridge_last_tick_receipt is None
