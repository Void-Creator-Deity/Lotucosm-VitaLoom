# Phase 6F WorldBridge Component Projection Prototype Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Use TDD for every behavior change.

## Summary

Phase 6F prototypes a narrow, read-only SR/PS component projection after Phase 6E proved the decision record. The goal is to project safe component facts into evidence/status surfaces only. It must not map live PS component behavior into `.pond`, mutate scene component graphs, or make unified Pond default-ready.

## Current State

- Phase 6D passed the mapping-loss audit and `size/radius` bridge gate.
- Phase 6E passed the component/membrane decision gate.
- `build_worldbridge_component_decision()` says `decision: read_only_projection_only`, `maps_live_components: false`, and `default_ready: false`.
- Safe projection candidates include identity/type/location/acquisition/attach/inspectable-property/count fields plus selected membrane/sensor/actuator inspectable fields.
- Forbidden behavior includes `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, `add_connection`, and live connection objects.

## Scope

- Add a read-only projection function that converts PS component objects or status dictionaries into stable evidence dictionaries.
- Cover `Component`, `Membrane`, representative sensor, and representative actuator facts without invoking live behavior methods.
- Expose projection evidence through a tool and, only if tests prove it safe, a read-only Command Registry command.
- Extend mapping audit/status evidence to report projection coverage separately from actual WorldBridge mapping.

## Non-Goals

- Do not mutate `.pond`.
- Do not add component graph data to SR scene entities.
- Do not call `update`, `sense`, `process_signal`, `auto_ingest`, `mutate`, `add_connection`, or connection update methods.
- Do not route projection through `Pond.update`.
- Do not make unified Pond default-ready.
- Do not claim live component graph mapping or lossless mapping.

## Files

- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_component_projection.py`
- Create: `tools/check_worldbridge_component_projection.py`
- Create: `tests/test_worldbridge_component_projection.py`
- Create: `tests/test_worldbridge_component_projection_tool.py`
- Modify: `world_bridge_mapping_audit.py` or `runtime_worldbridge_status.py` only after projection tests pass.
- Modify: `runtime_commands.py`, `mcp_adapter.py`, CLI/MCP tests only after tool evidence is green.
- Modify: `docs/mainline_status.md`, `docs/runtime_unification_roadmap.md`, `docs/adr/0005-unified-pond-bridge.md`, `docs/INDEX.md`, and a Phase 6F prompt.

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run `python -B tools/audit_worktree_groups.py`.
- [x] Run the Phase 6E verification subset:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py tests/test_worldbridge_mapping_audit.py tests/test_runtime_worldbridge_command_surfaces.py
python -B tools/check_worldbridge_component_decision.py
```

### Task 2: Add Projection Tests First

- [x] Write tests that create simple fake component/status objects with safe fields.
- [x] Assert projected output includes `component_id`, `component_type`, `location`, `acquired`, `congenital`, `attach_point`, `inspectable_properties`, and `connection_count`.
- [x] Assert forbidden behavior names are not invoked and live connection objects are not serialized.
- [x] Watch the tests fail because `world_bridge_component_projection.py` does not exist.

### Task 3: Implement Minimal Read-Only Projection

- [x] Implement a projection module that reads attributes and dictionaries without calling live behavior methods.
- [x] Keep output deterministic and JSON-serializable.
- [x] Include a `projection_state: "read_only_projection"` marker and `maps_live_components: false`.

### Task 4: Add Tool Evidence

- [x] Add `tools/check_worldbridge_component_projection.py`.
- [x] The tool must exit 0 only when projection is read-only, JSON-serializable, and reports `maps_live_components: false`.

### Task 5: Integrate Evidence Surfaces

- [x] Nest projection coverage in mapping audit or WorldBridge status without changing `world_bridge.py`.
- [x] Add read-only Command Registry/CLI/MCP surfaces only after the tool and focused tests pass.

### Task 6: Docs And Next Gate

- [x] Update status, roadmap, ADR, index, and prompt with exact evidence.
- [x] Record skipped/unavailable items and do-not-claim items.
- [x] Choose the next gate only after projection proof passes.

## Tests First

Use TDD. No production projection code may be added before a failing test proves the desired contract.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_worldbridge_component_decision.py
python -B tools/check_worldbridge_component_projection.py
python -B tools/check_worldbridge_mapping_audit.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check
```

## Evidence Ledger

Record:

- Worktree audit totals before and after.
- Projection tests red and green evidence.
- Tool output summary.
- Whether any live behavior method was invoked in tests.
- Command/CLI/MCP parity, if added.
- Bridge/comparability regression and dual comparability smoke.
- Do-not-claim list.

## Fallback / Unblock Path

- If safe projection cannot be proven without calling live methods, stop at the tool/decision layer and keep Phase 6E as authority.
- If command naming conflicts, keep the tool only and record the conflict.
- If projection risks `.pond` mutation, do not integrate it into runtime status.

## Phase-End Report Template

- Phase: Phase 6F - WorldBridge component projection prototype
- Status: complete | partially complete | blocked
- Implemented: files/features changed
- Verified: commands run and exact results
- Skipped/Unavailable: tests or surfaces not run with reasons
- Evidence: projection output, command ids, test results, comparability ticks/checkpoints
- Architecture impact: plugin boundary unchanged or explicitly documented
- Remaining risks: live behavior mapping, lossless mapping, default readiness
- Next phase: one concrete next phase and first file/command to inspect

## Phase-End Report

- Phase: Phase 6F - WorldBridge component projection prototype
- Status: complete
- Implemented: `world_bridge_component_projection.py`, `tools/check_worldbridge_component_projection.py`, nested `component_projection` in mapping audit/status evidence, read-only `runtime.worldbridge.component_projection`, CLI coverage, MCP helper, and Phase 6G execution material.
- Verified: projection/tool suite `4 passed in 0.30s`; decision/mapping/status suite `9 passed in 0.68s`; command/CLI/MCP suite `41 passed in 7.34s`; bridge/comparability regression suite `37 passed in 0.93s`; component decision/projection/mapping/status tools exited 0; dual comparability smoke reported `seed=42 ticks=20 all_passed=True`; core boundary and compileall guardrails passed.
- Skipped/Unavailable: no Phase 6F focused skips. Native acceleration and OpenGL default readiness remain outside this phase.
- Evidence: projection output reports `projection_state: read_only_projection`, `maps_live_components: false`, `default_ready: false`, `component_count`, `coverage`, safe projection fields, forbidden behavior, and do-not-claim items.
- Architecture impact: plugin runtime boundary unchanged; no `.pond` mutation, no `world_bridge.py` behavior expansion, no `Pond.update`, `GameViewport`, or component behavior changes.
- Remaining risks: live component graph mapping is still not implemented, lossless mapping is false, unified Pond remains opt-in and not default-ready, SR/PS tick merge remains unproven.
- Next phase: Phase 6G - WorldBridge component projection diagnostics. First file: `docs/superpowers/plans/2026-07-05-worldbridge-component-projection-diagnostics.md`.

## Next Phase Gate

Phase 6G execution material exists at `docs/superpowers/plans/2026-07-05-worldbridge-component-projection-diagnostics.md` and `docs/prompts/2026-07-05-worldbridge-component-projection-diagnostics-prompt.md`.

Do not mutate `.pond` or merge SR/PS tick semantics.
