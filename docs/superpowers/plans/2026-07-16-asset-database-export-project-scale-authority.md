# Phase 7 — Project Asset Index, Export Readiness, and Project-Scale Authority

**Date:** 2026-07-16  
**Status:** complete  
**Previous Gate:** Phase 6P — Command-backed selected-SR component projection Inspector integration  
**Architecture focus:** establish one deep, Qt-free project asset-index Module as the Authority for deterministic inventory, scene dependency diagnostics, export readiness, provenance correlation, and project-scale evidence while preserving existing Command Interfaces

## 1. Gate objective

Replace the current collection of repeated full-tree scanners with one immutable project asset-index snapshot Interface inside the VitaLoom product runtime.

This Gate does not claim a complete commercial-engine Asset Database. It establishes the first truthful Authority layer that later incremental import, rename preservation, cache persistence, and hot reload can deepen without keeping dependency semantics scattered across Commands, editor extensions, deletion checks, provenance tooling, and export preparation.

The Gate closes only when:

- one deterministic index snapshot owns canonical project-relative identity, file metadata, content digests, dependency edges, path containment diagnostics, malformed-scene diagnostics, and provenance correlation;
- `asset.scan`, `asset.dependencies`, `asset.validate`, `asset.export_closure`, and `export.player.prepare` consume that Authority through thin Adapters;
- a project-external absolute or traversal reference is not treated as an existing exportable dependency and cannot produce `ready = true`;
- legacy Command result fields remain compatible;
- synthetic project-scale evidence distinguishes build cost from view/projection cost and records an explicit baseline.

## 2. Previous Gate summary

Phase 6P completed the selected-SR read-only Inspector path:

- `runtime.sr.selected_entity_component_projection` remains the Command Authority;
- a Qt-free presentation Module validates strict JSON and SR identity/projection guardrails;
- exactly one editor selection loads an independent read-only foldout;
- ordinary Inspector properties and runtime-wide WorldBridge diagnostics remain compatible;
- broad Inspector/SR/PS/Command/CLI/MCP regression passed;
- no component mutation, `.pond` writeback, PS/SR equivalence, native-acceleration completion, or OpenGL default-ready claim was made.

Its unique next Gate was the present asset database/export/project-scale Authority decision.

## 3. Starting audit

### 3.1 Repeated shallow Implementations

Asset dependency meaning is currently implemented at least three times:

1. `core/VitaLoom/project/asset_dependency.py`
   - scans scenes on each reference query;
   - imports global `ProjectManager` and editor i18n state inside the Implementation;
   - exposes absolute-path/boolean semantics;
   - does not maintain the declared dependency index as an Authority.
2. `builtin/editor_extensions/asset_dependency_scan.py`
   - preserves JSON pointers and raw/resolved references;
   - scans `project.json` plus every `.pond`;
   - explicitly has no persistent cache;
   - silently drops malformed scenes.
3. `core/VitaLoom/commands/runtime_commands.py`
   - has a separate `_collect_scene_dependencies()` Implementation;
   - emits project-relative targets but loses JSON pointers;
   - is separately reused by validate/export Commands.

Deletion test: deleting any one current scanner does not remove complexity; equivalent path parsing, scene walking, existence checks, and summary rules remain in the others. They are shallow Modules with weak locality.

### 3.2 No live Asset Database Authority

`asset.scan` currently performs `assets/**` traversal and returns only path, byte count, and suffix. There is no stable index schema, revision/fingerprint, deterministic content digest, dependency ownership, provenance correlation, cache evidence, rename semantics, deleted-asset semantics, or project-scale Gate.

`asset.import` copies one file and returns a SHA-256 digest, but cannot refresh an index Authority because none exists.

### 3.3 Export semantics and path safety

`_build_asset_export_closure()` currently hashes the complete project inventory on every call and separately invokes the Command-local dependency scanner. The result is an inventory plus dependency diagnostics, not a dependency-minimal closure.

A project-external absolute dependency can currently pass the dependency `exists` check because `project / absolute_path` resolves to the absolute path. The later export-file collector refuses to include that file, but `missing_total` can remain zero, allowing `ready = true` for a non-reproducible export. This is a correctness and Authority defect, not merely a performance concern.

