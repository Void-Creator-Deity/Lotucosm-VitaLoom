# VitaLoom Phase 6C WorldBridge Unified Pond Gate Prompt

Use this prompt in a fresh C0dex session to continue VitaLoom's long-term mainline from repository truth.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository files and current command output.

You are reading the Phase 6C prompt after the read-only gate has been implemented and recorded. Keep the architecture plugin-shaped:
FrameCore -> FrameCore/plugins/lotucosm-vitaloom -> versions/1.0.0/runtime -> Project World.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/runtime_unification_roadmap.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-04-worldbridge-unified-pond-gate.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/comparability.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/viewports/game_viewport.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py
- tests/test_plasticity_and_world_bridge.py
- tests/test_game_viewport_unified_bridge.py
- tests/test_comparability.py
- tests/test_ai_command_cli.py
- tests/test_mcp_command_adapter.py

Current truth:
- Phase 6B is complete for read-only replay status through tool, Command Registry, CLI, and MCP.
- WorldBridge is not absent: `world_bridge.py`, GameViewport opt-in hooks, comparability utilities, and focused tests already exist.
- WorldBridge is also not default-ready: docs explicitly say mapping is minimal/lossy and full unified Pond is not complete.
- Default runtime mode remains dual unless a project explicitly sets `runtime_mode: unified_pond`.
- Do not claim unified Pond, SR/PS tick merge, full unified runtime replay, branching replay/conflict resolution, native acceleration, or OpenGL default-readiness.

Phase 6C evidence:
- Added read-only `core.VitaLoom.simulation.runtime_worldbridge_status.build_runtime_worldbridge_status(...)`.
- Added thin `tools/check_runtime_worldbridge_status.py`.
- Added `runtime.worldbridge.status` with `mutates=False`.
- Added CLI and MCP coverage, including `mcp_adapter.get_runtime_worldbridge_status(...)`.
- Focused command/tool suite: `31 passed in 7.22s`.
- Bridge/comparability/replay suite: `36 passed in 0.88s`.
- Comparability smoke: `python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20` exited 0 and reported `all_passed=True`.

Next mission:
- Start Phase 6D planning only.
- Audit WorldBridge mapping losses and propose the smallest safe mapping extension.
- Do not implement mapping expansion until a Phase 6D plan exists with TDD tests and explicit non-goals.

Use TDD:
1. Write failing tests for `runtime_worldbridge_status`, the tool, command, CLI, and MCP helper.
2. Observe red for the expected missing module/tool/command/helper.
3. Implement the smallest read-only status surfaces.
4. Run focused tests and comparability smoke.
5. Record skips and do-not-claim items honestly.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_runtime_replay_status.py

Phase 6C focused verification:
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/check_runtime_replay_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/runtime_unification_roadmap.md docs/adr/0005-unified-pond-bridge.md docs/prompts docs/superpowers/plans tools/check_runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py

Reporting rules:
- Distinguish pilot code, opt-in flag, command evidence, comparability smoke, and default readiness.
- Do not treat docs-only work as runtime implementation.
- End with the phase-end report template from the plan.
```
