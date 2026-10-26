# Phase 7B ? Persistent Asset Identity, Mutation Refresh, and Incremental Cache Authority

**Date:** 2026-07-16  
**Status:** complete  
**Previous Gate:** Phase 7 ? Project Asset Index, Export Readiness, and Project-Scale Authority  
**Architecture focus:** add a project-local persistent asset Registry as the Authority for stable file identity and truthful incremental refresh evidence, while leaving the Phase 7 Asset Index as the Authority for current filesystem/dependency/export facts.

## 1. Gate objective

Phase 7 deliberately established a fresh, immutable Asset Index snapshot. Its `id == path` rule is correct for a current filesystem fact but cannot preserve identity across rename, distinguish delete from absence, or prove reuse of unchanged content digests.

This Gate introduces one Qt-free deep Module:

```text
core/VitaLoom/project/asset_registry.py
```

Its public Interfaces remain small:

```python
load_project_asset_registry(project_root)
refresh_project_asset_registry(project_root)
```

The Registry owns persistent IDs, active-path mapping, tombstones, deterministic registry revisions, atomic writes, changed-file/cache evidence, and refresh diagnostics. `asset_index.py` continues to own complete current file/dependency/provenance/export facts. Neither Module may import PyQt, `ProjectManager`, editor globals, or Command Registry objects.

The Gate closes only when:

- every indexed project file can be projected with a stable persistent `asset_id` after explicit Registry refresh;
- no-change refresh does not change Registry revision and proves digest reuse rather than claiming a full scan is incremental;
- content modification keeps identity but updates digest/revision; deletion produces a tombstone; recreation at the same path with different content receives a new identity;
- an explicit command rename preserves identity; an external rename is recognized only when one digest-based match is unique, otherwise the output reports ambiguity and does not fabricate continuity;
- `asset.create`, `asset.import`, explicit `asset.refresh`, project open, and editor-side create/import/delete flows refresh through the same Authority seam;
- full Asset Index facts and Registry-supported projection have parity for inventory identity/digests/dependencies/export readiness;
- Registry metadata neither changes Phase 7 asset counts/closure nor enters Player export payload;
- project-scale evidence separates cold index build, unchanged refresh, one-file mutation refresh, cache hits/misses, and parity. It makes no watcher, hot-reload, or content-proof-over-metadata claim.

## 2. Previous Gate summary

Phase 7 consolidated three repeated dependency/export scanners into `asset_index.py`, a deterministic Qt-free current-facts Authority. Commands, legacy dependency adapters, provenance tooling, export preparation, and real Player export now share canonical relative paths, digests, JSON pointer diagnostics, containment truth, malformed-scene truth, and export readiness.

The Phase 7 scale baseline was `1,000` assets / `1,021` indexed files / `400` edges: cold build `4,146.483 ms`, same-content full rebuild `891.873 ms`, projection `0.309 ms`. It explicitly did **not** claim incremental caching.

## 3. Starting audit and boundary decision

### 3.1 Current mutation seams

- `runtime_commands.py` has `asset.create`, `asset.import`, and `asset.apply_to_scene`; create/import write project files but currently return only path/digest facts.
- There is no `asset.rename`, `asset.delete`, or `asset.refresh` Command.
- `ProjectManager.open_project()` is the live editor lifecycle seam after `current_project_path` is set and before final browser refresh.
- `SceneManager.create_scene()` creates `.pond` files independently; its caller must converge through an explicit refresh Adapter rather than making the deep Registry import Qt.

### 3.2 Existing bypasses that must not remain invisible

- `docks/library_browser.py` imports with `shutil.copy2` and deletes with filesystem calls.
- `viewports/scene_viewport.py` copies external image drops straight into `assets/`.
- `builtin/editor_extensions/project_browser_plugin.py` still owns a legacy event-bus create implementation.

These are Adapter debt, not reasons to add Registry knowledge to Qt classes. The solution is to route them to shared mutation Commands or, where compatibility requires an event seam, explicitly invoke the same refresh Adapter after a successful write.

### 3.3 Registry location and export/index separation

The Registry will be project-local at:

