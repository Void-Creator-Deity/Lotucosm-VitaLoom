# E237 WorldBridge Cross-Lane Checkpoint/Restore Feasibility and Replay Preconditions Decision Gate

Date: 2026-08-12
Status: complete

## Previous gate

E236 closed the strongest currently truthful failure boundary: an opt-in ordered hand-off now has preflight and phase-labelled failure receipts, but it remains explicitly non-atomic. Current public seams do not expose a shared SR/PS restoration protocol, so E236 admitted no rollback, atomic checkpoint, replay, or default readiness.

## Objective

Audit the real state ownership and serialization/restoration seams for one WorldBridge hand-off: SR runtime entities and scene state, Pond and organisms/systems, bridge link metadata, scheduler/clock state, input/lifecycle state, RNG state, trace/capture state, scripts/plugins/native extensions, and UI adapter state. Implement only a source-backed feasibility contract or bounded checkpoint mechanism that the current public contracts can honestly restore. Do not call copied observations, trace payloads, a partial snapshot, or a process-local object reference a checkpoint/replay authority.

## Required work

1. Inventory existing serialize/snapshot/checkpoint/restore/load/reset methods and identify their state owner, scope, mutability, versioning, and failure semantics.
2. Demonstrate whether an actual SR runtime and Pond can be restored from public seams after a bridge hand-off without changing .pond, manifests, AI registry/Inspector bindings, SR2D seams, or Qt-free L0-L4 contracts.
3. Record unrecoverable state categories, including random/input/lifecycle/plugin/native and partial Pond-system effects; distinguish observation from restoration.
4. Decide the strongest truthful scope: no checkpoint/restore admission with a feasibility inventory, or a bounded isolated checkpoint whose restore boundary and exclusions are mechanically proven.
5. Add Qt-free tests and a mechanical guard that reject atomicity/replay/default-ready overclaims and prove any claimed restoration behavior.
6. Run focused, wider WorldBridge, and full offscreen regression; record evidence, fallback/unblock, and exactly one next gate.

## Initial audit hypothesis

Existing dual-lane trace/capture modules create read-only, copy-isolated observations, but observation does not restore live objects. GameViewport/Pond lifecycle setup likely builds runtime object graphs rather than serializing/restoring them. E235 leaves PS randomness and bridge RNG transport unresolved; E234 leaves shared input/lifecycle authority unresolved. Unless source inspection finds a complete versioned SR+PS state protocol with restoration of linked objects and side effects, E237 must retain checkpoint/restore and replay as false.

## Non-goals

No general distributed transaction, no automatic rollback, no common scheduler/clock admission, no shared RNG protocol, no lossless mapping claim, no Unified Pond default enablement, and no native/OpenGL readiness claim.

## Decision and implementation

E237 completed the source-backed feasibility decision: **there is no available live cross-lane SR/PS checkpoint, restore, atomic snapshot, or replay admission in the current runtime.** The new Qt-free authority, `world_bridge_checkpoint_restore_feasibility.py`, records this as a read-only inventory rather than fabricating a restore API. Its validator rejects checkpoint, restore, replay, atomicity, rollback, lossless-mapping, and default-ready overclaims.

The audit distinguishes three useful but insufficient lane-local seams:

- SR runtime snapshots are epoch-scoped, copy-isolated JSON projections and expose no live entity/scene/RNG/input restoration operation.
- WorldBridge live traces and capture artifacts are read-only evidence; their own contracts retain `atomic_checkpoint=False` and no restore input/object authority.
- `PondSerializer.deserialize_pond()` constructs a fresh `pond_class(...)`; `serialize_pond()` does not persist `pond.time`, and neither seam restores root registration, bridge link metadata, or the in-place live Pond/SR graph.

`Pond.update()` also advances time and multiple stateful systems, while existing E234/E235 contracts still deny shared input/lifecycle restoration and SR/PS RNG state/order checkpoints. Runtime status now nests the E237 feasibility contract without changing `runtime_mode="dual"`, opt-in Unified Pond behavior, or `default_ready=False`.

## Evidence

- Focused E237 checkpoint/restore, E236 transaction, trace, replay, randomness, input, and status coverage: **43 passed in 7.35s**.
- Wider WorldBridge/status/GameViewport/SR-input coverage: **258 passed, 5 subtests passed in 38.08s**.
- Full offscreen regression: **2284 passed, 34 skipped, 55 subtests passed in 264.18s (0:04:24)**.
- E237 mechanical guard plus E234/E235/E236 guards passed. `git diff --check` exited 0; LF/CRLF messages are existing workspace warnings, not diff errors.

## Fallback and unblock path

Keep the E236 phase-labelled non-atomic failure receipts and treat the E237 inventory as an explicit non-admission. A future recovery or replay path must first define a versioned complete SR scene/entity/script bundle, complete in-place Pond/system state, bridge identity/link restoration, shared clock/input/lifecycle/RNG state and draw ordering, restore ordering, partial-failure compensation, and cross-lane replay/parity proof. Do not equate serializer reconstruction or trace capture with recovery.

## Exactly one intended next gate

E238 -- WorldBridge Cross-Lane Recovery Compensation and Controlled Restart Authority Decision Gate.
