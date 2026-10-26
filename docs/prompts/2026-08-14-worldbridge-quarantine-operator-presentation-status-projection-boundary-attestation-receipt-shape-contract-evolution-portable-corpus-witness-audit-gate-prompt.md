# VitaLoom Fresh Session Prompt -- E259 Attestation Receipt-Shape Contract Evolution Portable Corpus Witness Audit Gate

Continue VitaLoom mainline refactoring after completed E258 on 2026-08-14.

## Completed boundary

E258 added the Qt-free receipt-shape corpus contract-evolution authority:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_corpus_contract_evolution_audit.py`

It accepts canonical E257 receipt-shape compatibility records plus exact-current E257 contract/policy bytes and E257/status source text. It pins the corpus to current E257/E256 contracts and a common static receipt shape under a no-migration policy. It remains pure in-memory verification evidence: no migration, process, IPC, command/MCP, UI, receipt consumption, runtime reconstruction, persistence, replay/recovery, mutation, or admission/default-ready authority exists.

Verification on 2026-08-14:

- focused E258 through E250 suite: **26 passed in 69.29s**;
- all `test_worldbridge_*.py`: **323 passed, 5 subtests passed in 112.89s**;
- full offscreen suite: **2371 passed, 34 skipped, 55 subtests passed in 322.40s**;
- E258/upstream guards and isolated compilation passed; `git diff --check` exited 0 apart from existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add migration execution, process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Before implementation, write an E259 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E260 fresh-session prompt.

## E259 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Receipt-Shape Contract Evolution Portable Corpus Witness Audit Gate**.

Scope this conservatively as a read-only portable witness over caller-supplied canonical E258 contract-evolution records. It may validate a bounded lexical corpus, exact-current E258 contract and evolution-policy bytes, plus E258/status source text; it may recompute deterministic closure/provenance digests. It must not consume a receipt, execute a migration, or make an operational compatibility/admission/default-ready decision.

At minimum, the plan should require:

1. bounded canonical E258 audit corpus and exact-current E258 contract/policy bytes; lexical unique ordering; a minimum two-record corpus; and source provenance closure;
2. public E258 decode/validate seams, exact E257/E256 contract identity closure, common receipt-shape/policy contract digest proof, deterministic encoding, and byte-identical repeated output;
3. fail-closed handling for reorder/duplicate/truncate/substitute records, stale policy/contract/receipt-shape/provenance digests, non-canonical/duplicate-key JSON, static-policy/shape divergence, source topology drift, forbidden operational source edges, and result tampering;
4. explicit fixed false authority policies and static checks against operational imports/calls;
5. a focused test and standalone guard, then focused, all-WorldBridge, full offscreen, upstream guards, `py_compile`, and `git diff --check` evidence.

## One next gate only

After E259 closes, create exactly one E260 prompt. Its scope must remain deterministic, read-only portable-witness evidence rather than operational migration or authority growth.
