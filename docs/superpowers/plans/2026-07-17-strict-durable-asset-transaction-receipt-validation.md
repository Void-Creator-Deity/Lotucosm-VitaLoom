# Phase 7G - Strict Durable Asset Transaction Receipt Validation

**Date:** 2026-07-17

**Status:** complete

**Previous Gate:** Phase 7F - referenced single-file asset replacement transaction Authority

## Objective

Harden durable asset transaction receipts before recovery, resolution, undo, redo, or durable audit consumers can act on them. Invalid receipts must receive a structured refusal before any write-capable action.

## Scope

In scope: durable JSON schema, transaction-id coherence, known operation/state values, project-relative paths, digests, backup/target facts, file records, base64 payloads, and state consistency.

Out of scope: new operations, UI/Inspector work, folder/import/copy/remove-only behavior, journal repair/deletion, automatic recovery writes, semantic conversion, watchers, locking, generic filesystem undo, native completion, and OpenGL default readiness.

## Required safety contract

1. Invalid durable receipts are rejected before owner/source/replacement/backup/Registry/journal writes.
2. Recovery inspection/listing are read-only and retain invalid journals for operators.
3. Valid legacy receipts remain compatible.
4. Reader, inspection, resolution, undo, redo, and durable replay share strict ingress validation.

## TDD sequence

1. Add red cases for malformed JSON/root/schema/id/operation/state, unsafe paths, bad digest/base64, invalid records, missing backup/target facts, state conflicts, and truncation.
2. Snapshot project bytes and prove each rejection performs no write.
3. Implement the smallest shared strict validator; do not repair journals or add mutation fallback.
4. Verify transaction/recovery/command/Registry/CLI/MCP compatibility plus boundaries and compilation.

## Initial seam audit

- _read_journal only validates file, JSON, mapping root, and schema.
- _validate_recovery_journal checks a limited subset and misses id coherence, canonical digest/base64, record shape, duplicate paths, and strict state combinations.
- _decode runs after the weak reader, so malformed payloads can fail late in mutation-capable paths.

## Exit criteria

Every durable consumer has strict ingress validation; invalid receipts cannot mutate project facts; valid receipts retain lifecycle compatibility; next Gate is named only after evidence and closure.


## Implementation and evidence closure (2026-07-17)

**Result: complete.** Durable receipts now have one strict ingress validation path before recovery, resolution, undo, redo, or durable command replay consumers can act on journal data.

- _read_journal delegates to the same validator used by recovery inspection, turning malformed, partial, unknown, or inconsistent receipts into asset_transaction_malformed before write-capable code can decode payloads or resolve project paths.
- The validator checks exact schema-1 receipt fields, requested/recorded transaction-id coherence, known lifecycle states, expected rename/delete/replace_referenced plan fields, canonical safe project-relative paths, lower-case SHA-256 values, Registry revision digests, correct operation target/backup contracts, file-record key sets, duplicate owners, canonical base64, and byte-to-digest agreement.
- Recovery inspection preserves its read-only behavior: malformed journals classify deterministically, unknown states remain unknown_state, unsupported schemas remain unsupported_schema, and invalid raw journals are never rewritten, repaired, deleted, or used for recovery writes.
- Valid legacy rename/delete receipts and valid Phase 7F replacement receipts remain compatible across guarded undo/redo, recovery inspection/resolution, generic command undo/redo, and durable project audit replay.

### Evidence

- New receipt-validation coverage proves malformed JSON and non-object roots; transaction-id, source path/digest, state, and operation-contract corruption; unexpected/missing/misdirected backups; invalid/corrupted base64; base64/digest mismatch; unsafe or duplicate file records; truncated records; and missing replacement target digest. Every test snapshots project bytes and proves read-only inspection plus mutation refusal before a write.
- Focused asset transaction, recovery, command, CLI/MCP, Asset Index, and Registry parity set: 69 passed in 15.82s.
- Core, GUI, and release boundary checks passed. Temporary-pycache compileall of FrameCore, tools, main.py, and player.py passed. Relevant git diff --check passed.
- Player export smoke remains environment-limited: on 2026-07-17, tests/test_export_player_smoke.py produced 1 failed, 2 passed only because active Python 3.13 lacks PyQt6; export creation completed before the unchanged Player shell import failed. No Player/test behavior was changed to hide this. Unblock with a supported Python environment plus PyQt6, then rerun Player/full GUI/CLI/MCP evidence.

### Non-goals retained

This gate adds no new transaction operation, UI, Inspector behavior, folder/import/copy/remove-only semantics, journal repair/deletion, automatic recovery writes, watcher/hot reload/background indexing, cross-process locking, generic filesystem undo, semantic conversion, native acceleration completion, or OpenGL default readiness.

**Phase 7G is complete. Unique next Gate: Phase 7H - durable asset transaction retention and operator-controlled pruning policy Authority.**
