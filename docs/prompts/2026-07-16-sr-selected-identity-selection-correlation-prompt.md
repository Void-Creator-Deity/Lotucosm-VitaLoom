# VitaLoom Phase 6M PS Runtime Identity Authority Prompt

```text
Phase 6L is complete. Do not rerun SR selected-identity correlation as unfinished work.

Stable implementation:
- Qt-free SrRuntimeSnapshotAuthority with opaque epochs and stale-before-missing semantics
- GUI-side project_editor_selection(...) Adapter for trustworthy Node/Hierarchy selections
- Qt-free SrSelectedIdentityCorrelation with scene_correlated_not_unified identity semantics
- independent ISrSelectedIdentityHost / SR_SELECTED_IDENTITY_HOST Seam; ISimulationSrHost was not widened
- GameViewport selected-SR Adapter backed by the Phase 6K Authority
- runtime.sr.selected_entity_snapshot: read-only, JSON-only, Headless-safe; {} discovers current selection and optional identity proves stale queries
- runtime.worldbridge.component_projection_diagnostics remains runtime-wide with {} input and is unchanged

Verified on 2026-07-16:
- focused Phase 6L + Phase 6K regression: 50 passed in 1.29s
- expanded SR/WorldBridge/Inspector/schema/binding regression: 103 passed in 2.27s
- core boundaries OK
- release consistency OK
- git diff --check exited 0 with existing line-ending warnings only
- protected worktree audit: 990 dirty paths

Unique active Gate: Phase 6M — PS run/organism runtime identity snapshot Authority decision/implementation.

Read first:
- AGENTS.md
- CONTEXT.md
- docs/adr/0005-unified-pond-bridge.md
- docs/superpowers/plans/2026-07-16-worldbridge-selected-entity-diagnostics-authority-decision.md
- docs/superpowers/plans/2026-07-16-sr-runtime-identity-snapshot-authority.md (Completion Record)
- docs/superpowers/plans/2026-07-16-sr-selected-identity-selection-correlation.md (Completion Record)
- docs/mainline_status.md (final Phase 6L section)
- docs/runtime_unification_roadmap.md (final Phase 6L note)
- builtin/systems/ps_experiment_runner.py
- core/VitaLoom/simulation/ps_experiment_service.py
- core/Lotucosm/pond.py
- builtin/entity_types/organism.py
- builtin/entity_types/intelligent_organism.py
- core/Lotucosm/runtime/ecology_observation.py
- core/VitaLoom/simulation/simulation_coordinator.py

Audited starting facts:
- PS live organisms are owned by Pond.organisms inside one runner/Pond lifetime.
- PsExperimentRunner constructs or receives the Pond locally and exposes aggregate progress/summary snapshots, not a live organism identity Interface.
- PsExperimentService is PyQt-bound and supports sync and async runs, but currently has no formal opaque run_id or service-visible organism snapshot authority.
- Existing historical run directories/summary.json files are persisted experiment results, not proof of a currently live PS object lifetime.
- Future PS identity is run_id + organism_id. A bare organism_id is insufficient, and SR runtime_epoch must never be reused as a PS lifetime token.

Phase 6M requirements:
1. Preserve all unrelated migration work; do not stage, commit, reset, clean, revert, delete, or reorganize it.
2. First write docs/superpowers/plans/<date>-ps-runtime-identity-snapshot-authority.md. Audit sync run, async worker, unified-bridge run, cancellation, finish, error, restart, and runner/Pond ownership before choosing the Adapter seam.
3. Decide whether one truthful Authority can cover both run_sync and run_async without exposing Pond, Organism, QThread, QObject, callbacks, or mutable registries. If not, record the exact blocker, fallback, unblock path, and one next Gate instead of faking completeness.
4. If implemented, prefer a Qt-free deep Module such as PsRuntimeSnapshotAuthority with an opaque authority-issued run_id, complete snapshot replacement, strict scalar/JSON whitelist, copy isolation, explicit errors, and stale-before-missing ordering.
5. Lock lifecycle semantics before code: when run_id begins, whether it remains queryable after normal finish, and exactly when cancel/error/restart/end invalidate it. Do not infer this from timestamps or output directory names.
6. The mutable Pond/runner remains the Implementation owner. Any service/worker integration must be a narrow Adapter; do not move the product runtime out of FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime.
7. Test Headless import with PyQt6 blocked for the Authority Module. Test same organism_id across replacement runs, complete replacement after extinction, empty population publication, malformed identity, unsupported track, JSON/copy isolation, and lifecycle ordering.
8. Do not add a PS selected-entity command unless a separate later Gate proves trustworthy selection/discovery without caller knowledge of run_id. Phase 6M is the run/organism Authority Gate, not cross-track selection correlation.
9. Do not modify runtime.sr.selected_entity_snapshot, runtime.worldbridge.component_projection_diagnostics, Inspector binding, .pond semantics, SR2D Adapter seams, manifests, PyQt6/QPainter defaults, or the opt-in OpenGL path.
10. Never claim SR↔PS unified identity, selected WorldBridge component mapping, Inspector selected-entity UI, mutation, .pond writeback, tick merge, unified Pond default-readiness, native acceleration completion, or OpenGL default-readiness.
11. Close the phase with focused tests, relevant PS runner/service regressions, core/release checks, diff check, worktree audit, status/roadmap/plan/prompt updates, and exactly one next Gate.

First action:
.\.venv\python.exe -B tools/audit_worktree_groups.py
Then audit the real runner/service/Pond lifecycle and write the Phase 6M plan plus Qt-free failing tests before changing runtime code.
```