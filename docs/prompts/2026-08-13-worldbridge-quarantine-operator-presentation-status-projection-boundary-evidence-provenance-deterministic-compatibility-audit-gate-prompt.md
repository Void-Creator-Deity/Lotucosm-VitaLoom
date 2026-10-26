# VitaLoom Fresh Session Prompt -- E252 Status Projection Boundary Evidence Provenance and Deterministic Compatibility Audit Gate

Continue VitaLoom mainline refactoring after completed E251 on 2026-08-13.

## Completed boundary

E251 added the Qt-free canonical byte-boundary audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_audit.py`

It accepts only caller-supplied canonical E250 audit/contract bytes and supplied source metadata. It validates public E250 seams, rejects contract drift and prohibited source topology, and proves only a **conceptual** read-only byte boundary; it does not create a process, IPC transport, route, file, or network channel.

Verification on 2026-08-13:

- focused E251/E250/E249/E248/E247: **14 passed**;
- all 52 WorldBridge modules: **302 passed, 5 subtests passed**;
- full offscreen: **2350 passed, 34 skipped, 55 subtests passed**;
- E251-E245 relevant guards, isolated `py_compile`, and `git diff --check` passed.

## E252 goal

Add a Qt-free proof that E251 boundary evidence has deterministic provenance and compatibility semantics: equivalent canonical E250 input bytes and source metadata must yield equivalent fixed-scope E252 evidence, while source/contract/version/digest/ordering drift must fail closed. Stay entirely pure-input and read-only; do not introduce any transport or runtime authority.

## Non-negotiable constraints

- Before code, write/update an E252 plan under `docs/superpowers/plans/`.
- Preserve the runtime root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, and manifests.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- Do not add actual process/IPC transport, command/MCP route, PyQt/GameViewport authority, lifecycle observer, receipt consumer execution, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reuse, external artifact input, persistence, file/network I/O, or default-ready promotion.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E253 fresh prompt.
