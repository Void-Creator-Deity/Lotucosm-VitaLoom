# E227 WorldBridge Opt-In Respawn Artifact Consumer Boundary and Read-Only Inspection Gate

Date: 2026-08-03
Status: complete
Completed: 2026-08-03

## Previous gate

E226 sealed exactly one validated E225 decision-to-optional-mutation hand-off as bounded canonical diagnostic evidence. It proves local snapshot boundaries and ordered stream consumption, but the artifact remains an envelope, not a consumer API; no runtime caller should infer replay, checkpoint, or authority restoration from its bytes.

## Objective

Add a separate Qt-free, read-only consumer boundary that accepts only a fully validated E226 artifact or canonical artifact bytes and returns a copy-isolated inspection summary. The consumer must expose useful evidence for diagnostics while refusing to restore streams, execute mutation, admit replay, or treat artifact fields as live runtime state.

## Required work

1. Define a versioned inspection schema with exact keys, explicit source artifact identity/digest, outcome/step summary, stream-role names, snapshot digest references, and false replay/checkpoint/restore/default flags.
2. Accept a mapping only after strict E226 validation, and accept bytes only through strict canonical E226 decoding; reject malformed, tampered, non-canonical, duplicate-key, oversized, nested, or semantically overclaiming input.
3. Return deep-copy-isolated summary data with no nested mutable artifact payload. Do not call context restore, `mind_dict_mutate`, GameViewport, Pond, or module-global RNGs.
4. Keep the seam caller-owned and opt-in. Runtime status may expose a deterministic static contract, but GameViewport/default tick/Pond behavior must remain unchanged.
5. Add focused tests, source/call-graph guard, status nesting, isolated compilation, wider regression, and `git diff --check`; update mainline status and fresh-session prompt with exactly one next gate.

## Non-goals

No replay loader/admission, checkpoint restoration, stream reconstruction, mutation execution, default runtime wiring, common clock, cross-lane atomicity, entropy closure, lossless mapping, unified Pond readiness, OpenGL/native acceleration, or UI authority.

## Planned decision

The consumer summary will preserve only diagnostic identity and bounded local evidence: artifact ID/digest, context and stream roles, admitted/rejected outcome, ordered steps, mutation-consumed flag, snapshot digest references, and explicit negative capability flags. Nested snapshots and parent/child/delta payloads remain in the validated artifact and are not reinterpreted as executable state.


## Implementation and evidence

- Added the Qt-free `world_bridge_respawn_artifact_inspection` seam. Mapping inputs undergo E226 validation; byte inputs pass through E226 canonical decoding before inspection. The produced exact-schema summary is copy-isolated and limited to identity, stream-role, outcome, ordered-step, digest-reference, and bounded gene-count diagnostics.
- The inspection schema explicitly keeps replay, checkpoint, restore, mutation execution, live-runtime, and default-runtime authority false. It deliberately omits nested snapshots and parent/child/delta payloads. `runtime_worldbridge_status` exposes only a static opt-in contract; GameViewport, Pond, and default tick behavior were not wired to the seam.
- Focused regression passed **`30 passed in 2.09s`**. Wider WorldBridge/GameViewport/runtime-status regression passed **`177 passed, 5 subtests passed in 7.77s`**. E226 artifact and E227 inspection guards passed, and isolated compilation passed for the four E227 files. Full offscreen regression passed **`2215 passed, 34 skipped, 55 subtests passed in 188.11s (0:03:08)`**.

## Fallback and unblock

Reject malformed, non-canonical, oversized, duplicate-key, tampered, or semantically overclaiming artifact input; do not repair it, restore state, or execute mutation. Diagnostic inspection remains caller-owned. Replay/checkpoint admission, common clock and input ordering, full RNG authority closure, cross-lane atomicity, scene/Pond checkpoint semantics, lossless mapping, unified-Pond readiness, and native/OpenGL evidence remain separate blockers.

## Exactly one next gate

**E228 -- WorldBridge Opt-In Respawn Artifact Inspection/Projection Parity and Bounded Diagnostics Gate**.
