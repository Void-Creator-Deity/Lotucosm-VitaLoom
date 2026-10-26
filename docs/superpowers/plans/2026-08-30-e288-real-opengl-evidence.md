# E288 -- Real OpenGL Current-Context Pixel, Interaction, Parity, and Benchmark Gate

## Goal

Close the real OpenGL host-adapter evidence loop without changing the default backend policy. The engine remains Qt-free; QPainter and Qt/OpenGL remain host adapters only.

## Scope

- Real `QOpenGLWidget` current-context rendering with a non-empty `ViewportFrameSnapshot`.
- Logical RGBA capture and QPainter parity.
- Multi-frame interaction continuity: pan, zoom, selection, repeated identical frame, and resize.
- End-to-end adapter benchmark with lifecycle teardown evidence.
- Default policy audit: `auto` remains `qpainter` unless native geometry acceleration, parity, and speed gates all pass.

## Verification commands

All commands use the existing project interpreter `.venv\\python.exe`; no environment rebuild, `uv sync`, interpreter switch, or `uv.lock` change was made.

```text
.venv\\python.exe -m pytest -q tests/test_opengl_canvas_smoke.py tests/test_viewport_interaction_continuity.py tests/test_viewport_pixel_parity.py tests/test_benchmark_engine_viewport_variants.py
=> 30 passed, 2 skipped in 57.78s
```

```text
.venv\\python.exe -B tools/benchmark_engine.py --case viewport_adapter_end_to_end --repeats 1
=> completed in 50.07s
```

## Evidence

### Real current-context canvas

A non-empty scene frame produced real pixels through the Qt/OpenGL canvas:

- `qopenglwidget_available=true`
- `qapplication_available=true`
- `initialize_calls=1`
- `resize_calls=1`
- `paint_calls=5`
- `context_current=true`
- `rendered=true`
- `fallback_used=false`
- `draw_mode=qt_texture_blit`
- `gpu_draw_calls=1`
- `non_background_pixels=261`
- `occupied_bounds=[5,15,85,65]`
- `target_snapshot.context_current=true`
- `target_snapshot.fallback_required=false`

### Interaction continuity

A six-frame sequence (base, pan, zoom, selection, repeated selection, resize) produced:

- `completed=true`
- `context_released=true`
- `teardown_errors=[]`
- `target_recreations=6`
- `project_world_mutations=0`
- `plugin_publications=0`
- all six records had `context_current=true`, `fallback_required=false`, and no errors;
- logical digests changed for pan/zoom/selection/resize, remained equal for the repeated frame;
- logical dimensions changed to `[211,137]` on resize;
- pending instance counts matched frame instance counts on every record.

### End-to-end adapter benchmark

Workload: `1280x720`, 360 entities, 269 edges, 630 commands, 46 batches, 630 instances; warmup 1 and measured iterations 3.

- QPainter: ready, mean `1310.21 ms`, no fallback/errors/teardown errors.
- OpenGL: ready, mean `10878.53 ms`, current context true, framebuffer `1920x1080`, logical capture `1280x720`, draw mode `qt_texture_blit`, 3 GPU draw calls, no fallback/errors/teardown errors.
- Pixel parity: `ready=true`; mismatch ratio `0.01771484375`, mean channel error `0.878544`, bounds delta `[1,0,1,1]`, no parity failures.
- Policy decision: selected `qpainter`, `switch_allowed=false`, measured speedup `0.12044` versus required `1.1`; `auto_default_backend=qpainter`.

The benchmark therefore proves real rendering, lifecycle integrity, and parity, while also proving OpenGL is not default-ready: it is slower in this environment and does not provide native geometry acceleration.

## Result

E288 is complete. The next gate is native SR2D build/import provenance, native/fallback parity, and benchmark evidence. Conda/uv environment unification remains intentionally deferred until the mainline architecture and native evidence gates are closed.