```text
.vitaloom/asset_registry.json
```

Reasons:

- it travels with a project without modifying `project.json` or `project.lock.json`;
- it is outside `INDEXED_FOLDERS`, so it cannot self-invalidate the Asset Index;
- current Player export copies only `assets`, `scenes`, and `scripts`, so it stays editor metadata rather than runtime payload;
- it does not weaken manifests, `.pond` semantics, package manifests, or project manifests.

The Registry is durable metadata, not an asset and not an export Authority.

### 3.4 Identity and external-change rules

An active Registry entry stores `id`, canonical relative `path`, `bytes`, `mtime_ns`, `sha256`, `created_revision`, and `updated_revision`. A tombstone stores `id`, `last_path`, `last_sha256`, and `deleted_revision`.

- Fresh files receive opaque deterministic-format UUID IDs (`asset_<uuid4 hex>`); UUID creation happens only on a new persisted entry, so subsequent refresh output is stable.
- Explicit `asset.rename` performs the file rename then updates Registry path in the same refresh transaction. It returns the preserved ID. Scene references are **not** silently rewritten; a future reference-rewrite Gate must make that policy explicit.
- Explicit `asset.delete` is limited to project-contained files. It records tombstones. Recursive directory deletion is excluded from this Gate unless independently planned and proven.
- During an external refresh, a disappeared active entry and a new unregistered file are treated as a rename only if their SHA-256 match is unique on both sides. Identical-content ambiguity is surfaced in diagnostics and receives no guessed continuity.
- If a deleted path is recreated with different content, it receives a new active ID; tombstones remain historical evidence.

### 3.5 Incremental truth model

The Registry may reuse a stored digest only when `(path, bytes, mtime_ns)` match. This is a metadata-based cache optimization, not a proof that bytes are unchanged under every hostile filesystem clock scenario. The refresh result must expose counts for `cache_hits`, `cache_misses`, `changed_files`, new/deleted/renamed entries, and ambiguous rename candidates.

Every refresh still obtains the current Phase 7 Index snapshot for dependency/provenance/export truth. Registry projection must match it exactly for current indexed paths/digests; otherwise refresh fails explicitly rather than publishing a mixed Authority.

Persistence uses write-to-sibling-temp then `replace`; no partial registry file is accepted as success. A malformed registry returns an explicit recovery diagnostic and never claims prior stable IDs. Read-only scan commands remain pure and never create/update Registry files.

## 4. Implementation sequence (TDD)

1. **Red tests:** Add `test_project_asset_registry.py`, `test_asset_registry_command_integration.py`, and `test_asset_registry_incremental_parity.py` before implementation. Cover persistence, JSON-only output, no Qt/global imports, atomic persistence, no-change reuse, modified/deleted/recreated lifecycle, unique/ambiguous external rename, malformed-registry policy, Asset Index parity, and metadata isolation.
2. **Deep Module:** Implement Registry schema validation/load, initial registration, atomic write, refresh transaction, digest cache evidence, tombstones, unique external rename matching, and `asset_id` projection. Keep the complete current filesystem scan delegated to `build_project_asset_index` rather than cloning its path/dependency semantics.
3. **Index projection:** Add only additive identity/registry facts to Asset Index output through an explicit registry-supported projection path. Fresh `build_project_asset_index()` remains read-only and preserves its Phase 7 shape/semantics.
4. **Command adapters:** Add `asset.refresh`, `asset.rename`, and single-file `asset.delete`; refresh create/import success paths and return additive `asset_id`/`asset_registry_revision` fields. Preserve command envelope and existing fields.
5. **Editor adapters:** Converge project-browser create/import/delete and external image-drop import on shared Commands or their deliberate thin callers. Add open-project refresh after project context exists; surface refresh failures as diagnostics without pretending the open succeeded in Registry state.
6. **Evidence:** Run focused then broad tests, boundary/release/import checks, diff check, and `asset_index_scale` expanded with unchanged/one-file refresh timings. Record cache terms precisely.
7. **Documentation:** Close `docs/mainline_status.md`, roadmap, index, phase plan, and fresh-session prompt; name exactly one next Gate.

