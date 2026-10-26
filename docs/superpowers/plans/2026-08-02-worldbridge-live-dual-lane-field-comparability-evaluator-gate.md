# E217 WorldBridge Live Dual-Lane Field Comparability Evaluator Gate

Date: 2026-08-02
Status: complete

## Previous gate

E216 proved an opt-in, Qt-free producer can capture one ordered live WorldBridge hand-off with stable bridge pairs and honest non-atomic/no-replay labels. It did not evaluate whether mapped field observations agree or define field-specific tolerance semantics.

## Objective

Define and prove a deterministic evaluator for validated E216 live traces. It must compare only explicitly admitted mapped fields, report per-pair/per-field differences with documented tolerances, and keep lane-owned plus declared-loss fields outside parity claims.

## Required work

1. Reconcile the E213 field ledger with the actual E216 SR/PS projected fields and select the smallest defensible comparison set.
2. Define deterministic exact/tolerance rules for identifiers, position, velocity, acceleration, energy, size/radius, and any lifecycle field that is truly present on both sides.
3. Reject malformed, unvalidated, non-live, atomicity-overclaiming, or pair-incomplete traces before evaluation.
4. Emit per-pair, per-field results plus an aggregate status that distinguishes `comparable_pass`, `comparable_mismatch`, `not_observed`, and `declared_loss`; never emit `lossless` or replay/default admission.
5. Add Qt-free regressions, a guard tool, runtime-status nesting, explicit compilation, widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No clock equality, no common/atomic checkpoint, no scheduler merge, no replay admission, no default switch, no automatic correction, no removal of mapping losses, no UI authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.
## Decision

E217 admits a read-only, Qt-free evaluator for one validated E216 producer payload. It compares only the seven E213-covered fields actually projected on both linked rows: `position`, `energy`, `health`, `size`, `radius`, `velocity`, and `acceleration`. Scalar and vector values use an absolute `1e-9` tolerance solely for finite JSON/float representation noise; no semantic drift budget is admitted. The evaluator reports `comparable_pass`, `comparable_mismatch`, `not_observed`, and `declared_loss` per field and per bridge pair.

The SR checkpoint remains the observation before bridge hand-off and the PS checkpoint remains the Pond observation after update, so equal values are reported as `ordered_cross_boundary_observation_not_same_instant_parity`, not same-instant parity. Creation-only/partial ledger fields are `not_observed`; the six E213 mapping losses remain `declared_loss`. Link keys are checked exactly within the trace pair, while the evaluator makes no cross-track identity-equivalence claim. Invalid E216 payloads, contradictory row `linked_id` values, atomic/shared-clock/replay/lossless/default-ready overclaims, malformed field sets, and digest tampering are rejected.

## Evidence

- Added `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_live_trace_comparability.py` with deterministic per-field/per-pair evaluation, structural validation, SHA-256 evaluation digest, and no-claim invariants.
- Added `tools/check_worldbridge_live_trace_comparability.py` with repository runtime bootstrap; the guard proves equal-field pass, live drift mismatch, no replay/default admission, runtime-status nesting, and tamper rejection.
- Added `tests/test_worldbridge_live_trace_comparability.py` covering equal/mismatch/tolerance/not-observed/loss states, invalid producer payloads, identity-link rejection, structural re-seal tampering, digest/no-claim tampering, deterministic ordering/copy isolation, Qt-free import, and runtime status. The real offscreen `GameViewport` + live `Pond` trace test now consumes the evaluator.
- Focused evaluator plus offscreen GameViewport coverage passed **`18 passed in 0.88s`**; all WorldBridge/Viewport integration coverage passed **`76 passed, 5 subtests passed in 3.18s`**.
- Mapping-audit, ledger-closure, dual-lane-trace, tick/replay, live-producer, and E217 comparability guards passed. Explicit temporary-artifact compilation passed for evaluator, producer, runtime status, and E217 guard files.
- Full offscreen regression under `.venv\\python.exe` passed **`2117 passed, 34 skipped, 55 subtests passed in 217.92s (0:03:37)`**. `git diff --check` exited `0` and emitted only existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Keep live trace capture opt-in and use evaluator output for diagnostics only. If field projection, pair keys, linked IDs, or producer validation fail, reject the evaluation rather than guessing correspondence. A `comparable_mismatch` is an observed cross-boundary difference, not proof of an engine bug, causal drift, replay divergence, or admission failure. Stronger runtime admission still requires a common clock/delta policy, scheduler/input/seed semantics, atomic checkpoints, and deterministic replay/parity evidence.

## Exactly one next gate

**E218 -- WorldBridge Live Dual-Lane Comparability Time-Series Aggregation and Drift-Classification Gate**.

