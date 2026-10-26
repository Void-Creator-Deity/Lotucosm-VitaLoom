# Viewport Performance And Render Batching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Profile and improve dense-scene viewport frame time without changing VitaLoom's plugin architecture or switching OpenGL to default.

**Architecture:** Keep `GameViewport` as host/facade, QPainter as the default backend, and OpenGL as opt-in. Measure command compilation, QPainter command render, OpenGL batch compile, real widget OpenGL smoke/render metadata, and interaction timing separately before adding caches or batching changes.

**Tech Stack:** Python 3.11+, PyQt6, pytest, existing `ViewportFrameSnapshot`, `viewport_draw_commands`, `opengl_batching`, `OpenGLViewportBackend`, `QPainterViewportBackend`, and `tools/benchmark_engine.py`.

---

## Previous Phase Summary

Phase 1 - Real OpenGL viewport canvas passed its gate on 2026-07-03:

- `QOpenGLWidget` lifecycle is isolated in `opengl_canvas.py`.
- Explicit OpenGL mode delegates through `sr_gpu_canvas.py` into the new lifecycle canvas.
- `GameViewport` has separate QPainter and OpenGL canvas helpers.
- Current-context smoke renders non-empty pixels.
- Representative scenes (`empty`, `single`, `selected`, `edge`, `hidden`) feed frames through `OpenGLViewportBackend -> QtOpenGLInstancingTarget` inside `paintGL`.
- Real widget benchmark metadata exists as `viewport_opengl_canvas`.
- OpenGL remains opt-in and not default-ready.

## Current State

- `viewport_draw_dense`: 360 entities, 630 commands, 46 batches.
- `viewport_batch_compile`: 360 entities, 630 commands, 46 batches.
- Non-widget `viewport_opengl_render` is a Qt painter target bridge and still reports no current context for the instancing target.
- Real widget `viewport_opengl_canvas` proves current-context metadata but is a smoke benchmark, not optimized frame-rate evidence.
- User's original complaint is dense entity lag and low frame rate, so Phase 2 must measure dense repeated-frame behavior before optimizing.

## Scope

- Add benchmark cases that separate repeated-frame costs from one-shot setup costs.
- Add viewport profiler output for command compilation, QPainter command render, OpenGL batch compile, real widget smoke, and interaction events.
- Cache stable style/color/pen/brush/batch keys only where tests and benchmark output prove repeated allocation or recomputation cost.
- Keep `.pond`, AI commands, Inspector binding, SR2D adapter seams, package manifests, and plugin layout unchanged.

## Non-goals

- Do not switch `auto` to OpenGL.
- Do not claim final GPU performance from smoke metadata.
- Do not hide entities, reduce simulation semantics, or lower visual fidelity to improve numbers.
- Do not introduce Vulkan, Direct3D, Metal, Unity, Godot, Unreal, Electron, or a new RHI branch.
- Do not optimize SR2D physics in this phase unless the viewport profiler proves physics is the dominant frame bottleneck and the plan is updated.

## Files

- Modify: `tools/benchmark_engine.py`
  - Add repeated-frame viewport cases and timing breakdown metadata.
- Extend: `tests/test_benchmark_engine_viewport_variants.py`
  - Assert new benchmark fields and scenario sizes.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_profiler.py`
  - Add structured snapshot helpers if needed.
- Modify cautiously: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_draw_commands.py`
  - Add cache hooks only after tests prove stable snapshot cache keys.
