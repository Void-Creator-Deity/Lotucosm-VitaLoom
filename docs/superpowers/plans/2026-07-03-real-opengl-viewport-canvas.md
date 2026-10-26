# Real OpenGL Viewport Canvas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an opt-in Qt OpenGL viewport canvas that owns a real current GL lifecycle and consumes the existing `ViewportFrameSnapshot -> viewport_draw_commands -> opengl_batching` pipeline without changing QPainter as the default.

**Architecture:** Keep VitaLoom plugin-shaped under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. Add a focused OpenGL canvas module beside the existing viewport backends, route explicit OpenGL canvas creation through it, and keep `GameViewport` as the host/facade. QPainter remains default until this phase records current-context pixels, parity, interaction smoke, fallback behavior, and benchmarks.

**Tech Stack:** Python 3.11+, PyQt6, `QOpenGLWidget`, pytest, existing `OpenGLViewportBackend`, existing `ViewportFrameSnapshot`, existing benchmark tool.

---

## Previous Phase Summary

Phase 0 baseline passed on 2026-07-03:

- Worktree classified: 949 dirty entries, intentionally not cleaned.
- Boundary checks, release consistency, compileall, focused viewport tests, focused SR2D/native fallback tests, and benchmark baselines were recorded in `docs/mainline_status.md`.
- Native SR2D extensions are not importable on this machine; Python fallback remains required.
- OpenGL is still only opt-in batching/Qt-surface proof. It is not default-ready and not proven as high-performance shader rendering.

## Current State

- `OpenGLViewportBackend` compiles draw commands and OpenGL batches and can send them to a target exposing `draw_opengl_batches(...)`.
- `DiagnosticOpenGLRenderTarget` proves batch consumption without a GL context.
- `QtOpenGLRenderTarget` consumes batches through a Qt painter surface and uses `qt_painter_overlay` for text.
- `QtOpenGLInstancingTarget` exposes a shader/instancing seam and reports `fallback_no_current_context` when no current GL context exists.
- `sr_gpu_canvas.py` can return a `QOpenGLWidget` subclass for explicit OpenGL mode, but its current `paintGL()` path does not provide clean current-context rendering evidence and can nest painter ownership through `GameViewport._paint_sr_canvas(...)`.
- Local probe succeeded for importing `PyQt6.QtOpenGLWidgets.QOpenGLWidget`; `QOpenGLContext.currentContext()` is `None` outside widget lifecycle.

## Scope

- Add a focused OpenGL canvas module that owns `initializeGL`, `resizeGL`, and `paintGL` diagnostics.
- Refactor the explicit OpenGL canvas path so `GameViewport` can render a `ViewportFrameSnapshot` into a real current-context target.
- Preserve keyboard input behavior, canvas sizing, QPainter fallback, and explicit `VITALOOM_VIEWPORT_BACKEND=opengl` opt-in behavior.
- Add unit-level lifecycle tests and skip-safe GUI smoke tests.
- Add pixel/screenshot or deterministic offscreen pixel evidence when the environment can create a GL context.
- Extend benchmark/status output to distinguish command compile, batch compile, Qt painter bridge, and real canvas render path.

## Non-goals

- Do not switch `auto` to OpenGL.
- Do not migrate to Unity, Godot, Unreal, Electron, or another app shell.
- Do not introduce Vulkan, Direct3D, Metal, or a new RHI runtime branch.
- Do not hide text placeholder/overlay behavior.
- Do not solve SR2D physics performance in this phase.
- Do not delete or revert unrelated dirty worktree changes.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_canvas.py`
  - Owns the real Qt OpenGL canvas factory, lifecycle diagnostics, and current-context smoke surface.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_gpu_canvas.py`
  - Keep compatibility exports, but delegate explicit OpenGL canvas creation to `opengl_canvas.py`.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
  - Add small render helper methods so QPainter canvas and OpenGL canvas do not create nested painters.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_render_target.py`
  - Add current-context diagnostics and pixel evidence fields if the canvas can provide them.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py`
  - Keep `auto` conservative and use the new canvas probe for availability metadata.
- Modify: `tools/benchmark_engine.py`
  - Add or refine `viewport_opengl_canvas` benchmark metadata without requiring a visible window.
- Create: `tests/test_opengl_canvas.py`
- Create or extend: `tests/test_opengl_canvas_smoke.py`
- Extend: `tests/test_opengl_render_target.py`
- Extend: `tests/test_viewport_backend_selection.py`
- Extend: `tests/test_benchmark_engine_viewport_variants.py`
- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Update or create: `docs/prompts/2026-07-03-real-opengl-viewport-canvas-prompt.md`

## Step-by-step Tasks

### Task 1: Add Pure Lifecycle Canvas Factory Tests

