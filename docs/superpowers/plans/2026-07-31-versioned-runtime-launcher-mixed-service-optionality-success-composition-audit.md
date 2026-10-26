# Phase E157 -- Versioned Runtime Launcher Mixed-Service Optionality Success-Composition Audit

Date: 2026-07-31
Status: complete

## Previous gate

E156 completed repeated default-service isolation. Two no-splash launches that omit both services create distinct per-invocation InMemoryRuntimeCapabilityRegistry objects, pass no event_bus keyword, and retain no Launcher-global default service.

## Objective

Audit the two remaining successful mixed service-composition branches: caller-supplied capability registry with omitted event bus, and omitted capability registry with caller-supplied event bus. Verify validation, identity, default construction, optional-keyword behavior, startup ordering, and ownership remain correct without expanding Launcher authority.

## Evidence required

- Add deterministic direct coverage for both mixed combinations, preferably with explicit call-order recording around the real service validators and default-registry constructor seam.
- For explicit registry plus omitted event bus, prove the registry is validated and forwarded by identity, no default registry is constructed, and Kernel receives no event_bus keyword.
- For omitted registry plus explicit event bus, prove one default registry is constructed, the event bus is validated and forwarded by identity, and Kernel receives both intended keywords.
- Preserve successful no-splash or owned-splash startup ordering as appropriate, one app.exec() return per case, and the absence of unintended cleanup/global caching/lifecycle transfer.
- Add production code only for a demonstrated defect. Preserve FrameCore Qt-free L0, .pond semantics, AI command registry flows, Inspector command binding, SR2D public seams, and package/project manifests. Keep QPainter default; do not claim OpenGL/native default readiness.
- Run focused/composition/smoke/guard/signature/hygiene proof, update status/context/index/prompt, and name exactly one next gate.

## Completion record

- Added `tests/test_versioned_runtime_launcher_mixed_service_optionality_success_composition.py` with two deterministic no-splash successful launches covering the remaining mixed branches.
- The explicit-registry/omitted-bus case runs the real registry validator, forwards the exact registry identity, forbids default-registry construction and event-bus validation, and proves Kernel gets no `event_bus` keyword.
- The omitted-registry/explicit-bus case creates one real default registry, runs the real event-bus validator, forwards the supplied bus by identity, and proves Kernel receives exactly the intended two service keywords. Both paths resolve layers, load plugins, show Kernel, and enter `app.exec()` once without splash or cleanup behavior.
- No production correction was warranted. Launcher already composes the four explicit/implicit service-optionality states without cache or lifecycle authority expansion. FrameCore remains Qt-free L0; QPainter remains default; OpenGL/native is not default-ready; whole-refactor completion is not claimed.

## Verification

- Focused offscreen regression and scoped `py_compile`: `2 passed in 0.32s`.
- Versioned-runtime composition suite: `88 passed in 7.46s`.
- Editor smoke: `Editor smoke OK`, `plugins=13/20`.
- Guard scripts: project-plugin model, core boundaries, GUI boundaries, and release consistency all reported `OK`.
- Anaconda package-signature compatibility check: `2 passed in 0.31s`.
- UTF-8-no-BOM/CRLF/trailing-whitespace checks and `git diff --check` passed during closeout, with only existing LF/CRLF conversion warnings printed.

## Next gate

Exactly one active next gate: **E158 -- Versioned Runtime Launcher Invalid-Service Pre-UI Failure Matrix Audit**.