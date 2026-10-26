# OpenGL Viewport Parity And Batching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current OpenGL viewport backend from selection metadata into an opt-in, testable render path with QPainter/OpenGL semantic parity evidence and batching benchmarks.

**Architecture:** Keep PyQt6 as the editor shell and keep QPainter as the default backend. Introduce a backend-neutral draw-command layer compiled from immutable viewport snapshots, then let QPainter and OpenGL consume the same commands. OpenGL remains opt-in until parity and benchmark evidence are strong enough to change `auto`.

**Tech Stack:** Python 3.11+, PyQt6, Qt OpenGL widget bridge, pytest, existing `ViewportBackend`, existing `ViewportFrameSnapshot`, existing benchmark tool.

---

## Implementation Status

Status as of 2026-07-01:

- Implemented `viewport_draw_commands.py` with deterministic snapshot-to-command compilation.
- Implemented `opengl_batching.py` with pure Python OpenGL-friendly batch compilation.
- Added a `ViewportFrameSnapshot` command-render path to `QPainterViewportBackend` while preserving the legacy `QPainterViewportFrame` / `SrVisualRenderer.paint_frame(...)` path.
- Replaced the previous selection-info-only OpenGL backend with an opt-in command/batch path. It accepts `ViewportFrameSnapshot`, compiles commands and batches, records `last_command_count`, `last_batch_count`, `last_instance_count`, and forwards batches to `target.draw_opengl_batches(...)` when the target exposes it.
- Added `DiagnosticOpenGLRenderTarget` for plugin-internal batch consumption evidence. It records circle and line instances, keeps text as an explicit QPainter-overlay placeholder, and exposes a pixel-probe-style non-empty diagnostic.
- Added `QtOpenGLRenderTarget` so explicit OpenGL mode can consume the same batches through the active Qt painter surface and render text via `qt_painter_overlay`. This is a surface bridge, not a completed instanced shader renderer.
- Added `QtOpenGLInstancingTarget` and `probe_qt_opengl_instancing_support()` to report Qt shader, buffer, and current-context readiness. The target exposes a Qt-native `QOpenGLFunctions_4_1_Core.glDrawArraysInstanced` / `glVertexAttribDivisor` seam and keeps fallback explicit when no current GL context exists.
- `GameViewport` now uses `select_viewport_backend(...)`; `auto` still selects QPainter, while explicit OpenGL uses the opt-in backend and Qt target path with diagnostic fallback.
- Kept `VITALOOM_VIEWPORT_BACKEND=auto` on QPainter. OpenGL remains explicit opt-in through `VITALOOM_VIEWPORT_BACKEND=opengl`.
- Added viewport benchmark cases: `viewport_draw`, `viewport_draw_dense`, `viewport_batch_compile`, `viewport_qpainter_render`, and `viewport_opengl_render`.

Evidence already expected from this phase:

- Focused viewport tests cover command compilation, OpenGL batching, QPainter command rendering, OpenGL backend diagnostics, Qt target consumption, backend selection, and command/batch semantic parity.
- Benchmarks emit entity count, command count, batch count, instance count, backend name, batch draw calls, painter draw calls, first command snapshot, OpenGL pixel probe, text overlay policy, and instancing readiness/fallback state where applicable.
- The phase proves semantic command/batch parity, Qt surface consumption, text overlay, and an instanced draw seam. A later phase still needs a QOpenGLWidget/plugin canvas, screenshot/pixel comparison, dense interaction smoke, and current-context instanced GPU draw evidence before OpenGL can become `auto`/default.

## Current Facts

- `OpenGLViewportBackend` has an opt-in command/batch render path with diagnostic and Qt target consumers.
- `QPainterViewportBackend` renders legacy frames through `SrVisualRenderer.paint_frame(...)` and snapshots through backend-neutral draw commands.
- `ViewportFrameSnapshot` already copies entity/edge/camera data into immutable primitives.
- `VITALOOM_VIEWPORT_BACKEND=auto` intentionally selects QPainter until OpenGL visual parity and runtime evidence exist.
- `pygame` is legacy-only and must not enter the main GUI/runtime path.
- Vulkan, Direct3D, and Metal are deferred behind a future `rhi` or `native_batch` backend kind; they are not part of this phase.

