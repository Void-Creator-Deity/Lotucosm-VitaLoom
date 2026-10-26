# SR2D Native Build And Import Proof Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Use superpowers:test-driven-development for behavior changes and superpowers:verification-before-completion before claiming success.

## Summary

Phase 4 starts from the fact that C++ and Rust SR2D native backends are first-class optional paths, but not proven accelerated on this machine. The goal is to harden build/import proof tooling so a fresh session can distinguish source scaffold, build readiness, importability, kernel symbol availability, fallback behavior, parity skips, and benchmark evidence.

## Current State

- Phase 3 implemented a deterministic Python `spatial_hash` broadphase and kept O(n^2) `bruteforce` as the default because explicit spatial hash preserved parity but regressed timing in Python.
- Current SR2D focused suite after Phase 3: `27 passed, 16 skipped`; skips are native import skips.
- `check_sr2d_native.py` reports native unavailable: `_vitalloom_sr2d_cpp`, `_vitalloom_sr2d_rust`, and legacy `_vitalloom_sr2d` are not importable.
- Local toolchains/packages are missing: `cl`, `cmake`, `g++`, `clang++`, `nmake`, `cargo`, `maturin`, `pybind11`, `skbuild`, `scikit_build_core`, and `cibuildwheel`.
- `build_sr2d_native.py --backend all --check-only` reports backend readiness and build commands, but the proof contract can be more explicit about module names, kernel symbols, missing Python packages, and import-after-build checks.

## Scope

- Strengthen native build proof tooling and tests.
- Keep Python fallback mandatory and verified.
- Keep C++ and Rust source scaffolds as optional build targets.
- Do not require installing compilers or native Python build packages in this phase.
- Record exact unblock path for building native extensions later.

## Non-goals

- Do not claim C++ or Rust acceleration unless an extension builds, imports, exposes `step_pvaec_circles(...)`, passes parity, and appears in benchmarks.
- Do not change `.pond`, `GameViewport`, AI command layer, Inspector binding, project/package manifests, or SR2D public adapter seams.
- Do not introduce Box2D/Rapier or replace the Python solver.
- Do not silently fall back when the user explicitly requests `VITALOOM_SR2D_ADAPTER=cpp` or `rust`; explicit missing native should remain a clear `RuntimeError`.

## Files

- Modify: `tools/build_sr2d_native.py`
- Modify: `tests/test_sr2d_native_smoke_tool.py`
- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Add: `docs/prompts/2026-07-04-sr2d-native-build-import-proof-prompt.md`

## Step-by-step Tasks

### Task 1: Lock Native Build Proof Contract

- [x] Add tests that `build_sr2d_native.py --check-only` reports for each backend:
  - `module_name`
  - `kernel_symbol`
  - `source_project`
  - `build_command`
  - `import_check`
  - `toolchain`
  - `missing_tools`
  - `python_packages`
  - `missing_python_packages`
  - `ready`
- [x] Ensure missing tools keep check-only exit code `0`.

### Task 2: Harden Build Tool Output

- [x] Extend C++ status with `_vitalloom_sr2d_cpp` and `step_pvaec_circles`.
- [x] Extend Rust status with `_vitalloom_sr2d_rust` and legacy `_vitalloom_sr2d` compatibility note.
- [x] Report Python package readiness separately from compiler readiness.
- [x] Keep non-check build mode skip-safe with explicit `skip_reason` when toolchain or Python packages are missing.

### Task 3: Verify Runtime Fallback And Explicit Failure

- [x] Run SR2D adapter contract tests.
- [x] Run native smoke tests.
- [x] Run `check_sr2d_native.py`.
- [x] Run `build_sr2d_native.py --backend all --check-only`.
- [x] Confirm `auto` still falls back to Python and explicit missing C++/Rust still raises clear errors.

### Task 4: Update Docs And Status

- [x] Update `docs/mainline_status.md` with Phase 4 proof-tool evidence, native unavailable state, and unblock path.
- [x] Link this plan and prompt from `docs/INDEX.md`.
- [x] Update fresh-session prompt with exact verification commands.
- [x] Run doc placeholder scan and `git diff --check`.

## Tests First

Use TDD:

1. Add failing test expectations for the stronger build proof schema.
2. Observe failure against current `build_sr2d_native.py`.
3. Implement the minimal output schema change.
4. Re-run smoke/fallback tests and check-only command.

## Verification Commands

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr2d_native_smoke_tool.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
python -B tools/check_sr2d_native.py
python -B tools/build_sr2d_native.py --backend all --check-only
python -B tools/benchmark_engine.py --case sr2d --repeats 1
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools tests
```

## Evidence Ledger

Record:

- Native module import status.
- Kernel symbol status.
- Missing tools and missing Python packages.
- Build command and import-check command for C++ and Rust.
- Adapter fallback behavior.
- Native parity skips and reasons.
- Benchmark adapter metadata.

## Fallback/Unblock Path

- Fallback: `VITALOOM_SR2D_ADAPTER=auto` remains `PythonSrPhysics2DAdapter` when native modules are unavailable.
- C++ unblock: install a C++ compiler plus CMake/scikit-build-core/pybind11, then run `python -m pip install ./native/sr2d_cpp`, `python -B tools/check_sr2d_native.py`, and C++ parity tests.
- Rust unblock: install `cargo` plus `maturin`, then run the Rust build command recorded by the tool, `python -B tools/check_sr2d_native.py`, and Rust parity tests.
- If native builds fail after toolchain install, record build stdout/stderr tail and keep Python fallback as release-safe.

## Phase-End Report Template

- Phase: Phase 4 - SR2D native build/import proof
- Status: `<complete | partially complete | blocked>`
- Implemented: `<files/features>`
- Verified: `<commands and results>`
- Skipped/Unavailable: `<native builds/toolchains/packages>`
- Evidence: `<native smoke/build-proof output/parity/benchmark metadata>`
- Architecture impact: `<unchanged seam or documented boundary change>`
- Remaining risks: `<specific risks>`
- Next phase: `<one concrete next phase and first command/file>`

## Next Phase Gate

Phase 4 is complete only when one of these is true:

- Native toolchain exists and at least one C++ or Rust extension builds/imports, exposes `step_pvaec_circles(...)`, passes parity, and is benchmarked; or
- Toolchain remains unavailable but proof tooling, fallback tests, check-only build output, skips, and unblock path are all explicit and verified.
