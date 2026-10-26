# C0dex Prompt: Phase 1 Real OpenGL Viewport Canvas

Use this prompt in a fresh C0dex session to continue VitaLoom Phase 1 without old thread memory.

```text
Do not load old C0dex threads unless the user explicitly asks. Continue from repository files.

You are implementing Phase 1 of the VitaLoom long-term mainline: Real OpenGL viewport canvas.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/superpowers/plans/2026-07-03-vitaloom-baseline-truth-and-tracking-cleanup.md
- docs/superpowers/plans/2026-07-03-real-opengl-viewport-canvas.md
- docs/superpowers/plans/2026-06-30-opengl-viewport-parity-batching.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_render_target.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_gpu_canvas.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py
- tests/test_opengl_viewport_backend.py
- tests/test_opengl_render_target.py
- tests/test_viewport_render_parity.py

Current truth:
- Architecture stays plugin-shaped under FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime.
- PyQt6 remains the editor shell.
- QPainter remains the default viewport backend.
- OpenGL remains opt-in through VITALOOM_VIEWPORT_BACKEND=opengl or the existing explicit GPU request path.
- The previous OpenGL phase proved command/batch/Qt-surface consumption, not a default-ready high-performance shader renderer.
- Phase 1 must create real QOpenGLWidget lifecycle evidence: initializeGL, resizeGL, paintGL, current-context diagnostics, fallback behavior, and pixel/screenshot or skip-safe evidence.
- Do not introduce Unity, Godot, Unreal, Electron, Vulkan, Direct3D, Metal, or a new RHI runtime branch.
- Do not change .pond semantics, AI command flows, Inspector binding, SR2D adapter seams, package manifests, or project manifests.

Work loop:
1. Open the Phase 1 plan and mark the current task.
2. Write the failing test first for the task.
3. Run the test and record the expected failure.
4. Implement the smallest code change that moves the real OpenGL canvas goal forward.
5. Run the focused tests and update docs/mainline_status.md with evidence.
6. Keep skips explicit. A missing GL context is a skip/unavailable state, not a pass.
7. Do not claim OpenGL is default-ready until the plan acceptance checklist is proven.

First recommended task:
- Start with Task 1 in docs/superpowers/plans/2026-07-03-real-opengl-viewport-canvas.md.
- Create tests/test_opengl_canvas.py.
- Create opengl_canvas.py with the injectable lifecycle factory.
- Run:
  python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py

Required verification before a phase-end response:
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B -m pytest -q -p no:cacheprovider tests/test_opengl_canvas.py tests/test_opengl_canvas_smoke.py tests/test_opengl_render_target.py tests/test_opengl_viewport_backend.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py
python -B tools/benchmark_engine.py --case viewport_opengl_render --repeats 3
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans FrameCore tests tools

Final response must distinguish:
- implemented code;
- tests that passed;
- tests skipped because a real GL context was unavailable;
- benchmark numbers actually run;
- what remains before OpenGL can become default.
```
