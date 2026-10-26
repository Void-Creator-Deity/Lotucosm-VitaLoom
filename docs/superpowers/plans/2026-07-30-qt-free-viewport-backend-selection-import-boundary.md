# Phase E61 -- Qt-Free Viewport Backend Selection Import Boundary

Date: 2026-07-30
Status: completed

## Previous gate

E60 mapped the PyQt6/QPainter/OpenGL Editor host boundary. It found that the
immutable snapshot, command, batch, capture, parity, and backend contracts are
already Qt-free, while `sr_gpu_canvas.py` eagerly imported `QWidget` even when
only backend-selection modules were being loaded.

## Objective

Remove that eager import from the optional concrete SR OpenGL canvas wrapper.
Selection and immutable viewport-contract imports must remain usable before a
Qt host is chosen. Actual `QOpenGLWidget` probing and canvas construction must
remain lazy, concrete Adapter-local behavior.

## Implementation

- Replaced the runtime `QWidget` import in `viewports/sr_gpu_canvas.py` with a
  `TYPE_CHECKING`-only type reference and `Any` for the optional canvas class
  cache.
- Preserved `_probe_opengl_widget()` as the sole lazy point that imports
  `PyQt6.QtOpenGLWidgets.QOpenGLWidget`.
- Added a fresh `-S` interpreter regression in
  `tests/test_viewport_backend_selection.py`. It imports both the selection
  module and the concrete optional canvas wrapper, then proves no `PyQt6` module
  has been loaded.

## Non-goals

This phase does not create another backend registry, Host, renderer, widget
framework, or application shell. It does not change `auto` selection, real
OpenGL rendering, QPainter behavior, project semantics, plugin authority, or
OpenGL default readiness.

## Evidence

- Fresh interpreter import-boundary/selection suite: `8 passed in 0.47s`.
- Expanded viewport selection/render/capture/parity/interaction/OpenGL/QPainter/
  benchmark suite: `60 passed, 2 skipped in 26.87s`.
- Full project-local Qt regression excluding the separate signature collection:
  `1663 passed, 34 skipped, 34 subtests passed in 211.84s`.
- Standard/eager offscreen Editor smokes passed at `plugins=13/20` and
  `plugins=20/20`; project-plugin-model, core-boundary, GUI-boundary, and
  release-consistency guardrails all passed.
- The signature-only collection passed independently in the shared interpreter:
  `2 passed in 0.67s`. The project-local Qt environment still lacks
  `cryptography` for that one collection, which is an interpreter dependency
  split rather than a product failure.

## Closure

E61 is complete. The unique next gate is E62: Legacy Editor Shell
Command-and-State Boundary Discovery. Audit one bounded cut around EditorKernel
and LayoutManager command/state ownership before attempting any host migration.
