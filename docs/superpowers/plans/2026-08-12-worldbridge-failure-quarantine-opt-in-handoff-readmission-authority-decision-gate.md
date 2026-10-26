# E239 WorldBridge Failure Quarantine and Opt-In Handoff Re-Admission Authority Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E238 established post-failure containment for the tick path: a labelled `WorldBridgeHandoffFailure` stores a receipt, classifies it with a Qt-free authority, and suspends later opt-in tick hand-offs for the current runtime. Normal stop or scene discard drops the current Pond before clearing that current-lifetime suspension; a later start/reload is a fresh run, not recovery.

## Objective

Audit every actual legacy `GameViewport` entry point that can mutate the opt-in SR/PS bridge after a labelled failure. Define the strongest truthful Qt-free admission classification and lifecycle boundary for quarantine and a later fresh-instance re-admission. Close any same-runtime bypass without claiming retry safety, compensation, restore, replay, lossless synchronization, transactionality, or default readiness.

## Required work

1. Inventory every call site of `ensure_bridged_organisms`, `bridge_spawned_organism`, `_ensure_unified_pond`, and `unified_pond_step*` below the product runtime boundary; distinguish pre-bridge linkage, spawn linkage, and ordered tick hand-off.
2. Verify all writers of `_worldbridge_handoff_suspended`, including initialization, scene discard, stop, configuration refresh, and failure handling. Establish whether mode refresh, scene reload, normal stop/start, or a direct adapter call can re-admit the same SR/PS instance.
3. Add only a Qt-free classification authority that can decide whether a named opt-in bridge entry point is admitted for a currently unquarantined runtime and can describe fresh-instance re-admission as a lifecycle prerequisite. It must issue no UI, Pond, I/O, persistence, scheduler, thread, or mutation command.
4. Make all discovered GameViewport opt-in bridge writers ask that classification before invoking bridge mutation. When quarantined, preserve normal SR-side behavior but do not construct/reuse a Pond or call an SR/PS bridge mutator for the current failed runtime.
5. Preserve diagnostics across a fresh lifetime only as historical receipt data, clearly distinguish that historical evidence from restored state, and ensure suspension is cleared solely in lifecycle paths that discard the old Pond and SR runtime state first.
6. Add focused behavioral tests plus AST/static guard coverage for every entry point, lifecycle ordering, Qt-free boundary, dual/default-ready invariants, and rejected overclaims. Run focused, wider WorldBridge, and full offscreen regression; record evidence and exactly one next gate.

## Initial audit decision

The source contains three opt-in bridge mutation classes: scene-load `ensure_bridged_organisms`, runtime spawn `bridge_spawned_organism`, and tick `ensure_bridged_organisms` followed by `unified_pond_step*`. E238 currently guards only the tick path. `_refresh_unified_pond_mode()` may discard a Pond when disabled but does not clear the suspension; current source writers clear suspension only during initialization, `_discard_scene_runtime_state()`, and `_stop_simulation()`. Therefore E239 should centralize admission classification and guard all three mutation classes, while treating discard/stop followed by fresh runtime construction as the only current re-admission boundary.

## Decision and implementation

E239 admits **one-way current-runtime quarantine plus fresh-instance lifecycle re-admission only**. The new Qt-free `world_bridge_quarantine_readmission_authority.py` classifies all known opt-in WorldBridge writers: `scene_prebridge`, `spawn_bridge`, and `tick_handoff`. When a labelled E236/E238 failure has suspended the current runtime, each decision denies its writer before Pond construction/reuse and before the corresponding SR/PS bridge mutator. The classifier is read-only: it cannot clear suspension, construct a Pond, mutate either lane, schedule a restart, or restore/replay state.

`GameViewport` now asks that authority before all three writer classes: scene-load `ensure_bridged_organisms`, dynamic-spawn `bridge_spawned_organism`, and tick-path prebridge/`unified_pond_step*`. The existing explicit tick suspension check remains visible for the E238 containment seam; the authority records a last admission decision but does not alter failure receipts. As a result, a partial-mutation failure cannot be bypassed by prebridging a scene or connecting a newly spawned organism within the same quarantined SR/PS lifetime.

Source audit confirms that `_worldbridge_handoff_suspended` is cleared only during initialization and in `_discard_scene_runtime_state()` / `_stop_simulation()`. Both lifecycle methods discard `_unified_pond` before clearing suspension. `_refresh_unified_pond_mode()` can disable the feature and discard a Pond but does not clear quarantine. A later normal start/reload may re-enable opt-in writers only after the old runtime/Pond have been discarded and fresh instances exist. The retained failure receipt is historical diagnostic evidence only; it is not a restored state or a safe same-instance retry admission.

## Evidence

- Focused E239/E238/E237/E236/unified-bridge/runtime-status coverage: **32 passed in 3.57s**.
- Wider WorldBridge/status/GameViewport/SR-input coverage: **268 passed, 5 subtests passed in 20.62s**.
- Full offscreen regression: **2294 passed, 34 skipped, 55 subtests passed in 273.11s (0:04:33)**, using retained `.pytest-e239-full-3bf259878aef4c96a3736a94b0584ca4`.
- E239 quarantine/re-admission guard, E238 recovery containment, E237 feasibility, E236 transaction atomicity, E235 randomness, E234 input/pause, and runtime-status guards passed.
- `git diff --check` passed; its LF/CRLF messages are pre-existing workspace warnings, not diff errors.

## Fallback and unblock path

Fallback is complete per-current-runtime opt-in bridge quarantine: keep normal SR-side processing possible but skip every known SR-to-PS bridge writer until the host discards the old SR and Pond instances. Do not add direct flag clearing, automatic retry, mode-toggle re-admission, receipt repair, or state reconstruction. Any future same-instance retry/recovery admission requires complete versioned SR+PS checkpoints; identity/link restoration; clock/input/lifecycle/RNG/native/plugin coverage; a partial-mutation compensation policy; and replay plus interaction parity evidence.

## Non-goals

No direct same-instance retry, no automatic re-admission, no cross-lane rollback, no inverse mutation compensation, no in-place restore, no atomic recovery, no replay, no checkpoint admission, no scheduler/RNG/input authority expansion, no `.pond` semantic change, no manifest change, no AI command/Inspector/SR2D seam change, no Unified Pond default enablement, and no native/OpenGL readiness claim.

## Exactly one intended next gate

E240 -- WorldBridge Quarantine Diagnostic Provenance and Operator Visibility Decision Gate.
