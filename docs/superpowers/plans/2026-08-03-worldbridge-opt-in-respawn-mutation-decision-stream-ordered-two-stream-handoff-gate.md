# E225 WorldBridge Opt-In Respawn Mutation Decision Stream and Ordered Two-Stream Handoff Gate

Date: 2026-08-03
Status: complete

## Previous gate

E224 injects one caller-owned named stream into the SR/PS-aligned mind mutation delta consumer while preserving the default fallback. The preceding probability decision still calls module-global `random.random()`, so the complete opt-in respawn mutation event is not yet locally deterministic or fully attributable to the context.

## Objective

Add a distinct caller-owned `python_random` named stream for the respawn mutation probability decision and prove a strict ordered hand-off: decision stream first, mutation stream only when admitted. Preserve the existing no-context branch and avoid any replay, checkpoint, global entropy, or default-readiness claim.

## Required work

1. Extend the Qt-free adapter with a bounded decision function that validates probability, consumes exactly one named Python stream draw, and records before/after snapshot digests plus the sampled value and admitted/rejected result.
2. Replace the opt-in GameViewport branch only: when an explicit two-stream configuration is attached, use the decision stream for admission and the mutation stream for deltas. The no-context branch must retain the legacy module-global decision plus hash-derived mutation RNG.
3. Require distinct registered stream names and `python_random` family for both roles. Reject malformed probability, duplicate roles, missing streams, or wrong families before the runtime hand-off.
4. Add tests proving deterministic same-seed decisions, rejected decisions do not consume the mutation stream, admitted decisions consume in decision-then-mutation order, module-global RNG non-interference, lazy GameViewport adoption, and unchanged default fallback.
5. Update runtime-status evidence, add E225 guard, run E218-E225 guards, focused/wider/full offscreen regressions, isolated compilation, and `git diff --check`.

## Non-goals

No context construction in GameViewport, no automatic `.pond` configuration, no replacement of other randomness authorities, no restore/reseed API, no replay/checkpoint/common clock/cross-lane ordering claim beyond this two-call local hand-off, no lossless/default-ready claim, and no UI-host authority expansion.
## Decision

E225 is complete. The opt-in respawn pilot now supports two distinct caller-owned `python_random` streams: one for the probability decision and one for mutation deltas. The adapter consumes the decision stream first and consumes the mutation stream only when admitted. GameViewport/default behavior remains on the previous global-decision plus hash-derived fallback when no two-stream configuration is attached.

## Evidence

- Focused E224/E225 adapter coverage: `11 passed in 0.75s`.
- Wider WorldBridge/GameViewport/runtime-status regression: `167 passed, 5 subtests passed in 8.83s`.
- E218-E225 guards passed. The E225 guard proved rejection advances only the decision stream, leaves the mutation stream untouched, preserves global Python/NumPy RNGs, and keeps default readiness false.
- Seven explicit temporary compilations passed with bytecode written only to a system temporary directory.
- Full offscreen regression: `2205 passed, 34 skipped, 55 subtests passed in 214.85s (0:03:34)`.
- `git diff --check` exited 0 with only existing LF-to-CRLF warnings.

## Fallback/unblock

The two-stream pilot is still opt-in and caller-owned. It proves only this bounded local decision-then-mutation call order; it does not close other entropy authorities, establish cross-lane atomicity, or admit replay/checkpoint restore. The no-context GameViewport branch remains authoritative and unchanged in purpose.

## Exactly one next gate

**E226 -- WorldBridge Opt-In Respawn Two-Stream Artifact Binding and Failure-Semantics Gate**.