# VitaLoom Phase 6J Selected-Entity WorldBridge Diagnostics Authority Decision Prompt

```text
Continue from repository truth. Phase 6I is complete; do not redo the runtime-wide diagnostics Adapter or Inspector foldout.

Read first:
- AGENTS.md
- CONTEXT.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-15-worldbridge-inspector-diagnostics-implementation.md (final Phase 6I-C evidence)
- docs/superpowers/plans/2026-07-16-worldbridge-selected-entity-diagnostics-authority-decision.md
- docs/mainline_status.md (final Phase 6I-C section)
- docs/runtime_unification_roadmap.md (final Phase 6I-C note)
- core/VitaLoom/inspector/worldbridge_diagnostics.py
- core/VitaLoom/docks/inspector.py
- tests/test_inspector_worldbridge_diagnostics.py
- tests/test_inspector_worldbridge_diagnostics_ui.py

Stable and complete:
- Runtime-wide authority command: runtime.worldbridge.component_projection_diagnostics with {}.
- Qt-free validation/view-model Adapter.
- Real PyQt6 read-only, collapsed-by-default Inspector foldout.
- Runtime scope, authority label, unavailable state, warnings, and component_count meaning.
- Ordinary Inspector properties and mutation bindings remain separate and intact.

Unique Gate: Phase 6J — selected-entity WorldBridge diagnostics authority/interface decision.

Decision-only rules:
1. Audit the worktree first; do not stage, commit, reset, clean, revert, delete, or reorganize unrelated migration work.
2. Trace the real identity/authority sources for .pond scene entities, SR runtime entities, PS organisms/runs, and WorldBridge projections.
3. Decide whether selected-entity diagnostics should remain unavailable, use a new command, or use track-specific read-only Interfaces.
4. Define exact JSON identifiers, scope labels, output claims, stale/missing error modes, and do-not-claim guardrails.
5. Do not pass QWidget/QObject/Python component objects across the Command Registry Seam.
6. Do not extend the current runtime-wide command unless semantic compatibility is proven.
7. Do not implement live component mapping, selected-entity command behavior, Inspector mutation, or .pond writes in this Gate.
8. Run the Phase 6I regression and architecture checks, update status/roadmap/plan/prompt, and name exactly one next Gate.

First command: .\.venv\python.exe -B tools/audit_worktree_groups.py
```