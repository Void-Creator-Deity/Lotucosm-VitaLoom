# VitaLoom Phase 6H WorldBridge Inspector Diagnostics Decision Prompt

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
- docs/superpowers/plans/2026-07-05-worldbridge-component-projection-diagnostics.md
- docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- tests/test_runtime_worldbridge_command_surfaces.py
- tests/test_ai_command_cli.py
- tests/test_mcp_command_adapter.py
- Inspector command binding tests and UI modules discovered from the repository.

Current truth:
- Phase 6G is complete for read-only component projection diagnostics through tool, Command Registry, CLI, and MCP.
- No UI hook is approved yet.
- Diagnostics must remain command-backed and read-only.
- Do not mutate .pond or create UI-only semantics.

Next mission:
- Execute docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md.
- Audit Inspector command binding and decide whether a future read-only diagnostics panel is safe.
- Do not implement the panel in this decision phase.

Starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py tests/test_worldbridge_component_projection_diagnostics_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_worldbridge_component_projection_diagnostics.py

Reporting rules:
- Distinguish command diagnostics, UI decision, actual UI implementation, and default readiness.
- Record skips as skips with reasons.
- End with the phase-end report template from the Phase 6H plan.
```
