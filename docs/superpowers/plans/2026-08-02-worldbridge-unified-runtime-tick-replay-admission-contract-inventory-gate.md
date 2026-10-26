# E214 WorldBridge Unified-Runtime Tick and Replay Admission Contract Inventory Gate

Date: 2026-08-02
Status: complete

## Previous gate

E213 closed the 15-field mapping ledger for consistency review. It deliberately did not admit a unified runtime: the product remains `dual`, unified Pond is opt-in, and lossless mapping, tick merge, and full replay are forbidden claims.

## Objective

Inventory the concrete SR and PS execution loops, their clocks, queued external inputs, bridge hand-off points, and persistence/replay boundaries. Produce deterministic read-only evidence that states whether a safe shared tick or replay contract exists; preserve the dual runtime unless the evidence proves an admission path.

## Required work

1. Trace the actual SR frame/update entry points, PS tick entry points, and WorldBridge call sites without creating a new engine authority.
2. Inventory clock/delta ownership, input ordering, random-seed handling, pause/reset semantics, and error-isolation behavior for both lanes.
3. Inventory SR scene and PS Pond persistence/replay entry points, including where a deterministic shared snapshot would be required.
4. Add a read-only topology/admission guard and deterministic regressions that reject unsupported tick-merge or replay claims.
5. Run focused runtime/WorldBridge coverage and the widest practical baseline; record exact evidence, skips, fallback, unblock path, and exactly one next gate in `docs/mainline_status.md`.

## Non-goals

No tick merge, no default runtime flip, no live cross-lane scheduler, no automatic data migration, no replay implementation claim, and no removal of mapping-loss labels.
## Decision (complete)

The actual topology does **not** admit an SR/PS tick merge or full unified replay. SR is clocked by `GameViewport` with a scaled delta and an explicit seven-phase `SimulationDriver`; PS is invoked only from the SR snapshot phase through the opt-in bridge. `unified_pond_step` accepts the viewport delta but does not pass it to `Pond.update()`, whose clock increments by one and updates root entities with `1.0`.

SR input is captured as an `SrInputState` snapshot during SR preparation. There is no shared input log, random-seed policy, pause/reset/error-isolation policy, checkpoint, or replay contract spanning SR scene state and PS Pond state. The bridge remains a post-SR best-effort hand-off with its own error isolation, not a shared scheduler.

## Evidence

- Added `world_bridge_tick_replay_admission.py`, its deterministic command-line guard, AST regressions, and nested runtime-status evidence.
- Regressions pin the SR phase order; assert the bridge occurs after SR HUD refresh and before SR snapshot publication; prove that `Pond.update()` receives no viewport delta; and prove the distinct PS fixed-step clock.
- Focused runtime/WorldBridge/status coverage passed: `44 passed in 1.75s`.
- Tick/replay admission, ledger-closure, and runtime-status tools passed.
- Explicit temporary-artifact compilation of the new module, the runtime-status integration, and the guard passed. `git diff --check` passed with only pre-existing CRLF conversion warnings.
- Repository-wide offscreen baseline passed with `.venv\\python.exe`: `2091 passed, 34 skipped, 50 subtests passed in 205.98s (0:03:25)`.

## Fallback and unblock

Keep the dual scheduler and opt-in bridge. A future admission proposal must define and prove a common clock/delta policy, deterministic input queue order, random-seed policy, pause/reset/error-isolation semantics, an atomic scene/Pond checkpoint, and replay parity across the boundary. The proposal must also retain all E213 field-level mapping constraints.

## Next gate

Exactly one next gate: **E215 -- WorldBridge Dual-Lane Tick Comparability Contract Gate**.