- Modify cautiously: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py`
  - Add style object reuse only if benchmark evidence points there.
- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Create: `docs/prompts/2026-07-03-viewport-performance-render-batching-prompt.md`

## Step-by-step Tasks

### Task 1: Add Repeated-Frame Benchmark Baseline

**Files:**
- Modify: `tools/benchmark_engine.py`
- Extend: `tests/test_benchmark_engine_viewport_variants.py`

- [x] **Step 1: Write benchmark metadata test**

Add a test for `viewport_frame_loop_dense` that asserts:

- `frames >= 30`;
- `entities == 360`;
- `commands_per_frame == 630`;
- `batches_per_frame == 46`;
- fields exist for `command_compile_ms`, `batch_compile_ms`, `qpainter_render_ms`, and `opengl_canvas_smoke_ms`;
- `auto_default_backend == "qpainter"`.

- [x] **Step 2: Implement the benchmark case**

Use the existing dense snapshot and run repeated frames without opening the full editor. Measure each path separately and return JSON metadata.

- [x] **Step 3: Run baseline benchmark**

```bash
python -B tools/benchmark_engine.py --case viewport_frame_loop_dense --repeats 3
```

Record numbers in `docs/mainline_status.md`.

### Task 2: Add Interaction Timing Smoke

**Files:**
- Extend: `tests/test_opengl_canvas.py`
- Extend: `tools/benchmark_engine.py`

- [x] **Step 1: Assert keyboard and resize timing metadata**

Benchmark output must include resize event count, keyboard event count, and whether events were forwarded.

- [x] **Step 2: Implement lightweight interaction benchmark**

Use the injectable OpenGL canvas class and fake events; do not require a full editor window.

### Task 3: Profile Before Caching

**Files:**
- Modify: `viewport_profiler.py`
- Extend: focused tests under `tests/`

- [x] **Step 1: Add structured profiler snapshot test**

Assert profiler snapshots include named timing buckets and frame counts.

- [x] **Step 2: Wire benchmark output to profiler snapshots**

Expose profiler data in benchmark JSON so future optimization claims can cite named buckets.

### Task 4: Evidence-Gated Cache Or Batch Optimization

**Files:**
- Modify only the hotspot named by Task 1-3 evidence.

- [x] **Step 1: Write failing regression test for the selected cache/batch behavior**

The test must prove output semantics stay identical.

- [x] **Step 2: Implement one scoped optimization**

Examples allowed only if evidence points there:

- stable style key cache in draw-command compilation;
- QPainter pen/brush reuse in command renderer;
- OpenGL batch style grouping reuse for unchanged snapshots.

- [x] **Step 3: Re-run baseline and compare numbers**

Record before/after numbers in `docs/mainline_status.md`.

Implementation note: profiler evidence identified QPainter command rendering as the largest repeated CPU bucket. The scoped optimization reuses QPainter pen/brush style objects in `QPainterDrawCommandRenderer`; it does not change draw command ordering, entity visibility, `.pond` semantics, backend selection, or visual fidelity.

## Verification Commands

```bash
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B -m pytest -q -p no:cacheprovider tests/test_benchmark_engine_viewport_variants.py tests/test_opengl_canvas.py tests/test_opengl_canvas_smoke.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py
python -B tools/benchmark_engine.py --case viewport_frame_loop_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
python -B tools/benchmark_engine.py --case viewport_opengl_canvas --repeats 3
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans FrameCore tests tools
```

## Evidence Ledger

Record:

- repeated-frame scenario size;
- timing buckets;
- before/after numbers for any optimization;
- fallback and opt-in status;
- tests passed/skipped;
- remaining bottleneck.

## Fallback And Unblock Path

- If real widget OpenGL smoke is unavailable, keep QPainter and pure command/batch benchmarks as the measurable baseline and record the skip reason.
- If repeated-frame benchmark is noisy, increase repeats and record min/mean/max, not only mean.
- If no clear hotspot appears, do not add speculative caches; mark Phase 2 partially complete with profiler evidence and next measurement gate.

## Acceptance Checklist

- [x] Repeated-frame dense benchmark exists.
- [x] Benchmark output distinguishes setup, command compile, batch compile, QPainter render, and real widget OpenGL smoke.
- [x] Any optimization is tied to profiler evidence.
- [x] QPainter remains default.
- [x] OpenGL remains opt-in.
- [x] Mainline status records before/after or explicitly says no optimization was attempted.

## Next Phase Gate

Phase 3 - SR2D physics parity and Python broadphase can start only after viewport profiling either improves dense-frame time or identifies the next measured viewport bottleneck.
