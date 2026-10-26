"""Headless PS component-ecosystem sample migrated from the old root examples."""
from __future__ import annotations

import argparse
import random

import numpy as np

from _project_runtime import install_locked_runtime

install_locked_runtime()

from builtin.components.actuators import MuscleActuator
from builtin.components.hybrid import HybridComponent
from builtin.components.sensors import TouchSensor
from core.Lotucosm.pond import LotusPond


def add_floating_components(
    pond: LotusPond,
    *,
    count: int = 10,
    rng: random.Random,
) -> None:
    component_types = ("sensor", "actuator", "hybrid")
    for index in range(max(0, count)):
        component_type = rng.choice(component_types)
        position = np.array(
            [rng.randint(100, 1100), rng.randint(100, 700)],
            dtype=float,
        )
        if component_type == "sensor":
            component = TouchSensor(
                component_id=f"sensor_{index}",
                organism_id="floating",
            )
        elif component_type == "actuator":
            component = MuscleActuator(
                component_id=f"actuator_{index}",
                organism_id="floating",
            )
        else:
            component = HybridComponent(
                component_id=f"hybrid_{index}",
                organism_id="floating",
            )
        component.position = position
        pond.add_floating_component(component)


def run_demo(*, steps: int = 100, component_count: int = 10, seed: int = 7) -> LotusPond:
    rng = random.Random(seed)
    pond = LotusPond(
        name="组件生态系统演示",
        size=(1200, 800),
        initial_organisms=2,
        max_population=10,
    )
    add_floating_components(pond, count=component_count, rng=rng)

    print("=" * 60)
    print("组件生态系统演示（Headless PS）")
    print(f"初始生物体: {len(pond.organisms)}")
    print(f"漂浮组件: {len(pond.floating_components)}")
    for index in range(max(0, steps)):
        pond.update()
        if index % 10 == 0 or index == steps - 1:
            print(
                f"step={index:03d} organisms={len(pond.organisms)} "
                f"floating={len(pond.floating_components)}"
            )
    return pond


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--components", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    run_demo(steps=args.steps, component_count=args.components, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
