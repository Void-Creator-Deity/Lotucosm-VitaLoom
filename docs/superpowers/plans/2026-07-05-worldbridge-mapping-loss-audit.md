# WorldBridge Mapping Loss Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WorldBridge mapping loss explicit, machine-readable, and test-covered, then add the smallest safe field extension without making unified Pond default-ready.

**Architecture:** Keep SR_PLAY, PS_BATCH, and PS_REPLAY as separate lanes. WorldBridge stays an opt-in pilot behind project `runtime_mode: unified_pond`; this phase adds read-only audit evidence and a narrow `size/radius` mapping because both SR `EntityBase` and PS `Organism` already expose those fields.

**Tech Stack:** Python 3.11+, pytest, VitaLoom Command Registry, MCP adapter, existing plugin runtime modules under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.

---

## Summary

Phase 6C proved a read-only WorldBridge gate through runtime module, tool, Command Registry, CLI, and MCP. It did not prove lossless mapping, full unified replay, SR/PS tick merge, or default readiness. Phase 6D is next because the repository now needs a concrete mapping-loss ledger before any bridge expansion can be called real engine progress.

This phase has two deliverables:

- A machine-readable WorldBridge mapping audit that names covered, partial, missing, and unsafe fields.
- One smallest safe mapping extension: carry `size/radius` from SR entity to PS organism and back to SR display, without touching membrane, component, script, child hierarchy, AI commands, or `.pond` semantics.

## Current State

- `docs/mainline_status.md` says Phase 6C passed for read-only WorldBridge status/tool/CLI/MCP evidence.
- `tools/audit_worktree_groups.py` passed on 2026-07-04 with dirty total `967` in the latest local audit; the tree remains intentionally dirty.
- `python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_comparability.py` passed on 2026-07-04 with `29 passed in 0.80s`.
- `core/Lotucosm/runtime/world_bridge.py` currently maps or syncs:
  - position
  - energy
  - health
  - max_energy on creation
  - max_health on creation
  - developmental profile from spawn request
  - social enabled flag from spawn request
- Current known losses include:
  - velocity and acceleration
  - active/visible state
  - color/rendering identity
  - scripts and command bindings
  - membrane and component graph
  - parent/child hierarchy
  - memory genes and runtime memory system
  - full `.pond` roundtrip semantics

## Previous Phase Summary

Phase 6C implemented:

- `core.VitaLoom.simulation.runtime_worldbridge_status.build_runtime_worldbridge_status(...)`
- `tools/check_runtime_worldbridge_status.py`
- read-only `runtime.worldbridge.status`
- CLI coverage through `main.py command run`
- MCP helper `get_runtime_worldbridge_status(...)`
- explicit `project.json.runtime_mode == "unified_pond"` proof

Phase 6C verified:

- Focused command/tool suite: `31 passed`
- Bridge/comparability/replay focused suite: `36 passed`
- Comparability smoke: `all_passed=True` at ticks `10` and `20`
- Core boundary and compileall checks passed

Phase 6C did not attempt:

- mapping expansion
- default runtime switch
- SR/PS tick merge
- full unified runtime replay
- native or OpenGL work

## Scope

- Add a runtime-owned mapping audit module under `core/Lotucosm/runtime`.
- Add a thin check tool under `tools/`.
- Extend Phase 6C WorldBridge status output to include the mapping audit summary.
- Add a read-only Command Registry command for the audit.
- Add CLI and MCP parity tests for that command.
- Extend WorldBridge to preserve `size/radius` through creation and display sync.
- Update docs/status/prompt so fresh sessions can continue from the audit evidence.

## Non-Goals

- Do not make `unified_pond` the default runtime mode.
- Do not merge SR_PLAY and PS_BATCH tick semantics.
- Do not map membrane/component/script graphs in this phase.
- Do not add old root runtime folders or old-path shims.
- Do not write `.pond` files from audit commands.
- Do not route UI, CLI, MCP, or agent actions around the Command Registry.
- Do not claim lossless WorldBridge mapping after adding `size/radius`.
- Do not claim native acceleration or OpenGL default-readiness.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py`
- Create: `tools/check_worldbridge_mapping_audit.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Create: `tests/test_worldbridge_mapping_audit.py`
- Create: `tests/test_worldbridge_mapping_audit_tool.py`
- Modify: `tests/test_plasticity_and_world_bridge.py`
- Modify: `tests/test_runtime_worldbridge_command_surfaces.py`
- Modify: `tests/test_ai_command_cli.py`
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/runtime_unification_roadmap.md`
- Modify: `docs/adr/0005-unified-pond-bridge.md`
- Add: `docs/prompts/2026-07-05-worldbridge-mapping-loss-audit-prompt.md`
- Modify: `docs/INDEX.md`

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run current truth checks before planning:

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_comparability.py
```

