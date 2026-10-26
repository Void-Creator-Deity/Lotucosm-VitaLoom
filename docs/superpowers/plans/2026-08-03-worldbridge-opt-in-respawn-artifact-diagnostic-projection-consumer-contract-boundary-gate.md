# E229 WorldBridge Opt-In Respawn Artifact Diagnostic Projection Consumer/Contract Boundary Gate

Date: 2026-08-03
Status: complete
Completed: 2026-08-03

## Previous gate

E228 supplies a bounded canonical diagnostic projection for one E227 inspection summary, and can prove source parity only when the caller provides both objects. It deliberately does not define a downstream admission seam, so future diagnostics callers could otherwise decode/validate the two representations inconsistently or mistake a self-consistent projection for a source-proven one.

## Objective

Add a distinct Qt-free, caller-owned diagnostic-consumer seam that admits exactly a validated E227 inspection plus a validated E228 projection (mappings or their respective canonical bytes), proves source/projection parity before constructing an independently validated bounded receipt, and exposes no raw artifact/runtime/replay/checkpoint/mutation authority.

## Required work

1. Define an exact, canonical, bounded receipt schema with explicit paired source identities/digests, admitted diagnostic facts, source-projection parity result, negative capability flags, SHA-256 integrity, strict decoding, and duplicate/non-canonical/oversized rejection.
2. Decode mappings/bytes exclusively through E227/E228 validators/decoders, require the matching source media types and E228 parity validation, and reject raw E226 artifacts, missing pairs, mismatched pairs, tampered pairs, and semantic overclaims fail closed.
3. Keep output compact and copy-isolated: only receipt metadata plus already approved bounded diagnostic facts. Do not retain nested source objects, snapshots, genes, deltas, stream state, executable callbacks, or runtime references.
4. Keep the consumer explicit and diagnostic-only; use static runtime status evidence only. Do not add GameViewport/Pond/default-tick wiring, persistence, replay, checkpoint, restoration, mutation, common-clock, or atomicity authority.
5. Add admitted/rejected/mapping-and-byte/mismatch/tamper/canonical/bounds/copy-isolation/global-RNG tests, source/call-graph guard, status contract, isolated compilation, wider regression, full offscreen regression, diff check, status evidence, and a fresh-session prompt.

## Non-goals

No raw E226 artifact consumption, replay loader/admission, checkpoint persistence/restoration, stream reconstruction, mutation execution, live runtime state, common clock, input ordering, cross-lane atomicity, complete RNG closure, scene/Pond checkpoint semantics, lossless mapping, default runtime wiring, unified Pond readiness, OpenGL/native acceleration, or UI authority.

## Planned decision

The consumer will require both sides of the E227/E228 pair rather than taking a projection alone. That makes parity a mandatory admission condition at the consumer seam and localizes decoding, validation, source/projection matching, bounded receipt construction, and diagnostic-only negative capabilities behind one interface. It remains a read-only hand-off receipt, not a persistence/replay/checkpoint format.

## Exactly one next gate

**E230 -- WorldBridge Opt-In Respawn Diagnostic Receipt Presentation and Read-Only Inspector Adapter Gate**.


## Implementation

- Added the Qt-free `world_bridge_respawn_diagnostic_consumer` seam. It accepts only a validated E227 inspection and E228 projection (mapping or canonical bytes), requires E228 source parity before admission, and emits a copy-isolated canonical receipt bounded to 8 KiB.
- The receipt contains only paired source identities/digests and previously approved bounded diagnostic facts. Raw E226 artifacts, incomplete or mismatched source pairs, non-canonical/duplicate/oversized receipt bytes, digest tampering, and replay/checkpoint/restore/mutation/live-runtime overclaims fail closed.
- Added static runtime-status evidence only. The GameViewport, Pond, default tick, and runtime mode remain untouched; `runtime_mode=dual` and `default_ready=false` remain required.

## Evidence

- Isolated compilation: consumer, runtime status, E229 tests, and E229 guard compile successfully.
- Focused E226–E229/adapter/viewport/status coverage: `43 passed in 4.15s`.
- E226 artifact, E227 inspection, E228 projection, and E229 consumer guards passed, including source/call-graph, recomputed-digest mismatch, source-pair parity, and module-global Python/NumPy RNG checks.
- Wider WorldBridge/GameViewport/status coverage: `190 passed, 5 subtests passed in 18.66s`.
- Full offscreen regression: `2228 passed, 34 skipped, 55 subtests passed in 223.17s (0:03:43)`.
- `git diff --check` exited 0; it emitted only existing LF-to-CRLF warnings for unrelated tracked files.

## Fallback and unblock

Retain this receipt as a caller-owned diagnostic boundary. If a presentation adapter is not available, callers can keep the canonical receipt as an in-memory/read-only diagnostic object; no persistence, replay, checkpoint, restoration, or default-runtime route is implied. Any later presentation work must consume only this receipt and preserve its bounded, read-only, paired-source contract.
