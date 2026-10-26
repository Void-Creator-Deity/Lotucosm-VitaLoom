# Phase E32 -- Real Current-Context OpenGL Pixel, Interaction, and Benchmark Parity for Host-Adapter Readiness

Date: 2026-07-21
Status: complete (2026-07-23)

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

VitaLoom is a self-developed Unity/Godot-class engine. PyQt6, QPainter, and the current Qt/OpenGL canvas are concrete legacy/current UI Host Adapters. They are not L0/L1 roots, extension authorities, manifest authorities, or future framework rule sources. E32 must deepen evidence at the existing Qt-free `ViewportFrameSnapshot` / draw-command / `ViewportBackend` seams; it must not create a second Host, registry, renderer framework, composition root, plugin root, or direct native access to scene/editor objects.

## Previous Gate summary

E31 is complete:

- scikit-build-core now constrains CMake to `>=3.18,<4`, provisions Ninja `>=1.11`, and fails closed instead of silently changing generators;
- the package verifier discovers VS 2022 x64 MSVC through `vswhere`, forces Ninja, and uses an ephemeral backend build directory without machine-local product paths;
- a real `cp311-cp311-win_amd64` wheel built, passed structural inspection, installed into an isolated target, imported callable `step_pvaec_circles` through `python -S`, and passed packaged parity (`14 passed`);
- a clean no-native `python -S` process selected the Python Adapter and explicit unavailable C++ failed loudly;
- focused regression was `196 passed, 31 skipped, 17 subtests passed`; full non-signature was `1366 passed, 39 skipped, 34 subtests passed`; Editor smoke and all four architecture guardrails passed;
- signature-only collection remains blocked by missing `cryptography`.

## Current audit baseline

1. `ViewportFrameSnapshot` and `viewport_draw_commands.py` already provide immutable, Qt-free frame facts and deterministic commands.
2. `QPainterViewportBackend` and `OpenGLViewportBackend` are two concrete Adapters at the viewport seam; `auto` intentionally remains QPainter.
3. Existing OpenGL tests prove command/batch semantics, diagnostic target consumption, and a current-context canvas smoke when the environment permits it.
4. Existing OpenGL smoke primarily proves command/instance counts and context presence. It does not yet prove a captured non-empty framebuffer, per-scene pixel parity against the QPainter oracle, resize/pan/zoom/selection interaction continuity, or comparable end-to-end render timing.
5. Existing documentation explicitly forbids declaring OpenGL default-ready until real pixels, parity, interaction smoke, and benchmark evidence exist.
6. A future replacement UI Host must consume the same Qt-free L0-L4 contracts and show its own rendering/parity evidence. E32 prepares that evidence surface but does not select or implement a replacement shell.

## Implementation plan

### Task 1 -- Establish real-pixel red tests and environment truth

- Audit `opengl_canvas.py`, `opengl_render_target.py`, backend selection, and existing smoke probes.
- Add a real current-context capture Interface returning plain-data evidence: dimensions, format, non-background pixel count, alpha coverage, deterministic digest, fallback state, and errors.
- Add red tests that fail if explicit OpenGL reports success without a current context, silently uses the diagnostic/QPainter fallback, or produces an all-background frame.
- Keep environment-unavailable outcomes explicit. E32 cannot close on skipped current-context pixel evidence in the controlled Windows environment.

### Task 2 -- Pixel parity through the existing viewport seam

- Define deterministic reference scenes: empty, single entity, selected outline, hard edge, hidden entity, resize case, and dense scene.
- Render the same immutable snapshots/commands through QPainter and OpenGL Adapters into captureable targets.
- Compare dimensions, occupied bounds, alpha/non-background coverage, stable hashes where exactness is appropriate, and documented tolerance metrics where rasterization differs.
- Do not widen the Interface to expose Qt widgets, GL objects, SceneManager, EditorContext, or live entity instances.

### Task 3 -- Interaction continuity smoke

- Exercise resize, camera pan/zoom, selection outline, repeated frames, and target recreation through the public viewport/canvas seams.
- Prove that interaction state changes produce the expected new snapshots/pixels without stale batches, context leaks, duplicate plugin publication, or direct Project World mutation from the renderer.
- Include deterministic teardown and context release proof.

