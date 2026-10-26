# Phase E30 -- SR2D Native Extension Build/Import, Python Parity and Benchmark Evidence

Date: 2026-07-21
Status: completed

## Architecture authority

VitaLoom remains plugin-shaped:

```text
L0 FrameCore (sole root framework)
鈹斺攢 L1 lotucosm-vitaloom (sole engine/product mega-plugin and recursive plugin Host)
   鈹斺攢 versions/1.0.0/runtime (product runtime boundary)
      鈹溾攢 L2 capability/domain Modules
      鈹溾攢 L3 engine extensions and Host Adapters
      鈹斺攢 L4 Project World addons
```

The C++ or Rust SR2D implementation is only an Adapter behind the existing Qt-free SR2D seam. It must not create another framework, plugin Host, registry, manifest authority, composition root, or UI policy. The Python Adapter remains the behavior oracle and mandatory fallback.

## Previous Gate summary

Phase E29 completed Legacy Editor Localization Menu/Toolbar Contribution Refresh Adapter Isolation:

- exact `NestedPluginHost` remains the sole recursive downstream composition/control authority;
- `LegacyEditorPluginAdapter` owns live menu provider enumeration and concrete LayoutManager refresh mechanics;
- `LocalizationPlugin` publishes language state/events and invokes only a narrow Editor Host refresh seam;
- focused proof: `6 passed`;
- expanded non-signature proof recorded by E29: `1315 passed, 25 skipped, 34 subtests passed`;
- real offscreen Editor smoke recorded by E29: `plugins=13/20`;
- all four architecture guardrails passed.

## E30 objective

Build and import at least one real SR2D native extension in the repository environment, expose `step_pvaec_circles`, prove deterministic parity against the Python oracle, and record comparable Python/native benchmark evidence. Keep Python/default policy unless the measurements and stability evidence justify changing it.

## Fresh baseline -- 2026-07-21

Commands use `.\.venv\python.exe`.

### Native availability

`tools/check_sr2d_native.py` reports:

- `native_available=false`;
- `_vitalloom_sr2d_cpp`, `_vitalloom_sr2d_rust`, and legacy `_vitalloom_sr2d` are not importable;
- `cl/cmake/g++/clang++/nmake/cargo/rustc/maturin` are unavailable, including common Visual Studio, CMake, and user Cargo install locations;
- `pybind11/scikit_build_core/maturin` are absent from the project virtual environment.

### Genuine unavailable/build baseline

`tools/build_sr2d_native.py --backend cpp` exits `2` and records `build_skipped=true` because the toolchain and Python build packages are unavailable. This is a real environment blocker, not native completion evidence.

### Test baseline

```text
13 passed, 16 skipped in 1.28s
```

The sixteen skips are the unavailable C++/Rust parity cases and therefore do not prove a native Adapter.

### Python oracle benchmark baseline

Explicit `VITALOOM_SR2D_ADAPTER=python`, `--case sr2d --repeats 3`:

```text
adapter=PythonSrPhysics2DAdapter
entities=100
iterations=120
mean_ms=830.226
min_ms=568.777
max_ms=1082.729
```

These numbers are a local baseline only; the wide spread requires same-process/same-case comparison before policy decisions.

## Audit findings

1. `tools/build_sr2d_native.py` reports and executes the literal command `python -m pip ...`. That can target a different interpreter from the invoking `.venv`, weakening build/import evidence.
2. Build success currently records only pip return code and output tails. It does not automatically run the declared import/kernel check in the same interpreter after installation.
3. `tools/benchmark_engine.py` reports whichever Adapter auto-selection produced, but lacks a narrow CLI seam for explicit same-case Python versus native comparison.
4. Existing parity fixtures cover deterministic overlap, static/dynamic, pinned, membrane lock, boundary bounce, max-speed clamp, zero-dt, and empty inputs. They are suitable as the first oracle set once a module imports.
5. Both native sources implement the same narrow `step_pvaec_circles` kernel shape. C++ is the preferred first backend for this Windows workspace, but provisioning must be explicitly approved before installing a compiler/toolchain or build packages.

