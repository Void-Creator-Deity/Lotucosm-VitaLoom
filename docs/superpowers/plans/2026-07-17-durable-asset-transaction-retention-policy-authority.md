# Phase 7H - Durable Asset Transaction Retention and Operator-Controlled Pruning Policy Authority

**Date:** 2026-07-17

**Status:** complete

**Previous Gate:** Phase 7G - strict durable asset transaction receipt validation

## Objective

Establish one Qt-free, read-only Authority that inventories all durable transaction journals and private asset backups, joins each journal to the existing strict recovery classification, explains retention/protection facts deterministically, and distinguishes a review candidate from an actually safe prune action. This phase is policy and evidence only: it must not delete, compact, repair, rewrite, or hide a journal or backup.

## Scope

In scope: deterministic transaction artifact inventory; strict receipt/recovery classification reuse; terminal/nonterminal/malformed state grouping; private backup presence/digest facts; project-relative/export exclusion facts; command-audit provenance references when safely available; explicit per-artifact reasons; read-only policy summary; and no-write tests.

Out of scope: deletion/compaction, automatic cleanup, UI workflow, erase/repair of malformed evidence, changes to undo/redo/recovery, new asset operations, folders/import/copy/remove-only behavior, watchers, locks, generic filesystem undo, semantic conversion, native completion, and OpenGL default readiness.

## Required policy contract

1. Every discovered journal and orphan private backup receives a stable project-relative row and explicit disposition: protected, retained, review_candidate, or not_prunable.
2. Recovery-required, malformed, unsupported, unknown-state, user-conflicted, active/nonterminal, or provenance-referenced artifacts are protected. No rule may infer permission to delete from age alone.
3. A terminal transaction is never called safe to prune merely because it is terminal; valid undo/redo/audit evidence must remain protected unless a future mutation gate proves an explicit operator action and provenance-safe deletion.
4. Analysis is deterministic, JSON-only, and byte-for-byte read-only. Transaction artifacts remain outside Asset Index inventory and Player export truth.
5. The Authority must not inspect unsafe paths outside the project or silently discard unknown transaction-root files.

## TDD sequence

1. Audit transaction-root layout, journal/backup naming, strict journal reader/inspection/listing, command audit persistence, export exclusions, and Registry evidence.
2. Add red tests for deterministic ordering, valid terminal receipts, recovery-required receipts, malformed journal/root, changed/orphan backup, unknown files, and no-write snapshots.
3. Implement only a read-only policy Authority and a thin non-mutating command adapter if existing registry seams make that useful; do not add a prune command.
4. Prove Index/export isolation and focused transaction/recovery/command/CLI/MCP compatibility.

## Initial seam audit (2026-07-17)

- Transaction receipts are stored under .vitaloom/asset_transactions as transaction-id JSON journals. Delete and replace operations can create a sibling private transaction-id asset backup.
- Phase 7G makes journal inspection strict and read-only, but list_asset_reference_transaction_recovery intentionally returns only recovery-required journals; it is not a full retention inventory.
- Asset Index and Player export exclude private transaction artifacts, but no single Authority currently explains why terminal receipts/backups remain retained or whether a file is an orphan/unknown artifact.
- The receipt contains no authoritative age/acknowledgement/provenance-deletion permission. Therefore this phase must default to protection/retention and may expose review candidates only with explicit non-prunable reasons.

## Exit criteria

A deterministic read-only inventory/policy Authority exists with explicit artifact reason rows and no write behavior; malformed/recovery/provenance-sensitive artifacts remain protected; valid lifecycle behavior and export isolation remain proven; and exactly one next gate is named only after evidence and documentation closure.


## Implementation and evidence closure (2026-07-17)

**Result: complete.** The runtime now has one read-only durable transaction retention-policy Authority plus a thin non-mutating command Adapter. It deliberately provides evidence and reasons, not a deletion capability.

- analyze_asset_transaction_retention_policy inventories every JSON journal, private asset backup, and unknown transaction-root artifact in deterministic project-relative path order.
- Each journal reuses the strict Phase 7G recovery inspection classification and receives a conservative disposition. Recovery-required, malformed/unsupported/unknown, conflict, and unrecognized receipts are protected. Terminal receipts are retained with explicit lifecycle and missing-authorization reasons.
- Linked private backups inherit protected/retained lifecycle evidence. Orphan private backups and unknown transaction-root files are not_prunable because provenance and explicit operator authorization are unproven.
- The Authority always returns empty review_candidates and safe_prune_candidates and prune_authorized false. No terminal state, age inference, or artifact name is treated as safe deletion permission.
- asset.transaction.retention.analyze exposes the same JSON-only result through the existing Command Registry with mutates false. It adds no UI, background cleanup, or alternate mutation path.

### Evidence

- New Phase 7H tests prove deterministic no-write inventory for an empty root; terminal rename retention; recovery-required and malformed protection; linked delete backup retention; orphan/unknown artifact non-prunability; and direct command/Authority parity with non-mutating command metadata.
- Focused asset transaction, recovery, command, CLI/MCP, Asset Index, and Registry parity set: 74 passed in 16.84s.
- Core, GUI, and release boundary checks passed. Temporary-pycache compileall of FrameCore, tools, main.py, and player.py passed.
- Player smoke remains environment-limited: the active Python 3.13 environment lacks PyQt6. On 2026-07-17, tests/test_export_player_smoke.py remained 1 failed, 2 passed after export creation while importing the unchanged Player shell. No test or Player code was altered to hide this; unblock with supported Python plus PyQt6 and rerun Player/full GUI/CLI/MCP evidence.

### Non-goals retained

No journal/backup deletion, compaction, repair, automatic cleanup, UI, new asset operation, folder/import/copy/remove-only behavior, watcher/hot reload/background indexing, cross-process lock, generic filesystem undo, semantic conversion, native acceleration completion, or OpenGL default readiness was added.

**Phase 7H is complete. Unique next Gate: Phase 7I - explicit operator-confirmed durable transaction artifact prune execution Authority.**
