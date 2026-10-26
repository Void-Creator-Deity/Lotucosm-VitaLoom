# VitaLoom Fresh Session Prompt -- E257 Portable Witness Chain Attestation Receipt-Shape Compatibility Audit Gate

Continue VitaLoom mainline refactoring after completed E256 on 2026-08-14.

## Completed boundary

E256 added the Qt-free deterministic attestation authority:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_witness_chain_deterministic_attestation_audit.py`

It accepts caller-supplied canonical E255 witness/contract bytes and exact E255/status source text. It validates E255 through public seams, checks component linkage, emits a fixed lexical attestation digest, and statically checks source continuity. It remains a pure in-memory verification boundary: no process, IPC, transport, dynamic import, command/MCP, UI, runtime/Pond/SR reconstruction, file/network/persistence, replay/restore/recovery/retry, mutation, or default-ready authority exists.

Verification on 2026-08-14:

- focused E256 through E250 suite: **20 passed in 47.68s**;
- all `test_worldbridge_*.py`: **317 passed, 5 subtests passed in 90.50s**;
- full offscreen suite: **2365 passed, 34 skipped, 55 subtests passed in 326.64s**;
- E256/upstream guards and isolated compilation passed; `git diff --check` exited 0 apart from existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add actual process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Before implementation, write an E257 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E258 fresh-session prompt.

## E257 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Portable Witness Chain Attestation Receipt-Shape Compatibility Audit Gate**.

Scope this conservatively as compatibility evidence for the canonical E256 attestation shape across explicitly supplied equivalent encodings. It may validate a bounded ordered corpus of canonical E256 attestation records and prove deterministic receipt-shape compatibility, but it must not consume receipts, execute commands, operate MCP/UI routes, or make a promotion/admission decision.

At minimum, the plan should require:

1. bounded canonical E256 attestation bytes, exact-current E256 contract bytes, and a small ordered compatibility corpus of equivalent caller-supplied attestation records;
2. public decoder/validator use, exact-current contract equality, lexical corpus ordering, deterministic corpus/shape digests, and byte-identical repeated output;
3. fail-closed handling for reorder/duplicate/truncate/substitute records, stale attestation/component digests, contract drift, non-canonical/duplicate-key JSON, source topology drift, and result tampering;
4. explicit fixed false authority policies and static checks against operational imports/calls;
5. a focused test and standalone guard, then focused, all-WorldBridge, full offscreen, upstream guards, `py_compile`, and `git diff --check` evidence.

## One next gate only

After E257 closes, create exactly one E258 prompt. Its scope must remain a conservative read-only compatibility/provenance closure rather than operational authority growth.