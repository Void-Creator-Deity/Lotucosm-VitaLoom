# E221 WorldBridge Cross-Lane Randomness Authority and Seed-Capture Contract Gate

Date: 2026-08-02
Status: complete
Completed: 2026-08-03

## Previous gate

E220 proved a strict canonical offline artifact for one sealed E219 diagnostic session. The artifact preserves observed evidence and integrity but is explicitly not replay input, checkpoint state, persistence authority, or proof of deterministic execution.

## Objective

Inventory every randomness/entropy authority reachable during an actual SR-to-PS bridge hand-off and define deterministic, Qt-free read-only evidence for the minimum seed/state capture and restoration contract required by a future replay experiment, without changing default RNG behavior or claiming replay admission.

## Required work

1. Trace Python `random`, NumPy global RNG, explicit `Random`/`Generator` instances, time/UUID/OS entropy, and native/extension randomness reachable from SR preparation/update, bridge synchronization, `Pond.update()`, reproduction/inheritance/mutation, and PS-to-SR reflection.
2. Record each source's owner, scope, initialization path, consumption boundary, state serialization format, restore feasibility, ordering sensitivity, and whether it is covered by project/scene configuration today.
3. Define a Qt-free versioned inventory/contract that separates initial seed from consumed RNG state, rejects unsupported replay/determinism claims, and can later bind to an explicit experiment session without modifying module-global RNGs during status/guard construction.
4. Add AST/runtime regressions and a mechanical guard proving the inventory covers the actual bridge call graph and preserves current dual/default behavior. If a safe opt-in capture seam is implementable, keep it explicit and side-effect free until a caller requests capture.
5. Run focused WorldBridge/randomness coverage, relevant guards, explicit temporary compilation, the widest practical offscreen baseline, `git diff --check`, fallback/unblock, and exactly one next gate.

## Non-goals

No default reseeding, no monkey-patching production randomness, no clock merge, no deterministic replay claim, no scene/Pond restore, no atomic checkpoint, no automatic correction, no lossless/default-ready claim, no Qt/UI authority, and no changes to `.pond`, AI Command Registry, Inspector binding, SR2D seams, package manifests, or project manifests.


## Decision

E221 admits a deterministic, Qt-free authority inventory plus one explicit read-only observation seam for the two process-global RNGs that expose stable state APIs today: Python module-global `random` and NumPy's legacy global `RandomState`. The inventory records nine distinct authority classes, including ephemeral unseeded `Random()` instances, derived-seed instances, caller-owned `Random`/`Generator` instances, Python hash randomization, UUID4/OS entropy, dynamic script/plugin entropy, and unknown native/third-party RNG boundaries.

`capture_worldbridge_global_random_states(...)` serializes full consumed Python and NumPy states into canonical JSON-safe structures, validates a SHA-256 integrity digest, takes comparison reads before returning, and refuses an observation if either global state changed during collection. It never calls `seed`, `setstate`, or `set_state`. The capture remains explicitly non-thread-atomic and non-cross-authority-atomic, and it does not capture interleaved consumption order or any local/dynamic/native authority.

Runtime-status construction uses only locally owned `random.Random(221)` and `numpy.random.RandomState(221)` examples. It neither reads nor advances process-global RNGs, so the nested contract is deterministic. Initial seed sufficiency, complete authority capture, common time, atomic checkpointing, losslessness, replay input/admission, and default readiness remain false; the product remains dual and Qt remains a legacy host adapter.

## Evidence

- Added `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_randomness_authority.py` with the nine-authority inventory, JSON-safe Python/NumPy state serialization, explicit side-effect-free capture, exact-key validation, semantic-overclaim rejection, and SHA-256 capture integrity.
- Added `tests/test_worldbridge_randomness_authority.py` and `tools/check_worldbridge_randomness_authority.py`; runtime status now nests `cross_lane_randomness_authority_contract` and names `randomness_authority_module` without changing default runtime behavior.
- Focused E221 coverage passed **`13 passed in 0.60s`**. Wider WorldBridge/GameViewport/runtime-status coverage passed **`131 passed, 5 subtests passed in 6.88s`**.
- The E221 guard reported **9** authorities, exactly **2** supported global-state observations and **7** uncaptured blockers. It proved Python and NumPy global states unchanged and retained false claims for thread/cross-authority atomicity, seed sufficiency, complete capture, consumption order, replay, and default readiness. E218-E220 regression guards also passed.
- Seven relevant implementation, integration, test, guard, and regression files compiled to an isolated system temporary directory only. The full offscreen baseline under `.venv\python.exe` passed **`2169 passed, 34 skipped, 55 subtests passed in 214.63s (0:03:34)`**.
- The first wider invocation used the shell's Anaconda interpreter and stopped during collection because that interpreter lacks PyQt6. No test body failed; rerunning with the repository `.venv` completed the stated wider and full baselines. `git diff --check` exited `0` with only existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Keep RNG observation explicit, read-only, and outside the default tick. If either supported global state changes during the non-atomic observation window, reject rather than label the result atomic. Do not restore from E221 evidence. Ephemeral/caller-owned RNG instances, Python hash secret policy, UUID4/OS entropy, dynamic scripts/plugins, native dependencies, and exact cross-lane consumption order remain open blockers. Stronger experiment evidence next needs an explicit pre/post observation pair bound to one sealed E220 artifact, with only changed/unchanged diagnostics and no draw-count, attribution, causality, checkpoint, or replay claim.

## Exactly one next gate

**E222 -- WorldBridge Pre/Post Random-State Observation Pair and Sealed Artifact Binding Gate**.