Expected:

- Worktree remains dirty and is not cleaned.
- WorldBridge and comparability focused tests pass.
- No file is staged, committed, reverted, deleted, or cleaned.

Current planning evidence:

- `tools/audit_worktree_groups.py` passed with dirty total `967`.
- `tests/test_plasticity_and_world_bridge.py tests/test_comparability.py` passed with `29 passed in 0.80s`.

### Task 2: Add Mapping Audit Module

- [ ] Write the failing test in `tests/test_worldbridge_mapping_audit.py`:

```python
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


def test_mapping_audit_names_current_coverage_and_losses() -> None:
    audit = build_worldbridge_mapping_audit()

    assert audit["schema_version"] == 1
    assert audit["read_only"] is True
    assert audit["lossless"] is False
    assert audit["default_ready"] is False
    assert audit["fields"]["position"]["state"] == "covered"
    assert audit["fields"]["energy"]["state"] == "covered"
    assert audit["fields"]["health"]["state"] == "covered"
    assert audit["fields"]["size_radius"]["state"] == "covered"
    assert audit["fields"]["membrane_component_graph"]["state"] == "not_mapped"
    assert "lossless_worldbridge_mapping" in audit["do_not_claim"]
```

- [ ] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py
```

Expected red result:

- Collection fails because `core.Lotucosm.runtime.world_bridge_mapping_audit` does not exist.

- [ ] Create `world_bridge_mapping_audit.py` with this public function:

```python
from __future__ import annotations

from typing import Any


def build_worldbridge_mapping_audit() -> dict[str, Any]:
    fields = {
        "position": {"state": "covered", "direction": "sr_to_ps_and_ps_to_sr"},
        "energy": {"state": "covered", "direction": "sr_to_ps_and_ps_to_sr"},
        "health": {"state": "covered", "direction": "sr_to_ps_and_ps_to_sr"},
        "max_energy": {"state": "creation_only", "direction": "sr_to_ps"},
        "max_health": {"state": "creation_only", "direction": "sr_to_ps"},
        "developmental_profile": {"state": "partial", "direction": "spawn_request_to_ps"},
        "social_enabled": {"state": "partial", "direction": "spawn_request_to_ps"},
        "size_radius": {"state": "covered", "direction": "sr_to_ps_and_ps_to_sr"},
        "velocity_acceleration": {"state": "not_mapped", "direction": "none"},
        "active_visible_state": {"state": "not_mapped", "direction": "none"},
        "render_identity": {"state": "not_mapped", "direction": "none"},
        "scripts": {"state": "not_mapped", "direction": "none"},
        "membrane_component_graph": {"state": "not_mapped", "direction": "none"},
        "hierarchy": {"state": "not_mapped", "direction": "none"},
        "memory_genes": {"state": "not_mapped", "direction": "none"},
    }
    return {
        "schema_version": 1,
        "status": "worldbridge_mapping_loss_audit",
        "read_only": True,
        "lossless": False,
        "default_ready": False,
        "safe_extension_candidate": "size_radius",
        "fields": fields,
        "known_losses": [name for name, item in fields.items() if item["state"] == "not_mapped"],
        "do_not_claim": [
            "lossless_worldbridge_mapping",
            "unified_pond_default_ready",
            "sr_ps_tick_merge",
            "full_unified_runtime_replay",
        ],
    }
```

- [ ] Run the test again and make it pass.

### Task 3: Add Mapping Audit Tool

- [ ] Write the failing test in `tests/test_worldbridge_mapping_audit_tool.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit


ROOT = Path(__file__).resolve().parents[1]


def test_mapping_audit_tool_matches_runtime_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tools/check_worldbridge_mapping_audit.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout) == build_worldbridge_mapping_audit()
```

- [ ] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit_tool.py
```

Expected red result:

- Subprocess fails because `tools/check_worldbridge_mapping_audit.py` does not exist.

- [ ] Create `tools/check_worldbridge_mapping_audit.py` as a thin wrapper using `tools/_runtime_bootstrap.py`.

Required behavior:

- print sorted JSON from `build_worldbridge_mapping_audit()`
- exit `0` only when `read_only is True`, `lossless is False`, `default_ready is False`, and `lossless_worldbridge_mapping` is in `do_not_claim`

### Task 4: Extend Status Surface With Audit Summary

- [ ] Extend `tests/test_runtime_worldbridge_status_tool.py`:

