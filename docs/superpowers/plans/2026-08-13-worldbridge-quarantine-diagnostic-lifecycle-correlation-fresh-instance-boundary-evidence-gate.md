# E241 — WorldBridge Quarantine Diagnostic Lifecycle Correlation and Fresh-Instance Boundary Evidence Gate

**Status:** complete  
**Date:** 2026-08-13  
**Previous gate:** E240 — WorldBridge Quarantine Diagnostic Provenance and Operator Visibility Decision Gate

## Objective

Determine and expose, without adding recovery authority, whether an E240 retained failure diagnostic belongs to the current quarantined runtime, is merely historical after a disposal boundary, or has enough same-adapter evidence to identify a later SR/Pond lifetime as freshly constructed rather than a reuse of the failed instances.

## Audit findings

1. `GameViewport._begin_sr_snapshot_lifetime()` creates a new opaque `SrRuntimeSnapshotAuthority` epoch only after scene runtime loading; `_end_sr_snapshot_lifetime()` ends it. `_discard_scene_runtime_state()` and `_stop_simulation()` call the end method before clearing the suspended-quarantine flag.
2. The existing SR epoch can prove a new SR snapshot lifetime, but E240 currently does not capture the epoch at failure and there is no bounded identifier for the active unified Pond instance. Therefore E240's retained receipt is correctly historical after clear, but it cannot prove a fresh SR+Pond pair later.
3. `_ensure_unified_pond()` is the one GameViewport construction seam for the opt-in Pond. It already creates a new Pond only when `_unified_pond is None`; stop/discard explicitly set that field to `None` before clearing suspension.
4. The current diagnostic capability is adapter-owned and query-only. A lifecycle correlation extension can remain in that same seam: no global lookup, no new runtime construction, no process-wide identity registry, and no cross-adapter claim. If the composed host is absent, it must return explicit unavailable.
5. Existing lifecycle code cannot prove restore/replay, identity/link restoration, scene equivalence, cross-adapter continuity, or full checkpoint state. E241 must not infer any of those from a changed epoch/counter.

## Decision boundary

E241 may add only ephemeral, adapter-local, opaque lifecycle evidence:

- the active SR snapshot epoch already owned by the viewport;
- an adapter-local monotonic Pond-lifetime token assigned only when `_ensure_unified_pond()` constructs a Pond;
- a failure-time tuple of those two opaque values when both are present;
- a disposal observation recorded only while a quarantined tuple is being discarded; and
- a Qt-free/copy-isolated projection that distinguishes current quarantine, retained-history/no-current-runtime, incomplete current evidence, and same-adapter fresh-boundary observation.

A `fresh_instance_boundary_observed` result means only that the same adapter observed the failed SR/Pond tuple, then its explicit discard path, then a different active SR epoch and different newly constructed Pond token. It is **not** repair, recovery, re-admission, same-instance retry, exact world equivalence, cross-adapter correlation, replay, checkpoint restoration, lossless mapping, or default readiness.

## Mandatory negative capabilities

No E241 code may:

- mutate quarantine, invoke stop/start/reload, clear retained records, or make an admission decision;
- construct/reuse a Pond while querying, inspect live SR/Pond objects, expose object IDs/handles, or persist lifecycle records;
- introduce global process identity, file/network I/O, checkpoint/restore/replay/rollback/compensation, or scheduler control;
- treat a changed SR epoch alone as proof of a fresh SR+Pond pair;
- change `runtime_mode="dual"`, `unified_pond_enabled=false`, `default_ready=false`, `.pond` semantics, manifests, AI command registry flows, Inspector bindings, or SR2D seams.

## Implementation steps

1. Add a Qt-free authority with strict typed validation and static contract for failure tuple, disposal tuple, current tuple, and correlation states.
2. Capture opaque lifecycle tuple only at actual Pond construction/failure and observe it across existing stop/discard boundaries; add a copy-isolated GameViewport query that only reads these records and the E240 diagnostic result.
3. Add a headless non-mutating command/MCP surface using the existing diagnostic host seam, explicit unavailable behavior, focused tests, and an AST/source guard.
4. Run focused, wider WorldBridge, and full offscreen regressions; update plan/status/fresh-session prompt with exact evidence and exactly one next gate.

## Expected proof

- Current suspended runtime correlates only when its active tuple matches the captured failure tuple.
- After explicit same-adapter disposal and construction of a different SR epoch plus Pond token, the result says `fresh_instance_boundary_observed` while retaining every repair/replay/default-ready claim as false.
- Missing or partial tuple evidence is explicit unavailable/incomplete/historical evidence, never guessed fresh proof.
- Output remains copy-isolated, Qt-free, command/MCP read-only, and compatible with the existing capability release lifecycle.

## Fallback and unblock path

If either lifecycle tuple cannot be observed, project an explicit unverified/incomplete state and preserve E240's historical diagnostic only. Cross-adapter lifecycle correlation remains out of scope until a higher-level Qt-free owner supplies versioned lifecycle identity and disposal evidence. Recovery/replay remains blocked on complete cross-lane state, identity/link restoration, shared clock/input/lifecycle/RNG/native/plugin coverage, compensation policy, and parity evidence.

## Exactly one intended next gate

E242 — WorldBridge Quarantine Lifecycle Correlation Consumer Boundary and Bounded Operator Presentation Gate.


## Implementation completed

- Added the Qt-free `world_bridge_quarantine_lifecycle_correlation.py` authority. It validates opaque SR epoch/Pond lifetime pairs, explicit quarantined disposal observations, and copy-isolated correlation projections.
- Tightened fresh-boundary proof to require both a different SR epoch and a different adapter-local Pond lifetime token. A one-field change remains `current_lifecycle_not_proven_fresh_from_failure`.
- Added adapter-local capture/observation in `GameViewport`: tokens are assigned only after actual Pond construction; failure capture occurs before suspension; only `scene_runtime_discard` and `simulation_stop` record disposal observations.
- Extended the existing diagnostic host with an optional lifecycle protocol so old E240 hosts remain compatible and absent E241 support returns explicit unavailable output.
- Added the read-only headless command/MCP surface `runtime.worldbridge.quarantine_lifecycle_correlation` and nested the contract in runtime status.
- Added focused tests and `tools/check_worldbridge_quarantine_lifecycle_correlation.py`.

## Verification evidence

- Focused E241/E240/related command/status/GameViewport coverage: **49 passed in 10.56s**.
- Wider WorldBridge/status/GameViewport/SR-input coverage: **296 passed, 5 subtests passed in 35.02s**.
- Full offscreen suite: **2304 passed, 34 skipped, 55 subtests passed in 257.58s (0:04:17)**.
- E241 and E240 guards passed. `py_compile` passed for all modified runtime/test/guard files.

## Boundary and fallback

`fresh_instance_boundary_observed` proves only same-adapter observation of the failed tuple, its explicit stop/discard disposal, and a later pair with both opaque values changed. It does not clear quarantine, retry, repair, re-admit writers, restore/replay state, prove scene equivalence, correlate adapters, or make default-ready claims. If either token is missing or only one changes, the projection remains incomplete/unverified rather than guessing. Existing `.pond` semantics, manifests, SR2D seams, and default flags remain unchanged.

## Exactly one intended next gate

**E242 ? WorldBridge Quarantine Lifecycle Correlation Consumer Boundary and Bounded Operator Presentation Gate.**
