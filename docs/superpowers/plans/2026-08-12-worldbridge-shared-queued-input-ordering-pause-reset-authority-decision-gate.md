# E234 WorldBridge Shared Queued Input Ordering and Pause/Reset Authority Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E233 proved that SR scaled scene seconds and PS Pond unit ticks do not form a shared clock. It admitted only one existing opt-in serial handoff in `GameViewport.run_snapshot_phase`; it did not admit cross-call ordering, atomicity, replay, or default readiness.

## Objective

Audit the real SR input snapshot lifecycle and bridge handoff paths, then make the narrowest truthful authority decision for queued input, pause, reset, stop, and error isolation. Do not invent a shared queue or scheduler merge.

## Required work

1. Trace keyboard/mouse ingestion, `SrInputState.snapshot`, click-edge consumption, and propagation into SR script contexts.
2. Trace bridge handoff inputs and prove whether SR input is passed to PS/Pond or a shared queue exists.
3. Trace pause, stop, scene/context change, discard/reload, and bridge-exception paths. Separate facts backed by source from missing cross-lane guarantees.
4. Add a Qt-free static authority contract and bounded pure input observation helper. It may describe lane-local input only and must refuse shared queue, ordered input log, replay admission, checkpoint input state, cross-lane pause/reset authority, atomicity, lossless mapping, and default readiness.
5. Add deterministic tests/guards for key/click snapshot edge semantics, paused/stop clear semantics, SR script-before-bridge placement, no input argument on `Pond.update`, no default runtime wiring, static status evidence, and source-level no-overclaim.
6. Record focused/wider/full proof, `docs/mainline_status.md`, a fresh-session prompt, and exactly one next gate.

## Decision and implementation

E234 adds the Qt-free `world_bridge_input_pause_authority.py` inventory and bounded pure observation helper. It is nested in runtime status but has no GameViewport, Pond, default-tick, file, network, or queue wiring. The helper admits only SR-local snapshot availability; even an admitted opt-in bridge handoff reports `ps_received_input=false`, `shared_queue=false`, and `shared_event_log=false`.

The existing host lifecycle is hardened at the real mutable-buffer boundary: start, pause, resume, stop, and discard/reload all call `_sr_input_clear()`. In particular, start drops adapter events collected before a new SR lifetime, and resume drops events collected while paused. This is intentionally a discard policy, not a shared pause/reset coordinator or replay log.

E234 source evidence distinguishes non-game and game paths. Non-game mode captures SR input in `prepare_simulation_tick`, runs SR scripts through `SimulationDriver`, and only later reaches the opt-in snapshot-phase bridge. Game mode also snapshots input before SR scripts, but does not invoke the unified Pond bridge from its thin game tick.

## Verification

- Isolated compile, focused tests, and E234 guard: **`24 passed in 5.54s`**; guard reports all shared queue, replay, shared pause/reset, atomicity, and readiness admissions as false.
- Wider WorldBridge/status/GameViewport/SR-input coverage: **`230 passed, 5 subtests passed in 33.47s`**. E233 and runtime-status guards also passed.
- Full offscreen regression: **`2262 passed, 34 skipped, 55 subtests passed in 264.20s (0:04:24)`** using fresh basetemp `.pytest-e234-full-3cb14ac372374ba0940fdf5f1441e71d`.
## Non-goals

No shared input queue implementation, default scheduler merge, cross-thread queue, deterministic replay input log, shared pause/reset coordinator, shared checkpoint/restore, common clock conversion, common random seed, atomicity, lossless mapping, unified Pond readiness, UI authority, native/OpenGL readiness, or product-completion claim.

## Planned decision

The current source supports only SR-local input capture. The snapshot is taken during SR tick preparation and consumed by SR scripts before the opt-in bridge handoff. `unified_pond_step` synchronizes fields and calls argument-free `Pond.update`; it accepts no input parameter and has no queue. Pause and stop clear the SR input buffer, but PS does not have a shared pause/reset or queued-input contract. E234 will preserve these non-admissions and name the exact future unblock conditions.

## Fallback and unblock

A future shared input contract requires a scheduler owner, a canonical event schema and monotonic sequence source, explicit lane/phase routing, input admission/backpressure rules, pause/resume/stop/reset epoch semantics, error isolation, dropped-event policy, deterministic log serialization, shared RNG/checkpoint integration, and replay parity proof. Until then all input ordering remains SR-local.

## Exactly one intended next gate

**E235 -- WorldBridge Cross-Lane Randomness Authority Closure Decision Gate.**

