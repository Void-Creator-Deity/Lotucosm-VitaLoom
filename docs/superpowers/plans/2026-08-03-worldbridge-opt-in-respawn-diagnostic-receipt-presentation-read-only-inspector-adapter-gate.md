# E230 WorldBridge Opt-In Respawn Diagnostic Receipt Presentation and Read-Only Inspector Adapter Gate

Date: 2026-08-03
Status: complete
Completed: 2026-08-03

## Previous gate

E229 provides a bounded, canonical, paired-source diagnostic receipt. It deliberately stops at caller-owned data admission: no display model or inspector adapter exists yet, so a future UI caller could re-interpret receipt fields, retain raw sources, or attach executable/runtime semantics outside the E229 contract.

## Objective

Add a distinct read-only, Qt-free presentation adapter that accepts only a validated E229 receipt (mapping or canonical bytes), produces a bounded copy-isolated inspector presentation model, and makes every negative capability explicit. It must remain caller-owned and must not wire GameViewport, Pond, default tick, replay, checkpoint, restoration, mutation, or live runtime state.

## Required work

1. Define an exact canonical presentation schema that preserves only receipt-approved summary facts, source identities/digests, outcome, stream roles, snapshot digest references, gene counts, and explicit negative capabilities.
2. Accept E229 receipt mappings/canonical bytes exclusively through E229 validators/decoders. Reject raw E226 artifact, E227 inspection, E228 projection, malformed/non-canonical/duplicate/oversized data, tampering, semantic overclaims, and any missing receipt identity fail closed.
3. Ensure output is bounded and copy-isolated. It must not retain nested receipt/source objects, snapshots, genes, deltas, stream state, callbacks, runtime references, or UI widgets.
4. Expose static runtime-status evidence only. Do not add module-level GameViewport dependencies, default-runtime routes, persistence, replay, checkpoint, restore, mutation, common clock, input ordering, or cross-lane atomicity authority.
5. Add exact-schema/admitted/rejected/mapping-and-byte/tamper/canonical/bounds/copy-isolation/global-RNG tests, a source/call-graph mechanical guard, static-status coverage, isolated compilation, focused/wider/full regression, status evidence, and a fresh-session prompt.

## Non-goals

No UI framework authority, actual GameViewport or Inspector wiring, raw artifact/projection/inspection fallback, replay loader/admission, checkpoint persistence/restoration, stream reconstruction, mutation execution, live runtime state, common clock, input ordering, cross-lane atomicity, complete RNG closure, scene/Pond checkpoint semantics, lossless mapping, default runtime wiring, unified Pond readiness, OpenGL/native acceleration, or product-completion claim.

## Planned decision

The presentation adapter will be receipt-only and Qt-free. A future UI host may render its plain data model, but neither this gate nor its result will make UI host code an engine/plugin authority or add a default execution path.

## Implementation and closure

- Added `world_bridge_respawn_diagnostic_presentation.py`: a Qt-free, receipt-only adapter that validates/decodes E229 receipts and projects a canonical, copy-isolated presentation model bounded to 6 KiB.
- The model preserves only receipt media/source identity and digests, artifact identity, context, stream roles, outcome/admission/ordered-step facts, mutation-consumed fact, snapshot digest references, gene counts, and explicit negative capabilities. It retains neither receipt/source nesting, snapshots, genes, deltas, stream state, callbacks, runtime references, nor widgets.
- Validation enforces exact schema, strict canonical JSON and duplicate-key rejection, bounds, self-digest, negative-capability facts, and optional field-for-field parity against a supplied E229 receipt. Standalone validation proves only presentation self-integrity; receipt parity still requires its paired E229 receipt input.
- Runtime status exposes static opt-in presentation-contract evidence only. The adapter is not imported by GameViewport and does not alter Pond, ticks, default mode, mutation, replay, checkpoint, restore, common clock, input ordering, or cross-lane atomicity authority.

## Evidence

- Isolated compilation of the presentation module, runtime status, tests, and guard passed.
- Focused E230 presentation coverage: `7 passed in 0.56s`; E226–E230/adapter/viewport/status focused coverage: `50 passed in 6.93s`.
- E226 artifact, E227 inspection, E228 projection, E229 consumer, and E230 presentation guards passed. The E230 guard confirmed module-global Python/NumPy RNG stability, receipt parity, raw-source rejection, no UI authority, no restoration/mutation authority, `runtime_mode=dual`, and `default_ready=false`.
- Wider WorldBridge/GameViewport/runtime-status coverage: `197 passed, 5 subtests passed in 26.30s`.
- Full offscreen regression: `2235 passed, 34 skipped, 55 subtests passed in 227.94s (0:03:47)`.

## Fallback and unblock

Reject malformed, non-canonical, duplicate, oversized, semantically overclaimed, or receipt-parity-mismatched presentation data rather than repairing it. Keep presentation as a caller-owned diagnostic model. Any future display/export consumer must accept only E230 canonical presentation data and prove it cannot retain receipt sources or gain runtime, UI, persistence, replay, checkpoint, restore, mutation, or default-route authority.
## Exactly one next gate

**E231 -- WorldBridge Opt-In Respawn Diagnostic Presentation Consumer/Read-Only Export Boundary Gate**.
