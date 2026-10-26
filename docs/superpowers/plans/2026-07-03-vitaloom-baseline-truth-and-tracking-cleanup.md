# VitaLoom Phase 0 Baseline Truth And Tracking Cleanup

Date: 2026-07-03

> For fresh C0dex sessions: this is the first executable phase for the VitaLoom long-term mainline. Keep the architecture plugin-shaped. Do not stage, commit, revert, delete, or restore unrelated worktree changes unless the user explicitly asks.

## Summary

Phase 0 turns the current large migration state into a verifiable baseline before any more runtime or performance work. The purpose is not to make the worktree clean. The purpose is to make it clear what is real, what is planned, what is blocked, what is fallback-only, and what must not be claimed yet.

The project stays on the current architecture:

```text
FrameCore
  -> plugins/lotucosm-vitaloom
     -> versions/1.0.0/runtime
  -> Project World / workspace projects
```

## Current State

- The worktree is intentionally dirty from a large plugin-runtime migration.
- The migrated runtime is under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Root legacy runtime folders and sample projects appear as deletions and must not be restored by guesswork.
- PyQt6 remains the editor shell, QPainter remains the default viewport backend, and OpenGL remains opt-in.
- Existing OpenGL evidence is command/batch/Qt-surface consumption evidence, not default-ready shader/instancing proof.
- SR2D C++ and Rust native source/scaffolding may exist, but local native extensions are not importable on the current machine.
- The current machine lacks the native toolchain pieces needed to build SR2D native backends.

## Scope

- Classify the dirty worktree by meaningful groups.
- Reconcile tracking docs, prompt docs, and index links.
- Record current boundary, compile, native-smoke, and check-only evidence.
- Make the next phase gate unambiguous.
- Preserve the user's plugin architecture and existing uncommitted work.

## Non-goals

- Do not migrate to Unity, Godot, Unreal, Electron, or another shell.
- Do not switch OpenGL to default.
- Do not claim native acceleration.
- Do not implement Vulkan, Direct3D, Metal, Box2D, Rapier, or a new RHI in this phase.
- Do not clean, delete, revert, restore, stage, or commit the dirty worktree.
- Do not treat docs-only status cleanup as a runtime performance fix.

## Files

- Update: `docs/mainline_status.md`
- Update: `docs/INDEX.md`
- Update: `docs/prompts/2026-07-02-vitaloom-long-term-mainline-prompt.md`
- Update or reference: `docs/cleanup_stabilization_audit.md`
- Use evidence tools:
  - `tools/audit_worktree_groups.py`
  - `tools/check_gui_boundaries.py`
  - `tools/check_core_boundaries.py`
  - `tools/check_release_consistency.py`
  - `tools/check_sr2d_native.py`
  - `tools/build_sr2d_native.py`

## Step-by-step Tasks

- [x] Read repository authority docs instead of old C0dex thread memory.
- [x] Confirm project-specific rules: plugin-shaped runtime, PyQt6 shell, QPainter default, OpenGL opt-in, native fallback required.
- [x] Run dirty worktree grouping and record group counts.
- [x] Run architecture boundary checks and compile checks.
- [x] Run native check-only and import-smoke checks; record missing tools and missing modules.
- [x] Add a mainline status board so fresh sessions have one truth ledger.
- [x] Improve the long-term prompt so every phase must summarize, test, record evidence, and plan the next phase.
- [x] Run focused documentation validation after the latest edits.
- [x] Decide the next executable phase gate from evidence, not from old momentum.

## Tests First

This phase is documentation and verification infrastructure, so the "tests first" requirement means running guardrails before claiming the baseline:

```bash
python -B tools/audit_worktree_groups.py
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B tools/build_sr2d_native.py --backend all --check-only
python -B tools/check_sr2d_native.py
```

## Verification Commands

Required before closing Phase 0:

```bash
python -B tools/audit_worktree_groups.py
python -B tools/check_gui_boundaries.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m compileall -q FrameCore tools main.py player.py
python -B tools/build_sr2d_native.py --backend all --check-only
python -B tools/check_sr2d_native.py
git diff --check -- AGENTS.md docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans
```

Documentation scan:

```bash
rg -n "[T]ODO|[T]BD|[F]IXME|im[p]lement later|fill in det[a]ils" AGENTS.md docs/mainline_status.md docs/prompts docs/superpowers/plans docs/INDEX.md
```

Optional focused smoke before moving to Phase 1:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_viewport_snapshot.py tests/test_viewport_draw_commands.py tests/test_opengl_batching.py tests/test_qpainter_viewport_backend.py tests/test_qpainter_draw_command_renderer.py tests/test_opengl_viewport_backend.py tests/test_opengl_render_target.py tests/test_viewport_render_parity.py tests/test_viewport_backend_selection.py tests/test_benchmark_engine_viewport_variants.py
python -B -m pytest -q -p no:cacheprovider tests/test_sr_physics2d_world.py tests/test_sr_physics2d_adapter_contract.py tests/test_sr_physics2d_native_parity.py tests/test_sr_physics2d_cpp_parity.py tests/test_sr2d_native_smoke_tool.py tests/test_benchmark_engine_sr2d_variants.py
```

## Evidence Ledger

Record command output in `docs/mainline_status.md`. Distinguish:

- passed boundary checks;
- passed compile checks;
- worktree group counts;
- native modules missing;
- native toolchains missing;
- skipped tests and why;
- benchmarks actually run, including scenario sizes.

## Fallback And Unblock Path

- If native tools are missing, keep Python fallback as the passing path and record missing tools from `tools/check_sr2d_native.py` plus `tools/build_sr2d_native.py --check-only`.
- If Qt OpenGL cannot create a context in the local environment, keep QPainter default and record OpenGL pixel/screenshot tests as skipped, not passed.
- If the dirty worktree prevents broad verification, use focused paths and record the exact files or groups that block broader claims.
- If docs show mojibake in terminal output, do not rewrite architecture by assumption. Treat encoding cleanup as a narrow tracked task only if it blocks verification or reader use.

## Phase-End Report Template

- Phase: Phase 0 - Baseline truth and tracking cleanup
- Status: complete | partially complete | blocked
- Implemented:
- Verified:
- Skipped/Unavailable:
- Evidence:
- Architecture impact:
- Remaining risks:
- Next phase:

## Next Phase Gate

Recommended next executable phase after Phase 0 is Phase 1 - Real OpenGL viewport canvas.

First file to inspect:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/opengl_backend.py
```

First tests to inspect:

```text
tests/test_opengl_viewport_backend.py
tests/test_opengl_render_target.py
tests/test_viewport_render_parity.py
```

Gate for Phase 1:

- Add a real opt-in Qt OpenGL widget/window canvas with current-context lifecycle evidence.
- Keep QPainter default.
- Feed the existing snapshot -> draw commands -> OpenGL batching path.
- Add pixel/screenshot parity, interaction smoke, fallback behavior, and benchmark evidence before any default switch discussion.