## Implementation plan

### Task 1 -- Make build evidence interpreter-exact

- Add red tests requiring build metadata to identify `sys.executable`.
- Execute pip with an argument vector beginning with `sys.executable`, not shell text splitting.
- After a successful build, import the exact backend module in the same interpreter and verify `step_pvaec_circles`.
- Record build and import return codes/stdout/stderr separately.
- Preserve check-only status and truthful missing-tool/package facts.

### Task 2 -- Add comparable Adapter benchmark selection

- Add red tests for a narrow SR2D benchmark Adapter selector.
- Allow explicit `python`, `cpp`, `rust`, and `auto` selection without changing global engine defaults.
- Report requested Adapter, selected Adapter, availability, case parameters, and timing.
- Fail explicitly when a requested native Adapter is unavailable; never silently benchmark Python under a native label.

### Task 3 -- Provision/select exactly one first backend

- Preferred first backend: C++/pybind11 on Windows, because the repository already contains `native/sr2d_cpp` and a dedicated `CppSrPhysics2DAdapter`.
- Before installing MSVC/CMake/pybind11/scikit-build-core, obtain explicit user approval.
- If C++ provisioning is declined but Rust is approved/available, use Rust/PyO3 instead; do not build both for appearance.

### Task 4 -- Real build/import/parity/benchmark proof

- Build the selected extension into the project `.venv`.
- Run exact import and kernel-symbol smoke.
- Run explicit-backend and auto/fallback contract tests.
- Run all deterministic Python/native parity cases without native skips.
- Benchmark Python and native with identical entity set, iterations, broadphase, process policy, and repeats.
- Keep Python/default policy if native is slower, unstable, or semantically divergent.

### Task 5 -- Regression and phase closure

- Run focused SR2D tests and cross-domain regressions.
- Run full non-signature suite.
- Run real Editor smoke and all four architecture guardrails.
- Attempt signature-only collection and record the existing missing-`cryptography` blocker unless separately approved.
- Update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, this plan, and create exactly one next fresh-session prompt.

## Completion bar

E30 is complete only when all of the following are true:

1. At least one native extension actually builds in the repository environment.
2. The extension imports through the same `.venv` interpreter used to build it.
3. The imported module exposes callable `step_pvaec_circles`.
4. Explicit native Adapter selection does not silently fall back.
5. All shared deterministic Python/native parity cases pass without native skips.
6. Comparable Python/native benchmark evidence exists with raw configuration and timing.
7. Default policy is justified by evidence and Python fallback remains intact.
8. Relevant regressions, Editor smoke, and architecture guardrails pass.

Source scaffolds, check-only output, skipped parity tests, or a successful Python fallback are insufficient.

## Current fallback and unblock path

- Release-safe fallback: `VITALOOM_SR2D_ADAPTER=auto` continues to select `PythonSrPhysics2DAdapter` while no native module imports.
- Unblock path: explicit approval to provision one supported native toolchain plus the corresponding Python build packages, followed by real build/import/parity/benchmark commands.
- Until then, continue only work that strengthens truthful build/import/benchmark evidence; do not call E30 complete and do not switch to an easier unrelated Gate.

## Unique next Gate after E30

**Phase E31 -- SR2D C++ Reproducible Packaging, Release Artifact, and Clean-Fallback Proof.** Convert the successful local extension proof into a supported optional package/release path without machine-local tool/header assumptions, and prove both packaged import and clean Python fallback.


## Progress checkpoint -- 2026-07-21

### Completed evidence work

