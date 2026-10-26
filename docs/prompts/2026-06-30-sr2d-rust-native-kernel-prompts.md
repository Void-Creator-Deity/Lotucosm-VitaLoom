# C0dex Prompts: SR2D Native Phases

These prompts are meant for fresh C0dex sessions. Do not require old thread history.

## Phase 2A Prompt: C++ Native Kernel Completion

```text
Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the repository files.

Goal: complete C++ as a first-class SR2D native backend behind the existing SrPhysics2DAdapter boundary. C++ must be equal to Rust in adapter selection, tests, docs, and benchmark observability.

Read first:
- docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md
- docs/superpowers/plans/2026-06-30-sr2d-cpp-native-completion.md
- docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md
- docs/adr/0006-native-acceleration-seams.md
- docs/sr_physics2d.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/pvaec_contacts.py
- tests/test_sr_physics2d_adapter_contract.py
- tests/test_sr_physics2d_cpp_parity.py

Required skills:
- Use superpowers:subagent-driven-development or superpowers:executing-plans.
- Use superpowers:test-driven-development for each Python behavior change.
- Use superpowers:verification-before-completion before claiming success.

Guardrails:
- Keep SrPhysics2DWorld.step() as the public entry point.
- PythonSrPhysics2DAdapter remains the behavior oracle and fallback.
- The C++ module must not import or mutate Python scene entities directly.
- C++ module name is _vitalloom_sr2d_cpp.
- VITALOOM_SR2D_ADAPTER must support python, cpp, rust, and auto.
- auto selection order is cpp, then rust, then python.
- Unsupported native cases must fall back to Python unless the requested native module itself is missing.
- Do not stage or revert unrelated working-tree changes.

Acceptance:
- CppSrPhysics2DAdapter and is_cpp_sr2d_available() are exported.
- tests cover missing-C++ fallback, explicit missing-C++ RuntimeError, and Python/C++ parity when the extension is importable.
- native/sr2d_cpp contains pyproject.toml, CMakeLists.txt, src/kernel.cpp, src/bindings.cpp, and any small headers needed by the build.
- tools/benchmark_engine.py --case sr2d --repeats 3 reports adapter, native_available, cpp_available, and rust_available.
- If C++ tooling is absent, record missing tools and keep Python fallback tests passing.

Verification:
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
python -B tools/benchmark_engine.py --case sr2d --repeats 3
python -B -m compileall -q FrameCore tools
python -B tools/check_core_boundaries.py
```

## Phase 2B Prompt: Rust Native Kernel Prototype

```text
Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the repository files.

Goal: implement or maintain the Rust/PyO3 native PVAEC circle kernel behind the existing SrPhysics2DAdapter boundary. Rust is first-class alongside C++; it is not a replacement for the C++ backend.

Read first:
- docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md
- docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md
- docs/adr/0006-native-acceleration-seams.md
- docs/sr_physics2d.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/adapter.py
- tests/test_sr_physics2d_adapter_contract.py

Required skills:
- Use superpowers:subagent-driven-development or superpowers:executing-plans.
- Use superpowers:test-driven-development for each code task.
- Use superpowers:verification-before-completion before claiming success.

Guardrails:
- Keep SrPhysics2DWorld.step() as the public entry point.
- PythonSrPhysics2DAdapter remains the behavior oracle and fallback.
- The Rust module must not import or mutate Python scene entities directly.
- Rust standard module name is _vitalloom_sr2d_rust; legacy _vitalloom_sr2d may be accepted for compatibility.
- Unsupported native cases must fall back to Python unless VITALOOM_SR2D_ADAPTER=rust explicitly requests a Rust module and it is unavailable.
- Do not stage or revert unrelated working-tree changes.

First commands:
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py
python -B tools/benchmark_engine.py --case sr2d --repeats 1

Then execute Task 1 from docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md.
```

## Phase 3 Prompt: Parity Harness And Selection

