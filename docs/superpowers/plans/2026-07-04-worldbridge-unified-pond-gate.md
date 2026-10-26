# WorldBridge Unified Pond Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing WorldBridge/unified Pond pilot into a clearly gated, inspectable, read-only status and comparability proof path without making unified Pond the default runtime.

**Architecture:** Keep SR_PLAY, PS_BATCH, and PS_REPLAY explicit. Treat WorldBridge as an opt-in experiment behind `project.json.runtime_mode == "unified_pond"` and expose its readiness through tools, Command Registry, CLI, and MCP before expanding behavior. Do not move code out of the plugin runtime boundary.

**Tech Stack:** Python, pytest, VitaLoom Command Registry, MCP adapter, existing `world_bridge.py`, existing `run_dual_comparability.py`, Project World `project.json`.

---

## Summary

Phase 6B proved that runtime replay evidence is shared by the tool, Command Registry, CLI, and MCP surfaces. Phase 6C is next because repository truth shows a WorldBridge pilot already exists, while several docs still caution that unified Pond is not complete. This phase must convert that mixed state into explicit evidence: what exists, what is gated, what remains lossy, and what must not be claimed.

The first implementation target is not a larger bridge. The target is a read-only WorldBridge status gate plus command surfaces and comparability smoke proof. Only after those are green should later work consider expanding mappings.

## Current State

- `docs/mainline_status.md` records Phase 6B as passed for read-only command/CLI/MCP replay status.
- `docs/runtime_unification_roadmap.md` still treats C.4 unified Pond as the final high-risk milestone.
- `docs/adr/0005-unified-pond-bridge.md` says a pilot has landed, but also says mapping is minimal and not proven lossless.
- `core/Lotucosm/runtime/world_bridge.py` exists and provides `resolve_runtime_mode`, `unified_pond_enabled`, `ensure_bridged_organisms`, `bridge_spawned_organism`, and `unified_pond_step`.
- `GameViewport` has opt-in `_unified_pond_mode` helpers and calls `_run_unified_pond_bridge_tick(dt)` only when the mode flag is true.
- Tests already cover bridge primitives and viewport opt-in smoke:
  - `tests/test_plasticity_and_world_bridge.py`
  - `tests/test_game_viewport_unified_bridge.py`
  - `tests/test_comparability.py`
- Starting evidence from 2026-07-04:
  - `python -B tools/audit_worktree_groups.py` passed with dirty total `964`.
  - `python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py` -> `36 passed in 0.98s`.
  - `python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20` exited 0 and reported `all_passed=True`.
  - `python -B tools/check_runtime_replay_status.py` still reports `unified_pond_enabled: false` without a project path.

## Scope

- Add a runtime-owned read-only WorldBridge status module.
- Add a thin tool wrapper that reports WorldBridge readiness and do-not-claim items.
- Add Command Registry command `runtime.worldbridge.status`.
- Add MCP helper `get_runtime_worldbridge_status(...)`.
- Add tests proving default dual mode, explicit `unified_pond` opt-in, known lossy mapping limits, and tool/command/CLI/MCP parity.
- Add or extend docs so Phase 6C status distinguishes:
  - bridge pilot source code,
  - opt-in project flag,
  - viewport smoke,
  - comparability smoke,
  - full unified Pond not yet complete.

## Non-Goals

- Do not make `unified_pond` the default.
- Do not merge SR_PLAY and PS_BATCH tick semantics.
- Do not replace PS Runner with GameViewport.
- Do not claim lossless membrane/script/component mapping.
- Do not change `.pond` scene semantics or project lock semantics.
- Do not introduce Unity, Godot, Unreal, Electron, a new GUI shell, or a new renderer branch.
- Do not claim native acceleration or OpenGL default-readiness.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py`
- Create: `tools/check_runtime_worldbridge_status.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Create: `tests/test_runtime_worldbridge_status_tool.py`
- Create: `tests/test_runtime_worldbridge_command_surfaces.py`
- Modify: `tests/test_ai_command_cli.py`
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/INDEX.md`
- Modify: `docs/runtime_unification_roadmap.md`
- Modify: `docs/adr/0005-unified-pond-bridge.md`
- Add: `docs/prompts/2026-07-04-worldbridge-unified-pond-gate-prompt.md`

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run current truth checks:

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_runtime_replay_status.py
```

Expected:
- Worktree remains dirty and is not cleaned.
- WorldBridge focused tests pass.
- Comparability smoke reports `all_passed=True`.
- Default runtime replay status still reports `unified_pond_enabled: false`.

### Task 2: Add Runtime WorldBridge Status Module

- [x] Write the failing test in `tests/test_runtime_worldbridge_status_tool.py`:

