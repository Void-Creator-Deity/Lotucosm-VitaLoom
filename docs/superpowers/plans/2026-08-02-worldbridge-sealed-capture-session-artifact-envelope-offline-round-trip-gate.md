# E220 WorldBridge Sealed Capture Session Artifact Envelope and Offline Round-Trip Gate

Date: 2026-08-02
Status: complete

## Previous gate

E219 proved a bounded, opt-in, Qt-free live comparability session producer that collects validated E216/E217 hand-offs, preserves contiguous identity and pair churn, and seals a validated E218 aggregation without owning a scheduler, clock, replay path, persistence path, or UI authority.

## Objective

Define and prove a canonical, size-bounded, Qt-free artifact envelope and offline round-trip boundary for one validated sealed E219 session, preserving all nested evidence and no-claim semantics without making the artifact replay input, checkpoint state, default persistence, or engine authority.

## Required work

1. Define explicit artifact schema/version/identity/media type, canonical UTF-8 JSON encoding, payload length, session digest, payload digest, and copy-isolated in-memory encode/decode APIs.
2. Accept only fully validated sealed E219 sessions; reject open/aborted sessions, malformed JSON, duplicate/extra/missing structure, non-canonical encodings, unsupported versions/media types, size overflow, digest mismatch, and nested E216-E219 tampering.
3. Make byte limits explicit and deterministic before and after decode. Preserve session/sample order, source digests, pair churn, aggregation classifications, lifecycle completion, and every false no-claim flag exactly.
4. If optional filesystem helpers are justified, require caller-selected paths, bounded reads, explicit overwrite policy, and safe replacement; keep the in-memory codec authoritative and out of the default GameViewport/tick path.
5. Add Qt-free regressions, a guard tool, runtime-status nesting, optional real temporary-directory round trip, explicit compilation, the widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No replay loader, no scene/Pond restore, no scheduler/input/seed capture, no shared clock, no cadence or causality inference, no atomic checkpoint claim, no mismatch correction, no lossless/default-ready claim, no default autosave, no Qt/UI authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.


## Decision

E220 admits a Qt-free, canonical artifact envelope for exactly one fully validated sealed E219 session. The envelope carries a clean artifact identity, fixed schema/version/media type/UTF-8 encoding, canonical-JSON policy, payload schema/version, canonical payload byte length, session identity/digest, payload SHA-256 digest, and an outer artifact SHA-256 digest. The digest scope proves deterministic integrity only; it is not authentication, replay admission, or checkpoint proof.

The authoritative boundary is in-memory encode/decode. Encoding revalidates the entire E219 session and all nested E216-E218 evidence, emits sorted separator-minimal UTF-8 JSON, and enforces an explicit byte limit. Decoding accepts bytes-like input only, bounds bytes before parsing, rejects invalid UTF-8, duplicate object keys, non-finite JSON constants, non-object roots, unsupported/extra/missing structure, semantic overclaims, nested tampering, digest mismatch, and any byte representation that is not exactly canonical. It returns a deep copy. A temporary-directory round trip proved byte-for-byte offline transport without adding filesystem ownership or default persistence helpers.

Only lifecycle `sealed` with `session_complete=true`, `partial_evidence=false`, and a validated E218 aggregation is accepted. Open and aborted sessions remain diagnostic in-memory evidence and cannot be mislabeled as complete artifacts. Replay input, checkpoint state, persistence authority, clock/time alignment, causality, atomicity, losslessness, replay admission, and default readiness remain false. Runtime status nests the E220 contract while the product remains dual and Qt remains only a legacy host adapter.

## Evidence

- Added `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_live_capture_artifact.py` with strict canonical encode/decode, 64 MiB maximum artifact size, duplicate-key/non-finite rejection, exact-key schema validation, nested E219 validation, copy isolation, and payload/artifact SHA-256 integrity.
- Added `tests/test_worldbridge_live_capture_artifact.py` and `tools/check_worldbridge_live_capture_artifact.py`; runtime status now nests `sealed_live_comparability_capture_artifact_contract` and names `sealed_capture_artifact_module` without changing runtime mode/default behavior.
- Focused E220 coverage passed **`13 passed in 0.36s`**. The wider WorldBridge/GameViewport/runtime-status scope passed **`118 passed, 5 subtests passed in 5.43s`**.
- The E220 guard reported a canonical valid 28,454-byte artifact, sealed lifecycle, exact round trip, and all replay/checkpoint/persistence/time/causality/default claims false. E218 and E219 regression guards passed. Explicit temporary-artifact compilation passed for seven E217-E220 implementation, status, guard, and test files.
- Full offscreen regression under `.venv\python.exe` passed **`2156 passed, 34 skipped, 55 subtests passed in 208.60s (0:03:28)`**. `git diff --check` exited `0` with only existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Keep E220 as an optional offline diagnostic transport. Reject any non-canonical, oversized, unsupported, digest-broken, lifecycle-incomplete, or nested-invalid artifact; do not repair or partially import it. Callers may write returned bytes to explicitly chosen temporary or archival locations, but no default autosave, path registry, replay loader, or restore path is admitted. Replay remains blocked by the E214 gaps: common clock/delta, deterministic queued inputs, random-source/seed policy, pause/reset/error semantics, an atomic scene/Pond checkpoint, and parity evidence.

## Exactly one next gate

**E221 -- WorldBridge Cross-Lane Randomness Authority and Seed-Capture Contract Gate**.