```text
Do not load old C0dex threads. Continue from repository state and these docs:
- docs/superpowers/specs/2026-06-30-sr2d-native-roadmap-design.md
- docs/superpowers/plans/2026-06-30-sr2d-rust-native-kernel.md

Goal: expand SR2D Python/C++ and Python/Rust parity coverage and make adapter selection visible, deterministic, and benchmarked.

Acceptance:
- tests cover dynamic-dynamic, dynamic-static, pinned, membrane_locked, boundary bounce, max speed, zero dt, empty entities, and unsupported mode fallback.
- VITALOOM_SR2D_ADAPTER=python, cpp, rust, and auto have explicit tests.
- benchmark output includes adapter name, native availability, C++ availability, and Rust availability.
- benchmark has default, dense, and sparse SR2D cases.
- tools/check_sr2d_native.py reports C++/Rust import status, kernel symbol availability, native toolchain commands, and Python build packages.
- normal app launch degrades to Python fallback when the native extension is missing.
- native implementation exposes CppSrPhysics2DAdapter, RustSrPhysics2DAdapter, is_cpp_sr2d_available(), is_rust_sr2d_available(), is_native_sr2d_available(), _vitalloom_sr2d_cpp.step_pvaec_circles(...), and _vitalloom_sr2d_rust.step_pvaec_circles(...).

Required verification:
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py
python -B -m pytest -q -p no:cacheprovider tests/test_sr2d_native_smoke_tool.py tests/test_benchmark_engine_sr2d_variants.py
python -B tools/check_sr2d_native.py
python -B tools/benchmark_engine.py --case sr2d --repeats 3
python -B tools/benchmark_engine.py --case sr2d_dense --repeats 3
python -B tools/benchmark_engine.py --case sr2d_sparse --repeats 3
python -B tools/check_core_boundaries.py
```

## Phase 4 Prompt: Data-Oriented Broadphase

```text
Do not load old C0dex threads. Continue from the repository docs and current native SR2D implementation.

Goal: replace the native O(n^2) PVAEC candidate-pair loop with a deterministic data-oriented broadphase while preserving adapter behavior.

Design constraints:
- Start with a uniform spatial hash because it is deterministic, simple, and matches the current circle-heavy 2D scenes.
- Keep broadphase internal to the selected native backend. Python only passes snapshots and receives results.
- Prove candidate-pair equivalence against the simple O(n^2) path on small fixtures before using it in benchmarks.
- Keep an environment flag or test-only switch that can force the simple native pair builder for parity debugging.

Acceptance:
- native broadphase parity tests pass.
- benchmark has at least one dense case and one sparse case.
- default adapter selection still falls back cleanly without the native module.
```

## Phase 5 Prompt: Packaging And CI

```text
Do not load old C0dex threads. Continue from repository state after the SR2D Rust adapter is working locally.

Goal: package the C++ SR2D extension through scikit-build-core and the Rust SR2D extension through maturin. Add CI/runtime capability detection so releases can include native wheels without making C++ or Rust mandatory for developers.

Acceptance:
- native/sr2d_cpp can build with scikit-build-core on a supported local platform.
- native/sr2d_kernel can build with maturin on the supported local platform.
- pyproject or packaging docs record how each extension is built.
- CI has native build jobs separate from pure Python checks.
- runtime logs or benchmark output identify whether Python, C++, or Rust adapter was selected.
- missing native extension never prevents Python fallback in normal app execution.
```

## Phase 6 Prompt: Next Native Seam Selection

```text
Do not load old C0dex threads. Continue from current docs and benchmark evidence.

Goal: decide the next native seam only after SR2D C++/Rust parity, benchmark, and packaging evidence exist.

Compare these candidates:
- SR render batching
- PS batch experiment runner
- asset provenance/hash scanning
- SR2D GPU or third-party physics backend

Decision rule:
- pick the candidate with a stable Python interface, measurable benchmark case, behavior tests, and low user-facing API churn.
- write an ADR before implementation.
- do not replace the SR2D adapter contract unless evidence shows it is the bottleneck.
```