```python
from pathlib import Path

from core.VitaLoom.simulation.runtime_worldbridge_status import build_runtime_worldbridge_status


def test_worldbridge_status_defaults_to_dual_and_not_ready_for_default() -> None:
    status = build_runtime_worldbridge_status()

    assert status["schema_version"] == 1
    assert status["read_only"] is True
    assert status["runtime_mode"] == "dual"
    assert status["unified_pond_enabled"] is False
    assert status["default_ready"] is False
    assert "lossless_mapping" in status["known_gaps"]
    assert "full_unified_runtime_replay" in status["do_not_claim"]
```

- [x] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py
```

Expected: collection fails because `core.VitaLoom.simulation.runtime_worldbridge_status` does not exist.

- [x] Create `runtime_worldbridge_status.py` with:

```python
def build_runtime_worldbridge_status(project_path: Path | None = None) -> dict[str, Any]:
    ...
```

Return keys:
- `schema_version`
- `status`
- `read_only`
- `project_path`
- `runtime_mode`
- `unified_pond_enabled`
- `default_ready`
- `pilot_modules`
- `evidence`
- `known_gaps`
- `do_not_claim`

- [x] Keep implementation read-only: only read optional `project.json`, inspect importability, and report existing tests/tools as evidence labels.
- [x] Run the test again and make it pass.

### Task 3: Add Tool Wrapper

- [x] Extend `tests/test_runtime_worldbridge_status_tool.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_worldbridge_status_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_runtime_worldbridge_status.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout) == build_runtime_worldbridge_status()
```

- [x] Run and observe red because the tool is missing.
- [x] Create `tools/check_runtime_worldbridge_status.py` as a thin wrapper using `tools/_runtime_bootstrap.py`.
- [x] Exit 0 only when:
  - `read_only` is true,
  - `default_ready` is false,
  - `do_not_claim` includes `full_unified_runtime_replay`,
  - `runtime_mode` is `dual` when no project path is supplied.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py
python -B tools/check_runtime_worldbridge_status.py
```

Expected: pass; no files under Project World are created or modified.

### Task 4: Add Command Registry Surface

- [x] Create `tests/test_runtime_worldbridge_command_surfaces.py`:

```python
from core.VitaLoom.commands.registry import get_command_registry


def test_worldbridge_status_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.status")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_status_command_reports_gate_evidence() -> None:
    result = get_command_registry().run("runtime.worldbridge.status", {})

    assert result["ok"] is True
    status = result["result"]
    assert status["read_only"] is True
    assert status["default_ready"] is False
    assert status["unified_pond_enabled"] is False
    assert "world_bridge_module" in status["pilot_modules"]
```

- [x] Run the test and observe red because the command is not registered.
- [x] Add `CommandSpec(id="runtime.worldbridge.status", ...)` near `runtime.replay.status`.
- [x] Add `_runtime_worldbridge_status(payload, context)` that resolves optional `project_path` through `_resolve_workspace_path(...)` and calls the runtime module.
- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py
```

Expected: pass; command is read-only and has no audit entry.

### Task 5: Prove Explicit Project Flag Behavior

- [x] Add a test to `tests/test_runtime_worldbridge_command_surfaces.py` that creates a temporary project under `workspace/` with `project.json`:

```python
{
    "name": "worldbridge_flag_fixture",
    "runtime_mode": "unified_pond"
}
```

Expected assertions:
- `runtime_mode == "unified_pond"`
- `unified_pond_enabled is True`
- `default_ready is False`
- `known_gaps` is not empty

- [x] Run the test red/green through the runtime module and command handler.
- [x] Ensure no `.pond` file is written by this status command.

### Task 6: Prove CLI Surface

- [x] Update `tests/test_ai_command_cli.py` command list assertions to include `runtime.worldbridge.status`.
- [x] Add a CLI test:

```python
def test_run_runtime_worldbridge_status_reports_gate(self) -> None:
    proc = self._run("run", "runtime.worldbridge.status", "--json", "{}")
    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
    data = json.loads(proc.stdout)
    self.assertTrue(data["ok"])
    self.assertTrue(data["result"]["read_only"])
    self.assertFalse(data["result"]["default_ready"])
```

- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_cli.py tests/test_runtime_worldbridge_command_surfaces.py
```

Expected: pass; CLI uses the Command Registry.

### Task 7: Prove MCP Surface

- [x] Add `get_runtime_worldbridge_status(project_path: str = "")` to `mcp_adapter.py`.
- [x] Update `tests/test_mcp_command_adapter.py` list assertions.
- [x] Add an MCP test comparing:

```python
mcp_adapter.get_runtime_worldbridge_status()
mcp_adapter.run_command("runtime.worldbridge.status", {})
```

- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py tests/test_runtime_worldbridge_command_surfaces.py
```

Expected: pass; MCP remains a thin wrapper.

### Task 8: Preserve Existing Bridge And Comparability Evidence

- [x] Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
```