## File Structure

- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_draw_commands.py`
  - Owns backend-neutral draw commands and deterministic command compilation from `ViewportFrameSnapshot`.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_batching.py`
  - Owns pure Python batch compilation for OpenGL-friendly circles, lines, sprites, and text placeholders.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py`
  - Add a command-rendering path while keeping existing `QPainterViewportFrame` compatibility.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py`
- Keep the opt-in command/batch path that records diagnostics and only delegates target consumption to explicit OpenGL targets.
- Modify `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py`
  - Keep `auto` on QPainter; expose richer OpenGL readiness metadata.
- Modify `tools/benchmark_engine.py`
  - Add viewport command and batch compile benchmark cases.
- Create focused tests under `tests/`.
- Modify `docs/architecture.md`, `docs/suite_architecture.md`, and `docs/INDEX.md` after behavior is verified.
- Maintain `docs/cleanup_stabilization_audit.md` as the current dirty-worktree and cleanup baseline.

---

### Task 1: Add Backend-Neutral Draw Commands

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_draw_commands.py`
- Create: `tests/test_viewport_draw_commands.py`

- [x] **Step 1: Write failing tests for deterministic command compilation**

Create `tests/test_viewport_draw_commands.py` with tests for entity circles, edge lines, selected outlines, stable ordering, and snapshot-only inputs:

```python
from __future__ import annotations

from core.VitaLoom.viewports.viewport_draw_commands import (
    CircleCommand,
    LineCommand,
    compile_viewport_draw_commands,
)
from core.VitaLoom.viewports.viewport_snapshot import (
    ViewportEdgeSnapshot,
    ViewportEntitySnapshot,
    ViewportFrameSnapshot,
)


def test_compile_entities_and_edges_into_stable_draw_commands() -> None:
    frame = ViewportFrameSnapshot(
        width=320,
        height=240,
        entities=(
            ViewportEntitySnapshot(id="b", entity_type="nutrient", position=(20.0, 30.0), radius=5.0),
            ViewportEntitySnapshot(id="a", entity_type="organism", position=(10.0, 15.0), radius=8.0, selected=True),
        ),
        edges=(ViewportEdgeSnapshot(source_id="a", target_id="b", kind="hard"),),
    )

    commands = compile_viewport_draw_commands(frame)

    assert [command.kind for command in commands] == ["line", "circle", "circle", "circle"]
    assert isinstance(commands[0], LineCommand)
    assert isinstance(commands[1], CircleCommand)
    assert commands[1].entity_id == "a"
    assert commands[2].entity_id == "a:selected"
    assert commands[3].entity_id == "b"
```

- [x] **Step 2: Run the test and confirm it fails**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_draw_commands.py
```

Expected: import failure for `viewport_draw_commands`.

- [x] **Step 3: Implement immutable command dataclasses and compiler**

Implement `CircleCommand`, `LineCommand`, `TextCommand`, `DrawCommand`, and `compile_viewport_draw_commands(frame)`. The compiler must:

- sort entities by `id`;
- draw hard/signal edges before entities;
- draw selected outlines immediately after the selected entity body;
- resolve edge endpoints by entity id;
- derive colors from `entity_type` and `visual_state` with stable defaults;
- never keep live entity references.

- [x] **Step 4: Verify the tests pass**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_draw_commands.py tests/test_viewport_snapshot.py
```

Expected: all tests pass.

### Task 2: Add Pure OpenGL Batch Compiler

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_batching.py`
- Create: `tests/test_opengl_batching.py`

- [x] **Step 1: Write failing tests for batch grouping**

Create tests proving circles group by fill/stroke style and lines group by color/width:

```python
from __future__ import annotations

from core.VitaLoom.viewports.opengl_batching import compile_opengl_batches
from core.VitaLoom.viewports.viewport_draw_commands import CircleCommand, LineCommand


def test_compile_opengl_batches_groups_by_primitive_and_style() -> None:
    commands = (
        CircleCommand(kind="circle", entity_id="a", center=(1.0, 2.0), radius=3.0, fill=(10, 20, 30, 255), stroke=(0, 0, 0, 255), stroke_width=1.0),
        CircleCommand(kind="circle", entity_id="b", center=(5.0, 6.0), radius=4.0, fill=(10, 20, 30, 255), stroke=(0, 0, 0, 255), stroke_width=1.0),
        LineCommand(kind="line", edge_id="a:b", start=(1.0, 2.0), end=(5.0, 6.0), color=(80, 90, 100, 255), width=2.0),
    )

    batches = compile_opengl_batches(commands)

    assert [batch.primitive for batch in batches] == ["circle", "line"]
    assert batches[0].instance_count == 2
    assert batches[1].instance_count == 1
```

- [x] **Step 2: Run the test and confirm it fails**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_batching.py
```

Expected: import failure for `opengl_batching`.

- [x] **Step 3: Implement batch dataclasses and compiler**

Implement `OpenGLBatch` and `compile_opengl_batches(commands)`. The compiler must be pure Python, deterministic, and independent of an active OpenGL context. Store instance payloads as tuples of floats/ints so benchmark output is serializable.

- [x] **Step 4: Verify batch tests pass**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_batching.py tests/test_viewport_draw_commands.py
```

Expected: all tests pass.

### Task 3: Route QPainter Through Draw Commands Without Breaking Compatibility

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py`
- Create: `tests/test_qpainter_draw_command_renderer.py`

- [x] **Step 1: Write tests for command rendering delegation**

Create a fake painter that records draw calls, then render command objects through a new `QPainterDrawCommandRenderer`.

- [x] **Step 2: Keep the legacy `QPainterViewportFrame` path intact**

Do not remove `QPainterViewportFrame` or the existing `SrVisualRenderer.paint_frame(...)` call path. Add a second path that accepts `ViewportFrameSnapshot` and internally uses `compile_viewport_draw_commands(frame)`.

- [x] **Step 3: Verify both paths**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_qpainter_viewport_backend.py tests/test_qpainter_draw_command_renderer.py
```

Expected: existing QPainter backend tests and new command renderer tests pass.

### Task 4: Make OpenGL Backend Render Through Batches In Opt-In Mode

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py`
- Create: `tests/test_opengl_viewport_backend.py`

- [x] **Step 1: Write tests for OpenGL backend diagnostics**

Test that `OpenGLViewportBackend.render(fake_target, frame)` compiles draw commands and batches, records `last_command_count`, `last_batch_count`, `last_instance_count`, and does not require a real GL context when the target exposes no GL draw surface.

- [x] **Step 2: Implement opt-in batch render path**

`OpenGLViewportBackend.render(...)` must:

- accept `ViewportFrameSnapshot`;
- compile draw commands;
- compile OpenGL batches;
- record diagnostics in `stats()`;
- raise a clear `RuntimeError` only when asked to issue real GL calls without an initialized GL target;
- keep `supports_batching=True` only after the batch path is implemented and tested.

- [x] **Step 3: Verify OpenGL backend tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_viewport_backend.py tests/test_viewport_backend_selection.py
```

Expected: all tests pass, `auto` still selects QPainter.

### Task 5: Add Semantic Parity Harness

**Files:**
- Create: `tests/test_viewport_render_parity.py`

- [x] **Step 1: Build shared parity scenes**

Use deterministic `ViewportFrameSnapshot` fixtures for:

- empty scene;
- single organism;
- selected organism;
- two entities with one hard edge;
- dense 100-entity scene;
- mixed visible/hidden entities.

