# E219 WorldBridge Bounded Live Comparability Capture Session Producer Adapter Gate

Date: 2026-08-02
Status: complete

## Previous gate

E218 proved deterministic aggregation and conservative drift classification for explicitly indexed validated E217 evaluations. It deliberately does not acquire repeated live samples, own either clock, infer cadence, or establish replay/default admission.

## Objective

Define and prove a bounded, opt-in, Qt-free capture-session producer that accepts repeated actual E216 live producer payloads or E217 evaluations at existing bridge hand-offs, assigns explicit session/sample identity, preserves capture order and pair churn, and seals a validated E218 aggregation without becoming a scheduler, clock, replay, persistence, or UI authority.

## Required work

1. Define a session lifecycle and schema with explicit session identity, monotonically assigned sample indices, bounded capacity, open/sealed/aborted states, and copy-isolated JSON evidence.
2. Consume only validated E216/E217 evidence from actual bridge hand-offs; reject mixed schema, duplicate source digests, post-seal writes, missing indices, and fabricated/interpolated samples.
3. Define deterministic stop, overflow, partial-failure, and pair-churn behavior. Any retained partial evidence must be labeled diagnostic and must not imply time continuity, causality, atomicity, or replay completeness.
4. Expose the smallest optional GameViewport/WorldBridge adapter seam needed to feed the Qt-free session contract while preserving the existing one-tick bridge path and all defaults.
5. Add Qt-free regressions, one real offscreen adapter/session smoke, a guard tool, runtime-status nesting, explicit compilation, the widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No new scheduler or timer, no SR/PS clock merge, no cadence interpolation, no causal diagnosis, no automatic correction, no replay admission, no atomic scene/Pond checkpoint, no lossless/default-ready claim, no Qt engine authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.


## Decision

E219 admits a bounded, opt-in, Qt-free capture-session producer over validated E216 live traces or validated E217 evaluations. A session has an explicit clean identity, a capacity from 1 through 4096 samples, zero-based contiguous append indices, deterministic sample IDs, and open/sealed/aborted lifecycle states. Appends are immutable/copy-isolated, preserve source trace/evaluation digests, reject mixed evidence kinds and duplicate source traces, and never invent a timer, cadence, interpolation, or missing sample.

Sealing a non-empty session constructs and validates the E218 aggregation from the retained E217 evaluations. Overflow, invalid input, post-seal writes, and post-abort writes reject without mutating prior evidence. Explicit abort preserves bounded partial diagnostic evidence and labels it incomplete; it does not fabricate an aggregation. Validation recomputes the session digest and all nested E217/E218 evidence, sample identities, counts, source digests, lifecycle invariants, and conservative no-claim flags.

GameViewport exposes only an explicit feeder seam that requests one existing live bridge trace and appends it through the Qt-free API. The ordinary scene-runtime update path neither creates nor advances a capture session, so Qt remains a legacy host adapter and dual runtime remains the default. Scheduler ownership, common time, causality, atomicity, losslessness, replay admission, and default readiness remain false.

## Evidence

- Added `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_live_capture_session.py` with bounded lifecycle, immutable append, E216/E217 normalization, E218 sealing, abort semantics, structural validation, copy isolation, and SHA-256 session digest.
- Added `tests/test_worldbridge_live_capture_session.py` and `tools/check_worldbridge_live_capture_session.py`. Runtime status now nests `bounded_live_comparability_capture_session_contract` and names the pilot module. GameViewport provides only `_append_unified_pond_bridge_capture_session_sample(...)`; source inspection proves the default update path does not own capture-session lifecycle.
- Focused E219 coverage passed **`13 passed in 0.51s`**. The wider WorldBridge/GameViewport/runtime-status scope passed **`105 passed, 5 subtests passed in 4.81s`**.
- The E219 guard reported a valid sealed two-sample bounded session with scheduler/time/causality/replay/default claims false. The E218 regression guard also passed. Explicit temporary-artifact compilation passed for seven relevant implementation, integration, guard, and deterministic-regression files.
- The full baseline first exposed a pre-existing probabilistic assertion in `test_worldbridge_memory_gene_ownership_decision.py`: production inheritance intentionally uses `rate * strength`, so strength `0.8` was not guaranteed to inherit. The failure reproduced on the first isolated probe. The test now pins only its RNG with `unittest.mock.patch`; production inheritance and E213's no-memory-gene-WorldBridge-transfer decision are unchanged. The focused file passed **`3 passed`** and the target passed **20/20** repeated probes.
- Full offscreen regression under `.venv\python.exe` passed **`2143 passed, 34 skipped, 55 subtests passed in 209.32s (0:03:29)`**. `git diff --check` exited `0` with only existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Keep capture sessions explicit, bounded, in memory, and diagnostic. If a source trace/evaluation is invalid, duplicated, mixed, over capacity, or lifecycle-incompatible, reject without mutation; callers may explicitly abort and retain only labeled partial evidence. Do not wire the feeder into the default tick path. Portable evidence is still unproven: stronger offline inspection needs a canonical sealed-session artifact envelope with strict size/schema/digest validation and round-trip evidence, but that artifact must not become replay input or persistence/default authority.

## Exactly one next gate

**E220 -- WorldBridge Sealed Capture Session Artifact Envelope and Offline Round-Trip Gate**.