### Task 4 -- Comparable benchmark and policy decision

- Add exact workload benchmarks for QPainter and real current-context OpenGL using the same scenes, dimensions, warmup, iterations, and capture policy.
- Record frame time, commands, batches, instances, draw calls, pixel-capture cost, and fallback state.
- Keep `auto -> QPainter` unless real parity passes and measured OpenGL behavior justifies an explicit policy change. A faster command compiler or diagnostic target is not GPU render evidence.

### Task 5 -- Regression, architecture guardrails, and closure

- Run focused viewport/backend/canvas/parity/interaction tests and benchmark contract tests.
- Run Project World, `.pond`, AI command/Inspector, SR2D, package/manifests, Player/export, plugin reload/startup/shutdown regressions.
- Run the full non-signature suite, real Editor smoke, and project/core/GUI/release guardrails.
- Attempt signature-only collection and record the `cryptography` blocker unless dependency installation is separately approved.
- Update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, this plan, and create one next fresh-session prompt.

## Completion bar

E32 is complete only when:

1. real current-context OpenGL pixels are captured in the controlled environment without silent fallback;
2. representative scenes pass documented QPainter/OpenGL pixel parity tolerances;
3. resize, pan/zoom, selection, repeated-frame, recreation, and teardown smoke pass;
4. comparable end-to-end benchmark evidence exists and identifies whether `auto` should remain QPainter or may safely change;
5. Qt-free viewport Interfaces and the recursive L0-L4 framework-plugin topology remain intact;
6. focused/full regressions, Editor smoke, and all four architecture guardrails pass.

Command counts, diagnostic buffers, a context flag without pixels, skipped current-context tests, or a benchmark that excludes real draw/capture work are insufficient.

## Preserved contracts

Do not break `.pond` scene semantics, AI command registry flows, Inspector binding, SR2D seams, package/project manifests, Project World L4 lifecycle, Player/export, plugin reload/startup/shutdown, or the one L0/one L1 recursive plugin-host topology. Do not stage, commit, revert, clean, delete, or overwrite unrelated dirty work.

## Unique next Gate after E32

Not selected yet. E32 must first produce real current-context pixel, interaction, and benchmark evidence before choosing one next verified engine gap.

## Implementation checkpoint 1 -- strict framebuffer truth (2026-07-21)

Task 1 is complete, but Phase E32 is not complete.

- The former smoke result was disproved: a real current context reported 46 nominal draw calls while all 17,280 captured pixels were only the declared clear colour. The old `rendered=true` claim was therefore false.
- `viewport_capture_evidence.py` now defines a Qt-free plain-data evidence Module: dimensions, RGBA format, full pixel count, non-background coverage, alpha coverage, occupied bounds, deterministic SHA-256 digest, current-context state, fallback state, draw mode, GPU draw count, and explicit errors.
- `viewport_rgba_rasterizer.py` deterministically consumes the existing Qt-free `OpenGLBatch` facts. `QtOpenGLTextureTarget` presents those pixels through a real current `QOpenGLTexture`/`QOpenGLTextureBlitter` context. It explicitly reports `native_geometry_acceleration=false`; it is not allowed to masquerade as native instanced geometry acceleration.
- The controlled Windows current-context test is non-skippable and now proves non-background scene pixels, no diagnostic/QPainter fallback, no capture errors, an occupied pixel region, and a stable digest.
- Device-pixel-ratio handling now separates logical frame dimensions from the physical GL viewport instead of clipping high-DPI frame content.
- Real dense smoke evidence: logical target `120x64`, captured framebuffer `180x96`, `2,736` non-background pixels, digest `1c5e67ece465f7badb0df21ed6ab319c31f036cbf76c8c4d0822512fe2398f4c`, `draw_mode=qt_texture_blit`, `gpu_draw_calls=1`, `fallback_required=false`.
- Focused viewport evidence: `60 passed, 2 skipped in 6.03s`. The two skips are environment/empty-frame compatible smoke cases; the controlled Windows scene-pixel gate itself passed without skip.
- Architecture guardrails remain green: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, `release consistency OK`.

