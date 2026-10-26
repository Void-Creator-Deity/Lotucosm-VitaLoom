# WorldBridge Component Membrane Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only WorldBridge component/membrane mapping decision record so future mapping work has explicit safe candidates, forbidden semantics, tests, and command evidence.

**Architecture:** Keep WorldBridge opt-in and keep SR_PLAY, PS_BATCH, and PS_REPLAY separate. This phase does not map component graphs into `.pond`; it exposes a decision matrix and read-only command/tool surfaces that say which component facts may be projected and which behavior must stay unmapped.

**Tech Stack:** Python 3.11+, pytest, VitaLoom Command Registry, MCP adapter, existing plugin runtime modules under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.

---

## Summary

Phase 6D passed the mapping-loss audit and the `size/radius` bridge gate. The next risk is membrane/component graph mapping: PS components carry runtime behavior, registered Inspector properties, signal state, connections, genetics, and per-tick update logic, while SR membrane topology and scripts use different semantics. Mapping these directly would make unified Pond look more complete than it is.

Phase 6E must therefore add a decision record before any behavior expansion:

- identify safe read-only projection candidates;
- identify forbidden live-behavior mappings;
- expose this decision through a tool, status, Command Registry, CLI, and MCP;
- keep actual membrane/component graph mapping out of runtime behavior until a later gated phase.

## Current State

- `docs/mainline_status.md` records Phase 6D as passed for mapping audit, command surfaces, and `size/radius` roundtrip.
- Latest phase-start audit: `python -B tools/audit_worktree_groups.py` passed with dirty total `970`.
- Latest phase-start focused test: `python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_plasticity_and_world_bridge.py tests/test_comparability.py` -> `40 passed in 1.00s`.
- PS component facts:
  - `Component` has `component_type`, `connections`, `activation`, `state`, `input_signals`, `output_signal`, `genetic_strength`, `mutation_rate`, `location`, `acquired`, `congenital`, `attach_point`, and inspectable properties.
  - `Membrane` registers `radius`, `ingest_threshold`, and `efficiency`; it also has PS-only `auto_ingest(...)`.
  - Sensors and actuators expose runtime behavior through `sense(...)`, `process_signal(...)`, `get_force_vector(...)`, and update-time state.
- SR facts:
  - SR membrane topology is separate from PS `Membrane` and is referenced through `sr_membrane_topology.py`, GameViewport `_sr_membrane_attach`, and scene runtime environment fields.
  - `.pond` scene entities already have `components` and `scripts` data fields, but these are editor/project data, not proof of live PS component equivalence.

## Previous Phase Summary

Phase 6D implemented:

- `core.Lotucosm.runtime.world_bridge_mapping_audit.build_worldbridge_mapping_audit()`
- `tools/check_worldbridge_mapping_audit.py`
- `mapping_audit` nested inside runtime WorldBridge status
- read-only `runtime.worldbridge.mapping_audit`
- CLI and MCP coverage
- `size/radius` roundtrip in `world_bridge.py`

Phase 6D verified:

- final worktree audit `970`
- mapping audit/tool suite `2 passed`
- status/command/CLI/MCP suite `36 passed`
- bridge/comparability/replay suite `37 passed`
- dual comparability smoke `all_passed=True`
- core boundary and compileall checks passed

Phase 6D did not implement:

- membrane/component/script graph mapping
- lossless mapping
- unified Pond default-readiness
- SR/PS tick merge
- full unified runtime replay

## Scope

- Add a runtime-owned component/membrane mapping decision module.
- Add a thin check tool for that decision.
- Extend `build_worldbridge_mapping_audit()` with a nested component/membrane decision summary.
- Add a read-only Command Registry command.
- Add CLI and MCP parity tests.
- Update ADR, roadmap, status board, index, and fresh-session prompt.

## Non-Goals

