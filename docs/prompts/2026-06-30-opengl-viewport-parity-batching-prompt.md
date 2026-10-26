# C0dex Prompt: OpenGL Viewport Parity And Batching

> **架构状态：已由 2026-07-18 的引擎大插件 Host 架构裁定取代。** 本文件仅保留该历史 GUI 阶段的实施记录；不得据此把 PyQt6/QPainter/OpenGL 视为 L0/L1 架构前提。当前协作约束见 `AGENTS.md`、`CONTEXT.md`、`docs/architecture.md` 与 `docs/prompts/2026-07-18-engine-plugin-host-architecture-reconciliation-prompt.md`。

Use this prompt in a fresh C0dex session. Do not require old thread history.

```text
Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the repository files.

Goal: implement the next GUI/viewport refactor phase: OpenGL viewport parity and batching proof. Keep PyQt6 as the editor shell, keep QPainter as the default backend, keep OpenGL as the only concrete near-term GPU backend, and leave Vulkan/Direct3D/Metal behind future rhi/native_batch targets only.

Current status to verify before editing:
- viewport_draw_commands.py, opengl_batching.py, QPainter command rendering, OpenGL command/batch diagnostics, viewport parity tests, backend selection tests, and viewport benchmark cases may already exist.
- Treat the current worktree as authoritative. Inspect files and tests before assuming this prompt still requires first implementation.
- If the implementation already exists, finish hardening, docs, and verification instead of duplicating modules.

Read first:
- CONTEXT.md
- docs/architecture.md
- docs/suite_architecture.md
- docs/ai_native_command_layer.md
- docs/plugin_command_contract.md
- docs/superpowers/plans/2026-06-30-ai-native-gui-viewport-refactor.md
- docs/superpowers/plans/2026-06-30-opengl-viewport-parity-batching.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_snapshot.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_visual_renderer.py
- tools/benchmark_engine.py
- tests/test_viewport_snapshot.py
- tests/test_qpainter_viewport_backend.py
- tests/test_viewport_backend_selection.py

Required skills:
- Use superpowers:subagent-driven-development or superpowers:executing-plans to implement the plan task-by-task.
- Use superpowers:test-driven-development for every behavior change.
- Use superpowers:systematic-debugging if any test, render, benchmark, or Qt/OpenGL availability failure appears.
- Use superpowers:verification-before-completion before claiming success.

Guardrails:
- Do not migrate the editor to Unity, Godot, Unreal, Electron, or another app shell.
- Do not make OpenGL the default backend in this phase.
- Do not implement Vulkan, Direct3D, or Metal.
- Do not introduce raw platform graphics APIs outside the OpenGL backend.
- Do not let pygame enter the main GUI/runtime path.
- Do not change .pond scene semantics.
- Do not remove QPainter compatibility.
- Do not remove Python fallback from SR2D native work.
- Do not stage, revert, or delete unrelated working-tree changes.

Architecture target:
- ViewportFrameSnapshot remains the immutable source for render-facing data.
- viewport_draw_commands.py compiles deterministic backend-neutral draw commands.
- qpainter_backend.py can render through draw commands while keeping the existing SrVisualRenderer compatibility path.
- opengl_batching.py compiles draw commands into OpenGL-friendly batches without requiring an active GL context.
- opengl_backend.py is an opt-in backend that records command and batch diagnostics and forwards batches only to explicit `draw_opengl_batches(...)` targets.
- graphics_backend_strategy.py keeps VITALOOM_VIEWPORT_BACKEND=auto on QPainter until a later phase explicitly switches default behavior.
- Benchmark cases measure viewport draw-command and batch compilation without opening a GUI window.

Execution order:
1. Implement Task 1 from docs/superpowers/plans/2026-06-30-opengl-viewport-parity-batching.md and verify it.
2. Stop briefly and summarize changed files, passed tests, and any unrelated worktree dirt.
3. Continue through the plan one task at a time.
4. Keep commits optional unless the user explicitly asks for commits.

Acceptance:
- tests/test_viewport_draw_commands.py proves deterministic command compilation.
- tests/test_opengl_batching.py proves batch grouping.
- tests/test_qpainter_draw_command_renderer.py proves QPainter can consume draw commands.
- tests/test_opengl_viewport_backend.py proves OpenGL backend compiles commands/batches and reports stats.
- tests/test_viewport_render_parity.py proves QPainter/OpenGL semantic parity at command/batch level.
- tools/benchmark_engine.py supports viewport_draw, viewport_draw_dense, and viewport_batch_compile cases.
- auto backend selection still returns QPainter.
- OpenGL is opt-in only.

Do not declare OpenGL default-ready from this phase alone. This phase proves semantic command/batch parity. A later phase still needs a real Qt OpenGL draw surface, screenshot/pixel parity, interaction smoke, and unavailable-OpenGL fallback evidence before `auto` can move away from QPainter.

Required verification before final response:
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_snapshot.py tests/test_viewport_draw_commands.py tests/test_opengl_batching.py tests/test_qpainter_viewport_backend.py tests/test_qpainter_draw_command_renderer.py tests/test_opengl_viewport_backend.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py
python -B -m pytest -q -p no:cacheprovider tests/test_gui_boundaries.py tests/test_viewport_profiler.py tests/test_simulation_driver_viewport_tick.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py
python -B tools/benchmark_engine.py --case viewport_draw --repeats 3
python -B tools/benchmark_engine.py --case viewport_draw_dense --repeats 3
python -B tools/benchmark_engine.py --case viewport_batch_compile --repeats 3
git diff --check

Final response must distinguish:
- completed implementation
- verification commands and outputs
- skipped or blocked items
- why QPainter is still default
- what evidence is still required before OpenGL can become auto/default
```

