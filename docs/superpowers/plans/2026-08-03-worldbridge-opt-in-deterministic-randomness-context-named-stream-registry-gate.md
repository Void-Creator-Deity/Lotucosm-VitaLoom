# E223 WorldBridge Opt-In Deterministic Randomness Context and Named-Stream Registry Gate

Date: 2026-08-03
Status: complete

## Previous gate

E222 proved a strict diagnostic binding between one sealed E220 artifact and distinct pre/post E221 observations, but it can only report change for two process-global RNG states and cannot own or enumerate ephemeral/caller-owned RNG instances, stable derived seeds, UUID identity entropy, dynamic scripts, or native sources.

## Objective

Define and prove a Qt-free, explicit caller-owned deterministic randomness context with stable named-stream derivation and full consumed-state snapshot evidence, providing the minimum future injection authority for local Python and NumPy RNGs without changing any default bridge, scene, Pond, script, or plugin behavior.

## Required work

1. Define versioned context identity, explicit root seed material policy, SHA-256-based stable stream derivation independent of Python `hash`, wall time, process-global RNGs, and OS entropy.
2. Support bounded unique named streams for local Python `random.Random` and NumPy `Generator`/bit-generator families. Reject duplicate, malformed, unsupported, or over-capacity registration deterministically.
3. Provide explicit stream access and deterministic full consumed-state snapshots with exact owner/name/family/derivation metadata, copy isolation, strict validation, and integrity digests. If deterministic UUID-like identities are offered, label their namespace/stream ownership and do not confuse them with UUID4.
4. Prove context construction, stream registration/access, snapshot construction, and runtime-status examples never read, seed, restore, or advance module-global Python/NumPy RNGs. Keep GameViewport/default tick free of the context until a later adapter gate.
5. Add Qt-free tests, source/AST guards, runtime-status nesting, E221-E223 regression guards, isolated compilation, widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No monkey-patching or reseeding globals, no default GameViewport/Pond/script integration, no replacement of existing entropy behavior, no scene/Pond restore, no dynamic/native entropy closure, no common clock or cross-lane order claim, no atomic checkpoint, no replay loader/admission, no lossless/default-ready claim, no Qt/UI authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.

## Decision

E223 is complete. The opt-in caller-owned context is a diagnostic/injection foundation only: it owns bounded local Python and NumPy named streams, stable SHA-256 derivation, and full consumed-state snapshots. It is not connected to GameViewport, default WorldBridge ticking, `.pond` loading, replay, checkpoint restore, or any existing randomness authority.

## Evidence

- Focused E223 coverage: `12 passed in 0.63s`.
- Wider WorldBridge/GameViewport/runtime-status regression: `156 passed, 5 subtests passed in 9.18s`.
- E218-E223 guards all passed; the deterministic-context guard reported two streams, unchanged Python/NumPy globals, no Python `hash`, wall time, or OS entropy, no restore API, `replay_admitted=false`, and `default_ready=false`.
- Nine explicit temporary compilations passed, writing bytecode only under a system temporary directory.
- Full offscreen regression: `2194 passed, 34 skipped, 55 subtests passed in 242.67s (0:04:02)`.
- `git diff --check` exited 0 with only existing LF-to-CRLF warnings.

## Fallback/unblock

Keep the context opt-in and caller-owned. Do not silently substitute it for legacy global, dynamic, UUID4, native, or third-party entropy. Reject invalid stream registration/snapshot data rather than repairing it. Replay, checkpoint restore, lossless mapping, common-clock claims, and default readiness remain blocked until a later adapter proves a real consumer hand-off, parity, interaction behavior, and failure semantics.

## Exactly one next gate

**E224 -- WorldBridge Opt-In Named-Stream Adapter Adoption and One-Handoff Parity Gate**: choose one bounded real local RNG consumer, inject one explicitly named stream through a real SR/PS hand-off seam, prove opt-in parity and interaction evidence, and keep default GameViewport/Pond behavior unchanged.