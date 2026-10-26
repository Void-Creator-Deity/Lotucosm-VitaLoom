# Phase E31 -- SR2D C++ Reproducible Packaging, Release Artifact, and Clean-Fallback Proof

Date: 2026-07-21
Status: completed

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream Plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

The optional SR2D C++ extension remains an Implementation Adapter behind the existing `SrPhysics2DAdapter` Interface inside the sole L1 version runtime. Packaging must not create a peer FrameCore product plugin, second Host, registry, planner, manifest authority, composition root, UI framework, or direct native access to scene/editor objects. Python remains the behavior oracle and mandatory fallback.

## Previous Gate summary

E30 completed the first real native proof:

- VS 2022/MSVC, CMake/Ninja and an explicit existing pybind11 include tree built `_vitalloom_sr2d_cpp.cp311-win_amd64.pyd`;
- the project `.venv\python.exe` imported callable `step_pvaec_circles`;
- C++ Adapter/direct ABI proof: `47 passed, 1 skipped`;
- expanded SR2D proof: `66 passed, 16 skipped`, with no shared C++ parity/direct ABI skip;
- identical 100-entity / 120-iteration / bruteforce / 3-repeat benchmark: Python mean `505.462 ms`, C++ mean `62.205 ms`, about `8.126x` faster;
- full non-signature regression: `1354 passed, 25 skipped, 34 subtests passed`; Editor smoke and all four architecture guardrails passed.

E30 proves local build/import/parity/acceleration. It does not prove a clean-machine wheel, supported build dependency sourcing, isolated installation, release metadata, or absence-of-native fallback.

## Current audit baseline

1. `native/sr2d_cpp/pyproject.toml` already selects `scikit_build_core.build`, but still publishes version `0.1.0` while the product/version manifests are `1.0.0`.
2. The standard build requirements declare `scikit-build-core>=0.9` and `pybind11>=2.12`, but neither package is installed in the project `.venv`; no cached wheel exists. Installing/downloading them requires explicit approval.
3. The repository does not have the `build` frontend package. `python -m build` is additionally shadowed by the native `build/` directory namespace. The supported frontend for this phase will therefore be exact-interpreter `python -m pip wheel --no-deps`, which invokes the declared PEP 517 backend in build isolation.
4. `tools/build_sr2d_native.py` proves exact-interpreter editable/install import, but does not produce, inspect, install, or verify a wheel artifact.
5. The E30 extension is currently installed in the project `.venv`; clean-fallback proof must isolate `site-packages` (for example with `python -S`) and assert the imported Adapter/module path, rather than relying on ambient imports.
6. The accepted native roadmap requires C++ wheels through scikit-build-core and independent native CI while pure-Python CI remains valid without a native wheel.
7. Existing `.github/workflows/ci.yml` and other dirty files are prior/user work. Do not overwrite them; add a separate native workflow only if tests establish the required contract.

## Implementation plan

### Task 1 -- Define release metadata and wheel contract with red tests

- Add tests requiring the native distribution name/version/Python floor to align with the L1 product version (`1.0.0`, Python `>=3.11`).
- Require scikit-build-core and pybind11 as build-system dependencies, an extension-only wheel, and explicit source inclusion for CMake/C++ files.
- Add a narrow wheel tool contract: exact `sys.executable`, `pip wheel --no-deps`, deterministic output directory, one compatible wheel, parsed `METADATA`/`WHEEL`/`RECORD`, and callable-kernel verification after installation.

### Task 2 -- Implement exact-interpreter wheel build and inspection

- Deepen the existing native build tooling rather than create a package manager or runtime authority.
- Build through the PEP 517 pyproject with `sys.executable -m pip wheel --no-deps`.
- Inspect the wheel as a zip archive and validate distribution name, version, non-pure platform tag, extension filename, `METADATA`, `WHEEL`, and `RECORD` before installation.
- Keep build dependency sourcing standard and machine-independent; do not hardcode `D:\app`, Torch, or a local include path in product metadata or normal wheel commands.

### Task 3 -- Prove isolated install and clean fallback

- Install the built wheel with exact interpreter `pip install --no-deps --target <isolated-target>`.
- Run `python -S` with only the isolated target added and assert `_vitalloom_sr2d_cpp.__file__` is inside that target and `step_pvaec_circles` is callable.
- Run a separate `python -S` process with runtime source paths but no site-packages/native target; prove `auto` selects `PythonSrPhysics2DAdapter`, `is_cpp_sr2d_available()` is false, and explicit C++ construction fails loudly.
- Re-run shared parity against the isolated wheel path, not the ambient `.venv` installation, if the test harness permits; otherwise add an exact isolated parity runner.

### Task 4 -- Independent native CI and release consistency

- Add a separate Windows native workflow for supported CPython versions, wheel build, artifact inspection, isolated install/import, clean fallback, and focused parity.
- Do not make the existing pure-Python/Linux CI depend on native compilation.
- Extend release consistency checks only for stable repository-owned metadata, not machine-local build output.