- Do not map PS components into SR `.pond` entities.
- Do not create or mutate `.pond` component graph data.
- Do not call component `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, or `add_connection`.
- Do not make unified Pond default-ready.
- Do not claim membrane/component/script lossless mapping.
- Do not touch native or OpenGL work in this phase.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_component_decision.py`
- Create: `tools/check_worldbridge_component_decision.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Create: `tests/test_worldbridge_component_decision.py`
- Create: `tests/test_worldbridge_component_decision_tool.py`
- Modify: `tests/test_worldbridge_mapping_audit.py`
- Modify: `tests/test_runtime_worldbridge_command_surfaces.py`
- Modify: `tests/test_ai_command_cli.py`
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/runtime_unification_roadmap.md`
- Modify: `docs/adr/0005-unified-pond-bridge.md`
- Add: `docs/prompts/2026-07-05-worldbridge-component-membrane-decision-prompt.md`
- Modify: `docs/INDEX.md`

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run:

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_plasticity_and_world_bridge.py tests/test_comparability.py
```

Expected:

- Worktree remains dirty and is not cleaned.
- Phase 6D audit and bridge tests pass.
- No file is staged, committed, reverted, deleted, or cleaned.

Current planning evidence:

- Worktree audit passed with dirty total `970`.
- Focused tests passed with `40 passed in 1.00s`.

### Task 2: Add Component Decision Module

- [x] Write the failing test in `tests/test_worldbridge_component_decision.py`:

```python
from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)


def test_component_decision_names_safe_projection_and_forbidden_behavior() -> None:
    decision = build_worldbridge_component_decision()

    assert decision["schema_version"] == 1
    assert decision["read_only"] is True
    assert decision["maps_live_components"] is False
    assert decision["default_ready"] is False
    assert decision["decision"] == "read_only_projection_only"
    assert "component_type" in decision["safe_projection_fields"]
    assert "inspectable_properties" in decision["safe_projection_fields"]
    assert "auto_ingest" in decision["forbidden_behavior"]
    assert "process_signal" in decision["forbidden_behavior"]
    assert decision["component_kinds"]["Membrane"]["mapping_state"] == "decision_only"
```

- [x] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py
```

Expected red result:

- Collection fails because `core.Lotucosm.runtime.world_bridge_component_decision` does not exist.

- [x] Create `world_bridge_component_decision.py` with:

```python
from __future__ import annotations

from typing import Any


def build_worldbridge_component_decision() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "worldbridge_component_membrane_decision",
        "read_only": True,
        "decision": "read_only_projection_only",
        "maps_live_components": False,
        "default_ready": False,
        "safe_projection_fields": [
            "component_id",
            "component_type",
            "location",
            "acquired",
            "congenital",
            "attach_point",
            "inspectable_properties",
            "connection_count",
        ],
        "forbidden_behavior": [
            "update",
            "sense",
            "process_signal",
            "auto_ingest",
            "mutate",
            "add_connection",
            "live_connection_objects",
        ],
        "component_kinds": {
            "Membrane": {
                "mapping_state": "decision_only",
                "safe_projection_fields": ["radius", "ingest_threshold", "efficiency"],
                "forbidden_behavior": ["auto_ingest", "is_inside"],
            },
            "Sensor": {
                "mapping_state": "decision_only",
                "safe_projection_fields": ["signal_threshold", "sensing_range"],
                "forbidden_behavior": ["sense", "process_signal"],
            },
            "Actuator": {
                "mapping_state": "decision_only",
                "safe_projection_fields": ["energy_cost"],
                "forbidden_behavior": ["process_signal", "get_force_vector"],
            },
        },
        "do_not_claim": [
            "membrane_component_graph_mapping",
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
        ],
    }
```

- [x] Run the test again and make it pass.

### Task 3: Add Component Decision Tool

- [x] Write the failing test in `tests/test_worldbridge_component_decision_tool.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)


ROOT = Path(__file__).resolve().parents[1]


def test_component_decision_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_component_decision.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout) == build_worldbridge_component_decision()
```

