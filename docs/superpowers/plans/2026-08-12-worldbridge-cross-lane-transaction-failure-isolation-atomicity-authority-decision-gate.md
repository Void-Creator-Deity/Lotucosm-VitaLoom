# E236 WorldBridge Cross-Lane Transaction, Failure Isolation, and Atomicity Authority Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E235 closed only SR-local runtime randomness ownership. It explicitly left the bridge non-transactional: PS `Pond` retains legacy random owners, the bridge has no RNG context transport, no cross-lane draw ordering, and no checkpoint/replay authority.

## Objective

Audit the actual opt-in `unified_pond_step` and trace path for partial mutation and exception behavior. Implement only a source-backed, scope-bounded failure-isolation or transaction boundary that the current SR/PS public seams can honestly support. Do not represent exception catching, a trace, or a partial snapshot as rollback, atomicity, replay, or default readiness.

## Required work

1. Trace SR→PS synchronization, `Pond.update()`, PS→SR reflection, `GameViewport._run_unified_pond_bridge_tick()`, trace capture, and existing exception handling.
2. Inventory which mutations happen before an exception can occur and whether they can be restored with current public state.
3. Decide and document the strongest truthful behavior: no new runtime behavior with an explicit non-atomic contract, or a limited failure-isolation boundary with a precise committed/failed result and no rollback overclaim.
4. Keep the bridge opt-in and dual by default. Do not change `.pond`, manifests, AI registry/Inspector command bindings, SR2D seams, or Qt-free L0–L4 contracts.
5. Add source-backed tests and a mechanical guard covering success, SR-to-PS failure, `Pond.update()` failure, PS-to-SR failure, trace-path behavior, and status/default non-admissions.
6. Run focused, wider WorldBridge, and full offscreen regression; record evidence, fallback/unblock, and exactly one next gate.

## Initial audit hypothesis

The current bridge synchronizes SR entities into live PS organisms before `Pond.update()`, then reflects organisms into SR display entities. Existing viewport-level `try` isolation can prevent a UI tick crash, but it cannot undo prior mutations. The trace path captures before/after observations but is documented non-atomic. Therefore rollback/atomicity must remain false unless a bounded restoration protocol is explicitly implemented and proven across both lanes.

## Non-goals

No general distributed transaction, no full SR/PS checkpoint restoration, no scheduler/common-clock admission, no RNG protocol, no replay admission, no lossless mapping claim, no Unified Pond default enablement, and no native/OpenGL readiness claim.

## Exactly one intended next gate

**E237 -- WorldBridge Cross-Lane Checkpoint/Restore Feasibility and Replay Preconditions Decision Gate.**
## Audit conclusion and implemented boundary

- The original plain hand-off directly mutated live PS organisms during SR-to-PS synchronization, then called Pond.update(), then wrote PS state back to live SR display entities. The trace wrapper captured observations around the same live sequence. An exception at any live stage could therefore leave earlier work committed; the existing GameViewport catch contained a UI tick but did not restore either lane.
- Current public SR entity, PS Pond, organism/system, and trace seams do not provide one complete serialized checkpoint/restore protocol or a safe cross-lane compensation order. E236 therefore does not admit a transaction, rollback, atomic checkpoint, replay, lossless mapping, or default readiness.
- E236 adds the Qt-free world_bridge_transaction_authority.py contract and WorldBridgeHandoffFailure receipt. Both bridge entrypoints now materialize inputs before live sync; trace pair validation remains a pre-mutation ValueError admission check for compatibility. Live failures are labelled as sr_to_ps_sync, pond_update, ps_to_sr_reflection, or trace-capture phases, state which live phases began, make partial-mutation risk explicit, and skip later phases. Plain bridge behavior when pond.update is missing remains its historical no-op update behavior.
- The GameViewport adapter still contains an opt-in bridge tick error, but it now stores the structured receipt in _worldbridge_last_handoff_failure when the failure is bridge-labelled. That containment is deliberately not described as rollback.

## Evidence

- Focused E236 failure-isolation, trace, Viewport, clock/input, and status coverage: 39 passed in 7.64s.
- Wider WorldBridge/status/GameViewport/SR-input coverage: 254 passed, 5 subtests passed in 35.34s.
- Full offscreen regression: 2280 passed, 34 skipped, 55 subtests passed in 263.21s (0:04:23).
- tools/check_worldbridge_cross_lane_transaction_atomicity.py passed and mechanically rejects transaction/rollback/atomicity/replay/default-readiness overclaims. The E235 randomness guard also passed. git diff --check exits 0 with only pre-existing LF/CRLF warnings.

## Fallback / unblock

Retain the ordered opt-in dual-lane hand-off and its phase-labelled failure receipts. A later atomic or replay claim requires complete, versioned SR and PS checkpoints; restore ordering; compensation policy for partial Pond.update() and organism-system effects; serialized input/RNG/lifecycle state; and replay parity evidence. Until then, a labelled failure is not a rollback.
