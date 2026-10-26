# VitaLoom Fresh Session Prompt -- E256 Portable Witness Chain Deterministic Attestation Audit Gate

Continue VitaLoom mainline refactoring after completed E255 on 2026-08-14.

## Completed boundary

E255 added the Qt-free portable corpus witness closure authority:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_portable_corpus_witness_audit.py`

It accepts caller-supplied canonical E254/E253/E252 evidence, exact-current contracts/policy, ordered E252 corpus bytes, and E254/status source text. Through public decoders/validators only, it recomputes nested corpus and provenance closure, emits a lexical component-digest witness, and AST-checks static E254/status registration topology. It stays a pure in-memory verification boundary: no process, IPC, transport, dynamic import, command/MCP, UI, runtime/Pond/SR reconstruction, file/network/persistence, replay/restore/recovery/retry, mutation, or default-ready authority exists.

Verification on 2026-08-14:

- focused E255 through E250 suite: **17 passed in 40.61s**;
- all `test_worldbridge_*.py`: **314 passed, 5 subtests passed in 86.53s**;
- full offscreen suite: **2362 passed, 34 skipped, 55 subtests passed in 391.47s**;
- E255/upstream guards and isolated compilation passed; `git diff --check` exited 0 apart from existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add actual process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Before implementation, write an E256 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E257 fresh-session prompt.

## E256 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Portable Witness Chain Deterministic Attestation Audit Gate**.

Scope this conservatively as a read-only attestation over E255's canonical witness, its exact-current contract, and explicitly supplied source topology. It may prove deterministic attestation/provenance closure of supplied evidence, but must not construct a runtime session, replay records, operate commands, or treat an attestation as a promotion or admission decision.

At minimum, the plan should require:

1. bounded canonical E255 witness and exact-current E255 contract inputs, plus only the caller-supplied source text required to prove public seam and status registration continuity;
2. independent canonical recomputation of the E255 witness/contract/source component linkage before emitting a deterministic attestation digest;
3. fixed lexical input/source ordering, byte-identical repeated output, public decoder/validator use, and rejection of stale witness/contract/source digests, non-canonical or duplicate-key JSON, topology drift, and result tampering;
4. explicit fixed false authority policies and static checks against operational imports/calls;
5. a focused test and standalone guard, then focused, all-WorldBridge, full offscreen, upstream guards, `py_compile`, and `git diff --check` evidence.

## One next gate only

After E256 closes, create exactly one E257 prompt. Its scope must remain a conservative read-only provenance/attestation closure rather than operational authority growth.