### 3.4 Provenance is disconnected

`assets/manifest.json` and `tools/check_asset_provenance.py` provide a separate policy/check path. Current scan and export results do not correlate indexed assets with proven, missing, or invalid provenance records.

This Gate may correlate facts that the manifest actually proves. It must not invent origin, generator, license, or ownership values.

### 3.5 Starting verification evidence

Focused existing asset/export/Command/CLI/MCP/tool suite:

```text
1 failed, 64 passed in 30.48s
```

The failure is a pre-existing stale integration test that patches module-level `get_project_manager`; the current Implementation moved that import inside `get_asset_references()`. This is recorded as existing instability and must be resolved by the new explicit project-root/index Seam rather than by restoring hidden global coupling.

Current sample-only benchmarks:

```text
resource_scan, 5 repeats: mean 6.917 ms, min 1.530 ms, max 27.841 ms
asset_export_closure, 5 repeats: mean 14.229 ms, min 5.328 ms, max 48.313 ms
```

The sample had zero dependency edges and only two export files, so these numbers prove execution only; they do not prove project-scale behavior.

Protected worktree starting total:

```text
999 entries
```

The runtime migration tree is largely untracked. No status entry authorizes stage/commit/reset/clean/revert/delete or unrelated reconciliation.

## 4. Architecture decision

### 4.1 New deep Qt-free Module

Add:

```text
core/VitaLoom/project/asset_index.py
```

Primary public Interface:

```python
build_project_asset_index(project_root)
```

The returned value is a fresh JSON-only snapshot. The Interface owns:

- project-root validation and canonical resolution;
- deterministic project-relative file identity;
- supported project inventory discovery;
- byte count, suffix/kind, and SHA-256 metadata;
- stable snapshot fingerprint derived from semantic indexed facts rather than wall-clock time;
- `.pond` parsing and dependency extraction with JSON pointers;
- script-name and script-path normalization;
- project-root containment checks for absolute and relative references;
- distinct `missing`, `outside_project`, and `invalid` dependency states;
- explicit malformed-scene diagnostics;
- deterministic duplicate-edge handling and ordering;
- provenance-manifest parsing and correlation without fabricated facts;
- coverage/count summaries;
- export-readiness facts that distinguish missing, outside-project, invalid, malformed, and provenance warnings.

The index is an immutable snapshot by convention: callers receive fresh JSON data and Command Adapters must not expose shared mutable internal objects.

### 4.2 Authority and Adapter placement

The index Module is the Authority for project asset/index facts. Existing public Commands remain the seams visible to AI, CLI, MCP, Hub, and export preparation.

`runtime_commands.py` becomes a thin Adapter:

- `asset.scan` projects the index asset rows and preserves `project_path`, `assets`, and `asset_count`;
- `asset.dependencies` projects dependency edges and preserves existing missing fields while adding explicit outside/invalid/malformed facts;
- `asset.validate` reuses the same projection instead of rescanning;
- `asset.export_closure` reuses indexed file metadata/digests and preserves all existing closure fields;
- `export.player.prepare` derives readiness from the same closure plus the existing lock requirement.

The plugin manifest, package catalog, project manifest/lock resolution, and enabled-plugin logic remain in their existing Modules. The asset index does not absorb unrelated package management policy.

### 4.3 Compatibility fields

The following fields remain present with compatible types:

```text
asset.scan:
  project_path, assets, asset_count

asset.dependencies / asset.validate:
  project_path, total_edges, edges,
  missing_scripts, missing_assets,
  missing_total, missing_by_kind

asset.export_closure:
  project_path, files, file_count, file_metadata,
  dependency_edges,
  missing_scripts, missing_assets,
  missing_total, missing_by_kind,
  enabled_plugins, warnings, ready

export.player.prepare:
  project_path, project_lock, enabled_plugins,
  asset_dependencies, asset_export_closure, ready
```

Additive fields are allowed when they expose truthful index revision, outside-project references, malformed scenes, provenance coverage, or build evidence.

