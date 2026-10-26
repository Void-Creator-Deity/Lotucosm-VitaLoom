# E205 WorldBridge Kinematic Mapping-Loss Contract Gate

Date: 2026-08-01
Status: complete

## Previous gate

E204 refreshed the full-worktree evidence and found the WorldBridge mapping audit still explicitly non-lossless, with `velocity_acceleration` listed as a known loss. Passing the audit tool meant that loss was disclosed, not repaired.

## Decision and implementation

Both the SR entity and PS organism inherit the same `EntityBase` storage contract: `velocity` and `acceleration` are mutable float two-vectors initialized independently from `position`. The bridge can therefore copy those values as passive kinematic state without calling force, component, sensor, actuator, or tick APIs.

`world_bridge.py` now has a narrow private vector contract:

- `_finite_vector2()` accepts only two finite non-boolean `Real` values and returns a detached tuple; absent, malformed, non-numeric, or non-finite values yield `None`.
- `_write_vector2()` writes only an already existing mutable vector target; failed writes leave the target route without a fallback replacement or alias.
- `sr_entity_to_organism()` carries validated vectors at creation.
- Both existing sync directions copy only validated velocity/acceleration state. They do not write `.pond`, invoke component behavior, alter command authority, or merge SR/PS ticks.

The mapping ledger now records `velocity_acceleration` as `covered` in both directions and removes it from `known_losses`. It deliberately remains `lossless: false`, `default_ready: false`, with six other named losses and all prior do-not-claim markers intact.

## Evidence

- New contract coverage in `tests/test_worldbridge_kinematic_mapping_contract.py` proves creation copy isolation, SR→PS and PS→SR synchronization, malformed/non-finite no-op behavior, and non-escalation of pilot claims.
- Initial focused bridge/audit run passed `23 passed in 1.21s`.
- All WorldBridge-related tests, including Inspector/command/status/component-projection surfaces, passed `61 passed in 2.74s`.
- `py_compile` passed for both changed runtime modules and the new test. Runtime WorldBridge status, mapping-audit, component-decision, component-projection, and component-projection-diagnostics tools all exited `0`.
- Fresh complete suite after the implementation passed: **`2062 passed, 34 skipped, 50 subtests passed in 225.92s (0:03:45)`**.

## Boundary and next gate

This closes exactly the kinematic ledger item; it does not validate semantic activity control. `EntityBase.active` affects the base update/collision/draw paths, while `Organism.update()` begins component, sensing, and energy work before delegating to the base update. A naïve active-state copy could falsely imply that disabling an SR entity disables PS behavior. E206 must make that authority decision before changing `active_visible_state`; it must also assess whether `visible` has a genuine PS-side rendering consumer or is merely an inert inherited attribute.
