# Phase 7C Closure / Phase 7D Handoff Prompt

**Date:** 2026-07-16

**Closed Gate:** Phase 7C — dependency-aware asset reference migration and undo Authority

**Unique next Gate:** Phase 7D — asset transaction recovery resolution and operator-control Authority

## Stable architecture to preserve

- The VitaLoom runtime remains plugin-shaped at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`; keep the PyQt6 editor shell, QPainter default viewport, and OpenGL opt-in only.
- `asset_index.py` owns immutable current filesystem/dependency/provenance/export facts. `asset_registry.py` owns project-local persistent identity/tombstone/revision facts. Neither is a substitute for transaction recovery policy.
- `asset_reference_transaction.py` is the Qt-free Authority for reference-impact plans, structured write tokens, journal/backup receipts, guarded rename/delete apply, compensation, undo/redo, and recovery-required diagnostics. It must not import PyQt, ProjectManager, editor globals, or Command Registry.
- Commands are Adapters: `asset.rename`, `asset.delete`, `asset.transaction.undo`, and `asset.transaction.redo` share the transaction Module; generic and durable project undo replay their receipts.
- Keep `.pond`, project/package manifests, lock semantics, Inspector command binding, SR2D seams, Player export, CLI/MCP compatibility, and external/missing/invalid/malformed reference truth unchanged.
- Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated existing worktree changes.

## Phase 7C closure evidence

- Rename rewrites only canonical source matches and preserves project-relative, scene-relative, `active_scene`, and representable script shorthand styles. A non-representable script target blocks rather than guessing.
- Referenced single-file delete remains a deterministic hard block with explicit `blocked_references`; unreferenced delete records a private backup, produces a tombstone, and restores the same persistent ID only under verified Registry restore hints.
- Undo/redo digest guards reject user-recreated source/target/owner paths instead of overwriting them. Injected rename-owner-write and delete-Registry-refresh failures compensate to truthful current files and leave an explicit recovery-required journal.
- Project open reports, but does not automatically mutate, incomplete transaction journals. Transaction journals and backups stay outside Index inventory/export closure/Player payload.
- Verification: Phase 7C targeted regression **95 passed in 43.20 s**; focused transaction/command/CLI/MCP/tools regression **57 passed in 40.94 s**. Core/GUI/release checks, runtime import smoke, and diff check passed.
- Scale evidence at 1,000 assets / 20 scenes / 400 edges: rename plan **906.2123 ms**, apply **5,800.7294 ms**, undo **807.7566 ms**, redo **700.5388 ms**; unreferenced delete plan **936.2825 ms**, apply **1,847.7726 ms**, undo **1,006.6926 ms**, redo **1,107.6256 ms**. Export remained ready after redo and transaction metadata remained absent from export. These are one-run machine-local measurements, not performance guarantees.

## Start Phase 7D in this order

1. Read `docs/superpowers/plans/2026-07-16-asset-transaction-recovery-resolution-and-operator-control-authority.md` and audit current journal state/write transitions before changing behavior.
2. Establish red tests for journal classification and current-file digest permutations. Inspection must be JSON-only and non-mutating.
3. Specify a closed recovery action vocabulary and state/action matrix. Do not begin UI work or automatic recovery before every action has concrete digest preconditions and a conflict result.
4. Implement recovery inspection/planning in the existing Qt-free transaction Module. Add guarded resolution only for states whose compensation/Registry effects are proved.
5. Expose the same facts through ProjectManager diagnostics, Command Registry, CLI, and MCP; any UI follows those Adapters and must not parse journals itself.
6. Close with project-open/export/Index/Registry/command/CLI/MCP regression, fault injection, boundaries/release/import/diff proof, then update status/roadmap/index/prompt and name exactly one next gate.

## Explicit non-goals until separately planned

- Referenced-delete replacement/removal migration, recursive folders, automatic recovery, watchers/hot reload/background indexers, or cross-process locks.
- Generic undo for arbitrary external filesystem changes or an unproved UI conflict workflow.
- Unity/Godot/Electron migration, OpenGL default readiness, or native acceleration completion.
