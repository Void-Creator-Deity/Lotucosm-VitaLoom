# E233 WorldBridge Common Clock and Cross-Lane Ordering Authority Decision Gate

Date: 2026-08-12
Status: complete
Completed: 2026-08-12

## Previous gate

E232 closed the diagnostic chain as a final bounded, in-memory E231-export audit sink. It intentionally does not grant persistence, runtime, replay, checkpoint, restore, UI, or default-route authority. No more diagnostic wrappers may be created.

## Objective

Audit the actual SR and PS time and handoff paths, then establish the narrowest truthful authority contract for cross-lane ordering without fabricating a shared simulation clock, time conversion, atomic update, replay admission, lossless mapping, or default readiness.

## Required work

1. Inventory SR clock source, scaling, pause behavior, tick boundary, and phase ordering from the real GameViewport path.
2. Inventory PS Pond clock source, update granularity, root-entity update delta, and bridge handoff behavior from the real Pond/world-bridge path.
3. Decide explicitly whether a common clock or SR-seconds-to-PS-ticks conversion is admitted. If not, expose exact non-admission and prerequisites rather than a placeholder conversion.
4. Define only a serial handoff-order authority that is already true for one opt-in bridge invocation: SR mutation phases complete, SR HUD refresh, SR-to-PS sync, one Pond update, PS-to-SR display reflection, SR snapshot publication. It must not claim atomicity or ordering across calls/threads.
5. Add deterministic tests and a mechanical source/status guard for speed scaling, pause non-advance, one PS tick per bridge handoff, phase ordering, no conversion/shared clock/atomic/replay/default overclaim, static status evidence, and no default runtime wiring.
6. Record focused/wider/full evidence, `docs/mainline_status.md`, a fresh-session prompt, and exactly one next gate.

## Non-goals

No shared simulation timebase, time conversion function, default runtime change, scheduler merge, queued-input merge, cross-thread ordering, atomic checkpoint, full replay, common random-seed contract, checkpoint/restore semantics, lossless mapping, unified Pond readiness, UI host authority, native/OpenGL readiness, or final product-completion claim.

## Planned decision

Current evidence supports only a **single opt-in bridge-handoff serial order**, not a common clock. SR time is scaled scene seconds (`0.05 * max(0.2, simulation_speed)`) and stops while paused; PS time advances by one integer Pond update and ignores the SR delta. E233 will encode this as an explicit no-conversion/no-shared-clock authority contract plus concrete future unblock requirements.


## Implementation and closure

- Added `world_bridge_clock_ordering_authority.py`, a Qt-free static authority inventory plus a caller-reported observation helper. It records the real SR scaled-delta policy, PS one-unit Pond update policy, pause non-advance, and the only admitted sequence: one opt-in `GameViewport.run_snapshot_phase` handoff after SR phases and HUD refresh, before snapshot publication.
- The contract explicitly refuses a shared clock and any seconds-to-ticks conversion. `Pond.update()` takes no bridge delta, so one Pond update cannot truthfully mean a fixed amount of SR scene seconds; at slow and fast SR speeds it remains exactly one PS tick when invoked.
- It also refuses cross-call/cross-thread ordering, atomicity, replay, lossless mapping, and default readiness. It neither imports nor invokes UI/Pond runtime objects, scheduler APIs, I/O, persistence, or network APIs.
- Runtime status now nests the static clock/order contract only. `runtime_mode=dual` and `default_ready=false` remain required; GameViewport/Pond default wiring is untouched.

## Evidence

- Isolated compilation of the E233 module, runtime status, tests, and guard passed.
- Focused E233 + tick-admission/dual-trace/runtime-status coverage: **`18 passed, 5 subtests passed in 3.86s`**.
- E233 guard passed; it confirms source-backed pause early return, SR phase order, handoff placement, one argument-free `Pond.update`, one-unit Pond time increment, static-status nesting, no shared clock/conversion/atomic/replay/default overclaim, and no UI/I/O/scheduler authority.
- Wider WorldBridge/status/GameViewport coverage: **`219 passed, 5 subtests passed in 32.65s`**. The E233 guard, existing tick-admission guard, and runtime-status tool all passed in the same verification pass.
- Full offscreen regression: **`2255 passed, 34 skipped, 55 subtests passed in 306.33s (0:05:06)`**.
- Documentation closure completed with `git diff --check` exit code 0; any LF/CRLF messages are existing workspace warnings rather than a failure.
## Fallback and unblock

If a future runtime needs a shared clock, it must first define scheduler ownership, fixed/variable-step policy, pause/reset/error handling, accumulated-delta policy, SR-to-PS conversion rounding, dropped-frame behavior, queued input order, common deterministic RNG seeds, and atomic shared checkpoint/replay semantics. Until all are proven, retain dual mode and the non-admission flags.

## Exactly one intended next gate

**E234 -- WorldBridge Shared Queued Input Ordering and Pause/Reset Authority Decision Gate.**

