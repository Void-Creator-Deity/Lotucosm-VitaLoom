# Phase 7D Closure / Phase 7E Handoff Prompt

**Date:** 2026-07-16

**Closed Gate:** Phase 7D ? asset transaction recovery resolution and operator-control Authority

**Unique next Gate:** Phase 7E ? referenced-asset retirement/replacement policy and Authority decision

## Stable architecture and Phase 7D result

- Runtime remains plugin-shaped at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`; retain PyQt6 editor shell, QPainter default viewport, OpenGL opt-in, `.pond`/manifest/lock/Inspector/SR2D/Player/CLI/MCP seams.
- `asset_index.py` owns current filesystem/dependency/provenance/export facts; `asset_registry.py` owns persistent project-local identity/tombstone/revision facts; `asset_reference_transaction.py` is Qt-free Authority for durable reference-mutation receipts and recovery policy.
- New recovery Authority interfaces are `inspect_asset_reference_transaction`, `list_asset_reference_transaction_recovery`, and `resolve_asset_reference_transaction`.
- Inspection/listing is JSON-only, deterministic, and read-only. It emits journal state/classification, affected paths, per-file before/after/current digest facts, legal actions, and conflicts. Project open only publishes those facts; it never resolves a transaction automatically.
- Proven actions are deliberately narrow: `rollback` is legal only for `prepared_before_state` or `redoing_before_state`, writes only the receipt state to `undone`, and leaves assets/owners/backups/Registry untouched. `acknowledge_failure` is legal only for `failed_recoverable_before_state`, writes only `failed_acknowledged` plus a deterministic receipt annotation. All malformed/unsupported/unknown/mixed/user-modified facts have no action.
- `resume`, inferred applied acknowledgement, automatic cleanup, and UI conflict flow are not implemented. This is a safety conclusion, not missing polish.
- Delete redo now preflights its private backup and refuses `asset_transaction_backup_changed` before it can overwrite a user-modified backup.
- Adapter commands are `asset.transaction.inspect`, `asset.transaction.recovery.list`, and `asset.transaction.recovery.resolve`; CLI and MCP discover them from the same Command Registry.
- Receipts/backups retain no-auto-cleanup policy and stay outside Index inventory/export closure/Player payload. Do not stage, commit, reset, clean, revert, delete, or reorganize unrelated pre-existing worktree changes.

## Phase 7D evidence

- `tests/test_asset_reference_transaction_recovery.py` covers valid and compensated states, terminal states, malformed/unsupported/unknown journals, source/backup digest conflicts, no-mutation inspection, safe resolution, and backup overwrite refusal.
- Transaction command, project-open, MCP, and CLI coverage was expanded. Project-open proves it leaves malformed journal bytes unchanged.
- Final relevant suite: **107 passed in 52.88 s**. Core/GUI/release checks, compileall, runtime import, and `git diff --check` passed; only existing LF/CRLF warnings appeared.
- One-run 1,000 asset / 20 scene / 400 edge transaction benchmark remained export-ready after redo and kept transaction metadata out of export.

## Start Phase 7E in this order

1. Read `docs/superpowers/plans/2026-07-16-referenced-asset-retirement-replacement-policy-authority-decision.md` and retain the current referenced-delete hard block.
2. Audit canonical reference styles and type semantics from existing Asset Index/transaction helpers. Write red read-only policy/impact tests before designing any replacement action.
3. Establish an Authority-only, JSON-only candidate-analysis contract. It must report what can be represented and why unsupported/remove cases are refused; it must not write files or create an undo receipt.
4. Add read-only command/CLI/MCP exposure only after direct Module evidence. Do not add UI or mutation because a candidate exists.
5. Close each gate with Index/Registry/export/project-open/command parity and boundaries/release/import/diff proof. Name one next gate only after deciding whether a narrowly scoped replacement transaction is actually feasible.

## Explicit non-goals until separately planned

- Weakening `asset.delete` for referenced files, reference removal by null/empty guesses, replacement mutation, recursive folders, automatic recovery, watchers/hot reload/background indexing, cross-process locks, generic external filesystem undo, Unity/Godot/Electron migration, OpenGL default readiness, or native acceleration completion.
