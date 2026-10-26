# SR2D Native Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real SR 2D native acceleration boundary by routing `SrPhysics2DWorld.step()` through an adapter contract with a Python fallback, behavior parity tests, and benchmark evidence.

**Architecture:** Keep the current Python SR 2D behavior as the source of truth. Introduce an adapter boundary inside `core.Lotucosm.sr_physics2d` so future Rust/C++ implementations can replace the hot loop without changing `GameViewport`, `.pond` files, or gameplay/PVAEC semantics.

**Tech Stack:** Python 3, pytest/unittest-compatible tests, `tools/benchmark_engine.py`, existing FrameCore runtime package under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.

---

## Current Facts

- Runtime package: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/`.
- Current entry point: `world.py`, `SrPhysics2DWorld.step(entities, dt, width, height, mode=..., springs=...)`.
- PVAEC path: optional `core.Lotucosm.sr_link_physics.step_spring_network()`, then `integrator.integrate_all()`, then `pvaec_contacts.resolve_pvaec_contacts()`.
- Game path: `integrator.integrate_all()`, then `game_contacts.resolve_game_contacts()`.
- Existing tests: `tests/test_sr_physics2d_world.py`.
- Benchmark tool: `tools/benchmark_engine.py`.
- ADR requirement: `docs/adr/0006-native-acceleration-seams.md` says every native seam needs a Python interface, benchmark case, behavior tests, and fallback adapter before any native implementation is considered real.

## File Structure

- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`
  - Defines the adapter protocol, default Python adapter, and default adapter factory.
  - Owns the future native plug point.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/mode.py`
  - Owns `Physics2DMode` so `world.py` and `adapter.py` can both import it without a cycle.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/world.py`
  - Keeps `SrPhysics2DWorld.step()` as the stable public entry point.
  - Delegates implementation to the configured adapter.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`
  - Exports the adapter protocol and Python fallback for tests and future native implementers.
- Create `tests/test_sr_physics2d_adapter_contract.py`
  - Locks adapter behavior and world delegation without requiring native code.
- Modify `tools/benchmark_engine.py`
  - Adds an `sr2d` benchmark case that runs enough PVAEC steps to expose the adapter boundary cost.
- Modify `docs/sr_physics2d.md`
  - Documents the adapter boundary and the fallback rule.
- Modify `docs/adr/0006-native-acceleration-seams.md`
  - Records that SR2D is the first candidate adapter boundary, not a native implementation claim.

---

### Task 1: Add The Adapter Contract

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`
- Test: `tests/test_sr_physics2d_adapter_contract.py`

- [x] **Step 1: Write the failing adapter fallback test**

Create `tests/test_sr_physics2d_adapter_contract.py` with:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from types import SimpleNamespace

from core.Lotucosm.sr_physics2d import (
    Physics2DMode,
    PythonSrPhysics2DAdapter,
    SrPhysics2DConfig,
)


def _org(x: float, y: float, *, r: float = 22.0) -> SimpleNamespace:
    return SimpleNamespace(
        entity_type="organism",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=False,
        membrane_locked=False,
    )


def _nut(x: float, y: float, *, r: float = 14.0) -> SimpleNamespace:
    return SimpleNamespace(
        entity_type="nutrient",
        position=[x, y],
        velocity=[0.0, 0.0],
        radius=r,
        pinned=True,
        membrane_locked=False,
    )


def test_python_adapter_matches_pvaec_overlap_resolution() -> None:
    org = _org(50.0, 50.0)
    nut = _nut(50.0, 50.0)
    adapter = PythonSrPhysics2DAdapter()

    adapter.step(
        [org, nut],
        dt=0.016,
        width=400.0,
        height=400.0,
        mode=Physics2DMode.PVAEC,
        springs=(),
        config=SrPhysics2DConfig(contact_iterations=4),
    )

    dist = math.hypot(org.position[0] - nut.position[0], org.position[1] - nut.position[1])
    assert dist >= org.radius + nut.radius - 1.0
```

- [x] **Step 2: Run the new test and verify it fails**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py
```

