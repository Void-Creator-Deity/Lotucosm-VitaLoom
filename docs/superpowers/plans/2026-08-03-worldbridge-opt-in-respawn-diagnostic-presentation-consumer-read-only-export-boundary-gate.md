# E231 WorldBridge Opt-In Respawn Diagnostic Presentation Consumer and Read-Only Export Boundary Gate

Date: 2026-08-03
Status: complete
Completed: 2026-08-10

## Previous gate

E230 emits a canonical, bounded, caller-owned presentation model from exactly one validated E229 receipt. It deliberately has no rendering, export, persistence, or runtime wiring. A future caller could otherwise re-interpret its fields, retain the full presentation or source receipt, or make an export format appear to be a replay/checkpoint/runtime contract.

## Objective

Add a separate Qt-free consumer/export boundary that accepts only a validated E230 presentation model (mapping or canonical bytes), creates a bounded canonical read-only export record, preserves only E230-approved summary facts and explicit negative capabilities, and retains no nested presentation or receipt source object. It must remain caller-owned and must not wire GameViewport, Pond, default tick, persistence, replay, checkpoint, restoration, mutation, UI hosting, or live runtime state.

## Required work

1. Define an exact canonical export-record schema with export media/source identity and digest, artifact identity, context, stream roles, outcome/admission/ordered steps, mutation-consumed fact, snapshot digest references, gene counts, and explicit negative capabilities.
2. Consume E230 presentation mappings/canonical bytes exclusively through E230 validators/decoders. Fail closed for raw E226 artifacts, E227 inspections, E228 projections, E229 receipts, malformed/non-canonical/duplicate/oversized data, missing identities, self-integrity tampering, semantic overclaims, and field parity mismatches.
3. Bound and copy-isolate the output. Do not retain nested presentation/receipt/source objects, snapshots, genes, deltas, stream state, callbacks, runtime references, UI widgets, files, network destinations, or persistence handles.
4. Expose static runtime-status evidence only. Do not add module-level GameViewport dependencies, default routes, actual filesystem/network export, persistence, replay, checkpoint, restoration, mutation, live state, common-clock, input-ordering, or cross-lane atomicity authority.
5. Add exact-schema/admitted/rejected/mapping-and-byte/tamper/canonical/bounds/copy-isolation/global-RNG tests, mechanical source/call-graph guards, static-status coverage, isolated compilation, focused/wider/full regression, status evidence, and a fresh-session prompt.

## Non-goals

No actual file/network export, UI framework authority, GameViewport or Inspector wiring, raw artifact/inspection/projection/receipt fallback, replay loader/admission, checkpoint persistence/restoration, stream reconstruction, mutation execution, live runtime state, common clock, input ordering, cross-lane atomicity, complete RNG closure, scene/Pond checkpoint semantics, lossless mapping, default runtime wiring, unified Pond readiness, OpenGL/native acceleration, or product-completion claim.

## Planned decision

The export boundary will be presentation-only, Qt-free, and in-memory. It will emit an auditable canonical record for an explicit caller; it will not write or transmit anything and will not make UI host code an engine/plugin authority.

## Implementation and closure

- Added world_bridge_respawn_diagnostic_export.py: a Qt-free, presentation-only, in-memory consumer that accepts only an E230 presentation mapping or canonical bytes and emits a canonical, copy-isolated export record bounded to 6 KiB.
- The export record preserves only source presentation/artifact identity and digest facts, context, stream roles, outcome/admission/ordered-step facts, mutation-stream-consumed fact, snapshot digest references, gene counts, and explicit negative capabilities. It does not retain nested presentation/receipt/source objects, snapshots, genes, deltas, stream state, callbacks, runtime references, widgets, files, network destinations, or persistence handles.
- Validation enforces exact schema, strict canonical JSON, duplicate-key rejection, byte bounds, self-digest, static no-I/O/no-authority policies, and optional field parity against the validated E230 presentation. Standalone validation proves only export self-integrity; E230 parity still requires its source presentation.
- Runtime status exposes static opt-in export-contract evidence only. GameViewport and Pond remain untouched; runtime_mode=dual and default_ready=false remain required.

## Evidence

- Isolated compilation of E231 export module, runtime status, tests, and guard passed.
- Focused E231 export coverage: 7 passed in 0.66s; E226–E231/adapter/viewport/status focused coverage: 57 passed in 10.45s.
- E226 artifact, E227 inspection, E228 projection, E229 consumer, E230 presentation, and E231 export guards passed. The E231 guard confirmed presentation parity, Python/NumPy global RNG stability, raw-source rejection, no file/network/UI authority, no restoration/mutation authority, runtime_mode=dual, and default_ready=false.
- Wider WorldBridge/GameViewport/runtime-status coverage: 204 passed, 5 subtests passed in 22.30s.
- Full offscreen regression: 2242 passed, 34 skipped, 55 subtests passed in 253.72s (0:04:13).

## Fallback and unblock

Reject malformed, non-canonical, duplicate, oversized, semantically overclaimed, and presentation-parity-mismatched export records rather than repairing them. Keep E231 as an in-memory caller-owned record only. E232 must be the final bounded diagnostic sink boundary: it may audit/export evidence in memory, but must not create another chain of runtime-like wrappers; after that, work must move to the unresolved common-clock, cross-lane atomicity, replay/checkpoint/restore, lossless mapping, and default-readiness blockers.
## Exactly one next gate

**E232 -- WorldBridge Opt-In Respawn Diagnostic Export Record Read-Only Audit Sink Boundary Gate**.