# C0dex Goal Prompt: Implement SR2D Native Adapter Boundary

Do not read, resume, fork, or load old C0dex threads. Continue only from this prompt and the plan file below.

## Goal

Implement the first SR 2D native acceleration boundary for Lotuscosm VitaLoom by following:

`docs/superpowers/plans/2026-06-28-sr2d-native-adapter.md`

## Required Skills

- Use `superpowers:subagent-driven-development` or `superpowers:executing-plans`.
- Use `superpowers:test-driven-development` for each code task.
- Use `superpowers:verification-before-completion` before claiming success.

## Current Context

- `SrPhysics2DWorld.step()` is the stable runtime entry point.
- Existing implementation lives under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_physics2d/`.
- Existing behavior tests live in `tests/test_sr_physics2d_world.py`.
- `docs/adr/0006-native-acceleration-seams.md` requires a Python interface, benchmark case, behavior tests, and fallback adapter before native acceleration is considered real.
- The first implementation should create a Python fallback adapter and route `SrPhysics2DWorld` through it. Do not add Rust/C++ code until parity and benchmark evidence exist.

## Guardrails

- Do not stage or revert unrelated existing working tree changes.
- Use explicit `git add` paths from the plan.
- Keep `.pond`, `GameViewport`, AI commands, and user-facing APIs pointed at `SrPhysics2DWorld.step()`.
- Treat `PythonSrPhysics2DAdapter` as the behavior oracle for future native adapters.

## First Command

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py
```

Then begin Task 1 in the plan.

