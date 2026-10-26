# E226 Completion Handoff Prompt -- WorldBridge Opt-In Respawn Two-Stream Artifact Binding and Failure-Semantics Gate

E226 adds a Qt-free canonical, bounded, read-only artifact envelope for exactly one E225 opt-in SR respawn hand-off. The envelope binds the caller-owned context identity, distinct decision/mutation stream names and family, before/after-decision/final deterministic snapshots, probability/sample/admission, ordered steps, parent/child/delta evidence, and mutation consumption. E225 now includes deep-copied boundary snapshots so the artifact validator can prove which stream changed at each local boundary.

Admitted decisions seal `decision -> mutation`; rejected decisions seal `decision` with the mutation stream unchanged. Missing or malformed nested snapshots, wrong family, same stream names, digest/reference mismatch, changed stream layout, reordered steps, invalid probability/sample, delta mismatch, semantic overclaims, non-canonical JSON, duplicate keys, and size overflow fail closed. A mutation exception produces no hand-off artifact; no restore or repair is attempted.

Evidence: focused E226 artifact coverage `5 passed`; wider WorldBridge/GameViewport/runtime-status coverage `172 passed, 5 subtests passed`; E218-E226 guards including `tools/check_worldbridge_respawn_two_stream_artifact.py`; isolated compile checks for five changed implementation/test/guard files; full offscreen baseline and `git diff --check` are recorded in `docs/mainline_status.md` after completion.

Do not claim cross-lane atomicity, common clock/time alignment, full RNG authority closure, deterministic replay, checkpoint restore, lossless mapping, unified Pond default readiness, or native/OpenGL readiness. Keep artifact creation explicit, caller-owned, diagnostic-only, and outside default GameViewport/Pond/tick behavior.

## Next gate: E227

**E227 -- WorldBridge Opt-In Respawn Artifact Consumer Boundary and Read-Only Inspection Gate.** Add a separate consumer/inspection seam for a validated E226 artifact without making artifact bytes a replay/checkpoint authority or wiring them into default runtime behavior.