### Task 5 -- Regression and closure

- Run focused wheel/native tests and relevant package, manifest, Player/export regressions.
- Run the full non-signature suite, real Editor smoke, and project/core/GUI/release guardrails.
- Attempt signature-only collection and record the existing `cryptography` blocker unless installation is separately approved.
- Update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, this plan, and create exactly one next fresh-session prompt.

## Completion bar

E31 is complete only when all are true:

1. the repository has a supported machine-independent PEP 517 wheel route using scikit-build-core and pybind11 declarations;
2. native distribution metadata aligns with the product release contract;
3. a real compatible non-pure wheel is produced and structurally inspected;
4. the wheel installs into an isolated target and imports callable `step_pvaec_circles` from that target;
5. a no-native isolated environment proves automatic Python fallback and loud explicit-C++ failure;
6. shared parity is executed against the packaged artifact or an equivalently isolated installed artifact;
7. independent native CI exists without making pure-Python CI require native tools;
8. relevant regressions, Editor smoke, and architecture guardrails pass.

A locally installed `.pyd`, source-only CMake success, a machine-local pybind11 path, a pure-Python wheel, skipped packaged parity, or ambient-site import is insufficient.

## Preserved contracts

Do not break `.pond` scene semantics, AI command registry flows, Inspector binding, SR2D public seams, package/project manifests, Project World L4 lifecycle, Player/export, reload/startup/shutdown, or the recursive L0-L4 topology. Do not stage, commit, revert, clean, delete, or overwrite unrelated dirty work.

## Completion evidence -- 2026-07-21

- Re-audited the actual authority chain before continuing: `FrameCore` remains the sole L0 root; `lotucosm-vitaloom` remains the sole L1 engine/product mega-plugin and recursive downstream Plugin Host; `versions/1.0.0/runtime` remains the product boundary. The initial architecture proof was `36 passed`, followed by `project plugin model OK`, `core boundaries OK`, and `GUI boundaries OK`.
- Re-ran the repaired release consistency surface before native work: `12 passed`; `release consistency OK`.
- Generator/build-isolation contract red was `4 failed, 6 passed`. Final packaging contract is `11 passed`.
- `native/sr2d_cpp/pyproject.toml` now constrains CMake to `>=3.18,<4`, requests Ninja `>=1.11` through scikit-build-core, and disables generator fallback. Product metadata contains no machine-local Visual Studio, Torch, or `D:\app` path.
- `tools/package_sr2d_cpp.py` now forces `CMAKE_GENERATOR=Ninja`, discovers a supported VS 2022 x64 MSVC environment through `vswhere` and `VsDevCmd.bat`, and gives every build an ephemeral backend build directory so the failed VS18 cache cannot contaminate later builds.
- A real isolated PEP 517 build produced `dist/sr2d-cpp/lotucosm_vitaloom_sr2d_cpp-1.0.0-cp311-cp311-win_amd64.whl` (82,019 bytes, SHA-256 `719036407c11e6e98bf260fc8ea56bc71f6fcdb7c8d8d01b1bf1036453f8154a`). Wheel metadata, platform tag, native extension, and `RECORD` membership all passed inspection.
- Exact-interpreter isolated installation and `python -S` import proved `_vitalloom_sr2d_cpp.cp311-win_amd64.pyd` came from the temporary target and exposed callable `step_pvaec_circles`.
- A separate `python -S` no-native process proved `auto -> PythonSrPhysics2DAdapter`, while explicit C++ still failed loudly. Packaged Python-oracle parity executed without skip: `14 passed`.
- Focused SR2D/package/manifest/Player/export proof: `196 passed, 31 skipped, 17 subtests passed`. Full non-signature suite: `1366 passed, 39 skipped, 34 subtests passed in 129.59s`.
- Real offscreen Editor smoke remained healthy: `plugins=13/20`, zero discovery errors, deterministic reverse shutdown. All four guardrails passed: project plugin model, core boundaries, GUI boundaries, and release consistency.
- Signature-only collection still fails with `ModuleNotFoundError: No module named 'cryptography'`; signature verification is not claimed and no dependency was installed.

E31 is complete. Stable now: the optional C++ SR2D Implementation Adapter has a machine-independent, interpreter-exact Windows wheel route, isolated artifact proof, Python-oracle parity, and clean fallback while remaining behind the existing L1 runtime seam. Still unfinished: replacement UI Host parity, real current-context OpenGL pixel/interaction/benchmark readiness, signature verification, other platform wheels, and the wider engine roadmap. The persistent objective `彻底完善` remains active.

## Unique next Gate after E31

**Phase E32 -- Real Current-Context OpenGL Pixel, Interaction, and Benchmark Parity for Host-Adapter Readiness.** Keep the Qt-free viewport snapshot/draw-command Interface inside the sole L1 engine plugin runtime, treat QPainter and OpenGL as concrete legacy/current Host Adapters, and require real pixels, parity tolerances, interaction smoke, and comparable benchmarks before any `auto` policy change or future UI-host replacement claim.