Honest limitation: this closes real framebuffer truth only. The current target is a deterministic compatibility Implementation that uploads Qt-free RGBA pixels through GL; it is not native geometry acceleration, has not passed QPainter/OpenGL per-scene pixel parity, interaction continuity, teardown, or comparable end-to-end benchmark policy. `auto` remains QPainter.

**Unique next Gate inside E32: Task 2 -- QPainter/OpenGL pixel parity through the existing immutable viewport seam.** Build captureable QPainter evidence for the same empty/single/selected/edge/hidden/resize/dense snapshots, define tolerances, and keep all Qt/GL objects outside the Interface.



## Implementation checkpoint 2 -- logical QPainter/OpenGL pixel parity (2026-07-21)

Task 2 is complete without changing the L0-L4 authority structure:

- added Qt-free `ViewportPixelCapture` and `ViewportPixelParity` Modules. They carry tightly packed RGBA bytes plus plain evidence and compute dimensions, occupied-bounds delta, non-background/alpha coverage delta, per-pixel mismatch ratio, mean absolute channel error, and explicit fail-closed reasons;
- added the concrete `qpainter_capture.py` Host Adapter helper. It renders the existing immutable `ViewportFrameSnapshot` through `QPainterViewportBackend` into `QImage`, then translates the native object to plain RGBA at the Adapter seam; no Qt object was added to `ViewportBackend`, scene snapshots, L0/L1 registries, or plugin contracts;
- `QtOpenGLTextureTarget` now retains its logical Qt-free RGBA source as `ViewportPixelCapture` after a successful current-context texture blit. The smoke probe exposes it only when `include_logical_capture=True`; normal benchmark/report output remains plain and compact;
- the Windows smoke window is frameless so requested logical dimensions are not silently widened by the Windows top-level minimum tracking width. Physical framebuffer/DPR proof remains separate from logical parity normalization;
- red parity tests exposed a real batching error: the previous global sort drew circles before edges and could draw selected overlays before entity bodies. `compile_opengl_batches()` now preserves semantic layers (`edges -> entity bodies -> selected overlays -> text`) while still grouping matching styles. The dense benchmark contract remains `46` batches rather than degenerating to one batch per command;
- deterministic scenes now cover `empty`, `single`, `selected`, `edge`, `hidden`, `resize`, and `dense`. Ordinary-scene tolerance is bounds <= 2 px, coverage delta <= 0.03, alpha delta 0, channel threshold 32, mismatch ratio <= 0.08, and mean channel error <= 4.0. Dense tolerance keeps the same bounds/coverage/channel rules but allows mismatch ratio <= 0.14 and mean channel error <= 8.5 because many opaque/translucent primitive edges accumulate QPainter-versus-Qt-free rasterization differences;
- measured logical parity passed for all seven scenes. Representative results: exact empty parity; selected mismatch ratio `0.023112`; hard-edge `0.014323`; resize `0.004661`; dense `0.135742` with coverage delta `0.026042` and mean channel error `8.196126`;
- an empty scene is allowed to prove exact background parity, but it intentionally does not count as positive non-empty framebuffer readiness. All six non-empty scenes produced current-context framebuffer pixels without fallback or errors;
- focused viewport/backend/canvas/parity/benchmark regression: `62 passed, 2 skipped in 8.17s`; the two skips remain the compatibility smoke/empty-frame paths, not the controlled Windows logical parity gate;
- architecture guardrails pass: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.

No default policy changed. `auto` remains QPainter, `QtOpenGLTextureTarget` remains `native_geometry_acceleration=false`, and E32 is still in progress.

**Unique next Gate inside E32: Task 3 -- interaction continuity and deterministic target recreation/teardown.** Exercise resize, camera pan/zoom, selection changes, repeated frames, target recreation, and context teardown through the public immutable viewport/canvas seams; prove new snapshots produce new pixels without stale batches, fallback, context leaks, duplicate publication, or direct Project World mutation.


