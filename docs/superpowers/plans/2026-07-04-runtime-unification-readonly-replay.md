# Runtime Unification Read-Only Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn existing SR/PS/replay skeletons into a read-only evidence gate before any unified Pond or tick-merge work.

**Architecture:** Keep SR_PLAY, PS_BATCH, and PS_REPLAY as explicit lanes behind `SimulationCoordinator`. Phase 6 adds proof surfaces around ecology snapshots, replay overlays, and lane status without moving FrameCore boundaries or merging SR and PS runtime semantics.

**Tech Stack:** Python, pytest, existing VitaLoom simulation services, `.pond` scenes, PS `summary.json`, `docs/mainline_status.md`.

---

## Summary

Phase 6 starts after Phase 5 proved representative command/audit/undo paths but still reported `unified_undo_redo_runtime=false`. The next mainline risk is a different kind of false unification: SR play mode, PS batch experiments, and PS replay overlays already share some names and UI surfaces, but they are not one runtime and should not be described as one.

This phase therefore begins with read-only proof. It must let a fresh C0dex session and a user inspect how SR_PLAY, PS_BATCH, and PS_REPLAY relate, compare available evidence, and verify that replay overlay behavior does not mutate scenes or call PS tick logic inside `GameViewport`.

## Current State

- Architecture remains plugin-shaped under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- `SimulationCoordinator` already defines `SimulationLane.SR_PLAY`, `SimulationLane.PS_BATCH`, and `SimulationLane.PS_REPLAY`, and can enforce `disallow_parallel_sr_ps`.
- `core/Lotucosm/runtime/ecology_observation.py` already defines `EcologyLane.SR_PLAY`, `PS_BATCH`, and `PS_REPLAY`.
- `collect_ecology_snapshots(editor_context)` already aggregates SR and PS snapshots and appends a PS_REPLAY snapshot when the SR host reports overlay points.
- `ps_replay_overlay.py` already reads PS run `summary.json` and pushes normalized overlay points to the SR host.
- `PsReplayOverlayPlugin` already subscribes to `ps_experiment_finished` and pushes overlay points without merging tick loops.
- Existing tests cover the coordinator, ecology snapshot conversion, PS experiment service/panel smoke, and PS verify triple behavior.
- Phase 6A completion evidence now exists: `tools/check_runtime_replay_status.py` reports read-only lane/replay/ecology facts, and focused tests prove replay overlay ingestion does not mutate `.pond`.

## Scope

- Add a narrow Phase 6 evidence/status tool or command that reads current runtime facts and reports:
  - active lanes from `SimulationCoordinator`,
  - PS replay summary availability,
  - overlay point count,
  - ecology snapshot lane summaries,
  - whether evidence was read-only.
- Add focused tests proving PS_REPLAY remains read-only:
  - no `.pond` scene file writes,
  - no `Pond.update` call from replay overlay ingestion,
  - overlay points show up as `EcologyLane.PS_REPLAY` through ecology registry.
- Add comparison output for representative SR/PS metrics only where already available through `EcologySnapshot`.
- Update docs and prompts with real evidence and remaining non-goals.

## Non-Goals

- Do not merge SR_PLAY and PS_BATCH tick loops.
- Do not implement unified Pond mode in this phase.
- Do not bind PS `Organism` objects one-to-one to SR entities.
- Do not change `.pond` semantics or project manifests.
- Do not introduce Unity/Godot/Unreal/Electron or a new GUI shell.
- Do not claim unified undo/runtime replay; Phase 5 explicitly left that false.
- Do not optimize SR2D/native or OpenGL here unless a Phase 6 test exposes a direct regression.

## Files

- Create: `tools/check_runtime_replay_status.py`
  - Emits JSON read-only evidence for coordinator lanes, replay summary, overlay points, and ecology lanes.
- Create or modify: `tests/test_runtime_replay_status_tool.py`
  - Verifies the status tool output and read-only claims.
- Modify: `tests/test_simulation_coordinator.py`
  - Adds PS_REPLAY lane behavior if missing.
- Create or modify: `tests/test_ps_replay_overlay_readonly.py`
  - Proves overlay ingestion reads `summary.json`, updates overlay points, and does not mutate `.pond`.
- Modify: `docs/mainline_status.md`
  - Records Phase 6 start, evidence, skips, and next gate.
- Modify: `docs/INDEX.md`
  - Links this plan and the fresh-session prompt.
- Add: `docs/prompts/2026-07-04-runtime-unification-readonly-replay-prompt.md`
  - Fresh-session prompt for continuing Phase 6.

## Step-by-Step Tasks

### Task 1: Phase-start evidence gate

- [x] Run `python -B tools/audit_worktree_groups.py` and record the dirty total without cleaning, staging, reverting, or deleting unrelated files.
- [x] Run the Phase 5 focused command/audit suite to make sure the previous gate still holds:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_undo_redo_command_path.py tests/test_ui_command_actions.py tests/test_ai_command_durable_project_undo.py
python -B tools/check_ai_command_audit_status.py
```

Expected: focused suite passes; status still reports representative command/audit/undo proof and `unified_undo_redo_runtime=false`.

### Task 2: Prove PS_REPLAY lane remains explicit

- [x] Extend `tests/test_simulation_coordinator.py` with a test showing `SimulationLane.PS_REPLAY` can be registered independently and is not blocked by `disallow_parallel_sr_ps`.
- [x] Run the focused test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py
```