```python
def test_worldbridge_status_includes_mapping_audit_summary() -> None:
    status = build_runtime_worldbridge_status()

    audit = status["mapping_audit"]
    assert audit["status"] == "worldbridge_mapping_loss_audit"
    assert audit["lossless"] is False
    assert audit["safe_extension_candidate"] == "size_radius"
```

- [ ] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py
```

Expected red result:

- KeyError for `mapping_audit`.

- [ ] Modify `runtime_worldbridge_status.py` to import and include the audit:

```python
from core.Lotucosm.runtime.world_bridge_mapping_audit import build_worldbridge_mapping_audit

...
"mapping_audit": build_worldbridge_mapping_audit(),
```

### Task 5: Add Read-Only Command, CLI, And MCP Surfaces

- [ ] Add tests in `tests/test_runtime_worldbridge_command_surfaces.py`:

```python
def test_worldbridge_mapping_audit_command_is_read_only() -> None:
    spec = get_command_registry().describe("runtime.worldbridge.mapping_audit")

    assert spec["mutates"] is False
    assert spec["requires_gui"] is False
    assert spec["capability"] == "vitalloom.pvaec.simulation"


def test_worldbridge_mapping_audit_command_reports_losses() -> None:
    result = get_command_registry().run("runtime.worldbridge.mapping_audit", {})

    assert result["ok"] is True
    audit = result["result"]
    assert audit["read_only"] is True
    assert audit["lossless"] is False
    assert audit["fields"]["membrane_component_graph"]["state"] == "not_mapped"
```

- [ ] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py
```

Expected red result:

- `runtime.worldbridge.mapping_audit` is not registered.

- [ ] Add `runtime.worldbridge.mapping_audit` next to `runtime.worldbridge.status` in `runtime_commands.py`.

- [ ] Add CLI assertions to `tests/test_ai_command_cli.py`:

```python
def test_run_runtime_worldbridge_mapping_audit_reports_losses(self) -> None:
    proc = self._run("run", "runtime.worldbridge.mapping_audit", "--json", "{}")
    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
    data = json.loads(proc.stdout)
    self.assertTrue(data["ok"])
    self.assertFalse(data["result"]["lossless"])
```

- [ ] Add `get_runtime_worldbridge_mapping_audit()` to `mcp_adapter.py` and compare it to `run_command("runtime.worldbridge.mapping_audit", {})` in `tests/test_mcp_command_adapter.py`.

### Task 6: Add `size/radius` Roundtrip

- [ ] Extend `tests/test_plasticity_and_world_bridge.py`:

```python
def test_worldbridge_preserves_size_radius_on_creation_and_display_sync(self) -> None:
    class _Ent:
        id = "size1"
        position = [1.0, 2.0]
        energy = 80.0
        health = 70.0
        size = 18.0
        radius = 18.0
        sr_debug_hud = {}

    ent = _Ent()
    pond = Pond(name="size", size=(100.0, 100.0), initial_organisms=0, initial_components=0)
    org = sr_entity_to_organism(ent, pond)

    self.assertAlmostEqual(float(org.size), 18.0)
    self.assertAlmostEqual(float(org.radius), 18.0)

    org.set_size(24.0)
    sync_organism_to_sr_display(org, ent)

    self.assertAlmostEqual(float(ent.size), 24.0)
    self.assertAlmostEqual(float(ent.radius), 24.0)
```

- [ ] Run the red test:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py
```

Expected red result:

- `org.size` remains the default instead of matching SR entity size.

- [ ] Modify `sr_entity_to_organism(...)` to pass `size` when constructing `Organism`:

```python
size = float(getattr(entity, "size", getattr(entity, "radius", 10.0)) or 10.0)
org = Organism(..., size=size, ...)
org.radius = float(getattr(entity, "radius", size) or size)
```

- [ ] Modify `sync_organism_to_sr_display(...)`:

```python
if hasattr(entity, "set_size") and hasattr(organism, "size"):
    entity.set_size(float(organism.size))
elif hasattr(entity, "size") and hasattr(organism, "size"):
    entity.size = float(organism.size)
if hasattr(entity, "radius") and hasattr(organism, "radius"):
    entity.radius = float(organism.radius)
