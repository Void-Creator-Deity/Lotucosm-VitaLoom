# E218 WorldBridge Live Dual-Lane Comparability Time-Series Aggregation and Drift-Classification Gate

Date: 2026-08-02
Status: complete

## Previous gate

E217 defined and proved a deterministic evaluator for one validated E216 ordered, non-atomic live trace. It reports mapped-field pass/mismatch, not-observed, and declared-loss states without same-instant, replay, or default-readiness claims.

## Objective

Aggregate multiple validated E217 evaluations or E216 live traces into deterministic diagnostic evidence while preserving each sample's capture order, pair keys, source digests, field statuses, and mapping-loss declarations. Classify repeated observations conservatively without inferring common time, causality, replay divergence, or engine correctness.

## Required work

1. Define sample identity, ordering, schema compatibility, duplicate rejection, and copy-isolated JSON normalization for a multi-sample aggregation boundary.
2. Aggregate per-field/per-pair statuses and deltas without collapsing `not_observed` or `declared_loss` into parity outcomes.
3. Define conservative repeated-observation classifications such as `stable_pass`, `repeated_mismatch_observed`, `intermittent_observation`, and `insufficient_observation` only from explicit samples.
4. Reject invalid E217 evaluations, mixed contracts, duplicate sample identities, digest-invalid inputs, and clock/atomic/replay/lossless/default overclaims before aggregation.
5. Add Qt-free regressions, a guard tool, runtime-status nesting, explicit compilation, the widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No clock merge, no temporal interpolation, no causal diagnosis, no scheduler/input/seed merge, no replay admission, no atomic checkpoint, no automatic correction, no default switch, no removal of mapping losses, no UI-host authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.

## Decision

E218 admits a deterministic, read-only, Qt-free aggregation boundary over one or more validated E217 evaluations. Every sample carries an explicit non-empty `sample_id`, non-negative `sample_index`, intact E217 evaluation, source trace digest, and evaluation digest. Aggregation orders samples only by the explicit index; it rejects duplicate sample IDs, sample indices, and source-trace digests instead of inferring order from the incomparable SR-seconds and PS-unit-tick clocks.

The aggregate uses the union of validated bridge-pair keys. A pair absent from one sample remains an explicit `sample_pair_present=false` / `not_observed` observation rather than fabricated continuity. For every E213/E217 field it preserves all per-sample evidence and classifies only four conservative outcomes: `stable_pass`, `repeated_mismatch_observed`, `intermittent_observation`, and `insufficient_observation`. Single samples, missing pairs, creation-only/partial fields, and declared mapping losses cannot become stable parity.

The validator reconstructs observations and classifications from the nested validated E217 evidence, checks exact pair/field sets and counts, and seals the result with a SHA-256 aggregation digest. It now also converts malformed and unhashable nested status/classification inputs into validation errors rather than exceptions. The contract explicitly keeps clocks uncompared, time alignment and causality uninferred, checkpoint atomicity false, losslessness false, replay admission false, and default readiness false.

## Evidence

- Added `world_bridge_live_trace_time_series.py` with deterministic normalization, pair-union observations, conservative classification, structural validation, reconstruction-based tamper rejection, copy isolation, and aggregation digest.
- Added `tests/test_worldbridge_live_trace_time_series.py` and `tools/check_worldbridge_live_trace_time_series.py`; runtime status now nests `live_dual_lane_comparability_time_series_contract` and names the pilot aggregation module without changing runtime mode or defaults.
- Focused E218 coverage passed **`13 passed in 0.35s`**. The wider WorldBridge/GameViewport/runtime-status scope passed **`92 passed, 5 subtests passed in 4.76s`**.
- E213 mapping-audit, ledger-closure, E215 dual-lane-trace, E214 tick/replay-admission, E216 live-producer, E217 comparability, and E218 time-series guards all passed. Explicit temporary-artifact compilation passed for the E218 aggregator, E217 evaluator, runtime-status integration, and E218 guard. Contract smoke reported `contract_valid=True` with `10` insufficient, `1` intermittent, `0` repeated-mismatch, and `6` stable-pass field classifications.
- Full offscreen regression under `.venv\python.exe` passed **`2130 passed, 34 skipped, 55 subtests passed in 205.98s (0:03:25)`**. `git diff --check` exited `0` with only existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Keep E218 as opt-in diagnostic aggregation. Reject invalid, duplicate, digest-broken, or structurally malformed samples rather than guessing order or continuity. A stable pass is repeated ordered observation only; a repeated mismatch is not a causal diagnosis, engine-error proof, replay divergence, or admission failure. Stronger evidence first needs a bounded live session producer that collects repeated actual bridge hand-offs without owning either lane's clock, followed later by explicit scheduler/input/seed/checkpoint and replay work.

## Exactly one next gate

**E219 -- WorldBridge Bounded Live Comparability Capture Session Producer Adapter Gate**.
