# VitaLoom Phase 7G closure / Phase 7H retention-policy handoff

**Date:** 2026-07-17

## Resume point

Phase 7G - strict durable asset transaction receipt validation - is complete. Do not claim the whole product, asset lifecycle, native acceleration, or OpenGL path is complete.

Keep the plugin-shaped runtime boundary at FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime. Keep PyQt6 as editor shell, QPainter as default viewport, and OpenGL opt-in only. Preserve .pond, project/package manifests, Asset Index/Registry, SR2D seams, Player export, Command Registry, CLI, and MCP. Do not migrate to Unity, Godot, Unreal, Electron, or another shell.

## Stable Phase 7G facts

- asset_reference_transaction.py now treats every durable journal as untrusted input.
- The journal reader and recovery inspection share strict schema-1 validation before receipt data reaches undo/redo, recovery resolution, payload decode, path resolution, or durable command replay.
- The validator checks transaction-id coherence; known state/operation; complete plan keys; safe project-relative source/target/owner paths; lower-case SHA-256 values; Registry revision digests; target and private-backup rules; exact file-record key sets; duplicate owner paths; canonical base64; and decoded-byte digest parity.
- Invalid receipts cause asset_transaction_malformed in mutation-capable consumers. Recovery inspection/listing remain read-only and return deterministic malformed, unknown_state, or unsupported_schema classifications without repairing/deleting raw journal evidence.
- Valid legacy rename/delete and valid replace_referenced receipts continue through Authority undo/redo, recovery resolution, generic command undo/redo, durable project replay, CLI/MCP discovery, Index, and Registry parity tests.

## Evidence

- Focused asset transaction/recovery/command/CLI/MCP/Index/Registry suite: 69 passed in 15.82s.
- New corruption tests snapshot project bytes and prove no write for malformed JSON/non-object roots, id/path/digest/state corruption, unexpected/missing/wrong backup facts, unsafe/duplicate/partial file records, invalid base64, payload digest mismatch, and missing replacement target digest.
- Core/GUI/release boundary checks and temporary-pycache compileall passed.
- Player smoke still reports 1 failed, 2 passed on July 17, 2026 solely because current Python 3.13 lacks PyQt6 after export creation. Do not mask this; restore supported Python + PyQt6, then rerun Player/full GUI/CLI/MCP evidence.

## Unique next Gate: Phase 7H - durable asset transaction retention and operator-controlled pruning policy Authority

First write the Phase 7H plan under docs/superpowers/plans, then red tests. Start with a read-only policy/impact Authority that inventories terminal/nonterminal/malformed receipts and private backups; determines only clearly safe retention/pruning candidates; keeps recovery-required, malformed, current, user-modified, or provenance-needed artifacts protected; and exposes explicit reasons. Do not delete or compact anything until a later separately proven mutation gate.

Audit journal/backup locations, recovery list/inspection, command audit history, Asset Index/export exclusions, project manifests, and Registry evidence. Prove deterministic ordering, no writes during analysis, no loss of valid undo/redo/recovery evidence, and no inclusion of transaction artifacts in export. Do not add UI, automatic cleanup, folder/import/copy/remove-only behavior, watcher/hot reload, cross-process locking, semantic conversion, native completion, or OpenGL default readiness.

After the gate, record test/check evidence, document the Player environment fallback/unblock path if still applicable, update status/roadmap/INDEX, and name exactly one next Gate. Treat all pre-existing dirty/untracked worktree content as user/prior migration work; do not stage, commit, reset, clean, revert, or delete unrelated files.
