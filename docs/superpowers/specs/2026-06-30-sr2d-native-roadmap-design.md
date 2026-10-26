# SR2D Native Roadmap Design

Date: 2026-06-30

## Intent

The completed SR2D adapter boundary is only the first seam. The next refactor introduces real native-language implementations that can be selected, tested, benchmarked, packaged, and rolled back without changing `.pond` files, `GameViewport`, or AI command flows.

## Recommended Approach

Treat C++ and Rust as first-class native SR2D backends behind the same Python adapter boundary:

- C++/pybind11/scikit-build-core is the immediate first-class completion path because it matches common engine internals and external physics libraries.
- Rust/PyO3/maturin remains a first-class backend and a useful safety-oriented native path.
- Python remains the orchestration layer, fallback, and behavior oracle.

Both native backends own only the hot PVAEC circle integration/contact loop at first. They receive primitive arrays, return primitive arrays, and never own editor state, `.pond` parsing, AI commands, or viewport objects.

## Alternatives Considered

1. **C++ extension through pybind11**
   - Pros: close to commercial engine internals, CMake ecosystem, compatible with future Box2D-style experiments.
   - Cons: platform/compiler friction and native wheel complexity.
   - Decision: first-class backend now, with Python fallback mandatory when unavailable.

2. **Rust/PyO3 native kernel**
   - Pros: memory-safe native code, strong Python extension tooling, incremental packaging, straightforward fallback.
   - Cons: requires Rust toolchain and maturin packaging work.
   - Decision: first-class backend retained; short-term compatibility keeps `_vitalloom_sr2d` while the standard Rust name becomes `_vitalloom_sr2d_rust`.

3. **Adopt a full external physics engine immediately**
   - Pros: mature broadphase and solver behavior.
   - Cons: mismatches current PVAEC semantics and risks large behavior drift.
   - Decision: defer until the project has parity tests strong enough to compare a replacement engine honestly.

## Architecture

The native kernel receives a snapshot of primitive arrays, computes a step, and returns primitive arrays. It does not own scene entities, `.pond` data, Python objects, editor state, or AI command state.

```text
SrPhysics2DWorld.step()
  -> SrPhysics2DAdapter
     -> PythonSrPhysics2DAdapter
     -> CppSrPhysics2DAdapter
        -> _vitalloom_sr2d_cpp.step_pvaec_circles(...)
     -> RustSrPhysics2DAdapter
        -> _vitalloom_sr2d_rust.step_pvaec_circles(...)
        -> _vitalloom_sr2d.step_pvaec_circles(...)  # short-term legacy name
```

The first native paths cover PVAEC circle bodies without spring links. Unsupported modes or spring-linked PVAEC cases fall back to the Python adapter unless the user explicitly requests a native backend and the module itself is missing, in which case startup fails loudly.

Concrete Python-side additions:

- `CppSrPhysics2DAdapter`
- `RustSrPhysics2DAdapter`
- `is_cpp_sr2d_available()`
- `is_rust_sr2d_available()`
- `is_native_sr2d_available()` meaning either C++ or Rust is available
- `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`

Adapter selection:

- `python`: always use `PythonSrPhysics2DAdapter`
- `cpp`: require `_vitalloom_sr2d_cpp.step_pvaec_circles(...)`
- `rust`: require `_vitalloom_sr2d_rust.step_pvaec_circles(...)` or legacy `_vitalloom_sr2d.step_pvaec_circles(...)`
- `auto`: prefer C++, then Rust, then Python

Native module contracts:

- C++: `_vitalloom_sr2d_cpp.step_pvaec_circles(...)`
- Rust: `_vitalloom_sr2d_rust.step_pvaec_circles(...)`
- Rust legacy compatibility: `_vitalloom_sr2d.step_pvaec_circles(...)`

## Data Model

The first native boundary uses simple, explicit arrays:

- positions: `[(x, y), ...]`
- velocities: `[(vx, vy), ...]`
- radii: `[r, ...]`
- entity types: `["organism", "central_brain", "nutrient", "environment_well", ...]`
- pinned flags: `[bool, ...]`
- membrane-locked flags: `[bool, ...]`

