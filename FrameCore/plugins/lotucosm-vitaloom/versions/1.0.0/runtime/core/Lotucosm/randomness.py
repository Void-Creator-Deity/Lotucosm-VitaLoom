"""Small compatibility seam for caller-owned Python and NumPy RNGs.

Every draw requires an explicit owner.  The seam supports Python ``Random``
and NumPy ``Generator``-style objects without reopening process-global state.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Sequence

import numpy as np


def _require_rng(rng: Any) -> Any:
    if rng is None:
        raise RuntimeError("randomness owner is required")
    if not callable(getattr(rng, "random", None)):
        raise TypeError("randomness owner must expose random()")
    return rng


def random_unit(rng: Any) -> float:
    """Return one uniform value in ``[0, 1)`` from the selected owner."""

    value = _require_rng(rng).random()
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


def random_int(rng: Any, low: int, high: int) -> int:
    """Return an inclusive integer, matching ``random.randint`` semantics."""

    rng = _require_rng(rng)
    randint = getattr(rng, "randint", None)
    if callable(randint):
        return int(randint(low, high))
    integers = getattr(rng, "integers", None)
    if callable(integers):
        return int(integers(low, high + 1))
    return int(low + math.floor(random_unit(rng) * (high - low + 1)))


def random_uniform(rng: Any, low: float, high: float) -> float:
    """Return one uniform value from an explicit owner."""

    rng = _require_rng(rng)
    uniform = getattr(rng, "uniform", None)
    if callable(uniform):
        return float(np.asarray(uniform(low, high), dtype=float).reshape(-1)[0])
    return float(low + (high - low) * random_unit(rng))


def random_normal(rng: Any, mean: float, standard_deviation: float) -> float:
    """Return one Gaussian value from an explicit owner."""

    rng = _require_rng(rng)
    gauss = getattr(rng, "gauss", None)
    if callable(gauss):
        return float(gauss(mean, standard_deviation))
    normal = getattr(rng, "normal", None)
    if callable(normal):
        return float(np.asarray(normal(mean, standard_deviation), dtype=float).reshape(-1)[0])
    # This branch is only for small duck-typed owners that expose random().
    # It is deterministic and avoids falling back to the process-global API.
    u1 = max(random_unit(rng), np.finfo(float).tiny)
    u2 = random_unit(rng)
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return float(mean + standard_deviation * z)


def random_uniform_array(rng: Any, low: float, high: float, size: int | tuple[int, ...]) -> np.ndarray:
    """Return a uniform array without crossing the owner boundary."""

    rng = _require_rng(rng)
    uniform = getattr(rng, "uniform", None)
    if callable(uniform):
        try:
            return np.asarray(uniform(low, high, size=size), dtype=float)
        except TypeError:
            pass
    count = int(np.prod(size)) if isinstance(size, tuple) else int(size)
    values = [random_uniform(rng, low, high) for _ in range(count)]
    return np.asarray(values, dtype=float).reshape(size)


def random_normal_array(rng: Any, size: int | tuple[int, ...]) -> np.ndarray:
    """Return a standard-normal array without crossing the owner boundary."""

    rng = _require_rng(rng)
    normal = getattr(rng, "normal", None)
    if callable(normal):
        try:
            return np.asarray(normal(size=size), dtype=float)
        except TypeError:
            pass
    count = int(np.prod(size)) if isinstance(size, tuple) else int(size)
    values = [random_normal(rng, 0.0, 1.0) for _ in range(count)]
    return np.asarray(values, dtype=float).reshape(size)


def weighted_choices(
    rng: Any,
    population: Sequence[Any],
    weights: Iterable[float],
    count: int,
) -> list[Any]:
    """Choose with replacement using either supported owner family."""

    if count <= 0 or not population:
        return []
    probabilities = np.asarray(list(weights), dtype=float)
    total = float(probabilities.sum())
    if probabilities.size != len(population) or not math.isfinite(total) or total <= 0:
        return []
    probabilities = probabilities / total
    rng = _require_rng(rng)
    choices = getattr(rng, "choices", None)
    if callable(choices):
        return list(choices(population, weights=probabilities.tolist(), k=count))
    choice = getattr(rng, "choice", None)
    if callable(choice):
        indices = np.asarray(choice(len(population), size=count, replace=True, p=probabilities), dtype=int)
        return [population[int(index)] for index in indices.reshape(-1)]
    cumulative = np.cumsum(probabilities)
    result: list[Any] = []
    for _ in range(count):
        value = random_unit(rng)
        result.append(population[int(np.searchsorted(cumulative, value, side="right"))])
    return result


def random_sample(rng: Any, population: Sequence[Any], count: int) -> list[Any]:
    """Sample without replacement from an explicit owner."""

    if count <= 0:
        return []
    rng = _require_rng(rng)
    sample = getattr(rng, "sample", None)
    if callable(sample):
        return list(sample(population, count))
    choice = getattr(rng, "choice", None)
    if callable(choice):
        indices = np.asarray(choice(len(population), size=count, replace=False), dtype=int)
        return [population[int(index)] for index in indices.reshape(-1)]
    indices = list(range(len(population)))
    for index in range(count):
        swap_index = random_int(rng, index, len(indices) - 1)
        indices[index], indices[swap_index] = indices[swap_index], indices[index]
    return [population[index] for index in indices[:count]]


__all__ = [
    "random_int",
    "random_normal",
    "random_normal_array",
    "random_sample",
    "random_uniform",
    "random_uniform_array",
    "random_unit",
    "weighted_choices",
]