Expected: pass, proving the coordinator keeps PS_REPLAY visible and separate from SR/PS tick exclusivity.

### Task 3: Add read-only replay overlay test

- [x] Add `tests/test_ps_replay_overlay_readonly.py` with a temporary project scene and a temporary PS run `summary.json`.
- [x] The test should call `overlay_points_from_run_dir(...)` and `push_overlay_to_game_viewport(...)` through a fake SR host or patched `get_sr_host`.
- [x] Assert:
  - overlay point count is derived from `summary.json`,
  - scene file contents and modification time are unchanged,
  - no `Pond.update` or PS runner method is invoked,
  - `collect_ecology_snapshots(...)` emits a `PS_REPLAY` lane when overlay points exist.
- [x] Run the focused test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ps_replay_overlay_readonly.py tests/test_ecology_observation.py tests/test_simulation_coordinator.py
```

Expected: pass with no runtime mutation.

### Task 4: Add runtime replay status tool

- [x] Create `tools/check_runtime_replay_status.py`.
- [x] The tool should bootstrap the runtime like existing tools, avoid GUI construction, and output JSON containing:
  - `status`,
  - `read_only`,
  - `lanes.active`,
  - `lanes.disallow_parallel_sr_ps`,
  - `replay.summary_available`,
  - `replay.overlay_point_count`,
  - `ecology.lanes`,
  - `unified_pond_enabled`,
  - `do_not_claim`.
- [x] Add `tests/test_runtime_replay_status_tool.py` that executes the tool and asserts `read_only=true` and `do_not_claim` includes unified Pond/tick merge.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_replay_status_tool.py
python -B tools/check_runtime_replay_status.py
```

Expected: pass; the tool reports facts rather than pretending Phase 6 is complete.

### Task 5: Focused Phase 6 verification

- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py tests/test_ps_verify_triple.py tests/test_ps_experiment_service.py tests/test_ps_experiment_panel_smoke.py tests/test_ecology_observation.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py
python -B tools/check_runtime_replay_status.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools/check_runtime_replay_status.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py tests/test_simulation_coordinator.py
```

Expected: tests and guardrails pass. Any skipped GUI/Qt test must be recorded with the reason.

## Evidence Ledger

Record each command in `docs/mainline_status.md` with:

- command,
- result,
- pass/fail/skip count,
- whether any GUI/native/toolchain requirement was unavailable,
- whether any file mutation was expected,
- next gate.

Do not copy old results from prior sessions as fresh evidence.

## Fallback/Unblock Path

If the local environment cannot run Qt offscreen tests, keep Phase 6 headless by testing `ps_replay_overlay.py`, ecology snapshots, and the status tool. Record GUI smoke as unavailable rather than failed if the import/context is missing.

If the PS experiment service or panel smoke fails for reasons unrelated to Phase 6, isolate the regression with the smallest focused test before changing runtime code.

If `rg` is unavailable or blocked, use PowerShell `Select-String` or Python-free shell inspection; do not skip repository search because one tool is blocked.

## Phase-End Report Template

- Phase: Phase 6 - runtime unification and read-only replay
- Status: complete | partially complete | blocked
- Implemented: read-only replay/status evidence files and tests
- Verified: exact commands and results
- Skipped/Unavailable: GUI/offscreen/PS service/native checks with reasons
- Evidence: JSON status keys, test output, docs paths
- Architecture impact: SR_PLAY, PS_BATCH, and PS_REPLAY lanes remain explicit; plugin-shaped architecture unchanged
- Remaining risks: unified Pond, branching undo history, conflict resolution, full replay semantics, live UI ergonomics
- Next phase: one concrete next gate, with first command or file to inspect

## Phase-End Evidence

- Phase: Phase 6A - runtime unification and read-only replay
- Status: complete for the read-only evidence gate as of 2026-07-04.
- Implemented: `tools/check_runtime_replay_status.py`, `tests/test_runtime_replay_status_tool.py`, `tests/test_ps_replay_overlay_readonly.py`, and focused coordinator coverage.
- Verified: Phase 5 handoff suite `59 passed in 7.61s`; Phase 6A focused suite `26 passed in 0.81s`; `tools/check_runtime_replay_status.py`, `tools/check_core_boundaries.py`, and `compileall` passed.
- Skipped/Unavailable: no Phase 6A focused skips; native C++/Rust acceleration remains unavailable and outside this phase.
- Architecture impact: SR_PLAY, PS_BATCH, and PS_REPLAY lanes remain explicit; plugin-shaped architecture unchanged.
- Remaining risks: unified Pond, branching undo history, conflict resolution, full replay semantics, live UI ergonomics.

## Next Phase Gate

This read-only evidence gate has passed. The next selected gate is:

- Phase 6B: expose replay evidence through command/CLI/MCP surfaces without mutating scenes.

Do not start unified Pond implementation until Phase 6 read-only replay status is green and recorded.
