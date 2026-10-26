# E226 WorldBridge Opt-In Respawn Two-Stream Artifact Binding and Failure-Semantics Gate

Date: 2026-08-03
Status: in_progress

## Previous gate

E225 proved an explicit, caller-owned, opt-in SR respawn hand-off: one named Python stream decides admission first, and a distinct named Python stream is consumed only when the mutation is admitted. The result carries before/after snapshot digests and ordered local steps, but it is still an ephemeral return value rather than a canonical sealed evidence artifact.

## Objective

Define and prove a Qt-free, versioned, canonical, read-only artifact envelope for exactly one successful E225 decision-to-optional-mutation hand-off. Bind the context identity, stream roles, snapshot boundaries, decision sample, admission, mutation evidence, and ordered consumption semantics without turning the artifact into checkpoint state, persistence authority, replay input, or default runtime behavior.

## Required work

1. Define an exact artifact schema, media type, canonical encoding, bounded size, and SHA-256 outer integrity digest.
2. Validate and bind context identity, distinct stream names and family, before/after-decision/final snapshot digests, probability/sample/admission, ordered steps, mutation-consumed flag, parent/child/delta evidence, and nested stream-state evidence.
3. Construct artifacts only from a fully validated E225 result and copy inputs deeply; reject malformed, non-canonical, extra/missing, tampered, nested, cross-context, wrong-family, same-stream, invalid-probability, mutation-failure, or semantically overclaiming evidence.
4. Provide strict encode/decode plus byte-for-byte canonical round-trip; do not repair or partially accept malformed artifacts.
5. Keep construction explicit and caller-owned. Do not wire artifact creation into the default GameViewport tick, restore streams, admit replay, or claim atomic cross-lane/checkpoint semantics.
6. Add focused Qt-free tests, an executable guard, runtime-status nesting, isolated compilation, E218-E226 guard regression, wider tests, full offscreen regression, and `git diff --check`.
7. Update `docs/mainline_status.md` and add a fresh-session prompt. Close this phase with evidence, fallback/unblock, and exactly one next gate.

## Non-goals

No default capture lifecycle, no global RNG reseeding or restore, no deterministic replay loader, no checkpoint restore, no cross-thread or cross-authority atomicity, no common clock, no causal inference, no lossless mapping, no unified Pond default readiness, no OpenGL/native acceleration claim, no Qt/UI authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.

## Planned decision

The artifact will preserve only the bounded local hand-off evidence that E225 actually produces. A rejected decision is a valid complete hand-off with no mutation consumption; an admitted mutation must include complete child/delta evidence and a final snapshot. Any exception or incomplete mutation is a failed operation and produces no artifact. Integrity is SHA-256 over canonical JSON without the outer digest; it is integrity evidence, not authenticity or replay admission.

## Verification gates

- focused E226 artifact tests and guard;
- wider WorldBridge, GameViewport, and runtime-status tests;
- E218-E226 guards and isolated temporary compilation;
- full offscreen regression;
- `git diff --check`.

## Fallback and unblock

Reject malformed or partial evidence rather than repairing it. Keep artifact creation caller-owned and opt-in. Stronger replay/checkpoint claims remain blocked until common clock/input/RNG consumption order, atomic scene/Pond state, failure semantics, and parity evidence are implemented.

## Exactly one next gate

**E227 -- WorldBridge Opt-In Respawn Artifact Consumer Boundary and Read-Only Inspection Gate**.