**Files:**
- Create: `tests/test_opengl_canvas.py`
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_canvas.py`

- [x] **Step 1: Write the failing lifecycle test**

Create `tests/test_opengl_canvas.py` with an injectable fake base widget so the test does not need a real GUI context:

```python
from __future__ import annotations

from core.VitaLoom.viewports.opengl_canvas import create_opengl_viewport_canvas_class


class _FakeOpenGLWidget:
    class UpdateBehavior:
        PartialUpdate = "partial"

    def __init__(self, parent=None):
        self.parent = parent
        self.object_name = ""
        self.minimum_size = None
        self.focus_policy = None
        self.update_behavior = None
        self.update_calls = 0

    def setObjectName(self, name: str) -> None:
        self.object_name = name

    def setMinimumSize(self, width: int, height: int) -> None:
        self.minimum_size = (width, height)

    def setFocusPolicy(self, policy) -> None:
        self.focus_policy = policy

    def setUpdateBehavior(self, behavior) -> None:
        self.update_behavior = behavior

    def update(self) -> None:
        self.update_calls += 1


class _Host:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def _initialize_sr_opengl_canvas(self, canvas) -> None:
        self.calls.append(("initialize", canvas.object_name))

    def _resize_sr_opengl_canvas(self, canvas, width: int, height: int) -> None:
        self.calls.append(("resize", (width, height)))

    def _paint_sr_opengl_canvas(self, canvas) -> None:
        self.calls.append(("paint", canvas.object_name))


def test_canvas_factory_routes_qopengl_lifecycle_to_host() -> None:
    Canvas = create_opengl_viewport_canvas_class(_FakeOpenGLWidget)
    host = _Host()
    canvas = Canvas(host)

    canvas.initializeGL()
    canvas.resizeGL(640, 360)
    canvas.paintGL()

    assert canvas.object_name == "gameViewportOpenGLCanvas"
    assert canvas.minimum_size == (400, 300)
    assert canvas.update_behavior == "partial"
    assert host.calls == [
        ("initialize", "gameViewportOpenGLCanvas"),
        ("resize", (640, 360)),
        ("paint", "gameViewportOpenGLCanvas"),
    ]
    assert canvas.opengl_lifecycle_snapshot()["paint_calls"] == 1
```

- [x] **Step 2: Run the test and confirm the expected failure**

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py
```

Expected: import failure for `core.VitaLoom.viewports.opengl_canvas`.

- [x] **Step 3: Implement the minimal canvas factory**

Create `opengl_canvas.py` with:

```python
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Type

try:
    from PyQt6.QtCore import Qt
except Exception:
    Qt = None  # type: ignore[assignment]


def create_opengl_viewport_canvas_class(opengl_widget_cls: Type[Any]) -> Type[Any]:
    class OpenGLViewportCanvas(opengl_widget_cls):  # type: ignore[misc, valid-type]
        def __init__(self, host: Any):
            super().__init__(host)
            self._host = host
            self._initialize_calls = 0
            self._resize_calls = 0
            self._paint_calls = 0
            self._last_size = (0, 0)
            self.setObjectName("gameViewportOpenGLCanvas")
            self.setMinimumSize(400, 300)
            if Qt is not None:
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            if hasattr(opengl_widget_cls, "UpdateBehavior"):
                self.setUpdateBehavior(opengl_widget_cls.UpdateBehavior.PartialUpdate)

        def initializeGL(self) -> None:
            self._initialize_calls += 1
            callback = getattr(self._host, "_initialize_sr_opengl_canvas", None)
            if callable(callback):
                callback(self)

        def resizeGL(self, width: int, height: int) -> None:
            self._resize_calls += 1
            self._last_size = (int(width), int(height))
            callback = getattr(self._host, "_resize_sr_opengl_canvas", None)
            if callable(callback):
                callback(self, int(width), int(height))

        def paintGL(self) -> None:
            self._paint_calls += 1
            callback = getattr(self._host, "_paint_sr_opengl_canvas", None)
            if callable(callback):
                callback(self)

        def opengl_lifecycle_snapshot(self) -> dict[str, Any]:
            return {
                "target": "qt_opengl_canvas",
                "initialize_calls": self._initialize_calls,
                "resize_calls": self._resize_calls,
                "paint_calls": self._paint_calls,
                "last_size": list(self._last_size),
            }

    return OpenGLViewportCanvas


__all__ = ["create_opengl_viewport_canvas_class"]
```

- [x] **Step 4: Run the lifecycle test**

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py
```

Expected: the new lifecycle test passes.

### Task 2: Move sr_gpu_canvas Compatibility To The New Factory

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_gpu_canvas.py`
- Extend: `tests/test_opengl_canvas.py`

- [x] **Step 1: Add tests for explicit OpenGL selection and fallback**

