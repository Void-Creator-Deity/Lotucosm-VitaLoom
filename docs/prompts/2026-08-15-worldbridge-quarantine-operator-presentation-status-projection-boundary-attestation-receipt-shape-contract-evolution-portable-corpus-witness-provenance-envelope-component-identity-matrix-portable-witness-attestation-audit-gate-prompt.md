# VitaLoom Fresh Session Prompt -- E262 Component Identity Matrix Portable Witness Attestation Audit Gate

Continue VitaLoom mainline refactoring after completed E261 on 2026-08-15.

## Completed boundary

E261 added the Qt-free component-identity-matrix audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_audit.py`

It accepts canonical E260 provenance-envelope records, the exact-current E260 contract, an exact E261 policy, and E260/status source text. It proves E260/E259/E258/E257/E256 identity closure, shared receipt-shape/current-policy closure, deterministic provenance closure, and a digest-ordered component-identity matrix. It remains pure, read-only, in-memory evidence: it adds no migration, receipt consumption, process/IPC, dynamic source loading, command/MCP, UI, runtime admission/reconstruction, persistence, file/network I/O, replay/restore/recovery/retry, mutation, or default-ready authority.

Verification on 2026-08-15 with the project `.venv`, `QT_QPA_PLATFORM=offscreen`, and fresh workspace-local pytest base directories:

- focused E261 test: **3 passed in 6.75s**; focused E261-through-upstream boundary suite: **32 passed in 102.77s**;
- all `test_worldbridge_*.py`: **332 passed, 5 subtests passed in 153.14s**;
- full offscreen suite: **2380 passed, 34 skipped, 55 subtests passed in 243.33s**;
- E261/upstream guards, isolated compilation, UTF-8 BOM check, and `git diff --check` passed. The diff check had only pre-existing LF/CRLF warnings.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add migration execution, process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Do not delete the existing `.pytest-*` directories. If the host Temp directory yields `WinError 5`, use a fresh workspace-local `--basetemp` and document the rerun.
- Before implementation, write an E262 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E263 fresh-session prompt.

## E262 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Receipt-Shape Contract Evolution Portable Corpus Witness Provenance Envelope Component Identity Matrix Portable Witness Attestation Audit Gate**.

Keep it conservative: derive only a deterministic, read-only portable witness attestation from a bounded lexical corpus of canonical E261 component-identity-matrix audit records. It may require exact-current E261 contract/policy bytes and E261/status source text, revalidate E261 through public decoder/validator/contract seams, recompute fixed identity/provenance/component-matrix digests, and emit canonical byte-identical attestation output. It must not consume evidence operationally or make migration, compatibility, admission, execution, reconstruction, persistence, or default-ready decisions.

At minimum, require:

1. exact-current E261 contract/policy identity, at least two unique lexical E261 records, canonical deterministic output, and portable-witness attestation closure;
2. E261 public seam and E261/E260/E259/E258/E257/E256 identity proof, shared receipt-shape/policy/component-matrix/provenance proof, and exact source topology;
3. fail-closed behavior for corpus/order/contract/policy/identity/receipt-shape/provenance/matrix/source/result drift, non-canonical/duplicate-key JSON, and forbidden operational source edges;
4. fixed false authority policies, focused tests, standalone guard, complete layered verification, BOM preservation, and no touching unrelated dirty work.

## One next gate only

After E262 closes, create exactly one E263 prompt. Keep it deterministic and read-only; do not grow operational migration or authority behavior.