### 4.4 Locality and leverage

Locality improves because path canonicalization, dependency extraction, digest inventory, provenance correlation, and readiness rules have one Implementation and one test surface.

Leverage improves because Commands, editor dependency display, deletion checks, export tools, and future incremental refresh can consume a single snapshot schema instead of understanding scene traversal and path rules independently.

Deletion test after the change: deleting `asset_index.py` would force canonical identity, path-containment security, dependency JSON pointers, malformed-scene truthfulness, digests, provenance correlation, readiness, and scale fixtures back into several callers. The Module therefore earns its Interface.

## 5. TDD sequence

### 5.1 Qt-free index red tests

Create:

```text
tests/test_project_asset_index.py
```

Red tests must prove:

1. project-relative IDs and ordering are deterministic;
2. all returned values are JSON-only and independent across builds;
3. unchanged project content yields the same fingerprint;
4. changed file content changes file digest and index fingerprint;
5. absolute and traversal references outside the project are `outside_project` even when the target exists;
6. missing and outside-project counts are separate;
7. malformed `.pond` produces explicit diagnostics and blocks export readiness;
8. dependency edges preserve scene path, JSON pointer, kind, raw reference, canonical target when available, status, and existence;
9. duplicate references produce deterministic results;
10. provenance status is correlated from `assets/manifest.json` without invented fields;
11. the Module imports no PyQt, `ProjectManager`, editor context, Command Registry, or live editor objects.

### 5.2 Command integration red tests

Create:

```text
tests/test_asset_index_command_integration.py
```

Red tests must prove:

1. all five asset/export Commands use the new index Interface;
2. legacy output fields remain present;
3. one external existing dependency makes closure and player preparation not ready;
4. malformed scenes do not silently become dependency-free;
5. `asset.scan`, dependency validation, and export metadata agree on identity/digest facts;
6. CLI/MCP-visible Command result remains JSON-only.

### 5.3 Project-scale red tests and benchmark

Create:

```text
tests/test_asset_index_project_scale.py
```

Use deterministic synthetic fixtures rather than repository sample size. The first Gate should cover at least 1,000 assets and multiple scenes/references. Record:

- cold index build time;
- repeated full-build time;
- pure projection/view time from one built snapshot;
- file and edge counts;
- deterministic fingerprint agreement;
- a generous regression ceiling suitable for CI, not a marketing target.

Extend `tools/benchmark_engine.py` with an explicit synthetic asset-index case. Do not describe repeated full rebuilds as warm-cache or incremental refresh.

## 6. Implementation sequence

1. Add `asset_index.py` and make focused index tests green.
2. Adapt Command dependency/scan/export paths to one built snapshot per Command invocation.
3. Preserve compatibility fields and add explicit Authority diagnostics.
4. Redirect the editor dependency-scan Adapter and legacy reference manager only if this can be done without breaking their public seams; otherwise record them as the unique next Gate rather than adding another partial compatibility shim.
5. Add project-scale fixture/benchmark evidence.
6. Run focused and broad regressions, boundary/release checks, syntax/import smoke, and dirty-worktree audit.
7. Update status, roadmap, index, and fresh-session prompt with exactly one next Gate.

## 7. Verification Gate

Minimum closure evidence:

- focused index tests pass;
- focused Command integration tests pass;
- existing asset dependency, provenance, export-player, Command, CLI, and MCP tests pass;
- synthetic project-scale test and benchmark record truthful cold/full-build/projection timing;
- project-external existing dependencies block export readiness;
- malformed `.pond` files produce explicit diagnostics;
- legacy Command output fields remain compatible;
- `tools/check_core_boundaries.py` passes;
- `tools/check_gui_boundaries.py` passes if UI Adapter files change;
- `tools/check_release_consistency.py` passes;
- Python syntax/import smoke passes for changed runtime/tool files;
- UTF-8/replacement-character checks pass for changed files;
- `git diff --check` exits 0 apart from pre-existing line-ending warnings;
- final dirty-worktree count is recorded without stage/commit/reset/clean/revert/delete.

## 8. Non-goals

This phase does not add or claim:

