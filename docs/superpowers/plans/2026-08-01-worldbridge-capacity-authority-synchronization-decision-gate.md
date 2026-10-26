# E211 WorldBridge Capacity Authority and Synchronization Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E210 retained memory genes as a loss because SR descriptor/runtime learning and PS evolutionary/persistence semantics do not share a WorldBridge authority contract. The mapping ledger still labels `max_energy` and `max_health` as `creation_only` SR-to-PS fields.

## Objective

Trace the authority and lifecycle of maximum energy/health capacity on SR entities and PS organisms. Decide whether creation-only seed values are correct, whether any continuous direction can be made safe, or whether the ledger needs a stricter non-synchronization contract.

## Required work

1. Inventory SR maximum-capacity fields, repair/health/Inspector command routes, and `.pond` descriptor/persistence semantics.
2. Inventory PS max-capacity construction, clamping, metabolism/combat/development paths, serializer behavior, and any mutation/evolution route.
3. Prove the current bridge creation contract and detect whether bidirectional copying would silently change lane authority or repair behavior.
4. Add deterministic regression evidence prohibiting unreviewed continuous capacity synchronization through WorldBridge.
5. Record the decision, fallback, and unblock path; preserve the ledger state unless a field-level contract proves otherwise; name exactly one next gate.

## Non-goals

No capacity synchronization, health/energy repair rewrite, Inspector/Registry bypass, `.pond` schema change, replay claim, tick merge, or default-ready claim.


## Decision (complete)

The bridge retains a **creation seed only** contract for `max_energy` and `max_health`: the SR values initialize a newly constructed PS organism, but neither regular SR→PS nor PS→SR display synchronization reflects the capacity fields. The mapping ledger therefore remains `creation_only` / `sr_to_ps` for both fields.

This is deliberately stricter than a generic numeric-field sync. SR maximum values feed descriptor/Inspector authority, repair/health command semantics, and interoception normalization. PS maximum values are constructor- and health-clamp inputs, bound energy recovery/metabolism, affect reproduction/inheritance decisions, and round-trip through PS serialization. Continuous copying would therefore silently make tick ordering choose a capacity authority and could alter current-value repair/clamp behavior.

## Evidence

- Added the read-only `world_bridge_capacity_decision` payload and integrated it into the mapping-loss audit.
- Added a regression that proves creation seeding, both one-way sync paths preserve each lane's later capacity values, PS clamp/serializer behavior remains local, and the sync function AST contains no capacity reflection route.
- Focused WorldBridge coverage: `17 passed in 0.47s`.
- `tools/check_worldbridge_capacity_decision.py`, `tools/check_worldbridge_mapping_audit.py`, and `tools/check_runtime_worldbridge_status.py` passed.
- The default `py_compile` cache replacement first encountered an existing locked runtime `__pycache__` file (`WinError 5`). Compilation to an explicit temporary artifact then passed; focused tests and guard tools also imported and exercised the new modules successfully.

## Fallback and unblock

Keep capacity changes lane-local after construction. A future synchronization proposal must first establish a field-level SR/PS authority contract, Inspector and command-binding policy, scene/Pond persistence round trip, repair/clamp parity, and deterministic replay plus tick-order proof.

## Next gate

Exactly one next gate: **E212 -- WorldBridge Developmental Profile and Social Spawn Authority Decision Gate**.


