# VitaLoom Phase 6F WorldBridge Component Projection Prototype Prompt

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
- docs/superpowers/plans/2026-07-05-worldbridge-component-membrane-decision.md
- docs/superpowers/plans/2026-07-05-worldbridge-component-projection-prototype.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_component_decision.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/component.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/membrane.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/sensors.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/components/actuators.py

Current truth:
- Phase 6E is complete for read-only component/membrane decision evidence.
- The decision is read_only_projection_only.
- maps_live_components is false and default_ready is false.
- Forbidden behavior includes update, sense, process_signal, auto_ingest, mutate, add_connection, and live connection objects.
- No live component graph mapping, lossless WorldBridge mapping, or unified Pond default-readiness is proven.

Next mission:
- Execute docs/superpowers/plans/2026-07-05-worldbridge-component-projection-prototype.md task by task.
- Use TDD for every behavior change.
- Add only read-only projection evidence.
- Do not modify world_bridge.py, Pond.update, GameViewport, or component behavior methods unless the plan is explicitly revised first.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py tests/test_worldbridge_mapping_audit.py tests/test_runtime_worldbridge_command_surfaces.py
python -B tools/check_worldbridge_component_decision.py

Required verification:
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_decision.py tests/test_worldbridge_component_decision_tool.py tests/test_worldbridge_mapping_audit.py tests/test_worldbridge_mapping_audit_tool.py tests/test_runtime_worldbridge_status_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_worldbridge_component_projection.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py

Reporting rules:
- Distinguish decision evidence, projection evidence, actual bridge mapping, and default readiness.
- Record skips as skips with reasons.
- End with the phase-end report template from the Phase 6F plan.
```