## Implementation checkpoint 3 -- interaction continuity and deterministic teardown (2026-07-21)

Task 3 is complete without changing framework or plugin authority:

- `compile_viewport_draw_commands()` now applies the immutable `ViewportCameraSnapshot` at the existing Qt-free command seam: world coordinates are zoomed, optionally rotated in radians around the world origin, then translated by camera position. Entity radius, circle stroke width, selected-outline radius/stroke, and edge width scale with zoom; the default camera preserves the previous command stream; non-finite or non-positive `camera.zoom` fails explicitly.
- `probe_qt_opengl_interaction_sequence(frames, process_events)` accepts immutable frame snapshots and plain options only. It recreates the current Qt/OpenGL canvas/target path per frame, returns plain records, and does not access Project World, plugin publication, manifests, registries, or live scene/editor objects.
- `QtOpenGLTextureTarget` now exposes a monotonic creation generation in its diagnostic snapshot. The smoke teardown explicitly calls `doneCurrent()`, closes and schedules deletion of the widget, processes teardown events, records any teardown errors, and verifies that no OpenGL context remains current.
- The controlled six-frame sequence covers base, pan, zoom, selection, repeated selection, and resize. Base/pan/zoom/selection digests change; the repeated frame digest remains identical; resize changes logical and physical dimensions. Selection increases commands/instances from 3 to 4, every target reports pending instances equal to rendered instances, all observed generations are distinct, and input snapshots remain unchanged.
- Direct Windows evidence: `completed=true`, `context_released=true`, zero teardown errors, six observed target recreations, zero Project World mutations, zero plugin publications, no fallback, and no per-frame errors. Logical dimensions change from `160x120` to `211x137`; on the current DPR the framebuffer changes from `240x180` to `317x206`.
- Task 3 red/green verification: `4 passed in 2.66s`. Expanded E32 viewport/backend/canvas/parity/interaction/benchmark-contract regression: `66 passed, 2 skipped in 11.03s`. The skips are the existing compatibility smoke paths, not the controlled Windows interaction gate.
- Architecture guardrails remain green: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.

Honest limitation: this proves interaction continuity and deterministic Adapter teardown, not end-to-end performance superiority or native geometry acceleration. `QtOpenGLTextureTarget` still reports `native_geometry_acceleration=false`; `auto` remains QPainter; E32 and the wider engine objective remain incomplete.

**Unique next Gate inside E32: Task 4 -- comparable end-to-end QPainter/OpenGL benchmark and default policy decision.** Use identical scenes, dimensions, warmup, iterations, and capture policy; record real draw/capture cost, commands, batches, instances, draw calls, fallback/error state, and keep `auto -> QPainter` unless the evidence justifies an explicit change.

## Implementation checkpoint 4 -- comparable end-to-end Adapter benchmark and default policy (2026-07-21)

Task 4 is complete, but Phase E32 is not complete.

- `viewport_adapter_benchmark.py` is a Qt-free evidence Module whose public Interface accepts only immutable `ViewportFrameSnapshot` values and plain numeric options. Concrete QPainter/QImage and Qt current-context OpenGL objects remain inside their Host Adapters and the report contains only plain data.
- Both Adapters now run the exact same dense workload (`1280x720`, `360` entities, `269` edges, `630` commands, `46` batches/`630` instances), warmup, iterations, alternating order, per-frame render/capture/readback, and teardown lifecycle. The legacy `viewport_frame_loop_dense` remains phase-profiling evidence only and is not a default-policy comparison.
- Formal CLI evidence (`--case viewport_adapter_end_to_end --repeats 3`) recorded outer mean/min/max `24388.677/24279.632/24571.054 ms`. The last inner run recorded QPainter mean/median/p95 `588.461/588.542/588.686 ms` and OpenGL `5234.932/5238.438/5252.152 ms` with identical capture counts, no fallback/errors, current context and release proof, and parity ready (`mismatch=0.017715`, mean channel error `0.878544`).
- The measured QPainter/OpenGL ratio is `0.112410x`, below the required `1.10x`; current OpenGL also reports `native_geometry_acceleration=false`. Fail-closed policy therefore selects QPainter with reasons `native_geometry_acceleration` and `minimum_measured_speedup`. `auto` remains QPainter.
- Expanded sequential testing exposed a Host-lifecycle test hazard: a probe-created `QApplication` could lose its Python strong reference and later be replaced by an offscreen test application, preventing Windows `QOpenGLWidget.paintGL`. The concrete probe now retains its application instance; no engine/plugin authority moved into Qt.
- Verification: CLI/backend/benchmark contract `14 passed`; isolated current-context retry `19 passed`; expanded E32 viewport/OpenGL/QPainter-command/benchmark regression `92 passed, 2 skipped in 34.09s`; project plugin, core, GUI, and release guardrails all pass; scoped `git diff --check` passes.