- [x] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision_tool.py
```

Expected red result:

- Subprocess fails because `tools/check_worldbridge_component_decision.py` does not exist.

- [x] Create `tools/check_worldbridge_component_decision.py` as a thin wrapper using `tools/_runtime_bootstrap.py`.

Required behavior:

- print sorted JSON from `build_worldbridge_component_decision()`;
- exit `0` only when `read_only is True`, `maps_live_components is False`, `default_ready is False`, and `membrane_component_graph_mapping` is in `do_not_claim`.

### Task 4: Link Decision Into Mapping Audit

- [x] Extend `tests/test_worldbridge_mapping_audit.py`:

```python
def test_mapping_audit_includes_component_decision_summary() -> None:
    audit = build_worldbridge_mapping_audit()

    decision = audit["component_mapping_decision"]
    assert decision["status"] == "worldbridge_component_membrane_decision"
    assert decision["maps_live_components"] is False
    assert decision["decision"] == "read_only_projection_only"
```

- [x] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py
```

Expected red result:

- KeyError for `component_mapping_decision`.

- [x] Modify `world_bridge_mapping_audit.py` to include:

```python
from core.Lotucosm.runtime.world_bridge_component_decision import (
    build_worldbridge_component_decision,
)

...
"component_mapping_decision": build_worldbridge_component_decision(),
```

### Task 5: Add Command, CLI, And MCP Surfaces

- [x] Add tests in `tests/test_runtime_worldbridge_command_surfaces.py`:

```python
def test_worldbridge_component_decision_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.component_decision")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_component_decision_command_reports_forbidden_behavior() -> None:
    result = get_command_registry().run("runtime.worldbridge.component_decision", {})

    assert result["ok"] is True
    decision = result["result"]
    assert decision["maps_live_components"] is False
    assert "auto_ingest" in decision["forbidden_behavior"]
```

- [x] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py
```

Expected red result:

- `runtime.worldbridge.component_decision` is not registered.

- [x] Add `runtime.worldbridge.component_decision` next to `runtime.worldbridge.mapping_audit` in `runtime_commands.py`.

- [x] Add CLI test to `tests/test_ai_command_cli.py`:

```python
def test_run_runtime_worldbridge_component_decision_reports_forbidden_behavior(self) -> None:
    proc = self._run("run", "runtime.worldbridge.component_decision", "--json", "{}")
    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
    data = json.loads(proc.stdout)
    self.assertTrue(data["ok"])
    self.assertFalse(data["result"]["maps_live_components"])
    self.assertIn("auto_ingest", data["result"]["forbidden_behavior"])
```

- [x] Add `get_runtime_worldbridge_component_decision()` to `mcp_adapter.py` and compare it to `run_command("runtime.worldbridge.component_decision", {})` in `tests/test_mcp_command_adapter.py`.

### Task 6: Update Docs And Prompt

- [x] Update `docs/mainline_status.md` with Phase 6E evidence, skips, risks, and next gate.
- [x] Update `docs/runtime_unification_roadmap.md` with the component/membrane decision result.
- [x] Update `docs/adr/0005-unified-pond-bridge.md` with the decision-only result and forbidden behavior list.
- [x] Add `docs/prompts/2026-07-05-worldbridge-component-membrane-decision-prompt.md`.
- [x] Update `docs/INDEX.md` with Phase 6E plan and prompt links.

## Tests First

Behavior changes in this phase must follow TDD:

1. Add the failing test for one surface.
2. Run the exact focused test and observe the expected red result.
3. Implement the smallest read-only code path for that test.
4. Rerun the exact focused test.
5. Only then move to the next task.

Do not modify `world_bridge.py`, `Pond.update`, `GameViewport`, or component behavior methods in this phase.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_worldbridge_component_decision.py
python -B tools/check_worldbridge_mapping_audit.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/runtime_unification_roadmap.md docs/adr/0005-unified-pond-bridge.md docs/prompts docs/superpowers/plans tools/check_worldbridge_component_decision.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_component_decision.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py tests/test_worldbridge_mapping_audit.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
```

