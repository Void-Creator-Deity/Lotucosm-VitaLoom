# VitaLoom Phase 6K SR Runtime Identity Snapshot Authority Prompt

```text
Phase 6K is complete. Do not rerun it as unfinished work.

Stable implementation:
- Qt-free core.VitaLoom.simulation.sr_runtime_snapshot_authority.SrRuntimeSnapshotAuthority
- opaque SR runtime epochs and stale-before-missing query semantics
- strict JSON/copy isolation and full snapshot replacement
- GameViewport lifecycle Adapter for start/reload/pause-resume/stop/discard
- explicit serialized_scene_counterpart handling
- per-frame and empty-runtime snapshot publication
- existing runtime.worldbridge.component_projection_diagnostics remains runtime-wide with {} input

Verified on 2026-07-16:
- Authority + Adapter + GameViewport + Phase 6I/WorldBridge/Inspector combined regression: 79 passed in 1.43s
- core boundaries OK
- release consistency OK
- git diff --check exited 0 with existing line-ending warnings only
- pre-closure worktree audit: 986 dirty paths

Command decision:
- No SR query command was added because opaque epoch discovery and editor-selection correlation do not yet have a formal Interface.
- Do not expose a shallow command that requires callers to know an undiscoverable epoch.

Unique next Gate: Phase 6L — SR selected-identity acquisition and selection-correlation Interface decision/implementation.

Read first:
- AGENTS.md
- CONTEXT.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-16-worldbridge-selected-entity-diagnostics-authority-decision.md
- docs/superpowers/plans/2026-07-16-sr-runtime-identity-snapshot-authority.md (Completion Record)
- docs/mainline_status.md (final Phase 6K section)
- docs/runtime_unification_roadmap.md (final Phase 6K note)
- core/VitaLoom/simulation/sr_runtime_snapshot_authority.py
- core/VitaLoom/simulation/sr_host.py
- core/VitaLoom/viewports/game_viewport.py
- core/VitaLoom/core/editor_context.py
- core/VitaLoom/viewports/scene_viewport.py
- core/VitaLoom/inspector/worldbridge_diagnostics.py

Phase 6L requirements:
1. Audit the worktree first and preserve all unrelated migration work.
2. Trace the actual editor selection identity from SceneViewport/Hierarchy through EditorContext into Inspector.
3. Decide whether a selected .pond entity can be truthfully correlated to the active SR epoch without exporting QWidget, QObject, Node wrappers, live _SceneRuntimeEntity objects, or mutable registries.
4. Prefer one Qt-free Adapter with a narrow JSON-only Interface and deterministic unavailable/not_running/stale/missing/unsupported_track/invalid_identity/error states.
5. Preserve separation: .pond edit identity is scene_path + entity_id; SR live identity is runtime_epoch + runtime entity_id. Correlation is not unified identity.
6. Apply the deletion test: the Adapter must concentrate selection normalization, track/lifetime validation, scene correlation, and error semantics.
7. Write failing Headless tests before implementation. Add a real SR-specific read-only Command Registry Interface only if the identity acquisition Interface is usable and deep.
8. Do not extend the existing runtime-wide diagnostics command, add selected component mapping, mutate Inspector/.pond, create PS authority, or claim unified SR/PS identity.
9. Close the phase with focused tests, Phase 6K/6I regression, architecture/release checks, diff check, worktree audit, status/roadmap/plan/prompt updates, and exactly one next Gate.

First command: .\.venv\python.exe -B tools/audit_worktree_groups.py
```
