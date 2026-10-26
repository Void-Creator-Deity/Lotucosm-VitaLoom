# Phase 7 Closure / Phase 7B Handoff Prompt

**Date:** 2026-07-16  
**Closed Gate:** Phase 7 — project asset index, export readiness, and project-scale Authority  
**Unique next Gate:** Phase 7B — persistent asset identity, mutation refresh, and incremental index/cache Authority

## Stable state to preserve

- Product runtime remains under `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Keep the five-layer plugin-shaped architecture, PyQt6 editor shell, QPainter default viewport, and opt-in OpenGL path.
- `core/VitaLoom/project/asset_index.py` is the Qt-free Authority for immutable project asset-index snapshots.
- Preserve `.pond`, Command Registry, Inspector binding, SR2D Adapter, package/project manifests, locks, CLI/MCP, and Player export seams.
- Preserve legacy fields for `asset.scan`, `asset.dependencies`, `asset.validate`, `asset.export_closure`, and `export.player.prepare`.
- Outside-project, invalid, missing, and malformed-scene states remain distinct; all blocking states must keep export `ready = false`.
- Provenance correlation may expose only manifest-proven facts.
- Current scale evidence is full rebuild, not incremental cache.
- Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated migration work.

## Phase 7 evidence

- Red collection on missing asset-index Module; focused index `8 passed`.
- Red Command integration `3 failed`; final index/Command/legacy focused suite `21 passed`.
- Final asset/export/Command/CLI/MCP/tool suite `78 passed in 27.20s`.
- Synthetic 1,000 assets / 1,021 files / 20 scenes / 400 edges: cold `4,146.483 ms`, same-content full rebuild `891.873 ms`, projection `0.309 ms`, deterministic revision true, incremental cache false.
- Core/GUI boundaries, release consistency, compile/import, and diff checks passed. Protected worktree total `1002`, net `+3`.

## Start Phase 7B this way

Audit all asset mutation paths (`asset.create`, `asset.import`, file rename/delete, project open/reload, export) and decide the persistent identity and cache ownership model before implementing. The next deep Module must define how stable identity survives rename, how revisions and tombstones behave, how full rebuild and incremental refresh prove parity, and where cache files live without rewriting package/project manifests or exposing live editor objects. Write the Phase 7B plan first, establish red parity and invalidation tests, then implement one mutation-refresh Gate.

Do not claim watcher/hot reload, persistent GUID parity, importer-daemon completion, or commercial-engine Asset Database completion without direct evidence.

