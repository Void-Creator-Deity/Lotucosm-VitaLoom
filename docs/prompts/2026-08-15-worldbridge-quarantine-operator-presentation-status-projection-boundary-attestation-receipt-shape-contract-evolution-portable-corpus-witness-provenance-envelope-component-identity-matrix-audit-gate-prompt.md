# VitaLoom Fresh Session Prompt -- E261 Provenance Envelope Component Identity Matrix Audit Gate

Continue VitaLoom mainline refactoring after completed E260 on 2026-08-15.

## Completed boundary

E260 added the Qt-free provenance-envelope audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_audit.py`

It accepts canonical E259 witness records plus exact-current E259 contract bytes, an exact E260 policy, and E259/status source text. It proves E259/E258/E257/E256 closure, one receipt-shape/policy proof, and an ordered deterministic per-record provenance envelope. It remains pure, read-only, in-memory evidence?no migration, receipt consumption, process/IPC, dynamic source loading, command/MCP, UI, runtime admission/reconstruction, persistence, file/network I/O, replay/restore/recovery/retry, mutation, or default-ready authority exists.

Verification on 2026-08-15 with the project `.venv` and workspace-local pytest base directories:

- focused E260 through E250 suite: **29 passed in 36.70s**;
- all `test_worldbridge_*.py`: **329 passed, 5 subtests passed in 56.72s**;
- full offscreen suite: **2377 passed, 34 skipped, 55 subtests passed in 217.64s**;
- E260/upstream guards, isolated compilation, BOM check, and `git diff --check` passed. The diff check had only pre-existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add migration execution, process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Do not delete the existing `.pytest-*` directories. If the host Temp directory yields `WinError 5`, use a fresh workspace-local `--basetemp` and document the rerun.
- Before implementation, write an E261 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E262 fresh-session prompt.

## E261 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Receipt-Shape Contract Evolution Portable Corpus Witness Provenance Envelope Component Identity Matrix Audit Gate**.

Keep it conservative as a read-only component-identity matrix verifier over caller-supplied canonical E260 provenance-envelope records. It may validate a bounded lexical corpus, exact-current E260 contract/policy bytes, and E260/status source text; it may recompute deterministic identity-matrix, provenance, policy, and closure digests. It must not consume a receipt, execute a migration, or make an operational compatibility/admission/default-ready decision.

At minimum, require:

1. exact-current E260 contract/policy identity, at least two unique lexical records, and deterministic component-identity matrix closure;
2. E260 public decode/validate seams, exact E259/E258/E257/E256 identity proof, common receipt-shape/policy proof, and canonical deterministic output;
3. fail-closed behavior for corpus/order/contract/policy/receipt-shape/provenance/component-matrix/source/result drift, non-canonical/duplicate-key JSON, and forbidden operational source edges;
4. fixed false authority policies, focused tests, standalone guard, and the complete layered verification chain.

## One next gate only

After E261 closes, create exactly one E262 prompt. Keep it deterministic and read-only; do not grow operational migration or authority behavior.
