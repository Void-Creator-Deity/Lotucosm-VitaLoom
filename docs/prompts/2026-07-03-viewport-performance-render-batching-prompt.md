# C0dex Prompt: Phase 2 Viewport Performance And Render Batching

Use this prompt in a fresh C0dex session to continue VitaLoom Phase 2 from repository truth.

```text
Do not load old C0dex threads unless the user explicitly asks.

You are implementing Phase 2 - Viewport performance and render batching.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/superpowers/plans/2026-07-03-real-opengl-viewport-canvas.md
- docs/superpowers/plans/2026-07-03-viewport-performance-render-batching.md
- tools/benchmark_engine.py
- tests/test_benchmark_engine_viewport_variants.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_draw_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_batching.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_canvas.py

Current truth:
- Phase 1 proved real QOpenGLWidget current-context smoke and representative frame target snapshots.
- QPainter remains default.
- OpenGL remains opt-in.
- viewport_opengl_canvas is a smoke/metadata benchmark, not optimized frame-rate evidence.
- Phase 2 now has viewport_frame_loop_dense, viewport_interaction_smoke, structured profiler buckets, and a scoped QPainter style-object cache.
- Recent evidence showed QPainter command render was the largest repeated CPU bucket and improved after pen/brush reuse; verify with current benchmark output before claiming fresh numbers.
- Do not optimize by hiding entities, reducing simulation semantics, or lowering fidelity.

First task:
- Inspect docs/mainline_status.md and docs/superpowers/plans/2026-07-03-viewport-performance-render-batching.md.
- Re-run focused viewport tests and benchmarks before deciding whether Phase 2 is complete or needs another evidence-gated optimization.
- Run:
  python -B -m pytest -q -p no:cacheprovider tests/test_benchmark_engine_viewport_variants.py
  python -B tools/benchmark_engine.py --case viewport_frame_loop_dense --repeats 3
  python -B tools/benchmark_engine.py --case viewport_interaction_smoke --repeats 3

Final response must distinguish:
- baseline numbers;
- any optimization numbers;
- QPainter default status;
- OpenGL opt-in status;
- remaining bottleneck.
```
