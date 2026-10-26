# E228 WorldBridge Opt-In Respawn Artifact Inspection/Projection Parity and Bounded Diagnostics Gate

Date: 2026-08-03
Status: complete
Completed: 2026-08-03

## Previous gate

E227 established a Qt-free, read-only consumer for validated E226 respawn two-stream artifacts. It returns a strict canonical inspection summary but deliberately has no projection contract for compact diagnostics, nor proof that any later view preserves the inspected facts without adding authority.

## Objective

Add a distinct Qt-free diagnostic-projection seam that consumes only a validated E227 inspection summary or its canonical bytes and returns a compact, canonical, copy-isolated projection. Prove every projected fact is parity-bound to the source inspection summary, bounded in representation, and unable to restore streams, execute mutation, admit replay, or become default runtime state.

## Required work

1. Define exact, versioned projection schema, digest, canonical encoding/decoding, strict byte bound, and validation that rejects duplicate keys, non-canonical JSON, unknown fields, tampering, malformed inputs, and semantic overclaims.
2. Accept mapping input only after E227 summary validation and byte input only through E227 canonical decoding. Keep the source digest/identity and represented fields parity-bound to the validated source.
3. Limit the projection to diagnostic primitives: artifact identity/digests, context/stream-role labels, outcome/ordered-step/mutation summary, snapshot digest references, bounded gene-count metrics, and explicit negative authority flags. Do not forward nested snapshots, genes, deltas, or executable artifacts.
4. Make projection construction deterministic, copy-isolated, non-mutating, and independent of module-global Python/NumPy RNGs. Keep GameViewport, Pond/default tick, replay, checkpoint, restore, and mutation paths untouched.
5. Add focused admitted/rejected/parity/byte/canonical/tamper/bounds/copy-isolation tests, source/call-graph/global-RNG guard, static runtime-status contract, isolated compilation, wider regression, full offscreen regression, `git diff --check`, status evidence, and fresh-session prompt.

## Non-goals

No E226 artifact execution, replay loader/admission, checkpoint restoration, stream reconstruction, mutation execution, common clock, cross-lane atomicity, complete entropy closure, scene/Pond checkpoint semantics, lossless mapping, default runtime wiring, unified Pond readiness, OpenGL/native acceleration, or UI authority.

## Planned decision

The new module will be a deep diagnostic-projection seam: its caller supplies exactly one already validated inspection summary or canonical inspection bytes, and receives an independently validated compact projection whose digest binds the source inspection digest and every exposed diagnostic fact. It will neither accept raw E226 artifacts nor reach into runtime objects; callers must explicitly select E227 inspection first.


## Implementation and evidence

- Added `world_bridge_respawn_artifact_diagnostics`, a Qt-free deep diagnostic-projection seam. It accepts only E227-validated inspection mappings or canonical E227 inspection bytes; it does not accept raw E226 artifacts. The exact-schema output remains under a 16 KiB canonical JSON bound and carries source inspection identity/digest plus the selected diagnostic facts only.
- Projection validation checks exact structure, semantic negative-capability policies, SHA-256 self-integrity, byte bound, and, when supplied with its validated E227 source, field-by-field parity for every exposed identity, stream-role, outcome, snapshot-digest, and gene-count fact. The static runtime contract is visible without wiring GameViewport, Pond, or default tick to the module.
- Focused E226/E227/E228/adapter/viewport/status regression passed **`36 passed in 4.10s`**. Wider WorldBridge/GameViewport/runtime-status regression passed **`183 passed, 5 subtests passed in 16.93s`**. E226 artifact, E227 inspection, and E228 diagnostic-projection guards passed; isolated compilation passed for four E228 files. Full offscreen regression passed **`2221 passed, 34 skipped, 55 subtests passed in 233.15s (0:03:53)`**.

## Fallback and unblock

Reject raw artifacts, malformed/non-canonical/duplicate/oversized bytes, invalid inspection summaries, recomputed semantic overclaims, and source-parity mismatch; do not repair them, restore streams, execute mutation, or infer executable state. This compact diagnostic representation does not close common-clock/input ordering, complete RNG authority, cross-lane atomicity, scene/Pond checkpointing, replay admission, lossless mapping, unified-Pond readiness, or native/OpenGL evidence.

## Exactly one next gate

**E229 -- WorldBridge Opt-In Respawn Artifact Diagnostic Projection Consumer/Contract Boundary Gate**.