## Follow-up Prompt: QOpenGLWidget Instanced Canvas

Use this prompt when the command/batch phase already exists and the remaining problem is that OpenGL is still "batch to Qt painter surface" rather than a real GPU-backed viewport.

```text
Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the repository files.

Goal: implement the next OpenGL viewport phase inside the existing plugin architecture: add an opt-in QOpenGLWidget/plugin canvas that owns a current GL context and consumes the existing ViewportFrameSnapshot -> viewport_draw_commands -> opengl_batching pipeline through Qt-native shader/instanced drawing. Keep QPainter default. Do not change .pond, AI command layer, SR2D adapter seams, or the plugin-shaped runtime layout.

Current baseline to verify before editing:
- QPainter remains default through VITALOOM_VIEWPORT_BACKEND=auto.
- OpenGL is opt-in through VITALOOM_VIEWPORT_BACKEND=opengl.
- QtOpenGLRenderTarget renders circles/lines/text through a Qt painter surface and reports text_policy=qt_painter_overlay.
- QtOpenGLInstancingTarget exposes QOpenGLFunctions_4_1_Core.glDrawArraysInstanced / glVertexAttribDivisor and reports fallback_no_current_context when no current GL context exists.
- tools/benchmark_engine.py --case viewport_opengl_render reports instancing readiness/fallback state.

Read first:
- docs/cleanup_stabilization_audit.md
- docs/superpowers/plans/2026-06-30-opengl-viewport-parity-batching.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_render_target.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_batching.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py
- tests/test_opengl_render_target.py
- tests/test_opengl_viewport_backend.py
- tests/test_viewport_backend_selection.py
- tests/test_benchmark_engine_viewport_variants.py

Required implementation:
1. Add a plugin-local QOpenGLWidget canvas class or small backend-owned widget adapter; do not move the application to a new GUI framework.
2. In initializeGL(), create/compile/link Qt shader programs, VAO/VBO resources, and the instance buffer needed by QtOpenGLInstancingTarget or a direct target subclass.
3. In paintGL(), build a ViewportFrameSnapshot from the same runtime data and consume existing OpenGL batches. Text may remain QPainter overlay or a documented fallback, but it must not be reported as a placeholder in the live Qt target.
4. Keep QWidget/QPainter canvas as fallback when Qt OpenGL widget creation, shader compile, or context creation fails.
5. Add tests that skip pixel checks when no display/OpenGL context is available, but always pass fallback/selection behavior.
6. Add a diagnostic smoke command or benchmark case that reports context_current=true, shader_program_ready, instance_buffer_ready, gl_functions_ready, gpu_draw_calls, fallback_required, and a small pixel/nonblank signal when a GL context is available.

Guardrails:
- Do not make OpenGL default in this phase.
- Do not add Vulkan/Direct3D/Metal stubs.
- Do not import pygame into the main GUI path.
- Do not stage, commit, revert, or delete unrelated dirty worktree files.
- Keep all new runtime code under FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime.

Required verification before final response:
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_render_target.py tests/test_opengl_viewport_backend.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py tests/test_viewport_render_parity.py
python -B tools/benchmark_engine.py --case viewport_opengl_render --repeats 3
git diff --check

Final response must clearly say whether a real current-context GPU draw was verified on this machine. If no GL context/display is available, report that fallback and tests passed, but do not claim high-performance GPU rendering is complete.
```
