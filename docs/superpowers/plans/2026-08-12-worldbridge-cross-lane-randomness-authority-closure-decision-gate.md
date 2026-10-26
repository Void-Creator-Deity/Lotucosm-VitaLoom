# E235 WorldBridge Cross-Lane Randomness Authority Closure Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E234 proved that SR input is a lane-local mutable buffer, clears adapter input at start/pause/resume/stop/discard, and has neither a PS input route nor a shared input queue, event log, pause/reset owner, checkpoint protocol, or replay admission.

## Objective

Close the immediately remediable SR randomness ownership defects on the actual dual-lane path, then state the precise residual SR/PS/bridge authority boundary. The work must not turn read-only capture or a local deterministic pilot into a claim of cross-lane deterministic replay.

## Required work

1. Re-audit the current `GameViewport` random call sites, the existing E221--E225 contracts, Pond initialization/update randomness, and `unified_pond_step` signature.
2. Replace the SR runtime's unseeded temporary `random.Random()` mutation source and Python-`hash()`-derived respawn source with one explicit per-loaded-SR-runtime Python RNG owner.
3. Resolve that owner seed from `.pond` data without changing global Python or NumPy RNG state: `pond_config.sr_runtime_seed`, then existing `pond_config.proc_seed`, then documented constant `12345`.
4. Route SR entity initial velocity, nutrient placement, signal-edge mutation, and legacy respawn admission/mutation through that owner. Preserve the existing explicit caller-owned respawn two-stream pilot as an override.
5. Add a Qt-free engine-side authority module, deterministic unit tests and source guards. It must reject a claim that the PS legacy NumPy/Python globals, bridge RNG transport/seed agreement, atomic checkpoint, replay, lossless mapping, or default readiness are solved.
6. Update the earlier E221 inventory to remove only sources actually eliminated from the current SR bridge path; retain all real global/dynamic/native gaps.
7. Run focused, broader WorldBridge, and full offscreen regression evidence. Record proof, fallback/unblock, and exactly one next gate.

## Design decision

A loaded SR scene now owns one `random.Random` instance for its whole in-memory runtime lifetime. The source is explicit and deterministic for a given scene seed, but it is **SR-local**. It is not a shared SR/PS RNG, does not reseed or capture process-global Python/NumPy RNGs, does not transport RNG state through `unified_pond_step`, and does not make a bridge tick atomic or replayable.

`sr_runtime_seed` is an optional additive `.pond` field. In its absence, the pre-existing game procedural seed is reused; if neither field exists the preserved procedural default is `12345`. This resolves a stable seed before scene entity construction, avoids Python interpreter hash randomization, and leaves manifests and ordinary `.pond` structure compatible.

## Non-goals

No global reseeding, global-state restore, PS `Pond` RNG migration, cross-lane seed agreement, shared RNG context transport, random draw log, checkpoint/restore protocol, replay admission, scheduler merge, transaction/rollback, lossless mapping, unified Pond default activation, native/OpenGL readiness, or project-completion claim.

## Fallback and unblock

The dual bridge remains not deterministic-ready because `Pond` initialization/update and reachable PS systems use legacy global NumPy/Python RNG sources, scripts/plugins may own additional entropy, and the bridge has no seed/context/state transport. A future shared randomness authority needs a canonical scene/project seed schema, isolated PS RNG ownership, explicit lane stream allocation, bridge transport and ordered consumption semantics, checkpoint/restore, input integration, error/rollback policy, replay parity tests, and native/plugin entropy coverage.

## Exactly one intended next gate

**E236 -- WorldBridge Cross-Lane Transaction, Failure Isolation, and Atomicity Authority Decision Gate.**
## Completion evidence

- Implemented the Qt-free `world_bridge_sr_runtime_randomness.py` owner contract. It resolves `pond_config.sr_runtime_seed`, then `pond_config.proc_seed`, then `12345`, creates caller-held SR-local `random.Random` state, and exposes deterministic detached test/tool fallback state without advancing Python or NumPy process-global RNG state.
- Routed the actual `GameViewport` SR paths through the loaded-runtime owner: initial entity velocity, dynamic membrane entity construction, nutrient placement, signal-edge mutation, legacy respawn admission, and legacy respawn mind mutation. Direct nested-entity or direct test/tool invocation uses a deterministic detached fallback only when no real viewport owner exists. The existing caller-owned two-stream respawn pilot remains an explicit override.
- Added `tests/test_worldbridge_cross_lane_randomness_closure.py` and `tools/check_worldbridge_cross_lane_randomness_closure.py`. They prove seed precedence, Qt-free importability, process-global RNG neutrality, source routing, contract/status nesting, and explicit non-admission of PS migration, bridge RNG transport, seed agreement, ordered cross-lane consumption, checkpoint/restore, replay, lossless mapping, and default readiness.
- Updated the E221 inventory only for eliminated GameViewport sources: the authority count is six, with explicit caller-owned instances plus UUID, dynamic/plugin, and native/third-party entropy still uncaptured. This does not claim the PS lane is deterministic.
- Verification: E235 guard plus focused coverage `50 passed in 7.89s`; broader WorldBridge/status/GameViewport coverage `245 passed, 5 subtests passed in 34.26s`; full offscreen regression `2271 passed, 34 skipped, 55 subtests passed in 267.89s (0:04:27)`. E221 guard also passed. `git diff --check` exits 0; the workspace emits pre-existing inaccessible historical pytest-directory and LF/CRLF notices but no diff error.

## Closure boundary

E235 closes only local SR runtime ownership. It does **not** solve PS global RNG migration, common SR/PS seed agreement, bridge RNG context transport, cross-lane random draw ordering, transactional checkpoint/restore, rollback, deterministic replay, lossless mapping, unified Pond default readiness, native readiness, OpenGL readiness, or the project-wide refactor.
