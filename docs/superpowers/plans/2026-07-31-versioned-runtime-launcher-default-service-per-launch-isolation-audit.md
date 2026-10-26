# Phase E156 -- Versioned Runtime Launcher Default-Service Per-Launch Isolation Audit

Date: 2026-07-31
Status: complete

## Previous gate

E155 completed the explicit-service success composition audit. Caller-owned valid L1 registry and event-bus instances are validated before UI allocation and reach EditorKernel unchanged by identity; the explicit registry path does not construct a default registry.

## Objective

Audit the implicit default-service ownership seam across repeated launches in a single process. Verify that each successful no-splash launch that omits both services constructs a fresh per-launch default RuntimeCapabilityRegistry, does not pass `event_bus=None`, and does not retain a process-global Launcher cache or acquire external service lifecycle authority.

## Evidence required

- Add a deterministic direct regression that invokes `launch_editor(...)` twice in one process with `use_splash=False` and omits both `capability_registry` and `event_bus`.
- Capture both EditorKernel constructions and prove the two `capability_registry` keyword values are valid per-launch `InMemoryRuntimeCapabilityRegistry` instances with distinct identities.
- Prove Kernel receives no `event_bus` keyword when the caller omits it; prove both launches individually resolve layers, load plugins, show Kernel, and enter/return from `app.exec()` exactly once.
- Prove no splash show/message/finish/dismiss or startup-cleanup warning occurs on either successful no-splash launch, and do not introduce global cache or ownership transfer behavior.
- Add production code only for a demonstrated defect. Preserve FrameCore Qt-free L0, .pond semantics, AI command registry flows, Inspector command binding, SR2D public seams, and package/project manifests. Keep QPainter default; do not claim OpenGL/native default readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added `tests/test_versioned_runtime_launcher_default_service_per_launch_isolation.py`. It runs two successful `use_splash=False` launches in one process, intercepts the default-registry constructor, records both Kernel argument dictionaries, and makes every splash seam fail if called.
- The regression proves the two default registries are real `InMemoryRuntimeCapabilityRegistry` objects with different identities. Each Kernel receives only `capability_registry`, never `event_bus=None`; both launches independently resolve layers, load plugins, show the Kernel, and enter/return from `app.exec()` once.
- No production correction was warranted. Launcher already makes the default registry per invocation, omits the absent event-bus keyword, and has no process-global default-service cache. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Verification

- Focused offscreen regression and scoped `py_compile`: `1 passed in 0.35s`.
- Versioned-runtime composition suite: `86 passed in 7.98s`.
- Editor smoke: `Editor smoke OK`, `plugins=13/20`.
- Guard scripts: project-plugin model, core boundaries, GUI boundaries, and release consistency all reported `OK`.
- Anaconda package-signature compatibility check: `2 passed in 0.24s`.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks passed for the new regression and phase documents. `git diff --check` exited 0, with only existing LF/CRLF conversion warnings printed; existing historical trailing whitespace in untracked `docs/mainline_status.md` was isolated outside the appended E156 block and not reformatted.

## Next gate

Exactly one active next gate: **E157 -- Versioned Runtime Launcher Mixed-Service Optionality Success-Composition Audit**.