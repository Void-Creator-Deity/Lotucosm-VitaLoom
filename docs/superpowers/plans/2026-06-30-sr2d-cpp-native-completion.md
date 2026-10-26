# SR2D C++ Native Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Use superpowers:test-driven-development for Python behavior changes and superpowers:verification-before-completion before claiming success.

**Goal:** Make C++ a first-class SR2D native backend alongside Rust, with Python as fallback and behavior oracle.

**Architecture:** `SrPhysics2DWorld.step()` remains the public entry. C++ receives primitive snapshots, computes PVAEC circle integration/contact, and returns primitive positions/velocities. It never imports `.pond`, `GameViewport`, AI command code, or Python scene entities.

**Tech Stack:** Python 3.11+, pytest, C++17, pybind11, scikit-build-core, CMake, existing `SrPhysics2DAdapter` boundary.

---

## Current Facts

- Stable entry point: `SrPhysics2DWorld.step()`.
- Adapter boundary: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`.
- Python fallback and oracle: `PythonSrPhysics2DAdapter`.
- C++ extension module name: `_vitalloom_sr2d_cpp`.
- Rust standard module name: `_vitalloom_sr2d_rust`.
- Rust legacy module name: `_vitalloom_sr2d`.
- Adapter variable: `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`.
- `auto` order: C++, then Rust, then Python.
- Current local machine may lack C++ compilers, CMake, pybind11, and scikit-build-core; missing native support must not break Python fallback.

## File Structure

- `native/sr2d_cpp/`
  - Owns the C++/pybind11 extension that builds `_vitalloom_sr2d_cpp`.
- `native/sr2d_kernel/`
  - Owns the Rust/PyO3 extension path.
- `sr_physics2d/adapter.py`
  - Owns adapter selection, native availability checks, and Python fallback.
- `tests/test_sr_physics2d_cpp_parity.py`
  - Owns Python/C++ parity and fallback semantics.
- `tests/test_sr_physics2d_native_parity.py`
  - Owns Python/Rust parity and fallback semantics.
- `tools/benchmark_engine.py`
  - Reports adapter name and native availability in SR2D benchmark output.

---

### Task 1: Lock C++ Adapter Selection Semantics

**Files:**
- Modify: `tests/test_sr_physics2d_adapter_contract.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`

- [x] Add tests for `CppSrPhysics2DAdapter`, `is_cpp_sr2d_available()`, and explicit missing-C++ failure.
- [x] Define `is_native_sr2d_available()` as C++ or Rust availability.
- [x] Support `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`.
- [x] Ensure `auto` prefers C++, then Rust, then Python.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py
```

### Task 2: Add C++ Parity Harness

**Files:**
- Create: `tests/test_sr_physics2d_cpp_parity.py`
- Modify: `tests/test_sr_physics2d_native_parity.py`

- [x] Add fallback behavior when `_vitalloom_sr2d_cpp` is not importable.
- [x] Add Python/C++ parity comparison when `_vitalloom_sr2d_cpp` is importable.
- [x] Keep Rust parity gated on `is_rust_sr2d_available()`, not broad native availability.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_cpp_parity.py tests/test_sr_physics2d_native_parity.py
```

### Task 3: Add C++/pybind11 Kernel Scaffold

**Files:**
- Create: `native/sr2d_cpp/pyproject.toml`
- Create: `native/sr2d_cpp/CMakeLists.txt`
- Create: `native/sr2d_cpp/src/kernel.hpp`
- Create: `native/sr2d_cpp/src/kernel.cpp`
- Create: `native/sr2d_cpp/src/bindings.cpp`

- [x] Create scikit-build-core project metadata.
- [x] Create CMake target with `pybind11_add_module(_vitalloom_sr2d_cpp ...)`.
- [x] Expose `_vitalloom_sr2d_cpp.step_pvaec_circles(...)`.
- [x] Mirror Python PVAEC semantics: damping, max speed, boundary bounce, dynamic/static filters, circle collision, impulse, friction, hard separation, correction separation, final clamp.
- [ ] Build locally when C++ tooling exists.

Build command when toolchain exists:

```bash
python -m pip install scikit-build-core pybind11 cmake ninja
python -m pip install ./native/sr2d_cpp
```

Expected without toolchain: record missing `cl`, `cmake`, `g++`, `clang++`, or Python build packages; Python fallback tests still pass.

### Task 4: Make Benchmark Output Observable

**Files:**
- Modify: `tools/benchmark_engine.py`

- [x] Include `adapter`.
- [x] Include `native_available`.
- [x] Include `cpp_available`.
- [x] Include `rust_available`.

Verification:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 3
```

### Task 5: Update Roadmap, Prompts, And Index

**Files:**
- Modify: `docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md`
- Modify: `docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md`
- Modify: `docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md`
- Modify: `docs/INDEX.md`

- [x] Roadmap names C++ and Rust as first-class native backends.
- [x] Prompts include a C++ fresh-session prompt.
- [x] Index links the C++ completion plan.

### Task 6: Final Verification

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
python -B tools/benchmark_engine.py --case sr2d --repeats 3
python -B -m compileall -q FrameCore tools
python -B tools/check_core_boundaries.py
```

Doc and whitespace checks:

```powershell
Select-String -Path 'docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md','docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md','docs/superpowers/plans/2026-06-30-sr2d-cpp-native-completion.md','docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md' -Pattern ('TB' + 'D|TO' + 'DO|fill in ' + 'details|2026-06-' + '29')
git diff --check
```

## Self-Review Notes

- This plan implements a real C++ native-language seam, not a documentation-only option.
- C++ and Rust remain optional runtime capabilities; Python remains mandatory fallback.
- Current local environments may lack native toolchains, so fallback verification is a release blocker while native build verification is toolchain-dependent.

---

### Task 7: Phase 3 Parity And Build Proof

**Files:**
- Create: `tests/fixtures/sr2d_parity_cases.py`
- Create: `tests/test_sr2d_native_smoke_tool.py`
- Create: `tests/test_benchmark_engine_sr2d_variants.py`
- Create: `tools/check_sr2d_native.py`
- Modify: `tests/test_sr_physics2d_cpp_parity.py`
- Modify: `tests/test_sr_physics2d_native_parity.py`
- Modify: `tests/test_sr_physics2d_adapter_contract.py`
- Modify: `tools/benchmark_engine.py`

- [x] Share Python/C++/Rust parity scenarios across both native parity suites.
- [x] Cover dynamic-dynamic, dynamic-static, pinned, membrane-locked, boundary bounce, max speed, zero-dt, and empty entity cases.
- [x] Test native adapter fallback for GAME mode and PVAEC spring-linked mode without calling the native kernel.
- [x] Add `tools/check_sr2d_native.py` to report C++/Rust import status, `step_pvaec_circles(...)` availability, toolchain commands, and Python build packages.
- [x] Add `sr2d_dense` and `sr2d_sparse` benchmark cases with native metadata and iteration counts.

Verification:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py tests/test_sr2d_native_smoke_tool.py tests/test_benchmark_engine_sr2d_variants.py
python -B tools/check_sr2d_native.py
python -B tools/benchmark_engine.py --case sr2d_dense --repeats 1
python -B tools/benchmark_engine.py --case sr2d_sparse --repeats 1
```
