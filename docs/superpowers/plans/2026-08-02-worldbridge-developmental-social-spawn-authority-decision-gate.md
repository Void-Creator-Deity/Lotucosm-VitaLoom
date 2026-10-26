# E212 WorldBridge Developmental Profile and Social Spawn Authority Decision Gate

Date: 2026-08-02
Status: complete

## Previous gate

E211 retained maximum energy and health as creation-only SR→PS seeds. Its capacity-decision contract prohibits continuous copying because descriptor/Inspector authority, SR repair/interoception, and PS clamp/metabolism/reproduction/serialization behavior do not share a lifecycle policy.

## Objective

Trace the partial `developmental_profile` and `social_enabled` WorldBridge fields from spawn request through SR descriptor/command authority and PS organism construction/runtime behavior. Decide whether the existing spawn-request-only routes are correctly scoped or require an explicit mapping-loss contract.

## Required work

1. Inventory SR spawn descriptor, Registry, Inspector command-binding, and `.pond` persistence authority for developmental and social settings.
2. Inventory PS developmental application/reset, social-memory or signaling behavior, inheritance, mutation, and Pond persistence routes.
3. Prove the creation/spawn contract and whether any later bridge copying would change lifecycle, command, persistence, or replay semantics.
4. Add deterministic regressions that prevent unreviewed continuous developmental/social synchronization.
5. Record the decision, fallback, unblock path, and exactly one next gate in `docs/mainline_status.md`.

## Non-goals

No per-tick profile synchronization, no Inspector or Registry bypass, no `.pond` schema change, no inheritance-policy rewrite, no tick merge, replay claim, or default-ready claim.



## Decision (complete)

`developmental_profile` and `social_enabled` remain **partial, spawn-request-only SR-to-PS inputs**. The bridge may extract script properties from a spawn request, initialize a newly created PS organism, and expose the PS developmental stage in the SR debug HUD. It must not use normal tick synchronization to copy the profile, social enablement, or PS runtime state back into SR descriptors.

The boundary is intentional. PS developmental state owns stage, counters, plasticity and child-stage reset. PS social behavior is gated by its own runtime flag and memory-gene lifecycle. Inheritance resets a child stage and does not carry `social_learning_enabled`; the PS organism serializer does not persist these runtime fields. A continuous bridge copy would manufacture a source of truth across distinct lifecycle, inheritance, and persistence rules.

## Evidence

- Added the read-only `world_bridge_spawn_profile_decision` payload to the mapping audit.
- Added regression coverage for spawn seeding, later PS runtime changes surviving both normal sync directions, inheritance/serializer behavior, and the absence of profile/social reflection in normal sync ASTs.
- Focused coverage: `26 passed in 0.43s`.
- Spawn-profile, capacity, mapping-audit, and runtime-status tools passed.
- Explicit temporary-artifact compilation passed; `git diff --check` passed for relevant tracked paths.

## Fallback and unblock

Retain spawn-only authority. A broader route requires a field-level SR/PS lifecycle contract, Registry and Inspector command policy, scene/Pond persistence proof, inheritance/mutation/social-memory parity, and deterministic replay plus tick-order evidence.

## Next gate

Exactly one next gate: **E213 -- WorldBridge Mapping Ledger Closure and Unified-Runtime Admission Gate**.