- persistent GUID identity or rename preservation;
- filesystem watchers or hot reload;
- background importer workers;
- a binary/on-disk index cache;
- tombstone history;
- thumbnail generation/database;
- cloud asset registry;
- dependency-minimal package stripping;
- complete commercial-engine Asset Database parity;
- editor migration away from PyQt6/QPainter;
- package/project manifest rewrites;
- unified Pond default readiness;
- native acceleration completion;
- OpenGL default readiness.

## 9. Completion record

### 9.1 Implementation

- Added Qt-free `core/VitaLoom/project/asset_index.py` as the deep immutable-snapshot Module.
- The Module owns deterministic inventory, SHA-256 metadata, stable `index_revision`, `.pond` and active-scene dependency extraction, JSON pointers, containment checks, explicit missing/outside/invalid/malformed states, provenance correlation, coverage, and export readiness.
- `scene.validate`, `asset.scan`, `asset.dependencies`, `asset.validate`, `asset.export_closure`, and `export.player.prepare` now build and project the same Authority snapshot while preserving legacy fields.
- The legacy `AssetDependencyManager` and editor `asset_dependency_scan` remain compatible Adapters but no longer own separate traversal semantics.
- `tools/export_player.py` now refuses copying when the asset index is not export-ready and records index evidence in `export_manifest.json`.
- `tools/benchmark_engine.py` gained the explicit synthetic `asset_index_scale` case and states `incremental_cache_claimed = false`.

### 9.2 TDD and regression evidence

- Red index evidence: test collection failed because `core.VitaLoom.project.asset_index` did not exist.
- Index focused green: `8 passed in 0.49s`.
- Red Command integration: `3 failed`; existing Commands did not call the index, exposed no outside-project facts, and hid malformed scenes.
- Initial index + Command green: `11 passed in 0.59s`.
- Legacy Adapter convergence: final focused index/Command/legacy suite `21 passed in 0.88s`.
- Project-scale red: first 1,000-asset cold build exceeded the original 10-second ceiling at `14.376s`; removing redundant per-file `Path.resolve()` from known-contained inventory restored locality and the scale test passed in `5.43s` total.
- Final asset/export/Command/CLI/MCP/tool composition: `78 passed in 27.20s`.
- Core boundaries, GUI boundaries, release consistency, and Python compile/import checks passed.
- `git diff --check` exited 0 with pre-existing LF/CRLF warnings only.

### 9.3 Project-scale evidence

Synthetic fixture:

```text
1,000 assets
1,021 indexed project files
20 scenes
400 dependency edges
cold build: 4,146.483 ms
same-content full rebuild: 891.873 ms
snapshot projection: 0.309 ms
deterministic revision: true
incremental cache claimed: false
```

Sample-only post-change checks remained small and green:

```text
resource_scan mean 8.414 ms over 5 repeats
asset_export_closure mean 11.912 ms over 5 repeats
```

These sample figures are execution evidence, not project-scale proof; the synthetic case is the Phase 7 scale baseline.

### 9.4 Stable versus unfinished

Stable now:

- immutable deterministic project asset-index snapshots;
- canonical project-relative file identity and content digests;
- one dependency/readiness Authority across Commands, legacy editor Adapter, and export tool;
- explicit project-external and malformed-scene export blockers;
- provenance correlation without fabricated facts;
- truthful 1,000-asset cold/full-rebuild/projection evidence.

Still unfinished and not claimed:

- persistent GUID identity or rename preservation;
- on-disk cache, incremental refresh, watcher, hot reload, tombstones, or importer daemon;
- dependency-minimal package stripping;
- complete commercial-engine Asset Database parity;
- unified Pond, native acceleration, or OpenGL default readiness.

### 9.5 Worktree protection

The protected worktree moved from `999` to `1002` entries, net `+3`, exactly the three new test files. Runtime/tool/docs additions live under already-untracked aggregate paths. No stage, commit, reset, clean, revert, delete, or unrelated reorganization occurred.

## 10. Unique next Gate

**Phase 7B — persistent asset identity, mutation refresh, and incremental index/cache Authority.**

