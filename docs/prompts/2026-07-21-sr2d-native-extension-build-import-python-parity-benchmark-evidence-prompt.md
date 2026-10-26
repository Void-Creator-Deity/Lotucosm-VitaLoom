# Phase E30 Fresh-Session Prompt -- SR2D Native Extension Build/Import, Python Parity and Benchmark Evidence

Date: 2026-07-21

You are continuing VitaLoom after E29. Begin by reading `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0006, the existing SR2D native plans, and current source/tests. Do not rely on memory alone.

## Architecture authority

```text
L0 FrameCore (sole root framework)
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin)
   ├─ recursive downstream plugin Host / derived framework
   └─ versions/1.0.0/runtime (product runtime boundary)
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions and Host Adapters
      └─ L4 Project World addons
```

This is a self-developed Unity/Godot-class engine, not a migration to Unity, Godot, Unreal, Electron, or another shell. The current PyQt6/QPainter/OpenGL code is a concrete legacy/current UI Host Adapter, not the framework root or extension authority. Native SR2D must remain an Implementation Adapter behind the existing SR2D seam inside the one L1 version runtime; it must not create a new framework, plugin Host, registry, manifest authority, composition root, or UI policy.

## Previous Gate summary

E29 completed Localization/menu/toolbar contribution isolation:

- exact `NestedPluginHost` remains the sole recursive downstream composition/control authority;
- `LegacyEditorPluginAdapter` owns live menu provider enumeration and concrete LayoutManager refresh mechanics;
- `LocalizationPlugin` only publishes language state/events and invokes a narrow Editor Host refresh seam;
- production runtime has no external `kernel.plugin_loader` consumer;
- full non-signature proof: `1315 passed, 25 skipped, 34 subtests passed`;
- offscreen Editor smoke: `plugins=13/20`;
- four architecture guardrails passed;
- signature collection remains blocked because `.venv` lacks `cryptography`.

## Fresh native preflight from 2026-07-21

Using `.\.venv\python.exe`:

- `tools/check_sr2d_native.py` reports `native_available=false`;
- `_vitalloom_sr2d_cpp`, `_vitalloom_sr2d_rust`, and legacy `_vitalloom_sr2d` are not importable;
- C++ tools `cl`, `cmake`, `g++`, `clang++`, `nmake` are unavailable;
- Rust tools `cargo` and `maturin` are unavailable;
- Python native build packages `pybind11`, `scikit_build_core`, and `maturin` are unavailable;
- `tools/build_sr2d_native.py --backend all --check-only` reports both backends `ready=false`.

This is a real environment blocker, not evidence that native acceleration is complete. The existing Python SR2D Adapter is the fallback path. The unblock path is an explicitly approved supported native toolchain plus build packages, followed by real build/import/parity/benchmark commands. Do not install packages or toolchains without approval.


## Current E30 checkpoint

- Interpreter-exact build/import evidence chain is implemented and covered by `5 passed`.
- Real C++ attempt still exits `2` with `build_import_verified=false` because the native toolchain and project-venv build packages are absent.
- Explicit benchmark selection `--sr2d-adapter {auto,python,cpp,rust}` is implemented; unavailable native requests raise and do not silently fall back.
- Source-contract red baseline was `7 failed, 14 passed`; focused Adapter/smoke green proof is `21 passed in 0.94s`.
- The existing SR2D seam is hardened: callable kernel detection, zero/negative `dt` no-op, broadphase forwarding, complete result validation before mutation, strict C++ input lengths, Python-oracle kinematic integration semantics, C++ `bruteforce`/`spatial_hash`, and Windows CMake runtime installation.
- Future real-native parity fixtures now cover `spatial_hash` and non-contact kinematic integration. Focused SR2D proof is `43 passed, 20 skipped in 8.81s`; all skips are unavailable-native parity cases.
- All four architecture guardrails pass, confirming no second framework, Host, registry, manifest authority, composition root, or UI policy was introduced.
- Explicit Python measurement: 100 entities, 120 iterations, repeats=3, mean `512.113 ms`, min `475.855 ms`, max `579.665 ms`.
- Fresh preflight still finds no native module, C++ toolchain, project-venv `pybind11`, or `scikit_build_core`; known VS 2022/CMake locations are absent. No installation was performed.
- E30 remains blocked on explicit approval/provisioning of exactly one native backend. Do not redo Tasks 1-2 or mistake source-level green tests for real native completion.

## Unique Gate

**Phase E30 -- SR2D Native Extension Build/Import, Python Parity and Benchmark Evidence.**

Before production changes, create/update an E30 plan under `docs/superpowers/plans/` and capture a genuine failing or unavailable baseline. Then:

1. Audit `native/sr2d_cpp`, `native/sr2d_kernel`, SR2D Adapter selection, parity fixtures/tests, smoke/build tools, and benchmark cases.
2. Select exactly one first native backend based on actual available or explicitly approved toolchain provisioning. Do not attempt both merely for appearance.
3. Build and import a real extension exposing `step_pvaec_circles` through the existing Adapter seam.
4. Prove explicit-backend behavior, Python fallback behavior, and Python/native parity over the shared deterministic cases.
5. Benchmark Python and the built native Adapter with the existing benchmark tool. Report raw numbers and configuration honestly. If native is slower or unstable, keep Python/default policy unchanged.
6. Run focused SR2D tests, cross-domain regressions, full non-signature suite, real Editor smoke, and all four architecture guardrails.
7. Attempt signature-only collection and record the existing missing-`cryptography` blocker without installing it unless separately approved.
8. Update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, this phase plan, and create exactly one next fresh-session prompt.

## Completion bar

Do not call E30 complete unless at least one native extension actually builds and imports in the repository environment, exposes the expected kernel, passes deterministic parity against the Python oracle, and has benchmark evidence. Source scaffolds, skipped parity tests, check-only readiness reports, or a successful Python fallback are not sufficient.

## Preserved contracts

Do not break `.pond` semantics, AI command registry flows, Inspector command binding, SR2D public Adapter seams, package/project manifests, Project World L4 lifecycle, Player/export, reload, startup, or shutdown. Do not stage, commit, revert, clean, delete, or overwrite unrelated dirty work.

## Latest ABI audit checkpoint -- 2026-07-21

- A field-by-field Python/C++ semantics audit found and fixed broadphase canonicalization drift without changing framework/plugin topology. Native Adapters now receive the Python oracle's falsey/trim/lower mode semantics.
- C++ direct ABI now returns unchanged empty input before irrelevant mode validation, validates all array lengths, and rejects non-finite/out-of-range spatial-hash cell coordinates safely. Readiness checks require a callable kernel.
- Future real-native coverage includes canonicalized broadphase, dense multi-iteration spatial hash, intentionally raw contact coefficients, and direct ABI normalization/no-op/length/non-finite tests.
- Genuine red: `5 failed, 22 passed, 16 skipped`. Current focused SR2D: `49 passed, 32 skipped in 9.19s`; every new skip is still caused by unavailable native modules and is not completion evidence.
- Full non-signature: `1337 passed, 41 skipped, 34 subtests passed in 136.17s`. Offscreen Editor smoke: `plugins=13/20`. All four architecture guardrails pass.
- Fresh Python benchmark: mean `517.749 ms`, min `470.550 ms`, max `610.513 ms` for 100 entities, 120 iterations, bruteforce, repeats=3. Explicit C++ still exits loudly with no fallback.
- Signature-only collection remains blocked by missing `cryptography`; native build/import remains blocked by missing toolchains and project-venv build packages. No installation was performed.

Do not redo the completed source audit unless a real build exposes a discrepancy. The immediate next action, after explicit approval, is to provision exactly one backend (preferred Windows path: MSVC Build Tools + CMake + project-venv `pybind11`/`scikit-build-core`), build with the existing exact-interpreter tool, then run all previously skipped C++ parity/direct-ABI tests and the same-case native benchmark.

## E30 closed -- 2026-07-21

This prompt is historical. E30 is now complete with a real C++ build/import, unskipped shared C++ parity, direct ABI proof, and an approximately `8.126x` same-case speedup. Continue from the E31 fresh-session prompt; do not rerun E30 as though native were still unavailable.