Expected: FAIL with an import error for `PythonSrPhysics2DAdapter`.

- [x] **Step 3: Implement the Python fallback adapter**

Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`:

```python
# -*- coding: utf-8 -*-
"""SR 2D adapter boundary.

The Python adapter is the behavioral reference. Native adapters must preserve
this public contract before they are allowed behind SrPhysics2DWorld.
"""

from __future__ import annotations

from typing import Any, Iterable, Protocol, Sequence

from core.Lotucosm.sr_physics2d.config import SrPhysics2DConfig
from core.Lotucosm.sr_physics2d.integrator import integrate_all
from core.Lotucosm.sr_physics2d.mode import Physics2DMode
from core.Lotucosm.sr_physics2d.pvaec_contacts import resolve_pvaec_contacts


class SrPhysics2DAdapter(Protocol):
    def step(
        self,
        entities: Sequence[Any],
        *,
        dt: float,
        width: float,
        height: float,
        mode: Physics2DMode,
        springs: Iterable[Any] | None,
        config: SrPhysics2DConfig,
    ) -> None:
        """Advance entities in place for one SR 2D frame."""


class PythonSrPhysics2DAdapter:
    """Reference implementation used as fallback and parity oracle."""

    def step(
        self,
        entities: Sequence[Any],
        *,
        dt: float,
        width: float,
        height: float,
        mode: Physics2DMode,
        springs: Iterable[Any] | None,
        config: SrPhysics2DConfig,
    ) -> None:
        if dt <= 0.0 or not entities:
            return

        ent_list = list(entities)

        if mode == Physics2DMode.PVAEC and springs:
            from core.Lotucosm.sr_link_physics import step_spring_network

            step_spring_network(ent_list, springs, dt)

        integrate_all(ent_list, dt, width, height, config)

        if mode == Physics2DMode.PVAEC:
            resolve_pvaec_contacts(
                ent_list,
                width=width,
                height=height,
                config=config,
            )
        else:
            from core.Lotucosm.sr_physics2d.game_contacts import resolve_game_contacts

            resolve_game_contacts(ent_list, config=config)


def make_default_adapter() -> SrPhysics2DAdapter:
    return PythonSrPhysics2DAdapter()
```

Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`:

```python
from core.Lotucosm.sr_physics2d.adapter import (
    PythonSrPhysics2DAdapter,
    SrPhysics2DAdapter,
    make_default_adapter,
)
```

Add these names to `__all__`:

```python
    "SrPhysics2DAdapter",
    "PythonSrPhysics2DAdapter",
    "make_default_adapter",
```

- [x] **Step 4: Run the adapter test and verify it passes**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py tests/test_sr_physics2d_adapter_contract.py
git commit -m "feat: add sr2d physics adapter contract"
```

---

### Task 2: Route SrPhysics2DWorld Through The Adapter

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/mode.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/world.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`
- Modify: `tests/test_sr_physics2d_adapter_contract.py`

- [x] **Step 1: Add a delegation test**

Append this test to `tests/test_sr_physics2d_adapter_contract.py`:

```python
class RecordingAdapter:
    def __init__(self) -> None:
        self.calls = []

    def step(self, entities, *, dt, width, height, mode, springs, config) -> None:
        self.calls.append(
            {
                "entities": entities,
                "dt": dt,
                "width": width,
                "height": height,
                "mode": mode,
                "springs": springs,
                "config": config,
            }
        )


def test_world_delegates_step_to_configured_adapter() -> None:
    from core.Lotucosm.sr_physics2d import SrPhysics2DWorld

    adapter = RecordingAdapter()
    cfg = SrPhysics2DConfig(linear_damping=0.9)
    entities = [_org(10.0, 10.0)]

    world = SrPhysics2DWorld(cfg, adapter=adapter)
    world.step(entities, 0.02, 320.0, 240.0, mode=Physics2DMode.PVAEC, springs=())

    assert len(adapter.calls) == 1
    assert adapter.calls[0]["entities"] is entities
    assert adapter.calls[0]["dt"] == 0.02
    assert adapter.calls[0]["mode"] == Physics2DMode.PVAEC
    assert adapter.calls[0]["config"] is cfg
```

