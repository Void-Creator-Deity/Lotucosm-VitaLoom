# SR2D Python Broadphase And Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Use superpowers:test-driven-development for behavior changes and superpowers:verification-before-completion before claiming success.

## Summary

Phase 3 moves SR2D performance work forward without waiting for C++/Rust toolchains. Python remains the oracle and fallback. The goal is to add a deterministic spatial-hash broadphase to the Python PVAEC circle contact path, preserve the existing O(n^2) debug path, prove parity on focused fixtures, and record dense/sparse benchmark evidence.

## Current State

- Phase 2 viewport performance gate passed: dense viewport frame timing improved, QPainter remains default, OpenGL remains opt-in.
- SR2D native extensions are not importable on this machine. `check_sr2d_native.py` reports `_vitalloom_sr2d_cpp`, `_vitalloom_sr2d_rust`, and legacy `_vitalloom_sr2d` unavailable.
- Native toolchains are missing: `cl`, `cmake`, `g++`, `clang++`, `nmake`, `cargo`, and `maturin`.
- Current focused SR2D fallback suite: `21 passed, 16 skipped`; skips are native parity skips.
- Baseline SR2D benchmarks, all Python adapter:
  - `sr2d`: `464.262 ms`, 100 entities, 120 iterations.
  - `sr2d_dense`: `1230.823 ms`, 160 entities, 120 iterations.
  - `sr2d_sparse`: `137.761 ms`, 60 entities, 120 iterations.
- Current Python PVAEC contacts build every dynamic-dynamic and dynamic-static pair in O(n^2) order.

## Scope

- Add a deterministic Python spatial hash candidate builder for PVAEC circle contacts.
- Preserve the O(n^2) pair builder as a debug/reference path.
- Add tests that compare broadphase and brute-force candidate semantics and final step outputs on controlled fixtures.
- Add benchmark metadata that exposes the selected broadphase mode and pair counts.
- Current evidence keeps `bruteforce` as the default because the conservative Python spatial hash preserves dense parity but regresses benchmark time on this machine.
- Keep `SrPhysics2DWorld.step()` and `SrPhysics2DAdapter` public seams unchanged.

## Non-goals

- Do not build or require C++/Rust native extensions in this phase.
- Do not change `.pond`, `GameViewport`, AI command registry, Inspector binding, package manifests, or project lock semantics.
- Do not replace the solver, introduce Box2D/Rapier, or change PVAEC contact semantics to fit the broadphase.
- Do not hide entities, reduce contact iterations, or lower fidelity to improve benchmark numbers.
- Do not switch adapter default away from Python unless native proof exists in a later phase.

## Files

- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/pvaec_contacts.py`
- Modify if needed: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/config.py`
- Modify: `tools/benchmark_engine.py`
- Add or extend: `tests/test_sr_physics2d_broadphase.py`
- Extend: `tests/test_benchmark_engine_sr2d_variants.py`
- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Add: `docs/prompts/2026-07-03-sr2d-python-broadphase-prompt.md`

## Step-by-step Tasks

### Task 1: Lock Broadphase Candidate Semantics

- [x] Write tests for `build_pvaec_contact_pairs(..., broadphase="bruteforce")` and `broadphase="spatial_hash"`.
- [x] Cover dynamic-dynamic, dynamic-static, pinned, membrane_locked, far-apart sparse bodies, and dense overlapping bodies.
- [x] Assert spatial hash returns deterministic pair ordering compatible with brute force.
- [x] Assert non-PVAEC static/static and pinned-only pairs are excluded.

### Task 2: Add Spatial Hash Broadphase

- [x] Implement a deterministic grid keyed by integer cell coordinates.
- [x] Use a conservative cell size derived from the largest active PVAEC radius.
- [x] Generate nearby candidates from neighboring cells with conservative contact-iteration padding.
- [x] Sort final pair keys into the same deterministic order as the brute-force path.
- [x] Keep O(n^2) available through an explicit debug mode.

### Task 3: Route Python PVAEC Contacts Through Broadphase

- [x] Add `pvaec_broadphase` to `SrPhysics2DConfig`.
- [x] Keep `bruteforce` as the default after benchmark evidence showed Python spatial hash regression.
- [x] Allow `spatial_hash` for tests and diagnostics.
- [x] Keep unsupported scene values safe by falling back to the default.
- [x] Compare broadphase and brute-force final snapshots on shared fixtures and a dense multi-step case.

### Task 4: Benchmark And Metadata

- [x] Add SR2D benchmark metadata: `pvaec_broadphase`, `pvaec_pair_count`, `pvaec_spatial_pair_count`, and `pvaec_debug_pair_count`.
- [x] Add explicit spatial benchmark cases for default, dense, and sparse scenarios.
- [x] Run `sr2d`, `sr2d_dense`, `sr2d_sparse`, `sr2d_dense_spatial`, and `sr2d_sparse_spatial` benchmarks.
- [x] Record the entity count, iteration count, adapter, native availability, broadphase mode, pair count, and first entity snapshot.

### Task 5: Docs, Prompt, And Status

- [x] Update `docs/mainline_status.md` with Phase 3 evidence, skips, and next gate.
- [x] Add this plan and prompt to `docs/INDEX.md`.
- [x] Update fresh-session prompt with exact files, guardrails, verification commands, and current evidence.
- [x] Run documentation placeholder scan and `git diff --check`.

## Tests First

Use TDD for behavior changes:

1. Add failing tests for broadphase pair building and solver parity.
2. Confirm the tests fail because the broadphase API or metadata is missing.
3. Implement the smallest passing broadphase.
4. Re-run focused tests and benchmarks.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B tools/check_sr2d_native.py
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_broadphase.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py tests/test_sr2d_native_smoke_tool.py tests/test_benchmark_engine_sr2d_variants.py
python -B tools/benchmark_engine.py --case sr2d --repeats 3
python -B tools/benchmark_engine.py --case sr2d_dense --repeats 3
python -B tools/benchmark_engine.py --case sr2d_sparse --repeats 3
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans FrameCore tests tools
```

## Evidence Ledger

Record:

- Python oracle path and selected broadphase mode.
- O(n^2) debug path availability.
- Pair counts for dense/sparse/default benchmarks.
- Final snapshot parity between broadphase and brute force.
- Native import status and missing toolchain status.
- Benchmark before/after numbers tied to scenario size.

## Fallback/Unblock Path

- If spatial hash parity fails on a fixture, keep `bruteforce` as the default until the mismatch is understood.
- If benchmarks regress, keep broadphase explicit/diagnostic and record the failing pair count/scenario.
- If native toolchains remain missing, do not block Python broadphase verification; record native as unavailable and continue with Python fallback.
- If broadphase cannot preserve solver semantics for dense contact chains, document the exact fixture and keep O(n^2) default while broadphase stays diagnostic-only.

## Phase-End Report Template

- Phase: Phase 3 - SR2D Python broadphase and parity
- Status: `<complete | partially complete | blocked>`
- Implemented: `<files/features>`
- Verified: `<commands and results>`
- Skipped/Unavailable: `<native builds/toolchains/skips>`
- Evidence: `<benchmarks, pair counts, parity output>`
- Architecture impact: `<unchanged seam or documented boundary change>`
- Remaining risks: `<specific risks>`
- Next phase: `<one concrete next phase and first command/file>`

## Next Phase Gate

Phase 4 - SR2D C++ and Rust native proof can start only after Python broadphase is either:

- default-on with parity and benchmark evidence, or
- explicitly held behind a debug flag with a documented blocker and O(n^2) fallback evidence.