Expected:
- Focused bridge/comparability tests pass.
- Comparability smoke exits 0 and reports `all_passed=True`.
- Evidence remains a small smoke; do not extrapolate it to full default-readiness.

### Task 9: Update Docs And Prompts

- [x] Update `docs/mainline_status.md` with Phase 6C evidence, skipped/unavailable items, risks, and the next gate.
- [x] Update `docs/INDEX.md` with the Phase 6C plan and prompt links.
- [x] Update `docs/runtime_unification_roadmap.md` so C.4 says current state is "pilot present, gated and evidenced", not simply future or complete.
- [x] Update `docs/adr/0005-unified-pond-bridge.md` with the new status command/tool evidence and unchanged limitations.
- [x] Add `docs/prompts/2026-07-04-worldbridge-unified-pond-gate-prompt.md`.

## Tests First

Behavior changes in this phase must follow TDD:

1. Write a failing test for the status module, tool, command, CLI, or MCP helper.
2. Run the test and confirm the failure is due to missing behavior.
3. Implement only the minimum code for that test.
4. Rerun the exact focused test.
5. Only after green, proceed to the next surface.

Do not modify `world_bridge.py` behavior until status surfaces prove what the current pilot actually does.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/check_runtime_replay_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/runtime_unification_roadmap.md docs/adr/0005-unified-pond-bridge.md docs/prompts docs/superpowers/plans tools/check_runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
```

## Evidence Ledger

Record these facts in `docs/mainline_status.md`:

- Worktree audit total.
- WorldBridge status tool output summary.
- Command Registry command id and read-only flags.
- CLI and MCP parity result.
- Bridge focused pytest result.
- Comparability smoke command, tick count, checkpoints, and `all_passed` value.
- Skips and unavailable items.
- Do-not-claim list.

## Fallback / Unblock Path

- If comparability smoke fails, keep `runtime.worldbridge.status` but report `comparability_smoke_passed: false`; do not block read-only status.
- If a project path is outside `workspace/`, return `path_outside_workspace` from the command handler.
- If PyQt offscreen is unavailable for `test_game_viewport_unified_bridge.py`, record the skip/unavailable state and keep non-GUI status/tool tests passing.
- If `world_bridge.py` import fails, the status tool should return `world_bridge_importable: false`, exit non-zero, and preserve dual default.
- If docs show mojibake in the terminal, do not rewrite encoding in this phase; record it as display risk unless file bytes are proven invalid.

## Phase-End Report Template

- Phase: Phase 6C - WorldBridge unified Pond gate
- Status: complete | partially complete | blocked
- Implemented: files/features changed
- Verified: commands run and exact results
- Skipped/Unavailable: tests, GUI/offscreen, toolchains, or smoke checks with reasons
- Evidence: status output, command ids, comparability ticks/checkpoints, file paths
- Architecture impact: plugin boundary unchanged or explicitly documented
- Remaining risks: known mapping losses, default readiness, replay limits
- Next phase: one concrete next phase and first file/command to inspect

## Next Phase Gate

Chosen after Phase 6C passed:

- Phase 6D: WorldBridge mapping-loss audit and smallest safe mapping extension plan.

Do not start Phase 6D implementation until Phase 6C has a green status tool, Command Registry, CLI, MCP helper, focused bridge tests, and comparability smoke recorded in `docs/mainline_status.md`.

## Phase-End Report

- Phase: Phase 6C - WorldBridge unified Pond gate
- Status: complete for the read-only gate/evidence surface
- Implemented: runtime-owned `build_runtime_worldbridge_status(...)`, `tools/check_runtime_worldbridge_status.py`, read-only `runtime.worldbridge.status`, CLI coverage, MCP helper, explicit project flag test, and docs/status updates.
- Verified: phase-start audit `964`; focused command/tool suite `31 passed in 7.22s`; bridge/comparability/replay focused suite `36 passed in 0.88s`; WorldBridge status tool passed; replay status tool passed; dual comparability smoke exited 0 with `all_passed=True` at ticks `10` and `20`; core boundary check passed; compileall passed.
- Skipped/Unavailable: no Phase 6C focused skips; no native or OpenGL work attempted.
- Evidence: status output reports `runtime_mode: dual`, `unified_pond_enabled: false`, `default_ready: false`, `world_bridge_importable: true`, `world_bridge_step_available: true`, and known gaps including `lossless_mapping`.
- Architecture impact: plugin runtime boundary unchanged; status surfaces are read-only; default runtime remains dual.
- Remaining risks: lossless membrane/script/component mapping is not proven; full unified runtime replay and SR/PS tick merge are not complete.
- Next phase: Phase 6D mapping-loss audit and smallest safe mapping extension plan; first file to inspect is `core/Lotucosm/runtime/world_bridge.py`.