- [x] **Step 2: Compare QPainter command trace and OpenGL batch semantics**

The parity test must compare primitive counts, entity ids, edge ids, bounds, style keys, and selected outline semantics. It must not require pixel-perfect screenshots in this phase.

- [x] **Step 3: Verify parity harness**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_render_parity.py
```

Expected: all parity cases pass.

### Task 6: Add Viewport Benchmarks

**Files:**
- Modify: `tools/benchmark_engine.py`
- Create: `tests/test_benchmark_engine_viewport_variants.py`

- [x] **Step 1: Add benchmark tests for new cases**

Test that `--case viewport_draw`, `--case viewport_draw_dense`, and `--case viewport_batch_compile` return JSON with:

- `entities`;
- `commands`;
- `batches`;
- `instances`;
- `backend`;
- `first_command`.

- [x] **Step 2: Implement benchmark cases**

Add deterministic snapshot generators and cases that measure command compilation and batch compilation without opening a GUI window.

- [x] **Step 3: Run benchmarks**

Run:

```bash
python -B tools/benchmark_engine.py --case viewport_draw --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
```

Expected: each command prints JSON with mean/min/max timing and viewport-specific result metadata.

### Task 7: Keep Backend Selection Conservative

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py`
- Modify: `tests/test_viewport_backend_selection.py`

- [x] **Step 1: Add tests proving `auto` still selects QPainter**

Keep the existing test and add an assertion that OpenGL readiness metadata does not change `auto`.

- [x] **Step 2: Add explicit readiness metadata**

Expose `opengl_parity_ready`, `opengl_batching_ready`, and `default_switch_allowed` in backend stats or selection metadata. `default_switch_allowed` must be `False` in this phase.

- [x] **Step 3: Verify selection behavior**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_backend_selection.py
```

Expected: explicit `opengl` can select the opt-in backend when Qt OpenGL is available; `auto` remains QPainter.

### Task 8: Final Verification And Docs

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/suite_architecture.md`
- Modify: `docs/INDEX.md`

- [x] **Step 1: Document the new render pipeline**

Document:

- `ViewportFrameSnapshot`;
- `viewport_draw_commands`;
- `opengl_batching`;
- QPainter compatibility path;
- OpenGL opt-in path;
- why default remains QPainter.

- [x] **Step 2: Run focused verification**

Run:

```bash
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_snapshot.py tests/test_viewport_draw_commands.py tests/test_opengl_batching.py tests/test_qpainter_viewport_backend.py tests/test_qpainter_draw_command_renderer.py tests/test_opengl_viewport_backend.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py
python -B -m pytest -q -p no:cacheprovider tests/test_gui_boundaries.py tests/test_viewport_profiler.py tests/test_simulation_driver_viewport_tick.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py
python -B tools/benchmark_engine.py --case viewport_draw --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
git diff --check
```

Expected: all focused tests pass, benchmark JSON is printed, and diff check has no whitespace errors.

## Acceptance Checklist

- [x] Draw-command compilation is deterministic and covered by tests.
- [x] QPainter and OpenGL consume the same semantic command stream.
- [x] OpenGL has an opt-in batch path with diagnostic and Qt target consumers.
- [x] `auto` still selects QPainter.
- [x] Vulkan, Direct3D, and Metal are not implemented in this phase.
- [x] Benchmark output shows command counts, batch counts, instance counts, and timing.
- [x] Docs explain that this phase proves command/batch parity and batching, not a default backend switch.

## Next Phase Gate

Do not switch `auto` to OpenGL until a later plan proves all of the following:

- screenshot or pixel-level parity checks compare QPainter and OpenGL on representative scenes;
- dense-scene interaction smoke proves pan/zoom/selection stays responsive;
- a QOpenGLWidget/plugin canvas owns the GL context and verifies current-context shader/instancing draws;
- fallback behavior is clear when Qt OpenGL is unavailable;
- `tools/check_gui_boundaries.py`, focused viewport tests, and viewport benchmarks still pass.
