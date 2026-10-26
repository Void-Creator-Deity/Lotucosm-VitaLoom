# E224 WorldBridge Opt-In Named-Stream Adapter Adoption and One-Handoff Parity Gate

Date: 2026-08-03
Status: complete

## Previous gate

E223 proved an opt-in caller-owned deterministic randomness context with stable named streams and full local consumed-state snapshots, but no real SR/PS consumer accepts that context. GameViewport/default tick remains free of the context and legacy randomness behavior remains unchanged.

## Objective

Adopt exactly one named stream into one real, bounded SR/PS hand-off seam as an explicit opt-in adapter pilot. Prove that the adapter injects a caller-owned stream into the existing SR mind mutation consumer, that default GameViewport behavior is unchanged when no context is supplied, and that the opt-in path produces stable, inspectable parity evidence without claiming replay or global entropy closure.

## Scope

1. Add a Qt-free adapter module that validates the E223 context, selects one explicitly registered named Python stream, invokes the existing `sr_mind_gene.mind_dict_mutate` seam, and returns mutation output plus before/after snapshot evidence.
2. Add a narrow, lazy GameViewport hand-off seam for the existing war-respawn mind mutation path. No context is created in GameViewport, no module-global RNG is reseeded/restored, and the no-context branch remains byte/behavior compatible with the current fallback.
3. Add direct tests for adapter validation, named-stream ownership, consumed-state change, copy isolation, deterministic same-seed output, default no-context fallback, explicit opt-in viewport hand-off, and global RNG non-interference.
4. Update E223 guards/tests to distinguish lazy opt-in adapter availability from default ownership; keep runtime status dual, unified Pond disabled, replay admission false, and default readiness false.
5. Run focused tests, wider WorldBridge/GameViewport/status regressions, E218-E224 guards, isolated compilation, full offscreen regression, and `git diff --check`.

## Non-goals

No automatic context construction, no default tick adoption, no `.pond` or manifest changes, no replacement of global/dynamic/UUID4/native entropy, no restore API, no replay loader/admission, no checkpointing, no lossless mapping, no common clock/cross-lane order claim, and no OpenGL/UI authority change.

## Acceptance criteria

- The adapter is Qt-free and caller-owned; it rejects missing, wrong-family, missing-name, or unregistered streams without mutating the context.
- One real SR/PS mind mutation hand-off consumes only the named local stream when explicitly configured and records before/after local snapshot digests.
- With no configured context, the existing GameViewport mutation branch follows its current fallback and no context module is imported or instantiated by default construction/tick.
- E223 invariants remain true, with the guard changed only to permit a lazy opt-in seam and to assert no default context ownership.
- Evidence is recorded in this plan, the fresh-session prompt, and `docs/mainline_status.md`, with exactly one next gate.
## Decision

E224 is complete. One real SR war-respawn mind mutation hand-off can now consume one caller-owned E223 `python_random` named stream through a Qt-free adapter. GameViewport exposes only a lazy explicit setter/helper seam, creates no context, and preserves the previous `random.Random(hash(...))` fallback when no context is attached.

## Evidence

- Focused adapter coverage: `7 passed in 0.47s` after final encoding cleanup (`7 passed in 0.62s` on the first clean pass).
- Focused adapter/SR mind/GameViewport/status bundle: `18 passed in 1.67s`.
- Wider WorldBridge/GameViewport/runtime-status regression: `163 passed, 5 subtests passed in 8.60s`.
- E218-E224 guards passed. E224 reported a consumed named local stream, unchanged module-global Python/NumPy states, no default context creation, no default tick attachment, replay admission false, and default readiness false.
- Nine isolated temporary compilations passed with bytecode written only to a system temporary directory.
- Full offscreen regression: `2201 passed, 34 skipped, 55 subtests passed in 212.74s (0:03:32)`.
- UTF-8 BOM was removed from the new test/guard files; `git diff --check` exited 0 with only existing LF-to-CRLF warnings.

## Fallback/unblock

If no context is supplied, the existing fallback remains authoritative. The mutation probability decision still uses the legacy module-global Python RNG, so E224 does not make the whole respawn event deterministic. Broader adoption remains blocked until an independently named decision stream proves ordered decision-plus-mutation evidence while preserving the default branch.

## Exactly one next gate

**E225 -- WorldBridge Opt-In Respawn Mutation Decision Stream and Ordered Two-Stream Handoff Gate**.