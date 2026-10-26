# E238 WorldBridge Cross-Lane Recovery Compensation and Controlled Restart Authority Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E237 established that the current public seams do not provide a complete live SR/PS checkpoint, restore protocol, atomic capture, or replay admission. E236 provides phase-labelled non-atomic failure isolation only; an adapter exception catch and a receipt are not recovery.

## Objective

Audit the actual post-handoff-failure behavior at the WorldBridge and legacy GameViewport adapter boundaries. Determine the strongest truthful bounded response after `WorldBridgeHandoffFailure`: containment/reporting only, suspension of future opt-in hand-offs, a lane-local controlled fresh restart, or another source-backed scope. Implement only behavior whose owner, affected lane, lifecycle ordering, and failure semantics are mechanically proven. Preserve dual-mode default and never call an in-process mutation reversal compensation, rollback, atomic recovery, replay, or lossless synchronization without a complete protocol.

## Required work

1. Inventory WorldBridge failure receipt propagation, GameViewport scheduling/timer behavior, simulation start/stop/discard paths, Pond construction/disposal, and any existing restart or reset seams.
2. Separate UI containment, opt-in bridge suspension, lane-local fresh lifecycle restart, and true cross-lane recovery; list which state may already be partially mutated and which state is deliberately not repaired.
3. Decide whether a minimal Qt-free recovery authority can truthfully classify/report a recommended host action without issuing runtime mutation commands.
4. If an adapter behavior is added, ensure it can only stop/suspend the next opt-in hand-off after a labelled failure and cannot imply restoration; prove it does not alter `.pond`, manifests, AI command registry, Inspector bindings, SR2D seams, or the Qt-free engine-plugin boundary.
5. Add focused tests and a mechanical guard for non-rollback/non-replay/default-ready constraints plus any approved containment/restart lifecycle evidence.
6. Run focused, wider WorldBridge, and full offscreen regression; record evidence, fallback/unblock, and exactly one next gate.

## Initial audit hypothesis

`GameViewport._run_unified_pond_bridge_tick()` catches `WorldBridgeHandoffFailure` for UI containment and retains its receipt, but current E236/E237 contracts expose neither state restoration nor a dedicated bridge failure quarantine/restart owner. Existing start/stop/discard methods may rebuild only SR scene runtime or host state and may not reconstruct a synchronized Pond or bridge-link identity. Unless source inspection proves a bounded owner and ordering, E238 should remain classification/containment-only and leave controlled restart unadmitted.

## Decision and implementation

E238 admits **containment plus a controlled fresh lifecycle restart only**. After a labelled `WorldBridgeHandoffFailure`, the legacy `GameViewport` retains a copy-owned receipt, asks the Qt-free `world_bridge_recovery_authority.py` classifier for a read-only containment decision, and suspends every later opt-in WorldBridge hand-off for that current runtime lifetime. The ordinary SR host tick may continue; the adapter neither retries the failing Pond nor performs rollback, mutation compensation, restore, replay, or hidden scheduler control.

The containment decision accepts only the explicit E236 non-transaction receipt vocabulary. Its mandatory host action is `suspend_future_opt_in_handoffs_for_current_runtime`; it records that partial mutation may be possible and that neither SR state, PS state, nor bridge-link metadata has been repaired. The authority remains Qt-free and classification-only: it owns no Pond construction, UI, I/O, persistence, scheduler, or live mutation.

`GameViewport._discard_scene_runtime_state()` and `_stop_simulation()` now explicitly discard `_unified_pond` and clear the current-lifetime suspension. A later normal scene reload or stop/start therefore builds fresh host/runtime instances rather than reusing a Pond that participated in the failed hand-off. This is a controlled fresh restart boundary, not recovery of the failed run: it does not restore prior state, replay the failed hand-off, prove compensation, or make unified mode default-ready.

## Evidence

- Focused E238/E237/E236/unified-bridge/runtime-status coverage: **27 passed in 5.67s**.
- Wider WorldBridge/status/GameViewport/SR-input coverage: **263 passed, 5 subtests passed in 37.64s**.
- Full offscreen regression: **2289 passed, 34 skipped, 55 subtests passed in 282.25s (0:04:42)**, using `.pytest-e238-full-3f7cf353339643f59413262dd50d6714` as the retained base temp directory.
- `check_worldbridge_cross_lane_recovery_controlled_restart.py`, E237 feasibility, E236 transaction atomicity, E235 randomness, E234 input/pause, and runtime-status guards all passed.
- `git diff --check` passed; LF/CRLF messages are existing workspace warnings, not diff errors.

## Fallback and unblock path

Fallback remains phase-labelled non-atomic failure isolation plus current-runtime opt-in hand-off suspension. Do not repair receipts, clear suspension against the same Pond, or automatically restart/retry. A future true recovery admission would require a complete versioned SR+PS checkpoint bundle; identity/link, clock/input/lifecycle/RNG and native/plugin state coverage; a defined restore ordering and partial-mutation compensation policy; plus deterministic replay/parity proof. Until then, normal stop/reload may only discard contaminated instances and begin a distinct fresh run.

## Non-goals

No cross-lane rollback, no inverse mutation compensation, no in-place Pond restore, no replay, no transaction/atomicity admission, no shared scheduler/RNG/input authority, no lossless mapping claim, no Unified Pond default enablement, and no native/OpenGL readiness claim.

## Exactly one intended next gate

E239 -- WorldBridge Failure Quarantine and Opt-In Handoff Re-Admission Authority Decision Gate.
