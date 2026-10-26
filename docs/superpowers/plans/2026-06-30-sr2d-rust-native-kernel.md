# SR2D C++ And Rust Native Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep Rust as a first-class native-language SR2D path while adding C++ as an equal first-class backend. Both expose PVAEC circle kernels behind the existing Python adapter boundary.

**Architecture:** Python remains the runtime orchestration layer and behavior oracle. C++ and Rust receive primitive snapshots, compute the PVAEC circle step, and return primitive positions/velocities; neither imports `.pond`, `GameViewport`, AI commands, or Python scene entities.

**Tech Stack:** Python 3.11+, pytest, C++17, pybind11, scikit-build-core, CMake, Rust 2021, PyO3, maturin, existing `SrPhysics2DAdapter` boundary.

---

## Current Facts

- Stable entry point: `SrPhysics2DWorld.step()`.
- Existing adapter boundary: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`.
- Python fallback and oracle: `PythonSrPhysics2DAdapter`.
- C++ extension module name: `_vitalloom_sr2d_cpp`.
- Rust extension module name: `_vitalloom_sr2d_rust`.
- Rust legacy module name: `_vitalloom_sr2d`.
- Native selection variable: `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`.
- `auto` order: C++, then Rust, then Python.
- Current local machine may not have C++ compilers, CMake, pybind11, scikit-build-core, `cargo`, or `maturin`; missing native support must not break Python fallback.

## File Structure

- `native/sr2d_kernel/`
  - Owns the Rust/PyO3 crate that builds `_vitalloom_sr2d_rust`.
- `native/sr2d_cpp/`
  - Owns the C++/pybind11 project that builds `_vitalloom_sr2d_cpp`.
- `sr_physics2d/adapter.py`
  - Owns adapter selection, native availability checks, and Python fallback.
- `tests/test_sr_physics2d_native_parity.py`
  - Owns Python/Rust parity and fallback semantics.
- `tests/test_sr_physics2d_cpp_parity.py`
  - Owns Python/C++ parity and fallback semantics.
- `tools/benchmark_engine.py`
  - Reports adapter name and native availability in SR2D benchmark output.
- `docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md`
  - Contains fresh-session prompts for later phases.
- `docs/superpowers/plans/2026-06-30-sr2d-cpp-native-completion.md`
  - Contains the C++ first-class backend completion plan.

---

### Task 1: Lock Native Selection Semantics

**Files:**
- Modify: `tests/test_sr_physics2d_adapter_contract.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/__init__.py`

- [x] **Step 1: Add failing tests for native adapter symbols and fallback**

Add tests that import `RustSrPhysics2DAdapter`, `is_native_sr2d_available`, and `make_default_adapter`.

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py
```

Expected before implementation: import failure for `RustSrPhysics2DAdapter`.

- [x] **Step 2: Implement native adapter selection**

Implement:

```python
def is_native_sr2d_available() -> bool: ...
class RustSrPhysics2DAdapter: ...
def make_default_adapter() -> SrPhysics2DAdapter: ...
```

Rules:

- `VITALOOM_SR2D_ADAPTER=python` always returns `PythonSrPhysics2DAdapter`.
- `VITALOOM_SR2D_ADAPTER=cpp` raises `RuntimeError` if `_vitalloom_sr2d_cpp.step_pvaec_circles` is unavailable.
- `VITALOOM_SR2D_ADAPTER=rust` raises `RuntimeError` if `_vitalloom_sr2d_rust.step_pvaec_circles` and legacy `_vitalloom_sr2d.step_pvaec_circles` are unavailable.
- `VITALOOM_SR2D_ADAPTER=auto` prefers C++, then Rust, then Python.

- [x] **Step 3: Run adapter contract tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_adapter_contract.py
```

Expected: PASS.

---

### Task 2: Add Native Parity Harness

**Files:**
- Create: `tests/test_sr_physics2d_native_parity.py`

- [x] **Step 1: Add fallback and parity tests**

Create tests for:

- `auto` falls back to Python when native is unavailable.
- Rust adapter matches Python output when `_vitalloom_sr2d_rust` or legacy `_vitalloom_sr2d` is available.
- Shared scenarios cover dynamic-dynamic, dynamic-static, pinned, membrane-locked, boundary bounce, max speed, zero-dt, and empty entities.

- [x] **Step 2: Run native parity tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_native_parity.py
```

Expected without native extension: one PASS and one SKIP.

Expected with native extension: all PASS.

- [x] **Step 3: Share scenarios with the C++ parity suite**

Use `tests/fixtures/sr2d_parity_cases.py` as the single source for Python/C++ and Python/Rust parity cases.

---

### Task 3: Add Rust/PyO3 Kernel Scaffold

**Files:**
- Create: `native/sr2d_kernel/Cargo.toml`
- Create: `native/sr2d_kernel/pyproject.toml`
- Create: `native/sr2d_kernel/src/lib.rs`

- [x] **Step 1: Create crate manifest**

Create a `cdylib` crate named `_vitalloom_sr2d` with PyO3 `extension-module`.

- [x] **Step 2: Implement `step_pvaec_circles`**

Expose:

```rust
step_pvaec_circles(
    positions,
    velocities,
    radii,
    entity_types,
    pinned,
    membrane_locked,
    dt,
    width,
    height,
    config,
) -> {"positions": ..., "velocities": ...}
```

The first kernel mirrors Python semantics: damping, speed clamp, boundary bounce, dynamic/static PVAEC type filters, circle collision, restitution, friction, hard separation, correction separation, and final clamp.

