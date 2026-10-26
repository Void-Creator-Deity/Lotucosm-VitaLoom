# VitaLoom Phase 7H closure / Phase 7I prune-execution handoff

**Date:** 2026-07-17

## Resume point

Phase 7H - durable asset transaction retention and operator-controlled pruning policy Authority - is complete. This does not mean assets, transaction cleanup, the whole product, native acceleration, or OpenGL are complete.

Keep the plugin-shaped runtime boundary at FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime. Preserve PyQt6 editor shell, QPainter default viewport, opt-in OpenGL, .pond semantics, manifests, Asset Index/Registry, SR2D seams, Player export, Command Registry, CLI, and MCP. Do not migrate to Unity, Godot, Unreal, Electron, or another shell.

## Stable Phase 7H facts

- analyze_asset_transaction_retention_policy is the Qt-free read-only Authority for durable transaction artifacts.
- It inventories every journal, private backup, and unknown transaction-root file in deterministic project-relative order and reuses Phase 7G strict recovery inspection.
- Recovery-required, malformed/unsupported/unknown, conflict, and unrecognized receipts are protected. Valid terminal receipts are retained. Linked backups retain/protect with their journals. Orphan backups and unknown artifacts are not_prunable because provenance is unproven.
- Every row exposes disposition, reasons, digest facts where readable, and safe_prune false. prune_authorized is false. review_candidates and safe_prune_candidates are empty by design.
- asset.transaction.retention.analyze is a thin mutates-false command adapter. It adds no UI or cleanup write path.

## Evidence

- Focused asset transaction/recovery/command/CLI/MCP/Index/Registry suite: 74 passed in 16.84s.
- New policy tests prove no-write empty root, terminal receipt retention, recovery/malformed protection, linked delete backup retention, orphan/unknown non-prunability, deterministic ordering, and direct command/Authority parity.
- Core/GUI/release boundary checks and temporary-pycache compileall passed.
- Player smoke remains 1 failed, 2 passed on Friday, July 17, 2026 solely because active Python 3.13 lacks PyQt6 after export creation. Do not mask it. Restore supported Python plus PyQt6, then rerun Player/full GUI/CLI/MCP evidence.

## Unique next Gate: Phase 7I - explicit operator-confirmed durable transaction artifact prune execution Authority

First write a Phase 7I plan, then red tests. It may add at most one explicit mutation Authority for deleting only artifacts that Phase 7H proves are policy-reviewable and that the operator names exactly. It must fresh-revalidate the artifact snapshot, journal/backup linkage, recovery status, receipt integrity, command audit/provenance references, and export/Index exclusions immediately before deletion. It must refuse every recovery-required, malformed, unknown, conflicted, active, undo/redo-needed, or unproven artifact. It must be durable, auditable, compensated if possible, and never delete a source asset, owner, Registry state, or unrelated artifact.

Do not create automatic cleanup, age-only pruning, bulk deletion, UI cleanup wizard, folder/import/copy/remove-only behaviors, watcher/hot reload, cross-process locking, semantic conversion, native completion, or OpenGL default readiness. After the gate, prove no-write refusals/atomicity/recovery, update status/roadmap/INDEX, and name exactly one next Gate. Do not stage, commit, reset, clean, revert, or delete unrelated existing worktree files.
