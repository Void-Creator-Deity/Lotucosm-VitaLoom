# Phase E161 -- Versioned Runtime Launcher Explicit-Service Startup-Project Ordering Audit

Date: 2026-07-31
Status: complete

## Previous gate

E160 completed no-splash event-loop handoff coverage for valid explicit L1 services. It proves exact service identity, zero splash usage, and correct normal/ordinary/controlled event-loop outcomes after successful no-splash startup.

## Objective

Audit successful explicit startup-project composition with valid caller-supplied L1 registry and event bus. Prove normalized project path binds to Kernel after exact service composition and before plugin-layer loading, without changing `.pond` semantics, project manifest boundaries, or splash ownership.

## Completion record

- Added `tests/test_versioned_runtime_launcher_explicit_service_startup_project_ordering.py`. A relative public `pathlib.Path` request is normalized to the absolute `.pond` path while real explicit registry and event bus validate and reach Kernel by identity.
- The direct trace proves `set_startup_project()` runs after Kernel construction and before plugin-layer resolution/load, followed by show and one event-loop entry. Default registry construction and all splash adapters are forbidden, and no cleanup warning appears.
- No production change was needed. The existing Launcher sequencing preserves `.pond` request semantics and project/service boundaries. FrameCore remains Qt-free L0, QPainter remains default, and OpenGL/native is not default-ready.

## Verification record

- Focused offscreen compile plus regression: `1 passed in 0.26s`.
- Complete versioned-runtime suite: `97 passed in 8.32s`.
- Editor smoke: `plugins=13/20`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency guards: `OK`.
- Independent Anaconda package-signature regression: `2 passed in 0.30s`.
- `git diff --check` exited 0 with only existing LF/CRLF working-copy warnings; unrelated dirty worktree content was preserved.

## Next gate

E162 -- Versioned Runtime Launcher Explicit-Service Startup-Project Failure Ownership Audit.