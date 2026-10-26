# VitaLoom Fresh Session Prompt -- E254 Status Projection Boundary Corpus Replay-Independent Integrity and Fresh-Session Portability Audit Gate

Continue VitaLoom mainline refactoring after completed E253 on 2026-08-13.

## Completed boundary

E253 added the Qt-free compatibility-corpus and exact-current contract-evolution audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_compatibility_corpus_contract_evolution_audit.py`

It accepts a bounded ordered corpus of canonical E252 records, validates each record through public E252 seams, requires unique lexical digest order and exact-current contract/policy compatibility, and rejects mixed versions, stale digests, duplicate records, malformed/non-canonical JSON, source drift, and forbidden source topology. It remains a conceptual pure-input boundary: no process, IPC, transport, file, network, command, MCP, UI, runtime, receipt-consumer, replay, restore, recovery, retry, quarantine-clear, re-admission, mutation, or default-ready authority exists.

Verification on 2026-08-13:

- E253 focused: **3 passed in 6.59s**;
- combined E253/E252/E251/E250/E249/E248 focused suite: **17 passed in 19.67s**;
- all 52 WorldBridge modules: **308 passed, 5 subtests passed in 48.29s**;
- full offscreen: **2356 passed, 34 skipped, 55 subtests passed in 297.25s**;
- E253-E245 relevant guards, isolated `py_compile`, and `git diff --check` passed.

## E254 goal

Prove that a canonical E253 compatibility corpus can be independently re-validated in a fresh in-memory audit context without replaying, importing, executing, mutating, restoring, or reconstructing runtime state. Require integrity-preserving record extraction, provenance closure, stable corpus digests, and portable fresh-session validation from caller-supplied bytes only. Reject runtime-derived state, process/transport seams, corpus truncation, digest substitution, version/contract mismatch, and any attempt to use portability evidence as execution authority.

## Non-negotiable constraints

- Before code, write/update an E254 plan under `docs/superpowers/plans/`.
- Preserve the runtime root, `.pond` semantics, AI command registry flows, Inspector command binding, SR2D seams, and manifests.
- Do not stage, commit, revert, delete, clean, or remove dirty/untracked work or existing `.pytest-*` directories.
- Do not add actual process/IPC/transport, command/MCP route, PyQt/GameViewport authority, lifecycle observer, receipt consumer execution, replay/restore/recovery/retry/quarantine-clear/re-admission/mutation, Pond/SR reconstruction, persistence, file/network I/O, external artifact loading, or default-ready promotion.
- Keep `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- End with focused, all-WorldBridge, full offscreen, relevant guards, `py_compile`, `git diff --check`, a `docs/mainline_status.md` entry, and exactly one E255 fresh prompt.
