> **Closed on 2026-07-23.** E32 completed with final full non-signature `1412 passed, 34 skipped, 34 subtests passed`, Editor smoke `plugins=13/20`, and all four guardrails green. Continue with [the E33 fresh-session prompt](2026-07-23-qt-free-editor-contribution-contract-replacement-host-readiness-prompt.md); do not restart E32 Task 5.

# Phase E32 Fresh-Session Prompt -- Real Current-Context OpenGL Pixel, Interaction, and Benchmark Parity for Host-Adapter Readiness

Date: 2026-07-21

Begin by reading `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, the completed E31 plan, the E32 plan, the June OpenGL parity/batching plan, viewport backend/canvas/render-target Modules, and current tests. Do not infer architecture from the legacy PyQt editor.

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

VitaLoom is a self-developed Unity/Godot-class engine. PyQt6/QPainter/current Qt OpenGL are legacy/current UI Host Adapters only. Do not create a second Host, registry, manifest authority, composition root, renderer framework, UI framework, or peer FrameCore product plugin. A future UI-host replacement must preserve the same Qt-free L0-L4 contracts and prove its own parity.

## Previous Gate summary

E31 is complete:

- supported scikit-build-core/CMake `<4`/Ninja packaging route;
- VS 2022 x64 discovered without local product paths;
- real `cp311-cp311-win_amd64` wheel built and structurally inspected;
- isolated `python -S` import and callable C++ kernel proved;
- clean no-native Python fallback and explicit C++ failure proved;
- packaged Python-oracle parity: `14 passed`;
- focused `196 passed, 31 skipped, 17 subtests passed`;
- full non-signature `1366 passed, 39 skipped, 34 subtests passed`;
- Editor smoke `plugins=13/20`; all four architecture guardrails passed;
- signature-only collection remains blocked by missing `cryptography`.

## Unique Gate

**Phase E32 -- Real Current-Context OpenGL Pixel, Interaction, and Benchmark Parity for Host-Adapter Readiness.**

Follow the E32 plan. Establish red tests before production changes, then prove:

1. explicit OpenGL captures real non-background framebuffer pixels in a current context without diagnostic/QPainter fallback;
2. representative snapshots rendered through QPainter and OpenGL satisfy documented pixel parity tolerances;
3. resize, pan/zoom, selection, repeated frames, target recreation, and deterministic teardown work through public seams;
4. comparable end-to-end QPainter/OpenGL benchmark evidence exists;
5. `auto` remains QPainter unless parity and measurements justify a change;
6. no Qt widget/GL object/live scene instance leaks into the Qt-free viewport Interface;
7. focused/full regressions, real Editor smoke, and all four architecture guardrails pass.

Attempt signature-only collection and record the missing-`cryptography` blocker unless installation is separately approved. Update the E32 plan, `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and create exactly one next prompt at closure.

The persistent objective `彻底完善` remains active. Do not claim replacement UI Host completion, all-platform packaging, signature verification, or the whole engine complete.

## Current checkpoint (2026-07-21)

E32 Tasks 1, 2, 3, and 4 are complete. Do not repeat framebuffer truth, per-scene logical parity, interaction continuity, or benchmark-policy construction.

- Task 1 proved real current-context non-background framebuffer pixels, strict fallback/error rejection, deterministic capture evidence, and DPR-aware physical sizing.
- Task 2 added Qt-free capture/parity evidence and corrected semantic batch order to `edges -> entity bodies -> selected overlays -> text` while preserving the dense `46`-batch contract.
- Task 3 added immutable camera projection, zoom-scaled geometry/strokes, six-frame interaction/recreation proof, explicit teardown, context release, and zero Project World/plugin-publication side effects.
- Task 4 added Qt-free `benchmark_viewport_adapters()` and CLI case `viewport_adapter_end_to_end`. Both concrete Adapters receive identical snapshots, dimensions, warmup, iterations, alternating order, logical RGBA capture/readback, and recreate/render/capture/teardown lifecycle.
- Formal dense evidence (`1280x720`, `360` entities, `269` edges, `630` commands, `46` batches/`630` instances): outer repeats mean/min/max `24388.677/24279.632/24571.054 ms`; last inner QPainter mean `588.461 ms`; OpenGL mean `5234.932 ms`; parity ready; no fallback/errors; context released.
- Measured ratio is `0.112410x`, below required `1.10x`, and OpenGL still reports `native_geometry_acceleration=false`. Policy correctly keeps `selected=qpainter`, `switch_allowed=false`; runtime `auto` remains QPainter.
- Sequential E32 regression exposed and fixed probe `QApplication` lifetime locality. Expanded E32 regression is `92 passed, 2 skipped`; all four architecture guardrails pass.

Continue with exactly one Gate: **E32 Task 5 -- full regression, real Editor smoke, signature attempt, architecture guardrails, and E32 closure.**

Run Project World, `.pond`, AI command/Inspector, SR2D, package/manifests, Player/export, plugin reload/startup/shutdown regressions, then the full non-signature suite and real Editor smoke. Attempt signature-only collection without silently installing dependencies; if `cryptography` is still absent, record the exact blocker and unblock path. Re-run all four guardrails, update the E32 plan/status/context/index, and select exactly one verified next mainline Gate only after E32 closes. Do not claim replacement UI Host completion, native geometry acceleration, all-platform readiness, signature verification, or the whole engine complete.
