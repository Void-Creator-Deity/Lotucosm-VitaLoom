# VitaLoom Phase 6 Runtime Unification Read-Only Replay Prompt

Use this prompt only to understand the completed Phase 6A read-only replay evidence gate. For the next active phase, use `docs/prompts/2026-07-04-runtime-replay-command-surfaces-prompt.md`.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository truth.

You are continuing VitaLoom's long-term mainline. Keep the architecture plugin-shaped:
FrameCore -> FrameCore/plugins/lotucosm-vitaloom -> versions/1.0.0/runtime -> Project World.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/runtime_unification_roadmap.md
- docs/architecture.md
- docs/suite_architecture.md
- docs/superpowers/plans/2026-07-04-runtime-unification-readonly-replay.md
- docs/prompts/2026-07-02-vitaloom-long-term-mainline-prompt.md
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/simulation_coordinator.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/ps_replay_overlay.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/ecology_registry.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/editor_extensions/ps_replay_overlay_plugin.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/ecology_observation.py
- tests/test_simulation_coordinator.py
- tests/test_ecology_observation.py
- tests/test_ps_experiment_service.py
- tests/test_ps_experiment_panel_smoke.py

Current truth:
- Phase 0 baseline/tracking, Phase 1 real OpenGL canvas, Phase 2 viewport performance, Phase 3 SR2D Python broadphase, and Phase 4 native proof tooling have passed their documented gates.
- Phase 5 command/plugin authoring has representative UI/CLI/MCP command parity, durable audit, representative session undo/redo, explicit project undo/redo replay, and menu/toolbar undo-redo binding.
- Phase 5 still reports `unified_undo_redo_runtime=false`; do not claim full unified undo/runtime replay.
- SR_PLAY, PS_BATCH, and PS_REPLAY are explicit lanes. Do not merge their tick loops.
- PS replay overlay is read-only: it should read PS run `summary.json`, derive overlay points, and push them to the SR host for display without calling `Pond.update` or writing `.pond`.
- `collect_ecology_snapshots(...)` is the intended read-only aggregation surface for SR/PS/PS_REPLAY evidence.

Phase 6A completion truth:
- `tools/check_runtime_replay_status.py` exists and reports lane state, replay summary availability, overlay point count, ecology lanes, `unified_pond_enabled`, and "do not claim yet" facts.
- `tests/test_runtime_replay_status_tool.py`, `tests/test_ps_replay_overlay_readonly.py`, and coordinator/ecology tests cover the read-only evidence gate.
- The active next gate is Phase 6B: expose the same read-only evidence through Command Registry, CLI, and MCP surfaces.
- Do not change `.pond` semantics, AI command registry flows, Inspector command binding, SR2D adapter seams, package manifests, project manifests, or the plugin runtime layout.

Required starting checks:
python -B tools/audit_worktree_groups.py
python -B tools/check_ai_command_audit_status.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_undo_redo_command_path.py tests/test_ui_command_actions.py tests/test_ai_command_durable_project_undo.py

Phase 6 focused verification:
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py tests/test_ps_verify_triple.py tests/test_ps_experiment_service.py tests/test_ps_experiment_panel_smoke.py tests/test_ecology_observation.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py
python -B tools/check_runtime_replay_status.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools/check_runtime_replay_status.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py tests/test_simulation_coordinator.py

Reporting rules:
- Distinguish implemented, tested, skipped, unavailable, and planned.
- Record fresh command output in docs/mainline_status.md.
- Update docs/INDEX.md if new execution material is added.
- End with the phase-end report from the Phase 6 plan.
- Never say unified Pond, unified undo, or runtime merge is complete unless a later plan and tests prove it.
```
