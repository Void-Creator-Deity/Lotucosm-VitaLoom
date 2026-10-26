# Phase 6H WorldBridge Inspector Diagnostics Decision Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Use TDD for behavior changes.

## Summary

Phase 6H decides whether Phase 6G component projection diagnostics should feed a read-only Inspector/editor diagnostic panel. It must keep UI, CLI, MCP, and agent paths aligned through the Command Registry and must not create a UI-only semantics path.

## Current State

- Phase 6F provides read-only component projection evidence.
- Phase 6G provides read-only projection diagnostics via tool, command, CLI, and MCP.
- No UI diagnostic hook is approved yet.
- `runtime.worldbridge.component_projection_diagnostics` is the authority command for diagnostics.

## Scope

- Audit existing Inspector/diagnostic command binding patterns.
- Decide whether a read-only Inspector diagnostics hook is safe now.
- If safe, write a follow-up implementation plan with tests before touching UI.
- If not safe, keep diagnostics command/tool-only and record the blocker.

## Non-Goals

- Do not implement the UI panel in this decision phase.
- Do not add UI-only logic outside the Command Registry.
- Do not mutate `.pond`.
- Do not change `world_bridge.py`, `Pond.update`, or component behavior methods.
- Do not claim live component graph mapping or unified Pond default-readiness.

## Files To Inspect

- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Inspector command binding tests under `tests/`
- Scene/Inspector UI modules under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/`

## Step-by-Step Tasks

### Task 1: Phase-Start Recheck

- [x] Run worktree audit.
- [x] Run Phase 6G focused tests and command/tool smoke.

### Task 2: Audit UI Binding Patterns

- [x] Locate Inspector command-binding code and tests.
- [x] Identify whether a read-only diagnostics command can be displayed without bypassing Command Registry.
- [x] Record required tests for any future UI hook.

### Task 3: Write Decision Record

- [x] Update ADR/status with one of:
  - approve a later implementation plan for a command-backed read-only diagnostics panel;
  - keep diagnostics command/tool-only and document blockers.

### Task 4: Plan Next Gate

- [x] If approved, create a Phase 6I implementation plan and prompt.
- [x] Blocked path not applicable; the approved Phase 6I path was selected.

## Verification Commands

```bash
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection.py tests/test_worldbridge_component_projection_tool.py tests/test_worldbridge_component_projection_diagnostics_tool.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py
python -B tools/check_worldbridge_component_projection_diagnostics.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check
```

## Evidence Ledger

Record:

- Worktree audit totals.
- UI binding files inspected.
- Decision and rationale.
- Tests required for future UI work.
- Do-not-claim list.

## Phase-End Report Template

- Phase: Phase 6H - WorldBridge Inspector diagnostics decision
- Status: complete | partially complete | blocked
- Implemented: decision docs only or planned follow-up material
- Verified: commands run and exact results
- Skipped/Unavailable: UI hooks not implemented with reasons
- Evidence: inspected files, decision record, tests/commands
- Architecture impact: plugin boundary unchanged or explicitly documented
- Remaining risks: UI drift, command bypass, default readiness
- Next phase: one concrete next phase and first file/command to inspect

## Phase 6H Completion Evidence

### UI Binding Audit

Inspected Modules and Interfaces:

- `core/VitaLoom/docks/inspector.py` already imports `get_command_registry()` and uses the registry for scene mutation synchronization.
- `InspectorPanel._add_property_field()` already has a read-only structured JSON display path.
- `core/VitaLoom/inspector/schema.py` is a Qt-free schema Module and is suitable for a future Headless-tested diagnostics view-model Adapter.
- `core/VitaLoom/inspector/command_binding.py` is specifically an edit-to-command binding Interface; read-only diagnostics must not be routed through it.
- `runtime.worldbridge.component_projection_diagnostics` is already authoritative, `mutates: false`, `requires_gui: false`, and omits live component objects.

### Decision

**Approved with guardrails:** a later Phase 6I may add a dedicated, command-backed, read-only WorldBridge diagnostics foldout to Inspector.

The current command has an empty input schema and reports runtime-wide projection evidence. It does not describe the selected entity. Therefore the future UI must:

1. label the section as runtime-wide diagnostics rather than selected-entity component state;
2. call only `runtime.worldbridge.component_projection_diagnostics` through the Command Registry;
3. display summary fields only and preserve `read_only`, `maps_live_components`, `default_ready`, and `do_not_claim` warnings;
4. remain non-editable and never call `bind_inspector_edit` or a mutation command;
5. show command failure as an unavailable diagnostic state without breaking normal Inspector properties;
6. avoid claiming that `component_count: 0` means the selected entity has no components.

No Inspector/UI hook was implemented in Phase 6H.

### Headless Command Seam Fix

The phase-start command suite exposed a real import blocker: importing `runtime_commands.py` loaded `asset_dependency.py`, which eagerly imported PyQt-bound `ProjectManager` and `EditorContext`. `asset_dependency.py` now imports those GUI Modules only inside the two methods that actually need them. This preserves GUI behavior while allowing read-only Command Registry discovery and WorldBridge diagnostics in a no-PyQt6 process.

A regression test now blocks PyQt6 and proves the read-only diagnostics command can still be described through `get_command_registry()`.

### Verification

| Check | Result |
|---|---|
| Starting worktree audit | dirty total `982` |
| Initial historical Phase 6G aggregate command suite | `6 passed, 45 failed`; failures exposed eager PyQt6 imports rather than WorldBridge diagnostic semantics |
| Aggregate command suite after lazy-import fix | `37 passed, 8 failed`; remaining failures are PyQt-bound project creation/runtime replay paths outside this decision Gate |
| Phase 6H focused projection/diagnostics/Inspector suite | `24 passed in 0.79s` |
| Headless Command Registry regression + WorldBridge command surfaces | `16 passed in 1.02s` |
| Final combined Phase 6H focused regression | `29 passed in 1.34s` |
| Diagnostics tool | exited 0; `read_only: true`, `maps_live_components: false`, `default_ready: false`, `component_count: 0` |
| CLI command smoke | `runtime.worldbridge.component_projection_diagnostics` returned `ok: true` with the same read-only summary |
| Final guardrails | `core boundaries OK`; `release consistency OK`; temporary-pycache `compileall` passed; worktree audit remained `982`; `git diff --check` exited 0 with existing LF→CRLF warnings only |

### Required Phase 6I Tests

- Headless view-model Adapter consumes the exact command result and preserves authority/scope/warnings.
- The UI Adapter invokes the diagnostics command exactly once and never imports the projection builder directly.
- Per-component objects and a `components` list are rejected or ignored.
- Command errors produce a read-only unavailable section and do not remove normal Inspector fields.
- The diagnostics section contains no editable widgets and cannot reach `bind_inspector_edit`.
- A real PyQt6 Inspector smoke must prove the foldout renders before any UI-complete claim.

Phase 6H is complete. The plugin architecture and `.pond` semantics are unchanged.

**Unique next Gate: Phase 6I — command-backed read-only WorldBridge Inspector diagnostics implementation.**




