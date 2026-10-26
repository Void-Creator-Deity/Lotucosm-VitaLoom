# Runtime Replay Command Surfaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose Phase 6A read-only SR/PS/PS_REPLAY replay evidence through the shared Command Registry, CLI, and MCP adapter without mutating scenes.

**Architecture:** Keep the runtime plugin-shaped under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. Move replay status collection into a runtime-owned service module, then let `tools/check_runtime_replay_status.py`, `runtime.replay.status`, CLI, and MCP all call the same read-only implementation. This phase does not merge SR and PS ticks and does not implement unified Pond.

**Tech Stack:** Python, pytest, VitaLoom Command Registry, existing CLI `main.py command`, MCP adapter, PS `summary.json`, `.pond` scene files.

---

## Summary

Phase 6A proved a headless read-only replay status surface. Phase 6B makes that evidence useful to agents and users by routing it through the same command layer used by UI/CLI/MCP work. The important constraint is semantic unification, not runtime merging: every surface must report the same status keys and the same `do_not_claim` facts, while remaining non-mutating.

## Current State

- Phase 6B implementation is complete for the command-surface gate as of 2026-07-04.
- `runtime_replay_status.py` now owns `build_runtime_replay_status(project_path, run_dir)` under the plugin runtime.
- `tools/check_runtime_replay_status.py` is a thin wrapper and keeps the same JSON CLI and exit criteria.
- `runtime.replay.status` is registered as a read-only Command Registry command.
- CLI and MCP helper paths call the same Command Registry surface.
- `docs/mainline_status.md` records Phase 6A and Phase 6B evidence; full unified Pond remains not claimed.

## Scope

- Add a runtime-owned read-only status module:
  - `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_replay_status.py`
  - Expose `build_runtime_replay_status(project_path: Path | None = None, run_dir: Path | None = None) -> dict[str, Any]`.
- Keep `tools/check_runtime_replay_status.py` as a thin wrapper around the runtime module.
- Add Command Registry command:
  - id: `runtime.replay.status`
  - mutates: `False`
  - requires_gui: `False`
  - capability: `vitalloom.pvaec.simulation`
  - input: optional `project_path`, optional `run_dir`
- Add MCP helper:
  - `mcp_adapter.get_runtime_replay_status(project_path: str = "", run_dir: str = "")`
- Add focused tests proving CLI, MCP, and tool surfaces return equivalent read-only evidence.
- Update docs/status/prompt after verification.

## Non-Goals

- Do not implement unified Pond.
- Do not merge SR_PLAY, PS_BATCH, and PS_REPLAY tick loops.
- Do not mutate `.pond`, project manifests, PS run summaries, or plugin manifests.
- Do not change AI command undo/redo semantics.
- Do not claim native acceleration or OpenGL default-readiness.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_replay_status.py`
- Modify: `tools/check_runtime_replay_status.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Create: `tests/test_runtime_replay_command_surfaces.py`
- Modify: `tests/test_ai_command_cli.py`
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `tests/test_runtime_replay_status_tool.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/INDEX.md`
- Add: `docs/prompts/2026-07-04-runtime-replay-command-surfaces-prompt.md`

## Step-by-Step Tasks

### Task 1: Phase-start recheck

- [x] Run the previous gate checks:

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py tests/test_ps_verify_triple.py tests/test_ps_experiment_service.py tests/test_ps_experiment_panel_smoke.py tests/test_ecology_observation.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py
python -B tools/check_runtime_replay_status.py
```

Expected: audit reports dirty worktree without cleaning it; Phase 6A focused tests pass; status tool reports `read_only: true` and `unified_pond_enabled: false`.

### Task 2: Move status collection into runtime module

- [x] Create `runtime_replay_status.py` with `DO_NOT_CLAIM`, `_ReplayStatusSrHost`, `_load_project_config`, and `build_runtime_replay_status(...)`.
- [x] Update `tools/check_runtime_replay_status.py` so it bootstraps paths, imports `build_runtime_replay_status`, prints JSON, and keeps the same exit criteria.
- [x] Extend `tests/test_runtime_replay_status_tool.py` to import the runtime module and assert the tool output matches the module for default arguments.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_replay_status_tool.py
python -B tools/check_runtime_replay_status.py
```

Expected: pass; status schema remains `schema_version: 1`.

### Task 3: Add Command Registry read-only command

- [x] Add a `CommandSpec` in `runtime_commands.py`:

```python
CommandSpec(
    id="runtime.replay.status",
    title="Read Runtime Replay Status",
    description="Read SR/PS/PS_REPLAY replay evidence without mutating scenes.",
    input_schema={
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "run_dir": {"type": "string"},
        },
    },
    handler=_runtime_replay_status,
    capability="vitalloom.pvaec.simulation",
)
```

- [x] Add `_runtime_replay_status(payload, context)` that resolves optional paths under the workspace policy already used by existing commands, calls `build_runtime_replay_status(...)`, and returns `command_ok(status)`.
- [x] Add `tests/test_runtime_replay_command_surfaces.py` asserting:
  - `get_command_registry().describe("runtime.replay.status")["mutates"] is False`,
  - `run("runtime.replay.status", {})` returns `ok: true`,
  - result includes `read_only: true`, `lanes.defined`, `ecology.lanes_defined`, and `do_not_claim`.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_replay_command_surfaces.py tests/test_command_registry.py
```

Expected: pass; no `.pond` or project file mutation.

### Task 4: Prove CLI surface

- [x] Update `tests/test_ai_command_cli.py` command list assertions to include `runtime.replay.status`.
- [x] Add a CLI test that runs:

```bash
python -B main.py command run runtime.replay.status --json "{}"
```

and asserts `ok: true`, `result.read_only: true`, and `result.unified_pond_enabled: false`.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_cli.py tests/test_runtime_replay_command_surfaces.py
```

Expected: pass; CLI uses Command Registry rather than a separate tool-only implementation.

### Task 5: Prove MCP surface

- [x] Add `get_runtime_replay_status(project_path: str = "", run_dir: str = "")` to `mcp_adapter.py`.
- [x] Update `tests/test_mcp_command_adapter.py` so `list_commands()` includes `runtime.replay.status`.
- [x] Add an MCP adapter test asserting `mcp_adapter.get_runtime_replay_status()` returns the same normalized status keys as `mcp_adapter.run_command("runtime.replay.status", {})`.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py tests/test_runtime_replay_command_surfaces.py
```

Expected: pass; MCP remains a thin wrapper over the registry.

### Task 6: Final verification and docs

- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_replay_status_tool.py tests/test_runtime_replay_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_simulation_coordinator.py tests/test_ps_replay_overlay_readonly.py tests/test_ecology_observation.py
python -B tools/check_runtime_replay_status.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools/check_runtime_replay_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_replay_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_runtime_replay_status_tool.py tests/test_runtime_replay_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
```

- [x] Update `docs/mainline_status.md` with exact results, skips, unavailable requirements, and one next gate.

Expected: focused checks pass. If Qt/offscreen or native requirements are unavailable, record the exact unavailable item rather than weakening the claim.

## Evidence Ledger Requirements

Record:

- command,
- result,
- skip count,
- mutation expectation,
- path of any new command surface,
- next gate.

## Next Phase Gate

Chosen after Phase 6B passed:

- Phase 6C: design a small `WorldBridge` / unified Pond experiment behind an explicit project flag and ADR gate.

Do not start Phase 6C implementation until Phase 6B command/CLI/MCP evidence is green and recorded.

## Phase-End Report

- Phase: Phase 6B - Runtime replay command/CLI/MCP surfaces
- Status: complete for the read-only command-surface gate
- Implemented: runtime-owned `build_runtime_replay_status(...)`, thin status tool wrapper, `runtime.replay.status`, CLI coverage, MCP helper, and parity tests.
- Verified: Phase-start audit passed with dirty total `963`; final audit passed with dirty total `964` after Phase 6B additions; Phase 6A recheck `26 passed in 0.86s`; TDD red failed on missing runtime module; focused Phase 6B suite `28 passed in 6.01s`; final focused replay/command suite `38 passed in 5.94s`; status tool, core boundary check, compileall, and scoped diff check passed with the existing `docs/INDEX.md` LF/CRLF warning.
- Skipped/Unavailable: no Phase 6B test skips; native SR2D acceleration and OpenGL default-readiness remain outside this phase and must not be claimed.
- Evidence: command surfaces use the same read-only status keys: `read_only`, `lanes.defined`, `ecology.lanes_defined`, `replay`, `unified_pond_enabled`, and `do_not_claim`.
- Architecture impact: plugin runtime boundary unchanged; tool wrapper delegates into runtime; UI/CLI/MCP semantics remain command-registry shaped.
- Remaining risks: no unified Pond, no SR/PS tick merge, no branching replay/conflict resolution, and no full unified runtime replay.
- Next phase: Phase 6C planning for an explicit-flag `WorldBridge` / unified Pond experiment; first file to inspect is `docs/runtime_unification_roadmap.md`.
