# VitaLoom Fresh Session Prompt -- E255 Portable Corpus Witness and Independent Contract Closure Audit Gate

Continue VitaLoom mainline refactoring after completed E254 on 2026-08-13.

## Completed boundary

E254 added the Qt-free fresh-memory corpus portability audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_corpus_portability_audit.py`

It accepts caller-supplied canonical E253 audit/contract/policy bytes, an exact-current E252 contract, an ordered canonical E252 corpus, and exactly E253/status source text. It uses public E253/E252 seams to recompute the corpus closure and requires exact agreement with E253 evidence. It rejects canonical-format violations, truncation, reordering, duplicate/substituted corpus records, stale E251 provenance, contract/policy drift, and source topology drift. It remains a pure in-memory verification boundary: no process, IPC, transport, dynamic import, command/MCP, UI, runtime/Pond/SR reconstruction, file/network/persistence, replay/restore/recovery/retry, mutation, or default-ready authority exists.

Verification on 2026-08-13:

- E254 focused: **3 passed in 5.90s**;
- combined E254 through E248 focused suite: **20 passed in 26.28s**;
- all `test_worldbridge_*.py`: **311 passed, 5 subtests passed in 59.13s**;
- full offscreen suite: **2359 passed, 34 skipped, 55 subtests passed in 315.12s**;
- E254/upstream guards and isolated compilation passed; `git diff --check` exited 0 apart from existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add actual process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Before implementation, write an E255 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E256 fresh-session prompt.

## E255 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Portable Corpus Witness and Independent Contract Closure Audit Gate**.

The gate should make a compact canonical witness from an E254 portability result plus the precise caller-supplied contracts/policy/corpus closure. It must independently establish that the witness has no hidden dependence on ambient runtime state: only the admitted canonical byte payloads and source-text topology may determine the output.

At minimum, design the plan and implementation to:

1. accept bounded canonical E254 audit bytes, E254 contract bytes, E253 audit/contract/policy bytes, E252 contract bytes, and ordered E252 corpus bytes;
2. validate every nested audit through its public decoder/validator and require the supplied contracts/policy to exactly equal locally built current versions;
3. recompute the E252 corpus closure and require equality with both E253 and E254 fields, then emit a compact witness digest over canonical component digests in a fixed lexical source order;
4. require E254 source/status registration topology and independent-contract seams via static AST inspection of caller-supplied text, rejecting forbidden imports/calls and registration drift;
5. enforce byte-identical repeated output and fail closed on corpus ordering/duplicate/truncation/substitution, stale provenance, mismatched nested digest, prettified/duplicate-key JSON, contract/policy drift, source order/topology drift, and result tampering;
6. keep every authority policy false except explicit read-only/in-memory witness claims, and add no operational feature;
7. add a focused test and a standalone guard; run focused, all-WorldBridge, full offscreen, relevant upstream guards, `py_compile`, and `git diff --check` before declaring the gate complete.

The gate must not claim a real new process/session, load a runtime snapshot, run a replay, reconstruct state, or make a migration/default-ready decision. “Independent” means dependency closure over explicit canonical inputs only.

## One next gate only

After E255 closes, create exactly one E256 prompt. Choose its scope only after recording E255 evidence; it must remain a conservative read-only closure/provenance audit rather than operational authority growth.