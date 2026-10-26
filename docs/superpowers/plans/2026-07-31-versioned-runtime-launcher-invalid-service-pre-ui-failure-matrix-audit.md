# Phase E158 -- Versioned Runtime Launcher Invalid-Service Pre-UI Failure Matrix Audit

Date: 2026-07-31
Status: complete

## Previous gate

E157 completed successful mixed-service coverage. Every explicit/implicit registry and event-bus composition combination now has direct positive-path evidence for validation/default construction, argument identity, optional keyword behavior, and UI-host ordering.

## Objective

Audit invalid caller-supplied L1 services at the Launcher boundary. Verify malformed capability-registry and event-bus candidates fail at the intended validator before UI allocation or event-loop entry, without Kernel construction, layer resolution, plugin loading, splash adapters, cleanup, or app.exec().

## Evidence required

- Add deterministic direct coverage for invalid explicit registry and invalid explicit event-bus candidates, plus observable dual-invalid precedence.
- Prove validation exception semantics and ordering while all UI-host and Kernel work is forbidden.
- Prove no default service conceals an invalid caller input and no cleanup warning is emitted before startup begins.
- Preserve FrameCore Qt-free L0, .pond, AI, Inspector, SR2D, package/project manifest seams, and QPainter default; do not claim OpenGL/native readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added `tests/test_versioned_runtime_launcher_invalid_service_pre_ui_failure_matrix.py` with two direct cases. Dual-invalid explicit services fail at the real capability-registry validator, retain its exact TypeError text, and make event-bus validation unreachable. A valid real registry followed by an invalid explicit event bus reaches the validators in registry-then-bus order and retains the real event-bus TypeError text.
- Both cases forbid default-registry construction, Kernel creation, plugin-layer resolution, every splash adapter, cleanup, and app event-loop lookup. Neither logs the established splash-dismiss warning, confirming these failures occur before Launcher startup ownership exists.
- No production change was needed. The existing Launcher ordering already provides the required pre-UI failure boundary while keeping FrameCore Qt-free L0, QPainter default, and all .pond, AI, Inspector, SR2D, and manifest seams intact. OpenGL/native is not default-ready and whole-refactor completion is not claimed.

## Verification record

- Focused offscreen compile plus regression: `2 passed in 0.30s`.
- Complete versioned-runtime suite: `90 passed in 7.23s`.
- Editor smoke: `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`.
- Independent Anaconda package-signature regression: `2 passed in 0.19s`.
- `git diff --check` exited 0; it emitted only existing LF/CRLF working-copy warnings. Unrelated dirty worktree content was preserved.

## Next gate

E159 -- Versioned Runtime Launcher Explicit-Service Event-Loop Handoff Audit.