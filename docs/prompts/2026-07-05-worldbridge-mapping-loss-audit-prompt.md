# VitaLoom Phase 6D WorldBridge Mapping Loss Audit Prompt

Use this prompt in a fresh C0dex session to continue VitaLoom's long-term mainline from repository truth.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository files and current command output.

You are the long-term lead engineer for VitaLoom. Keep the architecture plugin-shaped:
FrameCore -> FrameCore/plugins/lotucosm-vitaloom -> versions/1.0.0/runtime -> Project World.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/runtime_unification_roadmap.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-04-worldbridge-unified-pond-gate.md
- docs/superpowers/plans/2026-07-05-worldbridge-mapping-loss-audit.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/comparability.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py
- tests/test_plasticity_and_world_bridge.py
- tests/test_comparability.py
- tests/test_runtime_worldbridge_status_tool.py
- tests/test_runtime_worldbridge_command_surfaces.py
- tests/test_ai_command_cli.py
- tests/test_mcp_command_adapter.py

Current truth:
- Phase 6C is complete only for read-only WorldBridge gate evidence through runtime module, tool, Command Registry, CLI, and MCP.
- Default runtime mode remains dual.
- WorldBridge is opt-in through `project.json.runtime_mode == "unified_pond"`.
- Current mapping is not lossless.
- Current mapped fields are position, energy, health, size/radius, max_energy/max_health on creation, and partial developmental/social profile fields from spawn requests.
- Current unmapped or unsafe fields include velocity/acceleration, active/visible state, render identity, scripts, membrane/component graph, hierarchy, memory genes, and full `.pond` roundtrip semantics.
- The completed smallest safe extension is `size/radius`, because SR `EntityBase` and PS `Organism` both already expose those fields.

Do not claim:
- unified Pond default-readiness
- lossless WorldBridge mapping
- SR/PS tick merge
- full unified runtime replay
- native acceleration
- OpenGL default-readiness

Next mission:
- Start Phase 6E planning for WorldBridge component/membrane mapping decision record.
- Use TDD for each behavior change.
- Keep read-only mapping audit evidence as the authority before any further bridge expansion.
- Do not map membrane/component/script graphs without a new Phase 6E plan and explicit non-goals.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_comparability.py

Phase 6D verification to rerun before building on it:
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py tests/test_comparability.py tests/test_runtime_replay_command_surfaces.py
python -B tools/check_worldbridge_mapping_audit.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/run_dual_comparability.py --ticks 20 --checkpoint 10 --checkpoint 20
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/runtime_unification_roadmap.md docs/adr/0005-unified-pond-bridge.md docs/prompts docs/superpowers/plans tools/check_worldbridge_mapping_audit.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_worldbridge_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plasticity_and_world_bridge.py

Reporting rules:
- Distinguish read-only audit, actual bridge mapping, command/CLI/MCP parity, comparability smoke, and default readiness.
- Record skips as skips with reasons.
- Do not treat docs-only work as runtime implementation.
- End with the phase-end report template from the Phase 6D plan.
```
