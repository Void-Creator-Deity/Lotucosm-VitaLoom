# Phase 7B Closure / Phase 7C Handoff Prompt

**Date:** 2026-07-16  

**Closed Gate:** Phase 7B — persistent asset identity, mutation refresh, and incremental cache Authority  

**Unique next Gate:** Phase 7C — dependency-aware asset rename/delete reference migration and undo Authority

## Stable architecture to preserve

- Product runtime stays plugin-shaped at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`; keep PyQt6 editor shell, QPainter default viewport, and OpenGL opt-in only.

- `core/VitaLoom/project/asset_index.py` is the Qt-free Authority for immutable current filesystem/dependency/provenance/export-readiness facts.

- `core/VitaLoom/project/asset_registry.py` is the separate Qt-free Authority for project-local persistent IDs, active paths, tombstones, refresh revision/generation, metadata digest-cache evidence, and registry projection. It must not import PyQt, ProjectManager, editor globals, or Command Registry objects.

- Registry persistence is JSON-only at `<project>/.vitaloom/asset_registry.json`; it must remain outside indexed asset folders and Player export payload, and must not rewrite `project.json`, `project.lock.json`, package manifests, or `.pond` semantics.

- Preserve command registry flows, Inspector binding, SR2D seams, CLI/MCP compatibility, provenance distinctions, and the export rule that project-external/missing/invalid/malformed references keep `ready = false`.

- Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated migration work.

## Phase 7B closure evidence

- Registry behavior covers atomic persistence/recovery, stable opaque ID, tombstone, same-path recreation, explicit rename continuity, unique external SHA-256 rename continuity, explicit ambiguity for duplicate content, and Index/projection parity.

- Commands: `asset.refresh`, `asset.rename`, `asset.delete`; `asset.create` and `asset.import` add `asset_id`, Registry revision, and generation. `asset.scan` stays a pure read.

- Project-open refresh and editor import/delete/image-drop paths converge through the command/refresh Adapter.

- Targeted Registry/index/command/project-open/export/dependency/CLI/MCP/tool regression: **95 passed in 33.12 s**; final SceneViewport bridge regression: **9 passed in 0.60 s**.

- Scale proof: 1,000 assets / 1,021 files / 400 edges; cold index **5,339.0366 ms**, full rebuild **1,445.4629 ms**, Registry cold refresh **1,352.7249 ms**, unchanged refresh **713.6772 ms**, one-file refresh **648.9053 ms**, projection **0.1791 ms**; unchanged cache **1,021 hits / 0 misses**, one-file cache **1,020 hits / 1 miss**, projection parity true.

- The cache is only `(path, bytes, mtime_ns)` digest reuse. Do not claim a watcher, hot reload, background indexing, cross-process coordination, or byte-level content proof when metadata does not change.

## Start Phase 7C in this order

1. **Write the Phase 7C plan first** under `docs/superpowers/plans/`. Audit all `.pond` asset reference shapes/JSON pointers and the existing dependency diagnostics before changing rename/delete behavior.

2. Define a single Qt-free transaction/plan Authority that computes impact and a reversible mutation record. It may consume the Index and Registry snapshots but must not put mutation semantics in PyQt widgets.

3. Make the policy explicit before writes: rename rewrite scope, delete policy (block/allow with diagnostics), missing-reference truth, undo/redo payload/retention, crash recovery/cross-file atomicity, folder semantics, and export readiness after a failed/partial operation.

4. Establish red tests for multi-scene reference rewrite, ambiguous/non-rewritable references, cancellation/no-op, failed persistence recovery, undo/redo, and registry/index/export parity. Implement only the planned smallest transaction.

5. Converge Commands and visible editor mutation seams through that transaction. Do not silently add recursive folder deletion or reference rewrite to existing Phase 7B commands.

6. Close the Gate with targeted regressions, export smoke, command/CLI/MCP parity where applicable, core/GUI/release checks, diff check, status/roadmap/index/prompt updates, and exactly one next Gate.

## Explicit non-goals until directly proven

- Filesystem watcher/hot reload/import daemon/background indexing.

- Generic global undo across unrelated editor/runtime systems.

- Recursive folder deletion/rename policy without a dedicated semantic design and proof.

- Unity/Godot/Electron migration, OpenGL default readiness, or native acceleration completion.