- Task 1 is complete: `tools/build_sr2d_native.py` now uses `sys.executable` argument vectors, `--no-build-isolation`, same-interpreter import/kernel proof, and separate truthful build/import results. Focused proof: `5 passed in 0.84s`.
- Check-only output identifies the repository `.venv\python.exe` exactly. A genuine C++ build attempt exits `2`, records `build_skipped=true`, and leaves `build_import_verified=false` while the toolchain/packages are absent.
- Task 2 is complete: `tools/benchmark_engine.py` now exposes `--sr2d-adapter {auto,python,cpp,rust}`, constructs the requested Adapter directly, reports `requested_adapter` and `selected_adapter`, and never mutates the process Adapter environment.
- Benchmark selector red baseline: `6 failed`; focused green group: `18 passed in 3.75s`.
- Full focused SR2D group: `36 passed, 16 skipped in 8.74s`. All sixteen skips remain native parity cases because no native module imports; they are not completion evidence.
- Architecture guardrails after the E30 evidence changes: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`.
- Explicit Python benchmark, same CLI seam, `100` entities, `120` iterations, bruteforce broadphase, three repeats: mean `512.113 ms`, min `475.855 ms`, max `579.665 ms`; selected Adapter was `PythonSrPhysics2DAdapter`.
- Explicit C++ benchmark request exits `1` with `RuntimeError` naming missing `_vitalloom_sr2d_cpp.step_pvaec_circles`; it does not silently run Python.

### Remaining blocker and completion state

E30 remains **in progress**. Tasks 1 and 2 are closed, but Tasks 3-5 cannot close until one native toolchain and its project-venv build packages are explicitly approved/provisioned, followed by real build/import, unskipped parity, comparable native benchmark, full regression, Editor smoke, and architecture guardrails. No native acceleration completion or default-policy change may be claimed yet.

### Source contract hardening checkpoint -- 2026-07-21

- Re-audited the actual authority chain: `FrameCore` remains the sole L0 root; `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and recursive Host; `versions/1.0.0/runtime` remains the product runtime boundary. PyQt6/QPainter/OpenGL remain concrete legacy/current UI Host Adapters rather than engine or plugin authority.
- Confirmed that Python `_hard_push_apart()` followed by `_separate()` is intentional oracle behavior; the analogous C++ position work is not a duplicate-correction defect.
- Captured a genuine source-contract red baseline: `7 failed, 14 passed`. The failures covered non-callable kernel attributes, zero-`dt` native calls, missing broadphase forwarding, malformed/short native result arrays, partial mutation risk, and missing Windows CMake runtime installation.
- Hardened the existing SR2D Adapter seam rather than creating a new Host or registry: kernel availability now requires a callable symbol; zero/negative `dt` and empty input are no-ops; `pvaec_broadphase` is forwarded; complete positions/velocities output is validated before any entity mutation.
- Hardened the C++ source scaffold: strict equal-length ABI inputs, Python-oracle kinematic integration semantics, `bruteforce` and `spatial_hash` pair selection, unsupported-mode errors, and Windows `RUNTIME DESTINATION .` installation.
- Added future real-native parity coverage for `spatial_hash` and for a non-contact kinematic entity, specifically guarding the two corrected C++ semantics.
- Focused contract/smoke green proof: `21 passed in 0.94s`. Expanded SR2D proof after the new parity fixtures: `43 passed, 20 skipped in 8.81s`; all twenty skips are real C++/Rust module-unavailable parity cases and are not completion evidence.
- Re-ran all four architecture guardrails: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, and `release consistency OK`. Changed Python/source compile proof also passed.
- Fresh native preflight still reports no importable module, no `cl/cmake/ninja/g++/clang++/nmake`, and no project-venv `pybind11/scikit_build_core`. Known Visual Studio 2022 Build Tools/Community and CMake locations were also absent. No dependency or toolchain was installed.

E30 therefore remains **in progress**. The source and Adapter Interface are substantially better prepared, but the completion bar still requires an explicitly approved toolchain, a real build/import, unskipped parity, and comparable native benchmark evidence.

### ABI semantics and direct-extension safety checkpoint -- 2026-07-21

