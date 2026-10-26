# Phase E155 -- Versioned Runtime Launcher Explicit-Service Success-Composition Audit

Date: 2026-07-31
Status: complete

## Previous gate

E154 completed the no-splash event-loop counterpart. Successful no-splash startup enters app.exec() once and preserves normal/RuntimeError/SystemExit/KeyboardInterrupt outcomes without any splash adapter or cleanup work.

## Objective

Audit the positive explicit-service composition seam. Verify that valid caller-supplied L1 RuntimeCapabilityRegistry and RuntimeEventBus instances are validated, retained by identity, and forwarded unchanged to EditorKernel, with Launcher neither constructing replacement services nor acquiring their lifecycle authority.

## Evidence required

- Add a deterministic direct regression that supplies real valid InMemoryRuntimeCapabilityRegistry and InMemoryRuntimeEventBus instances, reaches a successful Launcher startup, and proves Kernel receives the exact same objects under the intended constructor keywords.
- Prove no default registry is constructed on the explicit path, event-bus validation occurs before UI startup, and normal splash/event-loop ordering remains intact without altering service ownership.
- Cover an appropriate successful return path and ensure no service object is substituted, globally cached, or exposed through FrameCore L0.
- Add production code only for a demonstrated defect. Keep FrameCore Qt-free L0, preserve .pond, AI command registry, Inspector binding, SR2D, and package/project manifest seams; keep QPainter default and do not claim OpenGL/native default readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added `tests/test_versioned_runtime_launcher_explicit_service_success_composition.py`. It supplies real `InMemoryRuntimeCapabilityRegistry` and `InMemoryRuntimeEventBus` objects, wraps and invokes the real validators, blocks the default-registry constructor seam, and drives a complete splash-enabled successful launch.
- The regression proves validation order is registry, event bus, splash show, initial message, Kernel construction, plugin-load message, layer resolution, plugin load, restore message, Kernel show, splash finish, then `app.exec()`. The two caller-owned service objects reach `EditorKernel` unchanged by identity; no default registry is constructed, startup cleanup is not entered, and Launcher does not acquire service lifecycle authority.
- No production correction was warranted. Existing Launcher composition already honors the explicit-service contract. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Verification

- Focused offscreen regression: `1 passed in 0.33s`.
- Versioned-runtime composition suite: `85 passed in 8.12s`.
- Editor smoke: `Editor smoke OK`, `plugins=13/20`.
- Guard scripts: project-plugin model, core boundaries, GUI boundaries, and release consistency all reported `OK`.
- Anaconda package-signature compatibility check: `2 passed in 0.24s`.
- Scoped `py_compile` succeeded. UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the new regression and phase documents. `git diff --check` exited 0, with only existing LF/CRLF conversion warnings printed.

## Next gate

Exactly one active next gate: **E156 -- Versioned Runtime Launcher Default-Service Per-Launch Isolation Audit**.
