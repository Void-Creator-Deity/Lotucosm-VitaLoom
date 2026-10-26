# VitaLoom Fresh Session Prompt -- E253 Status Projection Boundary Compatibility Corpus and Contract Evolution Audit Gate

Continue VitaLoom mainline refactoring after completed E252 on 2026-08-13.

## Completed boundary

E252 added the Qt-free deterministic compatibility audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_audit.py`

It accepts bounded canonical E251 audit/contract bytes plus exactly two caller-supplied source units in a fixed lexical order. It validates the E251 contract against the local contract, records source/order/digest provenance, emits deterministic canonical evidence, and rejects contract, JSON, source-order, source-topology, and tampered-result drift. It remains a conceptual pure-input boundary: no process, IPC, transport, file, network, command, MCP, UI, runtime, receipt-consumer, replay, restore, recovery, retry, quarantine-clear, re-admission, mutation, or default-ready authority exists.

Verification on 2026-08-13:

- E252 focused: **3 passed in 6.39s**;
- combined E252/E251/E250/E249/E248 focused suite: **14 passed in 13.41s**;
- all 52 WorldBridge modules: **305 passed, 5 subtests passed in 24.77s**;
- full offscreen: **2353 passed, 34 skipped, 55 subtests passed in 217.75s**;
- E252-E245 relevant guards and isolated `py_compile` passed; `git diff --check` had no diff errors.

## E253 goal

Audit a bounded compatibility corpus and contract-evolution policy for the E252 conceptual evidence boundary. Prove that accepted corpus records are canonical, provenance-complete, version-compatible, deterministically ordered, and non-authoritative; reject mixed versions, duplicate corpus entries, stale/mutated digests, incompatible contract evolution, and any attempt to turn corpus evidence into execution or runtime authority.

## Non-negotiable constraints

- Before code, write/update an E253 plan under `docs/superpowers/plans/`.
- Preserve the runtime root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, and manifests.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- Do not add actual process/IPC/transport, command/MCP route, PyQt/GameViewport authority, lifecycle observer, receipt consumer execution, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reconstruction, persistence, file/network I/O, external artifact input, or default-ready promotion.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E254 fresh prompt.