```

- [ ] Run the test again and make it pass.

### Task 7: Update Docs And Evidence

- [ ] Update `docs/mainline_status.md` with Phase 6D evidence, skips, risks, and next gate.
- [ ] Update `docs/runtime_unification_roadmap.md` so WorldBridge C.4 says mapping audit is the current gate.
- [ ] Update `docs/adr/0005-unified-pond-bridge.md` with the field audit and `size/radius` decision.
- [ ] Add `docs/prompts/2026-07-05-worldbridge-mapping-loss-audit-prompt.md`.
- [ ] Update `docs/INDEX.md` with Phase 6D plan and prompt links.

## Tests First

Behavior changes in this phase must follow TDD:

1. Add the failing test for one surface or field.
2. Run the exact focused test and observe the expected red result.
3. Implement the smallest code path for that test.
4. Rerun the exact focused test.
5. Only then move to the next task.

Do not modify `GameViewport` or `Pond.update` in this phase.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_worldbridge_mapping_audit.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/runtime_unification_roadmap.md docs/adr/0005-unified-pond-bridge.md docs/prompts docs/superpowers/plans tools/check_worldbridge_mapping_audit.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plasticity_and_world_bridge.py
```

## Evidence Ledger

Record these facts in `docs/mainline_status.md`:

- Worktree audit total before and after the phase.
- Focused mapping audit tests and results.
- Tool output summary.
- Command Registry id and read-only flags.
- CLI and MCP parity result.
- `size/radius` red test and green test.
- Bridge/comparability regression result.
- Comparability smoke tick count, checkpoints, and `all_passed` value.
- Skips and unavailable items.
- Do-not-claim list.

## Fallback / Unblock Path

- If `size/radius` mapping changes comparability unexpectedly, revert only the Phase 6D `size/radius` code path and keep the read-only audit module/tool.
- If CLI or MCP command registration conflicts with existing command naming, keep the tool and status-module audit and document the command id conflict in `docs/mainline_status.md`.
- If docs show mojibake in the terminal, do not rewrite encodings in this phase unless file bytes are proven invalid.
- If `world_bridge.py` import fails, the audit tool should still report static mapping facts only after the failure is explicitly represented in status output.

## Phase-End Report Template

- Phase: Phase 6D - WorldBridge mapping-loss audit and size/radius extension
- Status: complete | partially complete | blocked
- Implemented: files/features changed
- Verified: commands run and exact results
- Skipped/Unavailable: tests, GUI/offscreen, toolchains, or smoke checks with reasons
- Evidence: audit output, command ids, test results, comparability ticks/checkpoints, file paths
- Architecture impact: plugin boundary unchanged or explicitly documented
- Remaining risks: known mapping losses, default readiness, replay limits
- Next phase: one concrete next phase and first file/command to inspect

## Next Phase Gate

Chosen after Phase 6D passes:

- Phase 6E: WorldBridge component/membrane mapping decision record.

Do not start component or membrane mapping until Phase 6D has a green audit tool, Command Registry/CLI/MCP parity, focused bridge tests, comparability smoke, and explicit do-not-claim items recorded in `docs/mainline_status.md`.

## Phase-End Report

- Phase: Phase 6D - WorldBridge mapping-loss audit and size/radius extension
- Status: complete for the mapping audit, read-only surfaces, and `size/radius` gate
- Implemented: `world_bridge_mapping_audit.py`, `tools/check_worldbridge_mapping_audit.py`, `mapping_audit` inside runtime WorldBridge status, read-only `runtime.worldbridge.mapping_audit`, CLI coverage, MCP helper, and `size/radius` roundtrip in `world_bridge.py`.
- Verified: final worktree audit `970`; mapping audit/tool suite `2 passed in 0.32s`; earlier combined audit/status suite `5 passed in 0.62s`; status/command/CLI/MCP suite `36 passed in 7.65s`; bridge/comparability/replay suite `37 passed in 1.40s`; mapping audit tool passed; WorldBridge status tool passed; dual comparability smoke exited 0 with `seed=42 ticks=20 all_passed=True`; core boundary check passed; compileall passed.
- Skipped/Unavailable: no Phase 6D focused skips; no native or OpenGL work attempted.
- Evidence: `tools/check_worldbridge_mapping_audit.py` reports `size_radius: covered`, `lossless: false`, `default_ready: false`, and known losses for velocity, active/visible state, render identity, scripts, membrane/component graph, hierarchy, and memory genes.
- Architecture impact: plugin runtime boundary unchanged; default runtime remains `dual`; WorldBridge remains opt-in.
- Remaining risks: lossless mapping is still false; membrane/component/script graph mapping is not implemented; full unified runtime replay and SR/PS tick merge are not complete.
- Next phase: Phase 6E - WorldBridge component/membrane mapping decision record; first files to inspect are `docs/adr/0005-unified-pond-bridge.md`, `world_bridge_mapping_audit.py`, `world_bridge.py`, and component/membrane classes under `runtime/builtin/components/`.
