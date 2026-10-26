"""Headless PS Pac-Man sample migrated from the old root examples."""
from __future__ import annotations

import argparse
import random

import numpy as np

from _project_runtime import install_locked_runtime

install_locked_runtime()

from builtin.components.actuators import CiliaActuator, MuscleActuator
from builtin.components.membrane import Membrane
from builtin.entity_types.intelligent_organism import IntelligentOrganism
from builtin.systems.simulation import Simulation


class PacManPond(Simulation):
    """Small PS simulation scene; unrelated to the SR GameViewport scene path."""

    def __init__(self, *, food_count: int = 60, seed: int = 7):
        super().__init__(enable_pygame=False)
        self._rng = random.Random(seed)
        self.food_count = max(0, food_count)
        self.name = "Pac-Man World"
        self.setup_pacman_environment()

    def setup_pacman_environment(self) -> None:
        self.environment.foods = []
        self.organisms = []
        self.pacman = IntelligentOrganism(
            organism_id="PacMan_Alpha",
            position=np.array([600.0, 400.0]),
            name="Pac-Man",
            energy=150.0,
        )
        self.pacman.add_component(
            Membrane(
                component_id="membrane_01",
                organism_id="PacMan_Alpha",
                position=(0, 0),
                radius=150.0,
                ingest_threshold=1.0,
            )
        )
        self.pacman.add_component(
            MuscleActuator(
                component_id="engine",
                organism_id="PacMan_Alpha",
                position=(0, 0),
                max_force=2.0,
            )
        )
        self.pacman.add_component(
            CiliaActuator(
                component_id="rudder",
                organism_id="PacMan_Alpha",
                position=(0, 0),
                max_torque=1.0,
            )
        )
        self.organisms.append(self.pacman)

        for _ in range(self.food_count):
            self.environment.add_food(
                (self._rng.randint(500, 700), self._rng.randint(350, 450)),
                energy=50.0,
            )
        for target_x in range(620, 800, 30):
            self.environment.add_food((target_x, 400), energy=100.0)

    def run_demo(self, *, steps: int = 300) -> None:
        print(f"--- {self.name}: {steps} steps ---")
        for index in range(max(0, steps)):
            for organism in self.organisms:
                engine = organism.get_component("engine")
                rudder = organism.get_component("rudder")
                if engine:
                    engine.process_signal(0.4)
                if rudder:
                    rudder.process_signal(self._rng.uniform(-0.05, 0.05))

                if organism.position[0] < 100:
                    organism.velocity[0] = abs(organism.velocity[0]) + 1.0
                elif organism.position[0] > 1100:
                    organism.velocity[0] = -abs(organism.velocity[0]) - 1.0
                if organism.position[1] < 100:
                    organism.velocity[1] = abs(organism.velocity[1]) + 1.0
                elif organism.position[1] > 700:
                    organism.velocity[1] = -abs(organism.velocity[1]) - 1.0

            self.update()
            if index % 20 == 0 or index == steps - 1:
                print(
                    f"step={index:03d} organisms={len(self.organisms)} "
                    f"food={len(self.environment.foods)} "
                    f"energy={self.pacman.energy:.1f}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--food-count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    PacManPond(food_count=args.food_count, seed=args.seed).run_demo(steps=args.steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

