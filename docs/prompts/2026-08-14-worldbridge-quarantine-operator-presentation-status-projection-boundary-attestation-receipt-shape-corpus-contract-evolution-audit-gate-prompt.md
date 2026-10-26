# VitaLoom Fresh Session Prompt -- E258 Attestation Receipt-Shape Corpus Contract Evolution Audit Gate

Continue VitaLoom mainline refactoring after completed E257 on 2026-08-14.

## Completed boundary

E257 added the Qt-free receipt-shape compatibility authority:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_attestation_receipt_shape_compatibility_audit.py`

It accepts a bounded lexical corpus of canonical E256 deterministic attestations plus exact-current E256 contract bytes and E256/status source text. It proves a static common receipt shape while preserving individual audit/source provenance. It remains pure in-memory verification evidence: no process, IPC, command/MCP, UI, receipt consumption, runtime reconstruction, persistence, replay/recovery, mutation, or admission/default-ready authority exists.

Verification on 2026-08-14:

- focused E257 through E250 suite: **23 passed in 59.56s**;
- all `test_worldbridge_*.py`: **320 passed, 5 subtests passed in 104.55s**;
- full offscreen suite: **2368 passed, 34 skipped, 55 subtests passed in 346.85s**;
- E257/upstream guards and isolated compilation passed; `git diff --check` exited 0 apart from existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Before implementation, write an E258 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E259 fresh-session prompt.

## E258 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Receipt-Shape Corpus Contract Evolution Audit Gate**.

Scope this conservatively as a read-only contract-evolution audit over caller-supplied canonical E257 receipt-shape compatibility records. It may validate a bounded lexical corpus, exact-current E257 contract bytes, and static evolution policy bytes; it may produce deterministic digest/provenance evidence for a common contract/shape. It must not execute migrations, consume a receipt, make an operational compatibility decision, or expand runtime authority.

At minimum, the plan should require:

1. bounded canonical E257 audit corpus and contract/policy bytes; exact-current E257 contract equality; lexical order and uniqueness; and a fixed two-or-more record corpus;
2. public E257 decode/validate seams, deterministic corpus/evolution digests, static common receipt-shape and contract identity closure, and byte-identical repeated output;
3. fail-closed handling for reorder/duplicate/truncate/substitute records, stale contract/policy/component or receipt-shape digests, non-canonical/duplicate-key JSON, static-policy/shape divergence, source topology drift, forbidden operational source edges, and result tampering;
4. explicit fixed false authority policies and static checks against operational imports/calls;
5. a focused test and standalone guard, then focused, all-WorldBridge, full offscreen, upstream guards, `py_compile`, and `git diff --check` evidence.

## One next gate only

After E258 closes, create exactly one E259 prompt. Its scope must remain deterministic, read-only evolution evidence rather than operational migration or authority growth.