- Completed a field-by-field Python-oracle/C++ audit across integration, body classification, inverse mass, impulse/friction, intentional hard-push plus correction, boundary clamp, pair ordering, configuration, and direct ABI error modes. Restitution, friction, slop, and correction remain intentionally unclamped because that is the current Python Interface semantics; no new geometry or scene policy was introduced.
- Captured a genuine red baseline of `5 failed, 22 passed, 16 skipped`: native Adapter broadphase values were not canonicalized, and the C++ scaffold lacked the direct-ABI normalization/no-op/finite-coordinate contracts.
- Added one shared Python canonicalization policy at the existing SR2D Module seam: every native Adapter now receives the same `strip().lower()` broadphase label as the Python oracle, with falsey values selecting `spatial_hash`. Unsupported non-empty labels still fail explicitly.
- Hardened the C++ binding/kernel without changing the L0/L1 topology: direct bindings mirror falsey/trim/lower broadphase semantics, empty equal-length input returns unchanged before irrelevant broadphase validation, and spatial-hash cell conversion rejects non-finite or out-of-range coordinates instead of relying on unsafe floating-to-integer conversion. `std::invalid_argument` remains a Python `ValueError` through pybind11.
- Made native readiness reporting truthful for malformed importable modules: `tools/check_sr2d_native.py` now requires a callable `step_pvaec_circles`, matching the Adapter and build/import proof.
- Expanded future unskipped parity coverage with canonicalized broadphase, dense spatial-hash multi-iteration contact, and intentionally unclamped contact coefficients. Added direct C++ ABI tests for normalization, empty no-op, mismatched lengths, and non-finite spatial-hash coordinates. These tests currently skip only because the extension is not built.
- Focused SR2D proof is now `49 passed, 32 skipped in 9.19s`. The 32 skips are unavailable-native cases (shared C++/Rust parity plus direct C++ ABI); they are not native completion evidence.
- Full non-signature regression passed: `1337 passed, 41 skipped, 34 subtests passed in 136.17s`. Real offscreen Editor smoke passed with `plugins=13/20`, zero discovery failures, and deterministic reverse shutdown. All four architecture guardrails passed.
- Fresh explicit Python benchmark, 100 entities / 120 iterations / bruteforce / repeats=3: mean `517.749 ms`, min `470.550 ms`, max `610.513 ms`; requested `python`, selected `PythonSrPhysics2DAdapter`. Explicit C++ still exits `1` with the missing callable-kernel RuntimeError and does not fall back silently.
- Signature-only collection still exits `2` because `.venv` lacks `cryptography`. Fresh native preflight still finds no importable backend, C++/Rust toolchain, or project-venv native build packages. No dependency or toolchain was installed.

At this historical checkpoint, E30 remained **in progress**. The completion path was a real same-interpreter build/import, unskipped parity/direct-ABI execution, and comparable native benchmark evidence; the final section below records that closure.
## E30 completion evidence -- 2026-07-21

- Existing, previously undiscovered system tools were sufficient: VS 2022 Community/MSVC 19.44, bundled CMake/Ninja, and an existing complete Torch pybind11 include tree. No installation or network download occurred.
- CMake now supports a normal pybind11 package and an explicit non-hardcoded header-only fallback through `PYBIND11_INCLUDE_DIR`; contract red `1 failed`, green `2 passed`.
- The real build produced `_vitalloom_sr2d_cpp.cp311-win_amd64.pyd`, installed it into the project `.venv`, and the same `.venv\python.exe` imported callable `step_pvaec_circles`.
- C++ Adapter/direct ABI proof: `47 passed, 1 skipped`. Expanded SR2D proof: `66 passed, 16 skipped`. No shared C++ parity/direct ABI test is skipped.
- Identical benchmark, 100 entities / 120 iterations / bruteforce / repeats=3: Python mean `505.462 ms`; C++ mean `62.205 ms`; approximately `8.126x` faster. `auto` selects C++ when importable; Python remains explicit and automatic fallback.
- Final non-signature regression: `1354 passed, 25 skipped, 34 subtests passed in 133.26s`. Editor smoke `plugins=13/20`; four architecture guardrails passed.
- Signature-only collection still fails because `cryptography` is absent. This is recorded, not hidden and not installed around.

E30 is complete. This proves one real native Implementation Adapter and its local acceleration evidence; it does not prove machine-independent wheel/release packaging or complete the whole engine.