- [x] **Step 2: Run the test and verify it fails**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py::test_world_delegates_step_to_configured_adapter
```

Expected: FAIL because `SrPhysics2DWorld.__init__()` does not accept `adapter`.

- [x] **Step 3: Modify `SrPhysics2DWorld`**

First move the enum into `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/mode.py` so `adapter.py` and `world.py` can both import it without circular imports. Replace:

```python
from core.Lotucosm.sr_physics2d.world import Physics2DMode
```

with:

```python
from enum import Enum


class Physics2DMode(str, Enum):
    PVAEC = "pvaec"
    GAME = "game"
```

In `world.py`, remove:

```python
from enum import Enum
```

and remove the local enum:

```python
class Physics2DMode(str, Enum):
    PVAEC = "pvaec"
    GAME = "game"
```

Then import the shared enum plus the adapter factory and protocol:

```python
from core.Lotucosm.sr_physics2d.mode import Physics2DMode
from core.Lotucosm.sr_physics2d.adapter import SrPhysics2DAdapter, make_default_adapter
```

Replace the constructor with:

```python
    def __init__(
        self,
        config: SrPhysics2DConfig | None = None,
        *,
        adapter: SrPhysics2DAdapter | None = None,
    ) -> None:
        self.config = config or SrPhysics2DConfig()
        self.adapter = adapter or make_default_adapter()
```

Replace the body of `step()` after the early return with:

```python
        self.adapter.step(
            entities,
            dt=dt,
            width=width,
            height=height,
            mode=mode,
            springs=springs,
            config=self.config,
        )
```

Remove now-unused imports from `world.py`: `integrate_all` and `resolve_pvaec_contacts`.

In `__init__.py`, change the public enum import to come from `mode.py`:

```python
from core.Lotucosm.sr_physics2d.mode import Physics2DMode, infer_physics2d_mode
from core.Lotucosm.sr_physics2d.world import SrPhysics2DWorld
```

- [x] **Step 4: Run SR2D tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/mode.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/world.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py tests/test_sr_physics2d_adapter_contract.py
git commit -m "refactor: route sr2d world through adapter"
```

---

### Task 3: Add SR2D Benchmark Evidence

**Files:**
- Modify: `tools/benchmark_engine.py`
- Test: `tools/benchmark_engine.py` command output

- [x] **Step 1: Add an `sr2d` benchmark case**

In `tools/benchmark_engine.py`, add this function near `_bench_ps_tick()`:

```python
def _bench_sr2d_step() -> dict[str, Any]:
    from types import SimpleNamespace

    from core.Lotucosm.sr_physics2d import Physics2DMode, SrPhysics2DConfig, SrPhysics2DWorld

    entities = []
    for i in range(80):
        entities.append(
            SimpleNamespace(
                entity_type="organism",
                position=[50.0 + (i % 10) * 18.0, 50.0 + (i // 10) * 18.0],
                velocity=[12.0, -8.0],
                radius=12.0,
                pinned=False,
                membrane_locked=False,
            )
        )
    for i in range(20):
        entities.append(
            SimpleNamespace(
                entity_type="nutrient",
                position=[80.0 + (i % 5) * 40.0, 80.0 + (i // 5) * 40.0],
                velocity=[0.0, 0.0],
                radius=10.0,
                pinned=True,
                membrane_locked=False,
            )
        )

    world = SrPhysics2DWorld(SrPhysics2DConfig(contact_iterations=2))
    for _ in range(120):
        world.step(entities, 1.0 / 60.0, 640.0, 480.0, mode=Physics2DMode.PVAEC)
    first = entities[0]
    return {"entities": len(entities), "first_position": [round(first.position[0], 3), round(first.position[1], 3)]}
```

Update the parser choices:

```python
choices=["all", "commands", "resources", "export_closure", "ps", "sr2d", "hub_startup", "editor_smoke_startup"],
```

