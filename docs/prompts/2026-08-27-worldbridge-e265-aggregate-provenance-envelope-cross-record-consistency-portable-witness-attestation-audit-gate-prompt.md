# VitaLoom Fresh Session Prompt -- E265 Aggregate Provenance Envelope Cross-Record Consistency Portable Witness Attestation Audit Gate

Continue VitaLoom mainline refactoring after completed E264 on 2026-08-27.

## Completed boundary

E264 added the Qt-free short-path envelope audit at:

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_e264_envelope_consistency_audit.py`

It accepts a bounded corpus of canonical E263 aggregate-provenance records, exact-current E263 contract/policy bytes, and E263/status source text. It revalidates the E263 → E262 → E256 evidence chain and emits canonical record, aggregate, source-topology, and cross-record consistency evidence with fixed false authority flags. It remains descriptive read-only proof only: no migration, receipt consumption, process/IPC/transport, dynamic source loading, command/MCP, UI/runtime authority, persistence, replay/restore/recovery/retry, mutation, or default-ready behavior.

Verification on August 27, 2026 with the existing project `.venv`:

- focused E264: **3 passed**;
- E263 + E264 boundary chain: **6 passed**;
- all `test_worldbridge_*.py`: **341 passed, 5 subtests passed**;
- standalone E264 guard passed;
- scoped compilation, BOM, and `git diff --check` passed. The status module BOM remains `EF BB BF`.

## Mandatory preserved constraints

- Runtime root remains `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- PyQt/GameViewport remains legacy UI-host only. Keep L0-L4 engine/plugin contracts Qt-free.
- Do not break `.pond`, command registry, Inspector binding, SR2D seams, package/project manifests.
- Defaults remain exactly `runtime_mode == "dual"`, `unified_pond_enabled is False`, and `default_ready is False`.
- The existing Conda/uv mixed environment is intentionally deferred until the refactor mainline is complete. Continue using `.venv\python.exe`; do not rebuild the environment, run `uv sync`, reinstall dependencies, switch interpreters, or modify `uv.lock` during E265.
- Preserve pre-existing dirty/untracked work. Do not stage, commit, reset, restore, clean, delete, or alter unrelated files.
- Do not delete existing `.pytest-*` directories. Use fresh workspace-local pytest bases if needed.

## E265 objective

Implement **WorldBridge Quarantine Operator Presentation Status Projection Boundary Aggregate Provenance Envelope Cross-Record Consistency Portable Witness Attestation Audit Gate**.

Keep it conservative, deterministic, Qt-free, bounded, and read-only. Build the next independently verifiable witness layer over canonical E264 envelope records. Require exact-current E264 identity and preserve the full upstream E264 → E263 → E262 → E256 closure. At minimum:

1. require bounded canonical unique records, deterministic lexical ordering, exact-current contract/policy bytes, and canonical byte-identical output;
2. revalidate envelope record, aggregate, source-topology, cross-record consistency, component identity, portable-witness, and fixed-false authority fields;
3. emit explicit digest-protected provenance/attestation evidence without turning it into compatibility, admission, migration, execution, receipt-consumption, persistence, or readiness authority;
4. fail closed for reorder, duplicate, truncate, malformed/noncanonical/duplicate-key JSON, contract/policy/identity/provenance/envelope/source/result tamper, and forbidden operational edges;
5. add focused tests, a concise Windows-safe standalone guard, layered verification, BOM preservation, and updates to `docs/mainline_status.md` plus exactly one E266 fresh-session prompt.

Before implementation, write or update the E265 phase plan under `docs/superpowers/plans/`. After implementation, close the gate with evidence and name exactly one next gate.

AST inspection may inspect caller-supplied source text but must never dynamically import or execute it. Do not introduce migration execution, process/IPC/transport, command/MCP/UI/runtime authority, receipt consumption, persistence, replay/restore/recovery/retry, mutation, or default readiness.

## One next gate only

After E265 closes, create exactly one E266 prompt. Do not claim the full refactor is complete; continue the mainline evidence gates.