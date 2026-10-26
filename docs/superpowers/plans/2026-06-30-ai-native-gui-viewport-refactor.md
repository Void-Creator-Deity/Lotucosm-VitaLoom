# AI-Native GUI And Viewport Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Use superpowers:test-driven-development for Python behavior changes and superpowers:verification-before-completion before claiming success.

**Goal:** Turn the VitaLoom editor GUI into an AI-native, command-driven workbench with a replaceable real-time viewport backend.

**Architecture:** Keep PyQt6 as the editor shell for docks, inspectors, project panels, package panels, and command surfaces. Move real-time rendering and simulation coordination behind explicit seams so QPainter becomes a fallback adapter, not the whole runtime. All human GUI actions and AI actions must converge on the existing command layer instead of mutating runtime objects through hidden widget code.

**Tech Stack:** Python 3.11+, PyQt6, pytest, existing FrameCore plugin layout, existing VitaLoom command registry, near-term Qt OpenGL viewport backend, future-compatible graphics abstraction for Vulkan/Direct3D/Metal through Qt RHI or a native renderer layer.

---

## Current Facts

- Main editor GUI is PyQt6, not pygame.
- `pygame` still appears in legacy runtime/builtin modules and must not remain on the main editor/runtime path.
- `core/VitaLoom/viewports/game_viewport.py` is too large and owns too many responsibilities: scene load, timer, tick orchestration, scripts, physics, fluid coupling, HUD, and rendering coordination.
- `core/VitaLoom/viewports/sr_visual_renderer.py` is the current QPainter visual implementation.
- `core/VitaLoom/viewports/sr_gpu_canvas.py` only switches the canvas widget to a Qt OpenGL widget; it does not yet provide GPU batching or a real shader-backed renderer.
- Existing command-layer docs:
  - `docs/ai_native_command_layer.md`
  - `docs/plugin_command_contract.md`
- Existing SR2D native work keeps Python fallback and optional C++/Rust acceleration; GUI refactor must not disturb that seam.
- Graphics API research:
  - Unity supports DirectX, Metal, OpenGL, and Vulkan per platform instead of making gameplay/editor code target only one raw API: <https://docs.unity3d.com/6000.4/Documentation/Manual/GraphicsAPIs.html>.
  - Unreal uses an RHI abstraction over platform APIs such as DirectX 12, Vulkan, and Metal: <https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/RHI>.
  - Godot exposes renderer choices and graphics drivers; its docs describe Vulkan, Direct3D 12, and Metal as modern low-level APIs and OpenGL as the broad compatibility path: <https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html>.
  - Qt `QRhi` is an abstraction over OpenGL, OpenGL ES, Direct3D, Metal, and Vulkan: <https://doc.qt.io/qt-6/qrhi.html>.
  - Qt `QOpenGLWidget` is the lowest-risk near-term bridge for OpenGL rendering inside the existing QWidget editor shell: <https://doc.qt.io/qt-6.11/qopenglwidget.html>.
  - Qt 6 notes that direct `QOpenGLWidget` usage means OpenGL proper at runtime for QWidget/QWindow applications; Qt Quick has broader RHI backend support: <https://doc.qt.io/qt-6/opengl-changes-qt6.html>.

## Graphics API Decision

- **Selected near-term API: OpenGL.** For this repository, pick one concrete GPU path now: `OpenGLViewportBackend` embedded through Qt widgets. It fits the current PyQt6/QWidget editor shell, can be introduced incrementally beside QPainter, has simple smoke-test and fallback behavior, and is easier for AI agents to read, patch, and debug than raw Vulkan, Direct3D 12, or Metal.
- **Default behavior remains QPainter until parity exists.** The implementation order is `QPainterViewportBackend` first, then opt-in `OpenGLViewportBackend`, then make OpenGL default only after visual parity and performance evidence.
- **Mainstream engine lesson:** Unity, Unreal, Godot, and Qt do not make high-level editor/game code call every raw graphics API directly. They put a renderer/RHI abstraction above platform backends. We should copy that shape, but only implement one real backend in this phase.
- **Why not Vulkan first:** Vulkan has a higher performance ceiling and good cross-platform reach, but it requires explicit device, queue, swapchain, synchronization, descriptor, shader, and memory-management code. That surface is too large for the first GUI refactor while the scene snapshot, command inspector, profiler, and backend contracts are still moving.
- **Why not Direct3D first:** Direct3D 12 is excellent on Windows, but it locks the first implementation to Windows-specific APIs and does not match the current Python/PyQt cross-platform shell. It is a future native backend candidate if Windows shipping performance becomes the dominant goal.
- **Why not Metal first:** Metal is the right native choice on Apple platforms, but it is Apple-only and does not fit the current Windows-focused workstation evidence. It belongs behind a future RHI/native renderer, not in the first pass.
- **Long-term route:** keep `ViewportBackend` as our internal abstraction and reserve `rhi`/`native_batch` as future backend kinds. If the editor later moves to Qt Quick/QRhi or a native C++ renderer layer, Vulkan, Direct3D, and Metal can sit underneath the same snapshot/backend contract.
- **Performance rule:** first win by batching draw calls, reducing Python per-entity work, and moving hot loops/native kernels. Graphics API choice is second-order until the renderer stops sending many small CPU-side QPainter operations every frame.

