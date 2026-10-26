# VitaLoom Phase 7F closure / Phase 7G strict durable receipt validation handoff

**Date:** 2026-07-17

## Resume point

Phase 7F ? Referenced Single-File Asset Replacement Transaction Authority ? is complete. Do not present the whole product, asset lifecycle, native acceleration, or OpenGL path as complete.

The runtime boundary remains:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime
```

Keep the project plugin-shaped. Preserve the PyQt6 editor shell, QPainter default viewport, opt-in-only OpenGL near-term path, `.pond` semantics, Registry/Index, project/package manifests, SR2D seams, Player export, Command Registry, CLI, and MCP contracts. Do not migrate to Unity, Godot, Unreal, Electron, or another app shell.

## Stable Phase 7F facts

- `core/VitaLoom/project/asset_reference_transaction.py` owns the explicit `replace_referenced` operation.
- Eligible pairs are different, project-contained, existing, non-protected single files. The operation rewrites all current canonical/representable source references while preserving source reference style, privately backs up then unlinks the source, and refreshes the source Registry identity into a tombstone.
- Replacement bytes and Registry identity remain untouched. The operation is structural only; it must not infer semantic/content/type/behavior compatibility.
- Plans include `target_sha256`. Before applying, the Authority replans current replacement-reference facts and compares exact edits, blocked references, owner digests, source/replacement digests, and Registry facts. Any new live reference, malformed `.pond`, unrepresentable reference, changed file, or conflict refuses without mutation.
- Undo/redo guard source, replacement, owner, and private-backup facts. Recovery validation recognizes the operation and requires `target_path` plus `target_sha256`; recovery inspection treats a changed replacement digest as `terminal_conflict`, not `terminal_applied`.
- `asset.referenced.replace` in `commands/runtime_commands.py` is a thin `mutates=True`, `undoable=True` adapter. It is visible through existing CLI and MCP registry discovery. `commands/registry.py` includes the operation in generic and durable project audit undo/redo replay.
- Referenced `asset.delete` remains a hard block.

## Phase 7F evidence

Focused proof passed:

```text
63 passed in 11.07s
```

The suite covered retirement policy, Authority lifecycle, recovery, command integration and durable replay, Project Asset Index, incremental Registry parity, selected CLI list/describe checks, and MCP command discovery. Core/GUI/release boundary checks passed. Temporary-pycache `compileall` passed. The Phase 7F diff check passed.

Scale benchmark (`asset_reference_transaction_scale`, 1,000 assets / 20 scenes / 400 edges, one repeat):

```text
replace_referenced plan: 817.7104 ms
replace_referenced apply: 2336.8935 ms
replace_referenced undo: 1097.2144 ms
replace_referenced redo: 1099.8438 ms
replacement_bytes_unchanged: true
replacement_source_retired_after_redo: true
export_ready_after_redo: true
transaction_metadata_in_export: false
```

Known environment limitation: `python -B -m pytest -q -p no:cacheprovider tests/test_export_player_smoke.py` yielded `1 failed, 2 passed`, solely because current Python 3.13 has no `PyQt6`; export creation completed before the unchanged Player shell import failed. Do not change Player/tests to hide this. Unblock by restoring supported Python with PyQt6, then rerun Player/full GUI/CLI/MCP proof.

## Unique next Gate: Phase 7G ? strict durable asset transaction receipt validation

First write a Phase 7G plan under `docs/superpowers/plans/`, then add red tests before code changes. Audit the durable receipt pipeline end to end:

1. `_read_journal` and `_validate_recovery_journal`;
2. receipt construction at apply/undo/redo;
3. recovery inspection and list/resolver paths;
4. any file-record/base64 parsing and state classification;
5. durable command audit replay boundaries.

Required red cases include malformed JSON; missing required fields; unknown/wrong operation-specific fields; invalid base64 or file-record structures; invalid path/digest values; impossible state combinations; partial/truncated receipts; and receipts where durable state conflicts with current file facts. The safety expectation is a structured refusal/classification only: malformed receipts must not write owners, source, replacement, private backup, Registry, or journal state.

Keep valid legacy rename/delete receipts and valid Phase 7F `replace_referenced` receipts compatible. Do not add another operation, UI, folder/import/copy/remove-only path, watcher, cross-process lock, semantic conversion, or lifecycle scope.

After the Gate: run relevant focused tests, boundary/release/import/compile checks, document skipped Player evidence with its fallback/unblock path if PyQt6 is still unavailable, update `docs/mainline_status.md`, `docs/runtime_unification_roadmap.md`, `docs/INDEX.md`, and write a fresh-session prompt. Name exactly one next Gate only when evidence is recorded.

## Worktree discipline

Treat existing uncommitted and untracked files as user/prior migration work. Do not stage, commit, reset, clean, revert, delete, or attribute unrelated dirty files to the Phase 7G work without explicit instruction.
