# -*- coding: utf-8 -*-
"""Widget-independent orchestration for a viewport simulation tick."""

from __future__ import annotations

from contextlib import nullcontext
from typing import Any, ContextManager, Protocol, runtime_checkable


@runtime_checkable
class SimulationTickContext(Protocol):
    def prepare_simulation_tick(self, dt: float) -> Any: ...

    def run_script_phase(self, state: Any) -> None: ...

    def run_spawn_phase(self, state: Any) -> None: ...

    def run_actuator_phase(self, state: Any) -> None: ...

    def run_fluid_phase(self, state: Any) -> None: ...

    def run_physics_phase(self, state: Any) -> None: ...

    def run_survival_phase(self, state: Any) -> None: ...

    def run_snapshot_phase(self, state: Any) -> None: ...


class SimulationDriver:
    """Run one scene-runtime tick through explicit, testable phases."""

    def tick(self, context: SimulationTickContext, dt: float) -> None:
        with self._measure(context, "total"):
            state = context.prepare_simulation_tick(dt)
            record_rng = getattr(context, "_worldbridge_record_rng_phase", None)
            if callable(record_rng):
                record_rng("sr.start")
            with self._measure(context, "script"):
                context.run_script_phase(state)
            with self._measure(context, "spawn"):
                context.run_spawn_phase(state)
            context.run_actuator_phase(state)
            with self._measure(context, "fluid"):
                context.run_fluid_phase(state)
            with self._measure(context, "physics"):
                context.run_physics_phase(state)
            context.run_survival_phase(state)
            if callable(record_rng):
                record_rng("sr.complete")
                record_rng("ps.start")
            context.run_snapshot_phase(state)
            if callable(record_rng):
                record_rng("ps.complete")

    def _measure(self, context: object, bucket: str) -> ContextManager[None]:
        profiler = getattr(context, "_viewport_profiler", None)
        measure = getattr(profiler, "measure", None)
        if measure is None:
            return nullcontext()
        try:
            return measure(bucket)
        except Exception:
            return nullcontext()


__all__ = ["SimulationDriver", "SimulationTickContext"]