**Unique next Gate inside E32: Task 5 -- full regression, real Editor smoke, signature attempt, architecture guardrails, and E32 closure.** Preserve `.pond`, AI command/Inspector, SR2D, manifests, Project World, Player/export, plugin reload/startup/shutdown, and the one-L0/one-L1 recursive framework-plugin topology. Do not claim E32 or the engine complete before this closure evidence exists.

## Implementation checkpoint 5 -- isolated current-context proof and phase closure (2026-07-23)

Task 5 and Phase E32 are complete. The wider engine objective remains active.

- A full non-signature run exposed a process-environment interaction rather than a renderer-contract failure: earlier tests can create an offscreen/minimal `QApplication`, after which a real Windows `QOpenGLWidget` cannot establish the required current-context pixel path in the same process. `opengl_probe_worker.py` now isolates only this concrete Qt/OpenGL Host Adapter probe in a child process with plain JSON/base64 snapshot and capture facts. It does not transport Qt/GL objects, become a renderer or Host, or touch Project World/plugin authority.
- `probe_qt_opengl_canvas_smoke()` routes polluted Windows processes to the isolated worker and retains a recursion guard. Timeout, process failure, malformed output, missing current context, fallback, and empty pixels all fail closed. Interaction records retain both the cross-frame sequence generation and the worker-local native target generation, so recreation evidence is not fabricated.
- Worker-focused proof is `6 passed`; expanded OpenGL proof is `40 passed, 2 skipped`. The final complete non-signature suite is `1412 passed, 34 skipped, 34 subtests passed in 160.20s`.
- The preceding full run had one load-sensitive asset-index wall-clock failure (`13.531s > 10.0s`) while all other 1,411 tests passed. Immediate isolated proof was `1 passed in 6.60s`; the formal three-repeat `asset_index_scale_1000` benchmark then recorded the last cold build at `4280.496 ms` and full rebuild at `1369.339 ms`, with deterministic revision and registry projection parity. The threshold was not loosened, and the subsequent full suite passed.
- Real Editor smoke passed with `plugins=13/20`, zero discovery/load errors, layout exercise, and deterministic reverse shutdown.
- Architecture guardrails passed: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`; scoped `git diff --check` passed for the E32 implementation files.
- Signature-only collection still fails before tests with `ModuleNotFoundError: No module named 'cryptography'`. No package was installed. Fallback is to keep signature verification explicitly unclaimed; unblock is to provision `cryptography` in the exact project `.venv` under a separately approved dependency step and rerun the signature-only file.

E32 therefore proves real current-context pixels, logical QPainter/OpenGL parity, interaction/recreation/teardown continuity, and comparable policy evidence at the existing Qt-free viewport seam. It does not prove native geometry acceleration, select a replacement UI shell, remove PyQt, complete signature verification, or complete the whole engine. `auto` remains QPainter.

**Unique next Gate: Phase E33 -- Qt-Free Editor Contribution Contract and Replacement Host Adapter Migration Readiness.** Deepen the existing L1 runtime plugin Host seam so L3 editor extensions can publish deterministic, plain-data editor contributions without making PyQt widget factories, live callables, or `LayoutManager` the framework contract. Keep `NestedPluginHost` / `RuntimePluginHost` / `ProjectScopedPluginHost` as the only authorities; the current Qt editor remains one legacy Adapter and no replacement shell is selected in advance.

