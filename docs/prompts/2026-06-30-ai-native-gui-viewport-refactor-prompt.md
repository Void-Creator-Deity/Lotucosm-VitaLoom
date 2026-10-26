# C0dex Prompt: AI-Native GUI And Viewport Refactor

> **架构状态：已由 2026-07-18 的引擎大插件 Host 架构裁定取代。** 本文件仅保留该历史 GUI 阶段的实施记录；不得据此把 PyQt6/QPainter/OpenGL 视为 L0/L1 架构前提。当前协作约束见 `AGENTS.md`、`CONTEXT.md`、`docs/architecture.md` 与 `docs/prompts/2026-07-18-engine-plugin-host-architecture-reconciliation-prompt.md`。

Use this prompt in a fresh C0dex session. Do not require old thread history.

```text
Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the repository files.

Goal: refactor the VitaLoom GUI into an AI-native editor workbench. Keep PyQt6 as the editor shell, quarantine pygame as legacy, move real-time rendering behind a ViewportBackend seam, choose OpenGL as the only concrete near-term GPU API, keep Vulkan/Direct3D/Metal as future RHI/native-backend targets only, and route inspector edits through schema-derived command payloads.

Read first:
- CONTEXT.md
- docs/architecture.md
- docs/suite_architecture.md
- docs/ai_native_command_layer.md
- docs/plugin_command_contract.md
- docs/superpowers/plans/2026-06-30-ai-native-gui-viewport-refactor.md
- FrameCore/plugins/lotucosm-vitaloom/plugin_manifest.json
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/version_manifest.json
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_visual_renderer.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_render_perf.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_gpu_canvas.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/docks/inspector.py
- tests/test_scene_viewport_command_bridge.py
- tests/test_game_viewport_unified_bridge.py
- tests/test_inspector_property_mapping.py

Required skills:
- Use superpowers:subagent-driven-development or superpowers:executing-plans to implement the plan task-by-task.
- Use superpowers:test-driven-development for every behavior change.
- Use superpowers:systematic-debugging if any performance, rendering, or test failure appears.
- Use superpowers:verification-before-completion before claiming success.

Guardrails:
- Do not migrate the editor to Unity, Godot, Unreal, Electron, or a new app framework in this phase.
- Keep PyQt6 as the editor shell for docks, panels, commands, and project/package UI.
- Do not let pygame remain on the main editor/runtime path. Legacy pygame modules may remain only when explicitly allowlisted by tools/check_gui_boundaries.py.
- Do not change .pond scene semantics.
- Do not break GameViewport public behavior while extracting seams.
- Do not make OpenGL the default until QPainter/OpenGL visual parity exists.
- Do not implement raw Vulkan, Direct3D, or Metal in this phase.
- Do not build parallel Vulkan, Direct3D, or Metal stubs that look production-ready. The only real GPU backend to implement in this phase is OpenGL.
- Represent Vulkan/Direct3D/Metal only through a future `rhi` or `native_batch` backend kind with clear fallback metadata.
- Do not remove Python fallback from SR2D native work.
- Do not stage, revert, or delete unrelated working-tree changes.

Architecture target:
- GameViewport becomes a host/facade, not the owner of all simulation and rendering behavior.
- ViewportSnapshotBuilder copies live scene entities into primitive render snapshots.
- ViewportBackend owns render calls. QPainterViewportBackend wraps the existing SrVisualRenderer first.
- OpenGLViewportBackend is the first and only concrete GPU bridge in this phase because it is the lowest-risk Qt/Python integration path.
- RhiViewportBackend is a future abstraction target for Vulkan, Direct3D, and Metal; it must not be implemented as a raw multi-API renderer in this phase.
- Mainstream engine pattern to follow: high-level code talks to a renderer/RHI abstraction, while platform graphics APIs sit behind it. Do not make GameViewport or inspector code know about OpenGL, Vulkan, Direct3D, or Metal directly.
- SimulationDriver owns SR tick orchestration without importing PyQt widgets.
- Inspector schema modules produce field models from entity/component metadata.
- Inspector command binding converts GUI edits into command-layer payloads that GUI, CLI, MCP, and AI agent code can share.

Execution order:
1. Implement Task 1 from docs/superpowers/plans/2026-06-30-ai-native-gui-viewport-refactor.md and verify it.
2. Stop and summarize what changed, what tests passed, and whether the worktree has unrelated changes.
3. Continue through the plan one task at a time, verifying after each task.
4. Keep commits optional unless the user explicitly asks for commits.

Acceptance:
- tools/check_gui_boundaries.py exists and passes.
- The main GUI path has an enforceable no-pygame guardrail.
- Viewport snapshot dataclasses exist and tests prove they do not store live entity objects.
- ViewportBackend protocol exists and QPainterViewportBackend delegates to the existing renderer.
- Frame profiler reports script, spawn, fluid, physics, render, and total buckets without crashing gameplay.
- SimulationDriver exists and preserves current SR tick ordering.
- Inspector schema and command binding exist, with tests proving GUI edits can become command payloads.
- VITALOOM_VIEWPORT_BACKEND=qpainter|opengl|rhi|auto selection exists, with QPainter remaining default.
- `rhi` reports a clear not-available/future-backend reason unless a real abstraction backend exists.
- OpenGL is the only concrete GPU backend attempted. Vulkan, Direct3D, and Metal are documented future backend targets, not implementation work for this prompt.
- Existing SR2D adapter tests continue passing.

Required verification before final response:
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools
python -B -m pytest -q -p no:cacheprovider tests/test_gui_boundaries.py tests/test_viewport_snapshot.py tests/test_viewport_backend_contract.py tests/test_qpainter_viewport_backend.py tests/test_viewport_profiler.py tests/test_simulation_driver_viewport_tick.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py tests/test_viewport_backend_selection.py
python -B -m pytest -q -p no:cacheprovider tests/test_command_registry.py tests/test_scene_viewport_command_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_sr_physics2d_adapter_contract.py
git diff --check

Final response must distinguish:
- completed implementation
- verification commands and outputs
- skipped or blocked items
- native/OpenGL limitations that remain
- why OpenGL was selected as the single near-term API, and why Vulkan/Direct3D/Metal were deferred behind a future RHI/native layer
```
