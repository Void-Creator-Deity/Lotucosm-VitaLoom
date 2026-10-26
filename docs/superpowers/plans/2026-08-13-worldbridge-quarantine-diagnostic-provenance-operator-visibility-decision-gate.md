# E240 — WorldBridge Quarantine Diagnostic Provenance and Operator Visibility Decision Gate

**Status:** complete  
**Date:** 2026-08-13  
**Previous gate:** E239 — WorldBridge Failure Quarantine and Opt-In Handoff Re-Admission Authority Decision Gate

## Objective

Make the current-runtime WorldBridge failure quarantine explainable to an operator through an explicit, Qt-free, copy-isolated diagnostic projection and an existing read-only command/service seam.  This gate must improve visibility of a labelled failure and its last denied bridge-writer admission without creating a control capable of clearing quarantine, retrying a handoff, recreating a Pond, or restoring state.

## Audit findings

1. `GameViewport._run_unified_pond_bridge_tick()` is the only current failure recorder.  For a labelled `WorldBridgeHandoffFailure`, it preserves `_worldbridge_last_handoff_failure`, derives `_worldbridge_last_recovery_decision`, then sets `_worldbridge_handoff_suspended = True`.
2. E239 protects all known opt-in writers (`scene_prebridge`, `spawn_bridge`, `tick_handoff`) through `_worldbridge_opt_in_bridge_entry_admitted()`, which records a copy-owned `_worldbridge_last_quarantine_admission` before it decides whether the caller can construct/reuse a Pond or mutate the bridge.
3. `_discard_scene_runtime_state()` and `_stop_simulation()` discard `_unified_pond` before clearing `_worldbridge_handoff_suspended`.  They deliberately do not restore failed SR/PS state.  The retained receipt is historical diagnostic evidence only.
4. `runtime.worldbridge.status` is a static read-only contract command.  Existing command infrastructure already supports a narrow Qt-free runtime-capability/service seam for adapter-owned, copy-isolated host snapshots (`PS_RUNTIME_SNAPSHOT_HOST`, `SR_SELECTED_IDENTITY_HOST`).  No existing WorldBridge quarantine host exposes the three live diagnostic records.
5. The editor's legacy Qt adapter has no safe current-runtime restart or repair authority.  Consequently, E240 must use a query-only service/command seam rather than add a HUD button, a mode toggle, direct flag mutation, or a restart operation.

## Decision

E240 admits exactly the following:

- a Qt-free projection that accepts only the E236 labelled failure receipt vocabulary plus the E238 containment decision and E239 admission decision vocabulary;
- a bounded, JSON-shaped, copy-isolated diagnostic record that reports quarantine state, failure phase/partial-mutation warning, containment host action, last bridge-writer admission, and the fact that a fresh lifecycle is required before future opt-in admission;
- an adapter-owned `GameViewport` query method published through a narrow runtime capability key; and
- an existing read-only `runtime.worldbridge.quarantine_diagnostic` command/MCP adapter that can return the projection or an explicit unavailable response.

The projection is diagnostic provenance, not recovery provenance.  It may describe where the facts originated, but it must not expose the live Pond, mutable SR entities, exception objects, scheduler handles, raw stack traces, or mutable adapter state.

## Mandatory negative capabilities

The new authority, host seam, command surface, and adapter query must not:

- clear or write `_worldbridge_handoff_suspended`;
- call `_ensure_unified_pond`, `Pond`, `ensure_bridged_organisms`, `bridge_spawned_organism`, `unified_pond_step*`, stop/start/reload methods, or bridge mutators;
- create persistence, file/network I/O, replay, checkpoint, restore, compensation, rollback, or automatic retry semantics;
- claim same-runtime safety, automatic quarantine clear, cross-lane atomic recovery, lossless mapping, default readiness, native readiness, or OpenGL readiness;
- change `.pond` scenes, manifests, AI command registry behavior outside the added read-only command, Inspector bindings, or SR2D public seams.

## Implementation steps

1. Add a Qt-free `world_bridge_quarantine_diagnostic_provenance.py` authority with strict input validation, copy isolation, a static contract, and a validator that rejects recovery/default-ready overclaims.
2. Add a narrow query-only WorldBridge quarantine diagnostic host/service seam with an unavailable response; expose a copy-owned projection from `GameViewport` and publish it alongside its existing SR host capabilities.
3. Register `runtime.worldbridge.quarantine_diagnostic` as a non-mutating/non-GUI command and expose it through the MCP adapter.  Nest only the static contract in `runtime_worldbridge_status`.
4. Add focused authority/host/command/adapter tests plus an AST/source guard for read-only containment.  Run focused, wider WorldBridge, and full offscreen regressions; record exact evidence and any blocked proof.

