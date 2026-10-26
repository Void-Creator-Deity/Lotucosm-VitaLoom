# E206 WorldBridge Active/Visible State Authority Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E205 closed only passive kinematic mapping. `active_visible_state` remained an unmapped WorldBridge loss, and shared attribute names did not prove shared semantic authority.

## Decision

`active_visible_state` remains intentionally **not mapped**.

- SR `EntityBase.active` gates base update work, collision checks, and drawing. In contrast, `Organism.update()` checks only `dead` before running component sensing/update/signaling, ingestion, actuator force, and energy paths; base-update delegation occurs afterwards. Copying false `active` would falsely advertise PS simulation inactivity while side effects continue.
- `visible` is inherited storage used by the legacy base drawing path, but no WorldBridge-owned PS display/render adapter consumes it as authoritative bridge output. Copying it would claim display parity without a proved consumer.
- The bridge contains no direct or reflective route for either flag, and the mapping audit continues to classify their joint field as `not_mapped`.

## Evidence

`tests/test_worldbridge_active_visible_authority_decision.py` proves that an inactive PS organism still runs a component update and loses energy, preserves the non-lossless/default-not-ready ledger classification, and AST-rejects unreviewed direct/reflection routes for both flags.

Focused decision/bridge/audit coverage passed **`22 passed in 1.05s`**. Runtime WorldBridge status and mapping-audit tools passed; the decision test compiled. `git diff --check` exited `0` with only pre-existing LF/CRLF warnings. E206 is test/document-only; the immediately prior fresh full-suite baseline remains **`2062 passed, 34 skipped, 50 subtests passed in 225.92s`**.

## Fallback, unblock path, and next gate

Keep lane-local active/visible behavior. Future active mapping requires a PS lifecycle guard that stops all component/lifecycle side effects before a false active state means simulation control. Future visible mapping requires a real PS display adapter plus rendered parity evidence.

E207 must inventory `render_identity` representations and renderer/display consumers before proposing a narrow projection. It must not equate color state transfer with visual parity.
