# Phase 6G WorldBridge Component Projection Diagnostics Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Use TDD for every behavior change.

## Summary

Phase 6G adds read-only diagnostic visibility for Phase 6F component projection evidence. The goal is to let tools and, if safe, editor diagnostics show projected component facts without mutating `.pond`, without changing WorldBridge behavior, and without implying live component graph mapping.

## Current State

- Phase 6E proved the read-only component/membrane decision record.
- Phase 6F proved read-only component projection, tool output, mapping audit integration, and Command Registry/CLI/MCP surfaces.
- `build_worldbridge_component_projection()` reports `projection_state: read_only_projection`, `maps_live_components: false`, and `default_ready: false`.
- Projection currently accepts component objects or status dictionaries but default command/tool output is an empty evidence envelope unless callers provide components.

## Scope

- Add a read-only diagnostic formatter or status builder for component projection evidence.
- Provide stable summary fields for UI/tool surfaces: component count, coverage by type, safe field names, forbidden behavior names, and do-not-claim items.
- Optionally add an editor diagnostic panel hook only if it routes through the command registry and has smoke tests.
- Keep diagnostic output separate from actual WorldBridge mapping.

## Non-Goals

- Do not mutate `.pond`.
- Do not add or edit scene component graph data.
- Do not call live component behavior methods.
- Do not alter `world_bridge.py`, `Pond.update`, or SR/PS tick semantics.
- Do not make unified Pond default-ready.
- Do not claim live component graph mapping.

## Files

- Create or modify only after tests:
  - `core/Lotucosm/runtime/world_bridge_component_projection.py`
  - `core/VitaLoom/simulation/runtime_worldbridge_status.py`
  - `core/VitaLoom/commands/runtime_commands.py`
  - `core/VitaLoom/commands/mcp_adapter.py`
  - focused tests under `tests/`
  - docs/status/ADR/roadmap/prompt/index

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run worktree audit.
- [x] Run Phase 6F projection, command, tool, and bridge regression tests.

### Task 2: Add Diagnostic Contract Tests

- [x] Write tests for a read-only diagnostic output shape.
- [x] Assert it summarizes `component_count`, `coverage`, `safe_projection_fields`, `forbidden_behavior`, and `do_not_claim`.
- [x] Assert it does not include live connection objects or mutate source inputs.

### Task 3: Implement Minimal Diagnostic Builder

- [x] Implement the smallest formatter/status builder needed by tests.
- [x] Keep output JSON-serializable and deterministic.

### Task 4: Optional UI/Command Hook

- [x] Add command/CLI/MCP or editor diagnostic hook only if tests first prove the shared command path.
- [x] Do not add a UI-only behavior path.

### Task 5: Verify And Record

- [x] Run focused and guardrail verification.
- [x] Update `docs/mainline_status.md`, roadmap, ADR, index, and fresh-session prompt.
- [x] Choose the next gate based on evidence.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_mapping_audit.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_worldbridge_component_projection.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check
```

## Evidence Ledger

Record:

- Worktree audit totals before and after: start `976`; final verification `978`.
- Diagnostic tests red and green evidence: recorded in `docs/mainline_status.md`; final focused projection/diagnostics suite `6 passed in 0.56s`.
- Tool/command output summary: diagnostics tool exits 0 and reports `diagnostic_state: read_only_projection_diagnostics`, `component_count: 0`, `maps_live_components: false`, and `default_ready: false`; command/CLI/MCP suite `48 passed in 8.47s`.
- Whether any UI hook was added or intentionally skipped: no UI hook was added; Phase 6H is a separate decision gate to avoid UI-only command bypass.
- Do-not-claim list: Inspector panel implementation, UI parity, live component graph mapping, `.pond` component mutation, lossless mapping, unified Pond default-readiness, SR/PS tick merge, full unified runtime replay, native acceleration, and OpenGL default-readiness.

## Fallback / Unblock Path

- If UI diagnostics would create a parallel path outside the command registry, stop at tool/command diagnostics.
- If diagnostic output risks implying actual mapping, keep it as command/tool-only evidence and update docs.

## Phase-End Report Template

- Phase: Phase 6G - WorldBridge component projection diagnostics
- Status: complete
- Implemented: read-only diagnostics builder, diagnostics tool, read-only `runtime.worldbridge.component_projection_diagnostics` command, CLI/MCP surfaces, and tracking docs.
- Verified: `python -B tools/audit_worktree_groups.py` -> dirty total `978`; projection/diagnostics pytest suite -> `6 passed in 0.56s`; mapping/command/CLI/MCP suite -> `48 passed in 8.47s`; projection, diagnostics, and runtime status tools exited 0; `check_core_boundaries.py` -> `core boundaries OK`; `compileall` passed; `git diff --check` exited 0 with LF-to-CRLF warnings only.
- Skipped/Unavailable: no UI hook was implemented in this phase by design.
- Evidence: `tools/check_worldbridge_component_projection_diagnostics.py` reports `diagnostic_state: read_only_projection_diagnostics`, `component_count: 0`, `maps_live_components: false`, and `default_ready: false`.
- Architecture impact: plugin boundary unchanged; diagnostics remain read-only and command-backed.
- Remaining risks: UI drift if a future Inspector panel bypasses the Command Registry; live component mapping and default readiness remain unproven.
- Next phase: Phase 6H - WorldBridge Inspector diagnostics decision; first command is `python -B tools/audit_worktree_groups.py`.

## Next Phase Gate

Phase 6H is the next gate: decide whether projected component diagnostics should feed a future read-only Inspector panel, still through the Command Registry. The first file to inspect is `docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md`.