Add the case selection before startup cases:

```python
    if args.case in ("all", "sr2d"):
        cases.append(("sr2d_step_120", _bench_sr2d_step))
```

- [x] **Step 2: Run the SR2D benchmark**

Run:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 1
```

Expected: JSON output containing `"name": "sr2d_step_120"` and `"entities": 100`.

- [x] **Step 3: Run all lightweight benchmarks once**

Run:

```bash
python -B tools/benchmark_engine.py --case all --repeats 1
```

Expected: JSON output includes `sr2d_step_120`. If unrelated startup smoke cases fail because of local GUI/runtime environment, record the failing case and keep the SR2D benchmark result in the final handoff.

- [ ] **Step 4: Commit**

```bash
git add tools/benchmark_engine.py
git commit -m "test: benchmark sr2d physics step"
```

---

### Task 4: Document The Boundary And Fallback Rule

**Files:**
- Modify: `docs/sr_physics2d.md`
- Modify: `docs/adr/0006-native-acceleration-seams.md`

- [x] **Step 1: Update SR2D docs**

Add this section to `docs/sr_physics2d.md` after the entry-point section:

```markdown
## Adapter Boundary

`SrPhysics2DWorld.step()` remains the public runtime entry point. Internally it delegates to `SrPhysics2DAdapter`.

- `PythonSrPhysics2DAdapter` is the reference implementation and default fallback.
- Future Rust/C++ adapters must pass `tests/test_sr_physics2d_world.py` and `tests/test_sr_physics2d_adapter_contract.py` before being enabled.
- `.pond` files, `GameViewport`, and AI command flows must not call a native module directly.
- Benchmark evidence lives in `tools/benchmark_engine.py --case sr2d`.
```

- [x] **Step 2: Update ADR-0006 verification**

Append this paragraph to `docs/adr/0006-native-acceleration-seams.md` under `## Verification` before the command block:

```markdown
SR 2D uses `SrPhysics2DWorld.step()` as the first adapter boundary. The Python adapter is required as the fallback and behavior oracle; native code is only acceptable after parity tests and benchmark evidence exist.
```

Add this command to the verification block:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 1
```

- [x] **Step 3: Inspect the docs**

Run:

```bash
python -B -m compileall -q tools FrameCore
```

Expected: PASS. This does not validate Markdown rendering, but catches syntax mistakes introduced in embedded import paths only if code was also edited during this task.

- [ ] **Step 4: Commit**

```bash
git add docs/sr_physics2d.md docs/adr/0006-native-acceleration-seams.md
git commit -m "docs: record sr2d native adapter boundary"
```

---

### Task 5: Final Verification

**Files:**
- Existing test and tool files only

- [x] **Step 1: Run focused tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py
```

Expected: PASS.

- [x] **Step 2: Run the SR2D benchmark**

Run:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 3
```

Expected: JSON output includes a stable `mean_ms` for `sr2d_step_120`.

- [x] **Step 3: Run broader guardrails**

Run:

```bash
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore workspace tools main.py player.py
```

Expected: PASS. If failures are unrelated to SR2D adapter work, capture exact failing command and the first actionable error in the final handoff.

- [ ] **Step 4: Commit final fixes if needed**

```bash
git status --short
git add FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d tests/test_sr_physics2d_adapter_contract.py tools/benchmark_engine.py docs/sr_physics2d.md docs/adr/0006-native-acceleration-seams.md
git commit -m "chore: verify sr2d adapter boundary"
```

Expected: Commit only if Step 3 required additional fixes. Do not stage unrelated existing deletions or untracked workspace migrations.

## Self-Review Notes

- Spec coverage: this plan covers interface, fallback, behavior tests, benchmark evidence, and docs required by ADR-0006.
- Scope control: it does not implement Rust/C++ yet. That is intentional because the adapter contract and parity oracle must exist first.
- Risk: the repo currently has many unrelated uncommitted changes. Use explicit `git add` paths from each task and avoid broad staging commands.
