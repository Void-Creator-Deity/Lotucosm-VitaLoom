# VitaLoom Phase 7E closure / Phase 7F fresh-session handoff

> **架构状态：已由 2026-07-18 的引擎大插件 Host 架构裁定取代。** 本文件仅保留该历史 GUI 阶段的实施记录；不得据此把 PyQt6/QPainter/OpenGL 视为 L0/L1 架构前提。当前协作约束见 `AGENTS.md`、`CONTEXT.md`、`docs/architecture.md` 与 `docs/prompts/2026-07-18-engine-plugin-host-architecture-reconciliation-prompt.md`。

## Current date and Gate

This handoff was closed on **2026-07-17**. Phase 7E is complete. The sole next Gate is **Phase 7F ? referenced single-file asset replacement transaction Authority**. Do not start a different Gate or claim that all project modernization is complete.

## Stable Phase 7E facts

- Keep the plugin runtime boundary: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Keep PyQt6 as the editor shell, QPainter default viewport, and OpenGL opt-in only. Do not migrate app shells.
- `asset_index.py` remains filesystem/dependency/provenance/export fact Authority; `asset_registry.py` remains persistent ID/tombstone Authority; `asset_reference_transaction.py` owns policy now and any future verified transaction Authority.
- `analyze_asset_retirement_policy(project_root, *, source_path, replacement_path=None)` is stable, Qt-free, JSON-only, deterministic, and strictly read-only.
- Result states: `replacement_candidate`, `unreferenced_delete_available`, `refused`.
- `replacement_candidate` only means current facts are compatible with a possible future Gate. It is not a durable plan, receipt, mutation permit, or semantic-compatibility proof.
- `asset.retirement.analyze` is a thin `mutates=False` command. CLI and MCP discover it through the existing registry.
- Referenced `asset.delete` remains hard-blocked with `asset_references_blocking`; do not bypass, weaken, or reinterpret it.
- Remove-without-replacement remains refused; folders, automatic removals, UI flow, watcher/hot reload/background indexing, cross-process locking, and generic external filesystem undo are not implemented.

## Phase 7E evidence

- Policy Authority tests: `7 passed in 0.86 s`.
- Focused Registry/CLI/MCP discovery/command tests: `4 passed in 0.69 s`.
- Larger transaction/Registry/Index/recovery/command set: `49 passed in 9.48 s`, followed by one environment-only Player import failure because active Python 3.13 has no PyQt6.
- 1,000 assets / 20 scenes / 400 edges: analysis `2,152.2431 ms`, deterministic, export remained ready, Registry was not created, transaction metadata was absent.
- Core/GUI/release checks passed. Compileall passed only with a temporary `PYTHONPYCACHEPREFIX` because repository pycache files are locked. `git diff --check` passed with pre-existing LF/CRLF warnings.
- `.venv` has package scripts but no `python.exe`; do not hide an environment rebuild in source changes. The unblock path for Player/full GUI evidence is a Python 3.11+ environment with PyQt6, then rerun existing tests.

## Phase 7F start protocol

1. First write a new Phase 7F plan under `docs/superpowers/plans/`; do not mutate source before red tests define the contract.
2. Start from a narrow single-file replacement question only. Define whether source bytes are unlinked, retained, or otherwise disposed; define Registry tombstone/identity policy. Do not assume that a Phase 7E candidate answers those questions.
3. Any apply path must freshly re-read/revalidate source, replacement, all owner digest/current facts, canonical locations, Index/export facts, and Registry state. Never trust a stale analysis result as permission.
4. Red tests must prove atomic owner/asset/Registry effects; conflict refusal/no overwrite; reference-style preservation; undo/redo/recovery behavior; export/index parity; and no transaction metadata in export.
5. Keep mutation authority inside `asset_reference_transaction.py`; commands/UI/CLI/MCP must be thin Adapters. Do not add a second parser, Registry refresh side effect, UI replacement wizard, remove-only behavior, or folder recursion.
6. Close Phase 7F with tests/checks/benchmark evidence, update `docs/mainline_status.md`, roadmap, INDEX, and a fresh-session prompt, then name exactly one next Gate.

## Worktree hygiene

The working tree contains extensive pre-existing migration work and `.history` removals. Treat it as user/prior work: do not stage, commit, reset, clean, revert, or delete unrelated changes. Do not use subagents for this project.
