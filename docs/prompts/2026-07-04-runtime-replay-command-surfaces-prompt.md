# VitaLoom Phase 6B Runtime Replay Command Surfaces Prompt

Use this prompt in a fresh C0dex session to continue VitaLoom's long-term mainline without jumping prematurely into unified Pond.

```text
Do not read, resume, fork, or load old C0dex threads unless the user explicitly asks. Continue from repository truth.

You are reading the Phase 6B prompt after the gate has been implemented and recorded. Keep the architecture plugin-shaped:
FrameCore -> FrameCore/plugins/lotucosm-vitaloom -> versions/1.0.0/runtime -> Project World.

Read first:
- AGENTS.md
- docs/mainline_status.md
- docs/runtime_unification_roadmap.md
- docs/architecture.md
- docs/suite_architecture.md
- docs/superpowers/plans/2026-07-04-runtime-replay-command-surfaces.md
- docs/superpowers/plans/2026-07-04-runtime-unification-readonly-replay.md
- tools/check_runtime_replay_status.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py
- tests/test_runtime_replay_status_tool.py
- tests/test_ai_command_cli.py
- tests/test_mcp_command_adapter.py

Current truth:
- Phase 6A is complete only for the read-only replay evidence gate.
- Phase 6B is complete for read-only tool/Command Registry/CLI/MCP replay status parity.
- `core.VitaLoom.simulation.runtime_replay_status.build_runtime_replay_status(...)` owns the status collection.
- `tools/check_runtime_replay_status.py` is a thin wrapper over the runtime module.
- `runtime.replay.status` reports lane definitions, replay summary availability, overlay point count, ecology lanes, `unified_pond_enabled`, and `do_not_claim`.
- `PS_REPLAY` is explicit and separate from SR/PS tick exclusivity.
- Replay overlay ingestion must remain read-only: no `.pond` writes, no `Pond.update`, no PS runner tick inside the viewport.
- Full unified Pond, SR/PS tick merge, branching replay semantics, conflict resolution, native acceleration, and OpenGL default-readiness are not complete.

Phase 6B evidence:
- TDD red first failed with missing `core.VitaLoom.simulation.runtime_replay_status`.
- Focused Phase 6B suite: `28 passed in 6.01s`.
- Final replay/command suite: `38 passed in 5.92s`.
- `python -B tools/check_runtime_replay_status.py`, `python -B tools/check_core_boundaries.py`, and `python -B -m compileall -q FrameCore tools main.py player.py` passed.
- Scoped `git diff --check` exited 0 with the existing `docs/INDEX.md` LF/CRLF warning.

Next mission:
- Start Phase 6C planning only.
- Design a small `WorldBridge` / unified Pond experiment behind an explicit project flag and ADR gate.
- Do not implement the bridge until a Phase 6C plan exists with tests, non-goals, fallback path, and next gate.

Use TDD:
1. Write the Phase 6C plan before touching runtime code.
2. Run it and observe failure.
3. Implement the smallest explicit-flag experiment only after the plan is accepted by repository truth.
4. Rerun the focused test.
5. Only then update docs.

Required starting checks:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_simulation_coordinator.py tests/test_ps_verify_triple.py tests/test_ps_experiment_service.py tests/test_ps_experiment_panel_smoke.py tests/test_ecology_observation.py tests/test_runtime_replay_status_tool.py tests/test_ps_replay_overlay_readonly.py
python -B tools/check_runtime_replay_status.py

Phase 6B focused verification:
python -B -m pytest -q -p no:cacheprovider tests/test_runtime_replay_status_tool.py tests/test_runtime_replay_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_simulation_coordinator.py tests/test_ps_replay_overlay_readonly.py tests/test_ecology_observation.py
python -B tools/check_runtime_replay_status.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tools/check_runtime_replay_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/runtime_replay_status.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py tests/test_runtime_replay_status_tool.py tests/test_runtime_replay_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py

Reporting rules:
- Distinguish implemented, tested, skipped, unavailable, and planned.
- Do not claim unified Pond, tick merge, full unified runtime replay, native acceleration, or OpenGL default-readiness.
- Record fresh command output in docs/mainline_status.md.
- End with a phase-end report and one next gate only.
```
