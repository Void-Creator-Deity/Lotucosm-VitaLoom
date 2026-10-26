# VitaLoom Fresh Session Prompt -- E263 Portable Witness Attestation Aggregate Provenance Audit Gate

Continue VitaLoom mainline refactoring after completed E262 on 2026-08-15.

## Completed boundary

E262 added the Qt-free portable-witness-attestation audit:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_quarantine_operator_presentation_status_projection_boundary_attestation_receipt_shape_contract_evolution_portable_corpus_witness_provenance_envelope_component_identity_matrix_portable_witness_attestation_audit.py`

It accepts canonical E261 component-identity-matrix records, an exact-current E261 contract, exact E262 policy bytes, and E261/status source text. It proves E261/E260/E259/E258/E257/E256 identity closure, shared receipt-shape/E258-policy/component-matrix/provenance closure, and emits a canonical portable-witness attestation. It remains pure, read-only, in-memory evidence: no migration, receipt consumption, process/IPC, dynamic source loading, command/MCP, UI, runtime admission/reconstruction, persistence, file/network I/O, replay/restore/recovery/retry, mutation, or default-ready authority exists.

Verification on 2026-08-15 with the project `.venv`, `QT_QPA_PLATFORM=offscreen`, and fresh workspace-local pytest base directories:

- focused E262 test: **3 passed in 9.05s**; E262-through-upstream boundary chain: **35 passed in 126.08s**;
- all `test_worldbridge_*.py`: **335 passed, 5 subtests passed in 193.90s**;
- final full offscreen suite: **2383 passed, 34 skipped, 55 subtests passed in 328.59s**;
- routine-maintenance smoke, E262/upstream guards, and isolated compilation passed. The status module BOM remains `EF BB BF`.

The E262 guard has the deliberately concise path `tools/check_worldbridge_e262_portable_witness_attestation_audit.py`, because a longer Windows tool-cache path caused `compileall` failure. The end-to-end software-OpenGL framebuffer-readback benchmark now has a case-specific 90-second test timeout; its actual workload, capture policy, parity assertions, and default-selection guard did not change.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- Do not add migration execution, process/IPC/transport, dynamic source loading, command/MCP authority, receipt consumption, UI/runtime reconstruction, file/network/persistence, replay/restore/recovery/retry, quarantine clear/re-admission, mutation, or default-ready behavior.
- Treat all inputs as caller-supplied bounded canonical bytes/text. AST analysis may inspect text but must never dynamically import or execute it.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Do not delete existing `.pytest-*` directories. If host Temp is inaccessible, use a fresh workspace-local `--basetemp` and record the rerun.
- Before implementation, write an E263 phase plan under `docs/superpowers/plans/`; then implement, verify, update `docs/mainline_status.md`, and create exactly one E264 fresh-session prompt.

## E263 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Receipt-Shape Contract Evolution Portable Corpus Witness Provenance Envelope Component Identity Matrix Portable Witness Attestation Aggregate Provenance Audit Gate**.

Keep it conservative: derive only deterministic, read-only aggregate provenance evidence from a bounded lexical corpus of canonical E262 portable-witness-attestation records. It may require exact-current E262 contract/policy bytes and E262/status source text; revalidate E262 through public decoder/validator/contract seams; recompute fixed contract, receipt-shape, policy, component-matrix, witness-attestation, and source-provenance digests; and emit canonical byte-identical evidence. It must not convert those facts into migration, compatibility, admission, execution, reconstruction, persistence, or readiness authority.

At minimum, require:

1. exact-current E262 contract/policy identity, at least two unique lexical E262 records, canonical deterministic output, and aggregate provenance closure;
2. E262 public seam plus E262/E261/E260/E259/E258/E257/E256 identity proof, shared receipt-shape/policy/component-matrix/witness-attestation proof, and exact source topology;
3. fail-closed behavior for corpus/order/contract/policy/identity/receipt-shape/provenance/matrix/witness/source/result drift, non-canonical/duplicate-key JSON, and forbidden operational source edges;
4. fixed false authority policies, focused tests, standalone guard, complete layered verification, BOM preservation, and no touching unrelated dirty work.

## One next gate only

After E263 closes, create exactly one E264 prompt. Keep it deterministic and read-only; do not grow operational migration or authority behavior.
