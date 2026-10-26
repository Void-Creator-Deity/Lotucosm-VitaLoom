# VitaLoom Fresh Session Prompt -- E251 Status Projection Contract Drift and Cross-Process Read-Only Boundary Audit Gate

Continue VitaLoom mainline refactoring after completed E250 on 2026-08-13.

## Completed boundary

E250 added the Qt-free status-projection audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_audit.py`

It consumes only already-produced `runtime.worldbridge.status` command/MCP envelopes plus bounded caller-supplied source text. It verifies the command/MCP direct mirror, projects only the E248/E249 static contracts and their pilot IDs, rejects raw receipt keys and operational consumer edges, and is registered in `runtime_worldbridge_status` as a static contract.

Verification on 2026-08-13:

- focused E250/E249/E248/E247: **12 passed**;
- all 51 WorldBridge modules: **300 passed, 5 subtests passed**;
- full offscreen: **2348 passed, 34 skipped, 55 subtests passed**;
- E250-E245 relevant guards, isolated `py_compile`, and `git diff --check` passed.

## E251 goal

Create a Qt-free audit that detects drift between the E250 static status-projection contract and the actual cross-process/read-only boundary. It must prove that any externally supplied status evidence is strictly canonical, bounded, contract-scoped, and non-authoritative; it must not create a new process boundary, transport, command/MCP route, persistence path, file/network I/O, or runtime/UI control channel. Use pure supplied records/source metadata and fail closed on contract, route, policy, digest, or authority drift.

## Non-negotiable constraints

- Before code, write/update an E251 plan under `docs/superpowers/plans/`.
- Preserve the runtime root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, and manifests.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- Do not add a process host, IPC transport, command/MCP route, PyQt/GameViewport authority, lifecycle observer, receipt consumer execution, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reuse, external artifact input, persistence, file/network I/O, or default-ready promotion.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E252 fresh prompt.