## 5. Non-goals and explicit deferrals

This Gate does not claim:

- filesystem watchers, automatic hot reload, background indexing, or cross-process locking;
- byte-level change proof when timestamp/size metadata is unchanged;
- automatic `.pond` reference rewrite on rename/delete;
- recursive folder identity/delete semantics;
- a Unity/Godot/Electron migration, OpenGL default readiness, native acceleration completion, or any altered `.pond`/manifest contract.

## 6. Verification matrix

| Claim | Required proof |
| --- | --- |
| persistent identity | initial/second refresh IDs equal; reopen/load remains equal |
| no-change cache | Registry revision stable; digest spy shows cache hit rather than rehash |
| lifecycle | modify preserves ID; delete tombstones; same-path different-content recreate gets new ID |
| rename correctness | explicit rename preserves ID; unique external rename preserves ID; duplicate-content ambiguity is explicit |
| current-facts parity | full Index and Registry projection have identical paths/digests/dependencies/export readiness |
| isolation | Registry file absent from inventory/assets/export closure/Player export payload |
| architecture | no PyQt/ProjectManager/global-editor/Command Registry imports in deep Module |
| UI/command convergence | command integration and targeted editor seam tests prove refresh calls |
| scale | cold build + unchanged refresh + one-file mutation refresh; hit/miss/changed count/parity recorded |

## 7. Completion record

Implemented the Qt-free persistent identity Authority at `core/VitaLoom/project/asset_registry.py`, while preserving `asset_index.py` as the current filesystem/dependency/provenance/export-facts Authority. The Registry persists JSON only at `<project>/.vitaloom/asset_registry.json`; it owns opaque persistent IDs, generation/revision, active entries, tombstones, metadata digest-cache evidence, atomic replacement, malformed-registry recovery, unique external-rename inference, ambiguity diagnostics, and Registry-supported index projection.

Adapters now converge through the Authority: `asset.refresh`, `asset.rename`, and `asset.delete` were added; successful `asset.create` and `asset.import` return additive Registry identity/revision fields; project open refreshes before the final browser refresh; the library browser and external image-drop path use Commands instead of direct copy/delete writes. `asset.scan` stays a pure read and does not create Registry metadata. Explicit rename/delete preserve the existing `.pond` contract: references are **not** silently rewritten, file deletion is single-file only, and folder-recursive mutation remains excluded.

TDD and targeted integration evidence: the Registry/index/command/project-open/export/dependency/CLI/MCP/tool suite passed **95 tests in 33.12 s**. After the final SceneViewport command-bridge extraction, its targeted regression set passed **9 tests in 0.60 s**. Coverage includes persistence, cache-hit proof, modification/recreation/tombstones, unique versus ambiguous external renames, malformed recovery, projection parity, atomic-write hygiene, command integration, pure-read scan behavior, project-open refresh, and external drag/drop command convergence.

Project-scale proof used 1,000 assets / 1,021 indexed files / 400 dependency edges: cold index build **5,339.0366 ms**; full rebuild **1,445.4629 ms**; Registry cold refresh **1,352.7249 ms**; unchanged refresh **713.6772 ms**; one-file refresh **648.9053 ms**; projection **0.1791 ms**. The unchanged refresh reported **1,021 hits / 0 misses**; the one-file refresh **1,020 hits / 1 miss**; projection parity was true. This is deliberately only a `(path, bytes, mtime_ns)` metadata digest-reuse claim. It is not watcher, hot-reload, background-indexing, cross-process-locking, or byte-level proof when those metadata values do not change.

Boundary, GUI-boundary, release-consistency, syntax/import-smoke, and diff checks passed. No files were staged, committed, reverted, deleted, or cleaned.

## 8. Unique next Gate

**Phase 7C — dependency-aware asset rename/delete reference migration and undo Authority.**

This Gate must first audit `.pond` JSON-pointer rewrite coverage, missing-reference diagnostics, inverse/undo records, cross-file atomicity and recovery, folder semantics, and export implications. It must not silently extend the Phase 7B file-only mutations or claim watcher/hot-reload behavior.
