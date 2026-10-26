# Phase E31 Fresh-Session Prompt -- SR2D C++ Reproducible Packaging, Release Artifact, and Clean-Fallback Proof

Date: 2026-07-21

Begin by reading `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0006, the completed E30 plan, native source/CMake/pyproject files, package/release manifests, and current tests. Do not infer architecture from the legacy PyQt editor.

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

VitaLoom is a self-developed Unity/Godot-class engine. PyQt6/QPainter/OpenGL are legacy/current UI Host Adapters, not the engine root, extension authority, or future framework rule source. SR2D native code remains an optional Implementation Adapter behind the existing Qt-free runtime Interface. Do not create another Host, registry, planner, manifest authority, composition root, UI framework, or peer FrameCore product plugin.

## Previous Gate summary

E30 is complete:

- existing VS 2022/CMake/Ninja and existing pybind11 headers built `_vitalloom_sr2d_cpp.cp311-win_amd64.pyd` without installing dependencies;
- the repository `.venv\python.exe` imported callable `step_pvaec_circles`;
- C++ Adapter/direct ABI proof: `47 passed, 1 skipped`;
- expanded SR2D proof: `66 passed, 16 skipped`, with no shared C++ parity/direct ABI skip;
- identical benchmark, 100 entities / 120 iterations / bruteforce / repeats=3: Python mean `505.462 ms`, C++ mean `62.205 ms`, approximately `8.126x` faster;
- `auto` selects C++ when importable; explicit/automatic Python fallback remains intact;
- full non-signature regression: `1354 passed, 25 skipped, 34 subtests passed`; Editor smoke `plugins=13/20`; all four architecture guardrails passed;
- signature collection remains blocked by missing `cryptography`.

The local build used an explicit external pybind11 include directory from this machine's existing Torch installation. That is valid E30 build evidence, but not a supported clean-machine packaging/release story.

## Unique Gate

**Phase E31 -- SR2D C++ Reproducible Packaging, Release Artifact, and Clean-Fallback Proof.**

Before production changes, create an E31 plan under `docs/superpowers/plans/` and capture a real clean/rebuild baseline. Then:

1. Audit the current CMake/pyproject/build helper, release/package manifests, export closure, optional dependency policy, and clean-environment fallback behavior.
2. Select one supported pybind11/build-dependency sourcing policy. Do not hardcode `D:\app`, depend on Torch headers as the product contract, or copy third-party headers without license/provenance review.
3. Make the optional C++ extension reproducibly buildable into a wheel or equivalent release artifact with the exact target interpreter and platform metadata.
4. Prove the packaged artifact imports and exposes callable `step_pvaec_circles` in an isolated project-compatible environment.
5. Prove a clean environment without the native artifact still starts and selects `PythonSrPhysics2DAdapter`; explicit unavailable C++ selection must fail loudly rather than silently relabel Python.
6. Preserve `.pond`, AI command registry, Inspector binding, SR2D public seams, package/project manifests, Project World L4 lifecycle, Player/export, reload/startup/shutdown, and the L0-L4 topology.
7. Run focused packaging/native tests, relevant export/player/package regressions, full non-signature suite, Editor smoke, and all four architecture guardrails.
8. Attempt signature-only collection and record the `cryptography` blocker unless dependency installation is separately approved.
9. Update `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, the E31 plan, and create exactly one next fresh-session prompt.

## Completion bar

E31 is complete only when a machine-independent supported build/package route exists, the produced artifact installs/imports through the intended interpreter, optional-native and clean-Python fallback paths are both proven, release/package metadata is consistent, and regressions/guardrails pass. The existing locally installed `.pyd`, a machine-local header path, or source-only CMake success is insufficient.

The persistent objective `彻底完善` remains active. Do not claim the entire engine, replacement UI Host, OpenGL default readiness, signature verification, or all platform packaging is complete.