Append tests proving `create_sr_canvas_class(...)` returns the host QPainter canvas when OpenGL is not requested or when the widget class is unavailable, and returns the new OpenGL canvas class when requested and available.

- [x] **Step 2: Refactor `sr_gpu_canvas.py`**

Keep `_probe_opengl_widget()` and `_opengl_viewport_requested()`, but replace the nested `_SrGpuCanvas` class with:

```python
from core.VitaLoom.viewports.opengl_canvas import create_opengl_viewport_canvas_class

...

    OGL = _OPENGL_WIDGET
    assert OGL is not None
    logger.info("SR canvas enabled OpenGL backend through QOpenGLWidget")
    return create_opengl_viewport_canvas_class(OGL)
```

- [x] **Step 3: Run canvas tests**

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py tests/test_viewport_backend_selection.py
```

Expected: explicit OpenGL remains opt-in; `auto` still selects QPainter.

### Task 3: Split GameViewport Painting Into QPainter And OpenGL Helpers

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
- Extend: `tests/test_game_viewport_unified_bridge.py` or create `tests/test_game_viewport_opengl_canvas.py`

- [x] **Step 1: Write tests for helper existence and non-nested OpenGL paint path**

The test should instantiate a lightweight `GameViewport` when PyQt6 widgets are available or inspect callable helper methods without opening a full editor. It should assert these methods exist:

```python
assert callable(getattr(GameViewport, "_build_sr_viewport_frame_snapshot"))
assert callable(getattr(GameViewport, "_paint_sr_opengl_canvas"))
assert callable(getattr(GameViewport, "_paint_sr_qpainter_canvas"))
```

- [x] **Step 2: Extract snapshot building**

Move the existing `build_viewport_frame_snapshot(...)` block into `_build_sr_viewport_frame_snapshot(width, height)`.

- [x] **Step 3: Add `_paint_sr_qpainter_canvas(...)`**

Keep the existing QPainter path here. It may still create `QPainter(canvas)` because QWidget/QPainter owns that lifecycle.

- [x] **Step 4: Add `_paint_sr_opengl_canvas(...)`**

This method must not create a nested `QPainter` for the whole frame. It should:

- build the viewport snapshot;
- create a current-context target, starting with `QtOpenGLInstancingTarget`;
- call `self._viewport_backend.render(target, frame)`;
- store target/backend snapshots for diagnostics;
- call `canvas.update()` only through normal widget scheduling, not recursively from `paintGL()`.

- [x] **Step 5: Make `_paint_sr_canvas(...)` delegate**

If the canvas exposes `opengl_lifecycle_snapshot`, delegate to `_paint_sr_opengl_canvas(canvas)`. Otherwise delegate to `_paint_sr_qpainter_canvas(canvas, event)`.

### Task 4: Add Current-Context And Pixel Evidence

**Files:**
- Extend: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_render_target.py`
- Create or extend: `tests/test_opengl_canvas_smoke.py`

- [x] **Step 1: Add skip-safe smoke test**

The test should skip when Qt cannot create a GUI/OpenGL surface. When available, it should create a `QApplication`, instantiate the OpenGL canvas, call lifecycle methods through Qt where possible, and assert:

- `initialize_calls >= 1`;
- `paint_calls >= 1`;
- target snapshot reports `context_current: true` during paint or records a clear unavailable reason;
- pixel probe reports non-empty only when primitives were actually submitted.

- [x] **Step 2: Extend target snapshot fields**

Add fields that separate:

- `context_current`;
- `gpu_draw_calls`;
- `fallback_required`;
- `text_overlay_required`;
- `pixel_probe`.

