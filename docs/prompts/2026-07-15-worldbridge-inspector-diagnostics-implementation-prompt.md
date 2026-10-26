> Phase 6I Gates A/B are complete. Continue with 2026-07-15-worldbridge-inspector-diagnostics-ui-gate-prompt.md for the unique UI Gate.

# VitaLoom Phase 6I WorldBridge Inspector Diagnostics Implementation Prompt

```text
Continue from repository truth. Do not recover old tasks.

Read first:
- AGENTS.md
- CONTEXT.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md
- docs/superpowers/plans/2026-07-15-worldbridge-inspector-diagnostics-implementation.md
- docs/mainline_status.md final Phase 6H section
- core/VitaLoom/inspector/schema.py
- core/VitaLoom/inspector/command_binding.py
- core/VitaLoom/docks/inspector.py
- core/VitaLoom/commands/runtime_commands.py

Phase 6H decision:
- A future Inspector diagnostics foldout is approved only as command-backed and read-only.
- Authority is runtime.worldbridge.component_projection_diagnostics.
- The diagnostics are runtime-wide, not selected-entity state.
- component_count: 0 must not be described as a selected entity having no components.
- No direct projection-builder import, edit binding, mutation command, live objects, or .pond writes.

Implement Phase 6I in order:
1. Write Headless tests for a Qt-free diagnostics view-model Adapter.
2. Implement the smallest Adapter behind a narrow Interface.
3. Add a tested Command Registry runner Seam.
4. Integrate a collapsed-by-default read-only Inspector foldout only if real PyQt6 UI verification is available.
5. Preserve normal Inspector fields and edit/undo behavior.
6. Update plan/status/prompt and close one Gate.

Current environment caveat:
- PyQt6 may be unavailable. If so, pure Adapter and command work may proceed, but the UI Gate remains incomplete and must not be claimed.
- Current worktree is an approximately 982-path migration snapshot. Do not stage, commit, reset, clean, revert, or delete unrelated work.

Start with:
python -B tools/audit_worktree_groups.py
python -B -m pytest -q -p no:cacheprovider tests/test_package_import_side_effects.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py
python -B tools/check_worldbridge_component_projection_diagnostics.py
```

