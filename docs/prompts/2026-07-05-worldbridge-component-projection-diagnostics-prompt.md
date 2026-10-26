# VitaLoom Phase 6G WorldBridge Component Projection Diagnostics Prompt

Use this prompt in a fresh C0dex session to continue VitaLoom's long-term mainline from repository truth.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository files and current command output.

Keep VitaLoom plugin-shaped:
FrameCore -> FrameCore/plugins/lotucosm-vitaloom -> versions/1.0.0/runtime -> Project World.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/runtime_unification_roadmap.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-05-worldbridge-component-projection-prototype.md
- docs/superpowers/plans/2026-07-05-worldbridge-component-projection-diagnostics.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_component_projection.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_mapping_audit.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py

Current truth:
- Phase 6F is complete for read-only component projection evidence.
- Phase 6G is complete for read-only component projection diagnostics through tool, Command Registry, CLI, and MCP.
- Projection and diagnostics are JSON-safe, read-only, and report maps_live_components=false/default_ready=false.
- This is not live component graph mapping and does not mutate .pond.

Next mission:
- If asked to re-open Phase 6G, first verify the evidence in docs/mainline_status.md and this plan.
- Otherwise continue with docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md and docs/prompts/2026-07-05-worldbridge-inspector-diagnostics-decision-prompt.md.
- Keep any future diagnostics UI command-registry aligned.
- Do not modify world_bridge.py, Pond.update, GameViewport, or component behavior methods unless a later phase plan is explicitly revised first.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py tests/test_worldbridge_mapping_audit.py tests/test_runtime_worldbridge_command_surfaces.py
python -B tools/check_worldbridge_component_projection.py

Reporting rules:
- Distinguish projection diagnostics, actual bridge mapping, UI hook, and default readiness.
- Record skips as skips with reasons.
- End with the phase-end report template from the Phase 6G plan.
```