## Target Shape

```text
PyQt Editor Shell
  -> command panels, docks, inspector, package manager, logs
  -> ViewportHost
       -> SimulationDriver
       -> ViewportSnapshotBuilder
       -> ViewportBackend interface
            -> QPainterViewportBackend
            -> OpenGLViewportBackend
            -> future RhiViewportBackend
            -> future external engine runner
```

## File Structure

- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
  - Keep as the QWidget host and compatibility facade during this refactor.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_backend.py`
  - Owns `ViewportBackend` protocol and backend capability metadata.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_snapshot.py`
  - Owns immutable render snapshot data extracted from runtime entities.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_profiler.py`
  - Owns per-frame timing buckets and rolling averages.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py`
  - Wraps current QPainter drawing through `SrVisualRenderer`.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/simulation_driver.py`
  - Owns the high-level SR tick phases currently embedded in `GameViewport`.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/schema.py`
  - Owns schema-driven inspector field models.
- Create `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/command_binding.py`
  - Owns conversion from inspector edits to command-layer operations.
- Create `tools/check_gui_boundaries.py`
  - Checks legacy pygame and forbidden direct mutation patterns on the main GUI path.
- Add focused tests under `tests/`.

---

### Task 1: Lock GUI Main-Path Boundaries

**Files:**
- Create: `tools/check_gui_boundaries.py`
- Create: `tests/test_gui_boundaries.py`
- Modify: `docs/INDEX.md`

- [ ] Add a boundary checker that scans the main editor/runtime GUI path for direct `pygame` imports.
- [ ] Allow legacy pygame only in explicitly listed legacy modules under `runtime/builtin`.
- [ ] Add a test that fails if `core/VitaLoom` or `core/Lotucosm/sr_*` start importing pygame directly on the main path.
- [ ] Document this checker in `docs/INDEX.md`.

Verification:

```bash
python -B tools/check_gui_boundaries.py
python -B -m pytest -q -p no:cacheprovider tests/test_gui_boundaries.py
```

### Task 2: Add Viewport Snapshot Model

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_snapshot.py`
- Create: `tests/test_viewport_snapshot.py`

- [ ] Define immutable dataclasses for `ViewportEntitySnapshot`, `ViewportEdgeSnapshot`, `ViewportFrameSnapshot`, and `ViewportCameraSnapshot`.
- [ ] Add a snapshot builder that copies primitive values from scene entities without storing live entity objects.
- [ ] Cover missing optional fields by using stable defaults for id, type, position, velocity, radius, and visual state.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_snapshot.py
```

### Task 3: Add Viewport Backend Interface

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_backend.py`
- Create: `tests/test_viewport_backend_contract.py`

- [ ] Define a small `ViewportBackend` protocol with `render(...)`, `resize(...)`, `set_quality(...)`, and `stats()` methods.
- [ ] Define `ViewportBackendInfo` with name, supports_gpu, supports_batching, and fallback_reason fields.
- [ ] Add a no-op test backend for contract tests.
- [ ] Keep the interface independent from `.pond`, `GameViewport`, and live runtime entities.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_backend_contract.py
```

### Task 4: Wrap Current QPainter Renderer As A Backend

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/qpainter_backend.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
- Create: `tests/test_qpainter_viewport_backend.py`

- [ ] Move calls to `SrVisualRenderer.paint_frame(...)` behind `QPainterViewportBackend.render(...)`.
- [ ] Keep existing visual behavior unchanged while the backend is selected.
- [ ] Add a smoke test with a fake painter or monkeypatched renderer to prove `GameViewport` delegates rendering through the backend seam.
- [ ] Keep QPainter as the default backend until a GPU backend has visual parity.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_qpainter_viewport_backend.py
python -B -m pytest -q -p no:cacheprovider tests/test_game_viewport_unified_bridge.py tests/test_scene_viewport_command_bridge.py
```

### Task 5: Add Frame Profiler Buckets

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/viewport_profiler.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
- Create: `tests/test_viewport_profiler.py`

- [ ] Track rolling milliseconds for script, spawn, fluid, physics, render, and total frame time.
- [ ] Expose profiler state as plain dictionaries so HUD, tests, logs, and AI diagnostics can consume it.
- [ ] Add a guard so profiler instrumentation cannot raise during gameplay.
- [ ] Do not optimize yet; this task only makes evidence visible.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_profiler.py
```

