# VitaLoom Phase 6E WorldBridge Component Membrane Decision Prompt

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
- docs/superpowers/plans/2026-07-05-worldbridge-mapping-loss-audit.md
- docs/superpowers/plans/2026-07-05-worldbridge-component-membrane-decision.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/component.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/components_base.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/membrane.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/sensors.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/actuators.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py
- tests/test_worldbridge_mapping_audit.py
- tests/test_runtime_worldbridge_command_surfaces.py
- tests/test_ai_command_cli.py
- tests/test_mcp_command_adapter.py

Current truth:
- Phase 6D is complete for mapping audit, read-only surfaces, and `size/radius` roundtrip.
- Default runtime mode remains dual.
- WorldBridge remains opt-in through `project.json.runtime_mode == "unified_pond"`.
- Current mapped fields are position, energy, health, size/radius, max_energy/max_health at creation, and partial developmental/social profile fields from spawn requests.
- Current unmapped fields include velocity/acceleration, active/visible state, render identity, scripts, membrane/component graph, hierarchy, memory genes, and full `.pond` roundtrip semantics.
- PS components are live runtime objects with update/sense/process_signal/auto_ingest/mutate behavior, connections, genetics, and Inspector registered properties.
- SR membrane topology and scripts are separate semantics; do not equate them with PS `Membrane`.

Do not claim:
- membrane/component/script graph mapping
- lossless WorldBridge mapping
- unified Pond default-readiness
- SR/PS tick merge
- full unified runtime replay
- native acceleration
- OpenGL default-readiness

Next mission:
- Execute `docs/superpowers/plans/2026-07-05-worldbridge-component-membrane-decision.md` task by task.
- Use TDD for each behavior change.
- Add only read-only component/membrane decision evidence.
- Do not modify `world_bridge.py`, `Pond.update`, `GameViewport`, or component behavior methods in this phase.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_plasticity_and_world_bridge.py tests/test_comparability.py

Required focused verification:
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

Reporting rules:
- Distinguish read-only decision evidence, actual bridge mapping, command/CLI/MCP parity, comparability smoke, and default readiness.
- Record skips as skips with reasons.
- Do not treat docs-only work as runtime implementation.
- End with the phase-end report template from the Phase 6E plan.
```