This keeps parity debugging easy before introducing shared memory, SIMD, parallelism, broadphase acceleration, or a third-party physics backend.

## Phase Roadmap

### Phase 2: Native SR2D Kernel Prototypes

Create native backends behind the same adapter contract:

- C++ under `native/sr2d_cpp`, built with pybind11 and scikit-build-core as `_vitalloom_sr2d_cpp`.
- Rust under `native/sr2d_kernel`, built with PyO3 and maturin as `_vitalloom_sr2d_rust`, with temporary support for `_vitalloom_sr2d`.

Both expose `step_pvaec_circles(...)` and mirror Python PVAEC semantics: damping, max speed, boundary bounce, dynamic/static body filters, circle collision, impulse, friction, hard separation, correction separation, and final clamp.

### Phase 3: Parity Harness And Adapter Selection

Expand deterministic parity scenarios for Python/C++ and Python/Rust. Cover dynamic-dynamic, dynamic-static, pinned, membrane-locked, boundary bounce, max speed, zero-dt, empty entity, unsupported-mode fallback, `VITALOOM_SR2D_ADAPTER=python|cpp|rust|auto`, explicit missing-native failures, native import/build smoke reporting, and benchmark metadata for selected adapter plus C++/Rust availability.

Benchmark evidence includes default, dense, and sparse SR2D cases. Native import/build smoke must report missing compilers or Python build packages without making normal Python fallback runs fail.

### Phase 4: Data-Oriented Broadphase And Batch Layout

Move from O(n^2) pair building toward a deterministic spatial hash or dynamic-tree-inspired broadphase. Keep the same adapter contract, retain an O(n^2) debug path, and prove parity before accepting speedups.

### Phase 5: Packaging, CI, And Capability Detection

Build native wheels through scikit-build-core for C++ and maturin for Rust. Add independent native CI jobs so pure Python checks still run when toolchains are missing. Runtime capability detection must keep normal app launches on Python fallback when native wheels are absent.

### Phase 6: Native Expansion Beyond Physics

Only after SR2D has parity and packaging evidence, consider native render batching, PS batch experiments, asset hashing, or a third-party physics backend. Each new seam needs its own adapter, benchmark, fallback, and behavior tests.

## Guardrails

- Python adapter remains the source of truth until parity evidence says otherwise.
- Native code cannot directly mutate scene entities or inspect editor objects.
- AI command, CLI, MCP, and UI paths keep calling the same Python runtime entry points.
- No broad rewrite of FrameCore, project manifests, or viewport loading is part of these phases.
- Every phase must leave the app runnable without C++, Rust, or native wheels installed.

## Research Notes

Modern engine and extension patterns point to adapter seams plus data-oriented kernels:

- pybind11 and scikit-build-core are a modern Python C++ extension path built around CMake and wheel packaging.
- PyO3 and maturin support Rust-based Python extension modules and wheel workflows.
- Unity DOTS/ECS and Burst emphasize data-oriented layout and native performance; the useful lesson here is array-oriented kernels behind clear system boundaries.
- Godot GDExtension shows a stable engine-facing extension boundary, matching the adapter-seam approach.
- Box2D and Rapier reinforce that broadphase/contact generation is a separate kernel concern from scene orchestration.

## Source References

- pybind11: https://pybind11.readthedocs.io/
- scikit-build-core: https://scikit-build-core.readthedocs.io/
- cibuildwheel: https://cibuildwheel.pypa.io/
- PyO3: https://pyo3.rs/
- maturin: https://www.maturin.rs/
- Unity Entities: https://docs.unity3d.com/Packages/com.unity.entities@latest
- Unity Burst: https://docs.unity3d.com/Packages/com.unity.burst@latest
- Godot GDExtension: https://docs.godotengine.org/en/stable/tutorials/scripting/gdextension/
- Box2D documentation: https://box2d.org/documentation/
- Rapier documentation: https://rapier.rs/docs/