### Task 6: Extract Simulation Driver

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/simulation_driver.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py`
- Create: `tests/test_simulation_driver_viewport_tick.py`

- [ ] Move high-level SR tick orchestration out of `GameViewport` without changing tick order.
- [ ] Keep the current order: input, script batches, spawn/removal, actuator coupling, fluid/field, SR2D physics, survival/removal, snapshots/HUD.
- [ ] Let `GameViewport` pass context and dependencies into `SimulationDriver`; the driver must not import PyQt widgets.
- [ ] Add tests for tick order using monkeypatched phase functions.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_driver_viewport_tick.py
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py tests/test_game_viewport_play_goals.py
```

### Task 7: Add Schema-Driven Inspector Field Model

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/schema.py`
- Create: `tests/test_inspector_schema.py`
- Modify only after tests pass: existing inspector modules that already own property display.

- [ ] Define `InspectorField` and `InspectorSection` dataclasses with field id, label, type, value, editable flag, source path, and validation metadata.
- [ ] Build field sections from entity/component metadata where available.
- [ ] Fall back to safe primitive fields for entities without component metadata.
- [ ] Keep UI widget creation out of this module; it only returns field models.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_inspector_schema.py tests/test_inspector_property_mapping.py
```

### Task 8: Bind Inspector Edits To Commands

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/inspector/command_binding.py`
- Create: `tests/test_inspector_command_binding.py`
- Modify: command registry or inspector modules only where the existing command path requires it.

- [ ] Convert field edits into command payloads instead of direct widget-to-entity mutation.
- [ ] Support rejection with structured error messages when a field is read-only or validation fails.
- [ ] Ensure the same command payload can be emitted by GUI, CLI, MCP, or AI agent code.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_inspector_command_binding.py tests/test_command_registry.py tests/test_plugin_command_contributions.py
```

### Task 9: Prepare Graphics Backend Selection Without Replacing Behavior

**Files:**
- Create or modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py`
- Create or modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/graphics_backend_strategy.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/sr_gpu_canvas.py`
- Create: `tests/test_viewport_backend_selection.py`

- [ ] Add backend selection with `VITALOOM_VIEWPORT_BACKEND=qpainter|opengl|rhi|auto`.
- [ ] Keep `auto` on QPainter until OpenGL render parity tests exist.
- [ ] If OpenGL widgets are unavailable, return a clear fallback reason.
- [ ] Keep `rhi` as a planned backend kind with a clear `not_available` fallback reason unless a real RHI adapter exists.
- [ ] Do not implement raw Vulkan, Direct3D, or Metal in this task. They must only appear behind future `rhi` or `native_batch` adapters.
- [ ] Do not introduce shader rendering in this task; only add the safe selection seam and strategy metadata.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_backend_selection.py
```

### Task 10: Final Verification And Docs

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/suite_architecture.md`
- Modify: `docs/ai_native_command_layer.md`
- Modify: `docs/INDEX.md`

- [ ] Document the editor shell, viewport backend seam, schema-driven inspector, and pygame legacy rule.
- [ ] Run focused GUI, command, viewport, and SR2D tests.
- [ ] Run guardrails and compile checks.
- [ ] Record remaining limitations: QPainter is still fallback/default, OpenGL backend is selection-only until visual parity exists, and native SR2D may still be unavailable on machines without toolchains.

Verification:

```bash
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools
python -B -m pytest -q -p no:cacheprovider tests/test_gui_boundaries.py tests/test_viewport_snapshot.py tests/test_viewport_backend_contract.py tests/test_qpainter_viewport_backend.py tests/test_viewport_profiler.py tests/test_simulation_driver_viewport_tick.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py tests/test_viewport_backend_selection.py
python -B -m pytest -q -p no:cacheprovider tests/test_command_registry.py tests/test_scene_viewport_command_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_sr_physics2d_adapter_contract.py
git diff --check
```

## Self-Review Notes

- This plan does not choose Unity, Godot, or any external engine as the primary editor GUI.
- This plan preserves PyQt6 as the editor shell while preventing PyQt/QPainter from owning the whole real-time runtime.
- This plan makes AI automation first-class by routing GUI edits through command payloads and schema-derived field models.
- This plan keeps a fallback path at every stage so the editor can keep running during the refactor.
- This plan chooses OpenGL as the first GPU bridge because it is the lowest-risk Qt/Python integration path. Vulkan, Direct3D, and Metal remain future backend targets behind an abstraction, not direct dependencies of the editor shell.