- [ ] **Step 3: Build locally when Rust tooling exists**

Run from `native/sr2d_kernel`:

```bash
python -B -m maturin develop
```

Expected with toolchain: extension builds and imports as `_vitalloom_sr2d`.

Expected without toolchain: document missing `cargo` or `maturin`; Python fallback tests must still pass.

---

### Task 3B: Add C++/pybind11 Kernel Scaffold

**Files:**
- Create: `native/sr2d_cpp/pyproject.toml`
- Create: `native/sr2d_cpp/CMakeLists.txt`
- Create: `native/sr2d_cpp/src/kernel.hpp`
- Create: `native/sr2d_cpp/src/kernel.cpp`
- Create: `native/sr2d_cpp/src/bindings.cpp`
- Create: `tests/test_sr_physics2d_cpp_parity.py`

- [x] **Step 1: Create C++ extension project**

Create a scikit-build-core project that builds `_vitalloom_sr2d_cpp` with `pybind11_add_module`.

- [x] **Step 2: Implement `step_pvaec_circles`**

Expose the same primitive-array contract as Rust and mirror Python PVAEC semantics.

- [ ] **Step 3: Build locally when C++ tooling exists**

Run:

```bash
python -m pip install scikit-build-core pybind11 cmake ninja
python -m pip install ./native/sr2d_cpp
```

Expected with toolchain: extension builds and imports as `_vitalloom_sr2d_cpp`.

Expected without toolchain: document missing compiler/CMake/build packages; Python fallback tests must still pass.

---

### Task 4: Make Benchmark Output Observable

**Files:**
- Modify: `tools/benchmark_engine.py`

- [x] **Step 1: Add adapter metadata to SR2D benchmark**

Include:

```python
"adapter": world.adapter.__class__.__name__
"native_available": is_native_sr2d_available()
"cpp_available": is_cpp_sr2d_available()
"rust_available": is_rust_sr2d_available()
```

- [ ] **Step 2: Run benchmark**

Run:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 3
```

Expected: JSON output contains `sr2d_step_120`, `adapter`, and `native_available`.

- [x] **Step 3: Add dense and sparse SR2D cases**

Run:

```bash
python -B tools/benchmark_engine.py --case sr2d_dense --repeats 1
python -B tools/benchmark_engine.py --case sr2d_sparse --repeats 1
```

Expected: JSON output contains `entities`, `iterations`, `adapter`, `native_available`, `cpp_available`, `rust_available`, and `first_position`.

---

### Task 4B: Add Native Import/Build Smoke Reporting

**Files:**
- Create: `tools/check_sr2d_native.py`
- Create: `tests/test_sr2d_native_smoke_tool.py`

- [x] **Step 1: Add smoke command**

Report C++ and Rust import status, whether `step_pvaec_circles(...)` is exposed, detected native toolchain commands, and Python build package availability.

- [x] **Step 2: Keep missing native non-fatal**

The command returns exit code 0 when native modules or compilers are absent, because Python fallback remains valid.

Run:

```bash
python -B tools/check_sr2d_native.py
python -B -m pytest -q -p no:cacheprovider tests/test_sr2d_native_smoke_tool.py
```

---

### Task 5: Update Roadmap, Prompts, And Index

**Files:**
- Modify: `docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md`
- Modify: `docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md`
- Modify: `docs/INDEX.md`

- [ ] **Step 1: Ensure roadmap names concrete native interfaces**

Roadmap must mention:

- `CppSrPhysics2DAdapter`
- `RustSrPhysics2DAdapter`
- `is_cpp_sr2d_available()`
- `is_rust_sr2d_available()`
- `is_native_sr2d_available()`
- `_vitalloom_sr2d_cpp.step_pvaec_circles(...)`
- `_vitalloom_sr2d_rust.step_pvaec_circles(...)`
- legacy `_vitalloom_sr2d.step_pvaec_circles(...)`
- `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`

- [ ] **Step 2: Ensure prompts point to this plan**

Prompts must reference:

```text
docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md
```

- [ ] **Step 3: Add index links**

Add links under `docs/INDEX.md` Agent execution materials for:

- native roadmap design
- C++ native completion plan
- Rust native kernel implementation plan
- native phase prompts

---

### Task 6: Final Verification

**Files:**
- Existing touched files only

- [ ] **Step 1: Run focused Python tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
```

Expected: PASS, with native parity skipped if `_vitalloom_sr2d` is unavailable.

- [ ] **Step 2: Run SR2D benchmark**

Run:

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 3
```

Expected: PASS and output includes adapter metadata.

- [ ] **Step 3: Run syntax and boundary guardrails**

Run:

```bash
python -B -m compileall -q FrameCore tools
python -B tools/check_core_boundaries.py
```

Expected: PASS.

- [ ] **Step 4: Run doc checks**

Run:

```bash
Select-String -Path 'docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md','docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md','docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md' -Pattern ('TB' + 'D|TO' + 'DO|fill in ' + 'details|2026-06-' + '29')
git diff --check -- docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md docs/prompts/2026-06-30-sr2d-rust-native-kernel-prompts.md docs/INDEX.md FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tools/benchmark_engine.py native/sr2d_kernel/Cargo.toml native/sr2d_kernel/pyproject.toml native/sr2d_kernel/src/lib.rs
```

Expected: no placeholder hits and no whitespace errors.

## Self-Review Notes

- This plan implements a real native-language seam, not just a Python-only refactor.
- Current environment may lack Rust tooling. That limits local build verification, but not Python fallback verification.
- Future broadphase work should happen only after this kernel passes parity.
