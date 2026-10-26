# Phase E60 -- Legacy Editor Host Rendering Boundary Discovery and Migration-Readiness Audit

Date: 2026-07-30
Status: completed

## Previous gate

E59 completed the public legacy UI-interface authority audit. The four legacy
UI types are quarantined to their public compatibility module; full isolated Qt
regression passed and all four guardrails passed.

## Scope

Map the existing PyQt6/QPainter/OpenGL editor-host seams: application startup,
layout management, dock/viewport payload projection, rendering canvases,
interaction handling, and smoke/pixel evidence. Classify each seam as already
Qt-free, Adapter-local, or still host-coupled. Identify the smallest safe next
extraction or parity proof; do not implement a replacement UI host in this
audit phase.

## Source-level boundary table

| Seam | Primary implementation | Classification | Evidence / limit |
|---|---|---|---|
| Product startup and smoke | `runtime/main.py` | Host-coupled composition | Creates `QApplication`, `EditorKernel`, and runs the current Qt smoke route. It is not an engine root. |
| Editor window and workspace | `kernel/editor_kernel.py`, `kernel/layout_manager.py` | Host-coupled | `EditorKernel` inherits `QMainWindow`; layout, docks, tabs, actions, geometry, and stylesheet application remain legacy Qt shell behavior. |
| Plugin editor payloads | `kernel/legacy_editor_plugin_adapter.py` | Adapter-local | The single Adapter projects copied `editor_contributions` and bounded legacy payloads into concrete Qt docks/viewports/themes. Runtime Host metadata remains the authority. |
| Immutable frame input | `viewports/viewport_snapshot.py`, `viewport_draw_commands.py`, `opengl_batching.py`, `viewport_pixel_capture.py`, `viewport_pixel_parity.py` | Qt-free | Immutable snapshots, draw commands, batches, logical RGBA facts, and parity decisions carry no Qt object. |
| Backend contract and compilation | `viewports/viewport_backend.py`, `opengl_backend.py`, `qpainter_backend.py` | Qt-free contract with Adapter rendering implementation | `ViewportBackend` accepts an immutable frame; OpenGL command compilation is plain data. QPainter execution is still a concrete host rendering path. |
| QPainter capture | `qpainter_capture.py`, `QPainterDrawCommandRenderer` | Adapter-local | Native `QImage`/`QPainter` are translated to Qt-free RGBA evidence only at this boundary. |
| Current-context OpenGL | `opengl_canvas.py`, `opengl_render_target.py`, `sr_gpu_canvas.py` | Adapter-local | `QOpenGLWidget` lifecycle and texture blit require a live Qt context. Probe results are serialized as plain data, including logical capture and framebuffer facts. |
| Game and scene interaction | `game_viewport.py`, `scene_viewport.py` | Still host-coupled | QWidget paint/input events, SR HUD/chrome, scene selection, drag/drop, menus, and direct widget state remain legacy editor-shell behavior. |
| Player shell | `player/player_shell.py` | Separate host-coupled shell | It is Qt shell code but not an EditorKernel/LayoutManager authority. It must not be folded into a new editor host. |

## Evidence collected

- Focused rendering/selection/capture/parity/interaction/OpenGL/QPainter/benchmark
  suite: `59 passed, 2 skipped in 30.01s` in the project-local Qt environment.
- A real Windows current-context probe rendered a representative immutable scene
  in an isolated process: `rendered=true`, `context_current=true`,
  `context_released=true`, `fallback_used=false`, `gpu_draw_calls=1`, and
  `980` non-background physical framebuffer pixels.
- The immutable interaction sequence changed logical frame digests across pan
  and zoom, preserved identical repeated-frame output, recreated targets, and
  released context without Project World mutations or plugin publications.
- End-to-end benchmark comparison was comparable and pixel-parity-ready, but
  retained QPainter as the default. The recorded OpenGL route was a Qt worker
  texture-blit path with `native_geometry_acceleration=false` and measured
  speedup `0.0182x`; it is therefore not default-ready.

## Decision

Do not introduce a replacement host, renderer framework, or new lifecycle
authority. The smallest safe extraction is an import boundary only: make the
optional SR OpenGL canvas wrapper lazy with respect to PyQt so the viewport
selection/immutable contract modules can load in a fresh interpreter without
loading PyQt. Keep actual `QOpenGLWidget` probing and canvas creation inside the
concrete Adapter-local path. This is Phase E61.

## Closure

E60 is complete. The unique next gate is E61: Qt-Free Viewport Backend Selection
Import Boundary. It must preserve the one current Qt Adapter, make no default
backend change, and prove a fresh selection import does not load PyQt.