- [x] **Step 3: Run smoke tests**

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py tests/test_opengl_canvas_smoke.py tests/test_opengl_render_target.py
```

Expected: pure tests pass. Real context tests pass when a Qt GL context is available and skip with a clear reason when unavailable.

### Task 5: Add Pixel/Command Parity For Representative Scenes

**Files:**
- Extend: `tests/test_viewport_render_parity.py`
- Extend: `tests/test_opengl_canvas_smoke.py`

- [x] **Step 1: Reuse existing parity frames**

Use the existing empty, single organism, selected organism, hard-edge, dense, and hidden-entity scenes.

- [x] **Step 2: Compare QPainter command trace against OpenGL target snapshot**

For headless tests, compare primitive counts, command ids, selected outlines, bounds, text overlay counts, and target policy.

- [x] **Step 3: Compare pixels only when the environment can render**

If a real OpenGL context is available, assert a representative scene produces non-empty pixels and the primitive bounds overlap the QPainter command bounds.

### Task 6: Benchmark And Backend Metadata

**Files:**
- Modify: `tools/benchmark_engine.py`
- Extend: `tests/test_benchmark_engine_viewport_variants.py`
- Extend: `tests/test_viewport_backend_selection.py`

- [x] **Step 1: Add benchmark metadata tests**

Assert `viewport_opengl_canvas` or the refined `viewport_opengl_render` output includes:

- `backend`;
- `target`;
- `context_current`;
- `gpu_draw_calls`;
- `fallback_required`;
- `commands`;
- `batches`;
- `instances`;
- `text_policy`;
- `first_command`.

- [x] **Step 2: Implement benchmark case**

The case may use lifecycle diagnostics in headless mode and should not require a visible editor window.

- [x] **Step 3: Run benchmark commands**

```bash
python -B tools/benchmark_engine.py --case viewport_opengl_render --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
```

### Task 7: Interaction Smoke

**Files:**
- Extend: `tests/test_opengl_canvas.py`
- Extend: `tests/test_game_viewport_opengl_canvas.py`

- [x] **Step 1: Add keyboard forwarding tests**

Use a fake key event with `text() == "w"` and assert the OpenGL canvas forwards `W` to host `_sr_input_press(...)` and `_sr_input_release(...)`.

- [x] **Step 2: Verify resize lifecycle evidence**

The existing lifecycle test calls `resizeGL(640, 360)` and asserts the host receives the resize event.

- [x] **Step 3: Run interaction smoke tests**

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py tests/test_game_viewport_opengl_canvas.py
```

Expected: tests pass without creating a visible editor window.

### Task 8: Documentation And Status Update

**Files:**
- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Create: `docs/prompts/2026-07-03-real-opengl-viewport-canvas-prompt.md`

- [ ] **Step 1: Record evidence**

Update `docs/mainline_status.md` with:

- tests run and pass/skip counts;
- whether a current GL context was available in smoke;
- whether pixels were rendered or skipped;
- OpenGL remains opt-in;
- `auto` remains QPainter.

- [ ] **Step 2: Link plan and prompt**

Add links to `docs/INDEX.md` under Agent execution materials.

- [ ] **Step 3: Add fresh-session prompt**

The prompt must tell the next C0dex session to read this plan, `docs/mainline_status.md`, `opengl_canvas.py`, `sr_gpu_canvas.py`, `game_viewport.py`, and the OpenGL tests before changing code.

## Verification Commands

```bash
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py tests/test_opengl_canvas_smoke.py tests/test_opengl_render_target.py tests/test_opengl_viewport_backend.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py
python -B tools/benchmark_engine.py --case viewport_opengl_render --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans FrameCore tests tools
```

## Evidence Ledger

Record each item in `docs/mainline_status.md`:

- QOpenGLWidget import availability.
- Current context availability during widget lifecycle.
- Pixel/screenshot evidence or skip reason.
- Target snapshot fields.
- QPainter fallback status.
- Benchmark numbers with entity count, commands, batches, and instances.
- Tests passed, failed, and skipped.

## Fallback And Unblock Path

- If Qt cannot create a GUI/OpenGL surface locally, pure lifecycle and backend tests must still pass and real-context tests must skip with a reason.
- If `QOpenGLWidget` cannot import, explicit OpenGL selection must return an unavailable backend and QPainter must remain the fallback.
- If shader/instancing APIs are present but no context is current, target snapshots must say `fallback_no_current_context`.
- If text remains overlay-only, report `qt_painter_overlay` or `placeholder_for_qpainter_overlay` explicitly.

## Acceptance Checklist

- [x] OpenGL canvas creation is isolated in `opengl_canvas.py`.
- [x] `sr_gpu_canvas.py` delegates to the new factory and remains compatibility-only.
- [x] `GameViewport` no longer nests whole-frame QPainter creation inside `paintGL()`.
- [x] Explicit OpenGL mode owns a `QOpenGLWidget` lifecycle.
- [x] QPainter remains default in `auto`.
- [x] Tests prove lifecycle routing, fallback, backend selection, and parity metadata.
- [x] Real-context smoke either renders pixels or skips with a clear environment reason.
- [x] Benchmark output distinguishes real canvas render metadata from command/batch compilation.

## Phase-End Report Template

- Phase: Phase 1 - Real OpenGL viewport canvas
- Status: complete | partially complete | blocked
- Implemented:
- Verified:
- Skipped/Unavailable:
- Evidence:
- Architecture impact:
- Remaining risks:
- Next phase:

## Next Phase Gate

Phase 2 - Viewport performance and render batching can start only after Phase 1 records:

- real current-context canvas evidence or a precise environment skip;
- screenshot/pixel parity or a skip-safe replacement accepted by the plan;
- interaction smoke for resize, paint, focus, and keyboard forwarding;
- benchmark output for `viewport_opengl_render`;
- `auto` still selecting QPainter.