## Evidence Ledger

Record these facts in `docs/mainline_status.md`:

- Worktree audit total before and after the phase.
- Focused component decision tests and results.
- Tool output summary.
- Mapping audit nested decision status.
- Command Registry id and read-only flags.
- CLI and MCP parity result.
- Bridge/comparability regression result.
- Comparability smoke tick count, checkpoints, and `all_passed` value.
- Skips and unavailable items.
- Do-not-claim list.

## Fallback / Unblock Path

- If component decision import fails, keep Phase 6D mapping audit as the authority and document the missing decision module in status.
- If command naming conflicts, keep the tool and mapping audit nested summary, then record the command id conflict in `docs/mainline_status.md`.
- If any focused bridge/comparability regression fails, do not expand runtime behavior; this phase should remain read-only and correct the decision surface only.
- If docs display mojibake in the terminal, do not rewrite encoding unless file bytes are proven invalid.

## Phase-End Report Template

- Phase: Phase 6E - WorldBridge component/membrane mapping decision record
- Status: complete | partially complete | blocked
- Implemented: files/features changed
- Verified: commands run and exact results
- Skipped/Unavailable: tests, GUI/offscreen, toolchains, or smoke checks with reasons
- Evidence: decision output, command ids, test results, comparability ticks/checkpoints, file paths
- Architecture impact: plugin boundary unchanged or explicitly documented
- Remaining risks: known mapping losses, default readiness, replay limits
- Next phase: one concrete next phase and first file/command to inspect

## Phase-End Report

- Phase: Phase 6E - WorldBridge component/membrane mapping decision record
- Status: complete
- Implemented: `world_bridge_component_decision.py`, `tools/check_worldbridge_component_decision.py`, nested `component_mapping_decision` in mapping audit, read-only `runtime.worldbridge.component_decision`, CLI coverage, MCP helper, and Phase 6F execution material.
- Verified: component decision suite `2 passed in 0.29s`; mapping/status suite `6 passed in 0.52s`; command/CLI/MCP suite `37 passed in 7.25s`; bridge/comparability regression suite `37 passed in 1.30s`; component decision/mapping/status tools exited 0; dual comparability smoke reported `seed=42 ticks=20 all_passed=True`; core boundary and compileall guardrails passed.
- Skipped/Unavailable: no Phase 6E focused skips. Native acceleration and OpenGL default readiness remain outside this phase.
- Evidence: `tools/check_worldbridge_component_decision.py` reports `decision: read_only_projection_only`, `maps_live_components: false`, `default_ready: false`, safe projection fields, forbidden behavior, and `do_not_claim`.
- Architecture impact: plugin runtime boundary unchanged; no `.pond` mutation, no `world_bridge.py` behavior expansion, no `Pond.update`, `GameViewport`, or component behavior changes.
- Remaining risks: membrane/component/script graph mapping is still not implemented, lossless mapping is false, unified Pond remains opt-in and not default-ready, SR/PS tick merge remains unproven.
- Next phase: Phase 6F - SR/PS component projection prototype. First file: `docs/superpowers/plans/2026-07-05-worldbridge-component-projection-prototype.md`.

## Next Phase Gate

Chosen after Phase 6E passes:

- Phase 6F: SR/PS component projection prototype plan. Execution material exists at `docs/superpowers/plans/2026-07-05-worldbridge-component-projection-prototype.md` and `docs/prompts/2026-07-05-worldbridge-component-projection-prototype-prompt.md`.

Do not prototype component projection until Phase 6E proves the decision record through tool, Command Registry, CLI, MCP, focused tests, and docs.
