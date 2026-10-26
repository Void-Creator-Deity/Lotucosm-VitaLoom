# VitaLoom Fresh Session Prompt -- E264 Aggregate Provenance Envelope Cross-Record Consistency Audit Gate

Continue VitaLoom mainline refactoring after completed E263 on 2026-08-27.

## Completed boundary

E263 added the Qt-free aggregate-provenance audit at:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_e263_aggregate_provenance_audit.py`

It accepts a bounded, canonical, digest-sorted corpus of E262 portable-witness-attestation records, exact-current E262 contract/policy bytes, and caller-supplied E262/status source text. It emits explicit `aggregate_provenance`, `aggregate_provenance_digest`, and `aggregate_provenance_valid` evidence while retaining the inherited E262 witness closure. It is descriptive read-only proof only: no migration, compatibility/admission, execution, process/IPC, dynamic source loading, receipt consumption, UI/runtime authority, persistence, replay/restore/recovery/retry, mutation, or default-ready behavior.

Verification on August 27, 2026 with the existing project `.venv`, `QT_QPA_PLATFORM=offscreen`, and workspace-local pytest bases:

- focused E263: **3 passed in 6.28s**;
- E262 + E263 boundary pair: **6 passed in 10.41s**;
- all `test_worldbridge_*.py`: **338 passed, 5 subtests passed in 153.52s**;
- standalone E263 guard passed;
- scoped `.venv` compilation, BOM, and `git diff --check` passed.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- The existing Conda/uv mixed environment is intentionally deferred until the refactor mainline is complete. Continue using `.venv/python.exe`; do not rebuild the environment, run `uv sync`, reinstall dependencies, or modify `uv.lock` during E264.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Do not delete existing `.pytest-*` directories. Use fresh workspace-local pytest bases if needed.

## E264 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Attestation Aggregate Provenance Envelope / Cross-Record Consistency Audit Gate**.

Keep it conservative and deterministic. Build a separate read-only envelope over canonical E263 aggregate-provenance records. The envelope must prove exact-current E263 identity and cross-record consistency without adding operational authority. At minimum, require:

1. bounded, canonical, unique, digest-sorted E263 records and exact-current E263 contract/policy bytes;
2. exact E263 through E256 identity, receipt-shape, policy, provenance, component-matrix, portable-witness, and aggregate-provenance closure;
3. cross-record consistency for aggregate payload fields, corpus-record digests, source order/topology, and all fixed false authority flags;
4. fail-closed behavior for reorder, duplicate, truncate, malformed/noncanonical/duplicate-key JSON, contract/policy/identity/provenance/source/result drift, aggregate-envelope tamper, and forbidden operational edges;
5. focused tests, a concise Windows-safe standalone guard, layered verification, BOM preservation, and updates to `docs/mainline_status.md` plus exactly one E265 fresh-session prompt.

AST inspection may inspect caller-supplied source text but must never dynamically import or execute it. Do not introduce migration execution, process/IPC/transport, command/MCP/UI/runtime authority, receipt consumption, persistence, replay/restore/recovery/retry, mutation, or default readiness.

## One next gate only

After E264 closes, create exactly one E265 prompt. Do not claim the full refactor is complete; continue the mainline evidence gates.