## Expected proof

- Every projection is fresh/copy-isolated and stays valid when callers mutate returned mappings.
- A quarantined source projects the labelled receipt, E238 host action, E239 denied writer, `requires_fresh_runtime_lifecycle_before_re_admission=True`, `restores_failed_runtime_state=False`, and `replays_failed_handoff=False`.
- An unquarantined or unavailable source cannot fabricate a failure/recovery admission.
- Static status remains `runtime_mode="dual"`, `unified_pond_enabled=false`, and `default_ready=false`.
- Command and MCP surfaces are explicitly read-only and do not need a GUI.

## Fallback and unblock path

If no current `GameViewport` capability is composed, return the explicit unavailable diagnostic rather than reading globals or constructing a runtime.  If input provenance is incomplete or contradictory, reject it rather than repairing/guessing a diagnostic.  Operators must continue to use the ordinary host lifecycle only to discard contaminated instances; a future recovery gate remains blocked on complete versioned SR+PS checkpoint, identity/link, clock/input/lifecycle/RNG/native/plugin coverage, partial-mutation compensation, and replay/interaction parity evidence.

## Exactly one intended next gate

E241 — WorldBridge Quarantine Diagnostic Lifecycle Correlation and Fresh-Instance Boundary Evidence Gate.
## Completion record

### Implemented

1. Added the Qt-free `world_bridge_quarantine_diagnostic_provenance.py` authority.  It validates the E236 labelled failure receipt, E238 containment classification, and optional E239 admission record before producing a fresh JSON-shaped copy.  A suspended runtime must provide matching receipt/containment evidence; a retained record after current quarantine is cleared is explicitly labelled `historical_or_unverified_after_current_quarantine_cleared`, never recovery or re-admission proof.
2. Added `worldbridge_quarantine_diagnostic_host.py` and `WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST`.  The capability resolves only a composed adapter-owned host; without one it returns an explicit read-only unavailable model and neither reads globals nor creates a runtime.
3. Added `GameViewport.query_worldbridge_quarantine_diagnostic()` and published it in the existing adapter capability lease.  The method only reads the four retained provenance fields and delegates validation/projection; it has no quarantine-clear, Pond, bridge-mutator, restart, stop/start, I/O, checkpoint, restore, or replay path.
4. Registered headless non-mutating `runtime.worldbridge.quarantine_diagnostic`, exposed it via the MCP adapter, and nested only the static E240 contract in `runtime_worldbridge_status`.
5. Added `tests/test_worldbridge_quarantine_diagnostic_provenance.py` and `tools/check_worldbridge_quarantine_diagnostic_provenance.py`.  Coverage includes copy isolation, contract-overclaim rejection, Qt-free import, explicit unavailable behavior, real adapter capability publication/release, command/MCP wiring, retained-history semantics, AST mutation exclusion, and dual/default-ready boundary checks.  The pre-existing capability lifecycle expectation was updated to include the newly published diagnostic key; this preserves exact-lease cleanup rather than weakening it.

### Evidence

- Focused E240/E239/E238/E236/command/status regression: **37 passed in 7.38s**.
- E240 plus predecessor/runtime-status mechanical guards: **8 guards passed** (`check_worldbridge_quarantine_diagnostic_provenance.py`, E239, E238, E237, E236, E235, E234, and runtime status).
- Wider WorldBridge/status/GameViewport/SR-input regression: **284 passed, 5 subtests passed in 31.05s**.
- Full offscreen regression: **2299 passed, 34 skipped, 55 subtests passed in 224.51s (0:03:44)** using retained `.pytest-e240-full-20260813-b`.

### Failed-run disposition and fallback

The first full run exposed one exact capability-lease test expectation that still listed only the prior two GameViewport capabilities.  It was corrected to assert publication and release of the new diagnostic host key as part of the same adapter lifecycle; the complete rerun passed.  No production fallback was needed.  If a host is absent, the supported fallback remains the explicit unavailable read model.  If provenance is incomplete or contradictory, projection rejects it rather than guessing, repairing, restoring, or re-admitting anything.

### Remaining boundary

E240 makes existing quarantine facts visible; it does **not** correlate those facts across lifecycle disposal/recreation, prove that a later adapter represents fresh SR/Pond instances, grant current-instance recovery, or establish replay/parity/default-ready evidence.  Those claims remain blocked on complete versioned cross-lane state and identity/link restoration, shared clock/input/lifecycle/RNG/native/plugin coverage, a compensation/restore policy, and replay/interaction parity proof.

