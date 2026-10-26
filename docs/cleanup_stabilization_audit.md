# Cleanup Stabilization Audit

Date: 2026-07-01

This audit records the current cleanup baseline without changing the project architecture. The repository remains a plugin-shaped runtime:

```text
FrameCore
  -> plugins/lotucosm-vitaloom
     -> hub
     -> versions/1.0.0/runtime
```

## Current Working Tree Classes

| Class | Meaning | Action |
|---|---|---|
| `FrameCore/` untracked tree | The migrated plugin/runtime layout and current implementation surface | Treat as product runtime baseline; do not move back to root `core/` or `builtin/` |
| `docs/` untracked plans/specs plus modified `docs/INDEX.md` | Architecture, prompt, and plan materials for the plugin runtime | Keep linked and consistent; avoid conflicting backend/default claims |
| `tests/` untracked focused tests plus modified legacy tests | Regression evidence for plugin runtime, GUI, SR2D, native smoke, and command layer | Use focused suites before broad cleanup |
| `tools/` untracked runtime tools and modified legacy tools | Boundary checks, benchmark runner, export/build helpers, native smoke | Keep checks runnable without native toolchains |
| `native/` untracked tree | Optional C++/Rust native backend scaffolds | Keep optional; Python fallback remains mandatory |
| deleted legacy root files | Old root-level runtime/examples/tool scripts removed by migration | Do not restore unless a boundary check proves a required entrypoint is missing |

## Fixed In This Stabilization Pass

- `GameViewport` now uses the existing `select_viewport_backend(...)` strategy instead of hard-coding QPainter construction.
- `VITALOOM_VIEWPORT_BACKEND=auto` still resolves to QPainter; explicit `opengl` can select the opt-in OpenGL backend when Qt OpenGL is available.
- `DiagnosticOpenGLRenderTarget` consumes OpenGL batches inside the plugin runtime and reports circle, line, text-placeholder, unsupported, draw-call, and pixel-probe diagnostics.
- `QtOpenGLRenderTarget` consumes the same batches through the active Qt painter surface for explicit OpenGL mode and renders text through a Qt painter overlay; this is still a Qt OpenGL surface bridge, not a completed shader renderer.
- `QtOpenGLInstancingTarget` and `probe_qt_opengl_instancing_support()` report Qt shader/buffer/context readiness. The target now exposes the Qt-native `QOpenGLFunctions_4_1_Core.glDrawArraysInstanced` / `glVertexAttribDivisor` seam and only attempts it when a current GL context exists.
- `OpenGLViewportBackend.stats()` records the last target snapshot when a target consumes batches.
- Viewport benchmarks now include `viewport_qpainter_render` and `viewport_opengl_render` in addition to command and batch compilation cases; the OpenGL render case reports text overlay policy and instancing readiness/fallback state.

## Still Intentionally Not Changed

- The project is not converted to Unity, Godot, Unreal, Electron, or a non-plugin layout.
- QPainter is not replaced as the default backend.
- Vulkan, Direct3D, and Metal are not implemented as runtime stubs.
- Text in the diagnostic target remains a placeholder; text in the Qt OpenGL target is rendered through `qt_painter_overlay`.
- The live `GameViewport` canvas is still QWidget/QPainter-backed; a real QOpenGLWidget/plugin canvas plus screenshot or pixel parity is required before claiming default-ready GPU rendering.
- C++/Rust SR2D backends remain optional; missing toolchains must not break Python fallback.
- `tools/build_sr2d_native.py --check-only` reports C++/Rust build commands and missing toolchains without requiring native builds.
- `tools/audit_worktree_groups.py` groups the dirty worktree for deliberate staging; it does not delete, revert, stage, or commit.

## Required Evidence Before Default OpenGL

- Pixel/screenshot parity compares QPainter and OpenGL scenes.
- Pan, zoom, selection, dense-scene interaction, and fallback behavior are covered by smoke tests.
- `tools/check_gui_boundaries.py`, focused viewport tests, SR2D fallback tests, and benchmark cases all pass.
