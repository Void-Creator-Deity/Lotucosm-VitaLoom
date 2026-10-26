# Phase 7D — Asset Transaction Recovery Resolution and Operator-Control Authority

**Date:** 2026-07-16

**Status:** complete

**Previous Gate:** Phase 7C — dependency-aware asset reference migration and undo Authority

**Architecture focus:** deepen the existing transaction Module so incomplete or failed asset transactions have explicit, inspectable, guarded recovery choices instead of a project-open diagnostic that leaves every decision implicit. The transaction Module remains the Authority; ProjectManager, Command Registry, CLI, MCP, and any future UI are Adapters.

## 1. Gate objective

Phase 7C safely plans and applies single-file rename/delete, compensates tested failures, and reports incomplete journals on project open without guessing how to overwrite project files. That safety rule remains correct, but an operator currently receives only `recovery_required` and a list of journal paths. Phase 7D must provide a small, JSON-only operator Interface that classifies journal state, proves whether a specific rollback/resume action is safe under current digests, and refuses conflicts deterministically.

The deep Module remains:

```text
core/VitaLoom/project/asset_reference_transaction.py
```

Its additive Interface should be designed and tested before any UI work:

```python
inspect_asset_reference_transaction(project_root, transaction_id)
list_asset_reference_transaction_recovery(project_root)
resolve_asset_reference_transaction(project_root, transaction_id, *, action)
```

`action` must be a closed policy vocabulary such as `rollback`, `resume`, or `acknowledge_conflict`; the final names and states must be selected only after discovery tests establish what byte/digest evidence makes each action safe. Project open remains read-only: it may refresh facts and publish recovery diagnostics, but it must never automatically resume or roll back a transaction.

## 2. Authority and seam rules

- **Asset Index Authority:** current filesystem/dependency/export facts only. It does not own recovery policy.
- **Asset Registry Authority:** persistent asset identity/tombstone and revision facts only. It participates only through verified rename/restore hints.
- **Asset transaction Module Authority:** journal state machine, safe action classification, mutation guards, compensation facts, recovery receipts, and retention/acknowledgement policy.
- **Adapters:** ProjectManager publishes read-only diagnostics; Command Registry exposes the same Module Interface to UI/CLI/MCP. No adapter may parse journals or implement an alternate recovery policy.
- Keep the product boundary at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`; retain PyQt6 shell, QPainter default viewport, OpenGL opt-in, `.pond`/manifest semantics, Inspector command binding, SR2D seams, Player export, and CLI/MCP command parity.

## 3. Required policy decisions before implementation

1. Define journal state vocabulary: `prepared`, `applying`, `applied`, `undone`, compensated failure, malformed, and conflict. State names must map to observable filesystem/digest facts; do not infer completion from a filename alone.
2. For each state/action pair, specify preconditions, no-op result, guarded writes, Registry hint, audit fields, and conflict result. Any ambiguity must be a refusal with diagnostics—not a best-effort overwrite.
3. Decide private backup/journal retention after a resolved transaction. Retention must preserve undo/redo guarantees and remain absent from Index inventory, export closure, and Player payload.
4. Decide recovery acknowledgement semantics. An acknowledgement may record that a human inspected a conflict, but must not conceal unresolved export-relevant filesystem facts or simulate a successful rollback.
5. Confirm whether existing `asset.transaction.undo`/`redo` are sufficient for terminal receipts and keep recovery resolution separate from generic undo history.

## 4. TDD implementation sequence

1. **Red discovery tests:** synthesize each incomplete/failed/malformed journal shape and current filesystem permutation. Assert a deterministic classifier with paths, expected/current digests, legal actions, and no mutation.
2. **Pure recovery planner:** implement one Qt-free inspection/listing Interface and a closed action planner. Verify Index/export truth is unchanged by inspection.
3. **Guarded resolver:** add only proven-safe rollback/resume actions, atomic journal transition, compensation handling, Registry continuity, and conflict refusal. Inject failures at each mutation stage and prove the resolver never overwrites later user edits.
4. **Adapter convergence:** expose read-only recovery listing/status and explicit recovery resolution through Command Registry, CLI, and MCP; ProjectManager publishes only the same Module facts. Add an Inspector/UI hook only if the command contract and failure presentation have already passed.
5. **Closure evidence:** targeted recovery/command/CLI/MCP/project-open/export tests, Index/Registry parity, core/GUI/release/import/diff checks, and a recovery-resolution scale/timing case if action scanning is non-trivial.

## 5. Required invariants

- No automatic rollback, resume, deletion, acknowledgement, or journal cleanup at project open.
- No referenced-delete replacement/removal migration, recursive folder mutation, watcher/hot reload, background indexer, cross-process locking, or generic filesystem undo.
- Recovery actions must compare durable expected digests with current file facts before writes; they must never overwrite a user-created source/target/owner file.
- Journal/backup/recovery acknowledgement artifacts remain private `.vitaloom` metadata outside Asset Index inventory, export closure, and Player payload.
- Command output must include transaction ID, prior/new state, selected action, registry revision/generation when changed, and explicit conflict/recovery diagnostics.

## 6. Verification matrix

| Claim | Required proof |
| --- | --- |
| inspection | each journal state produces deterministic JSON-only status, legal actions, affected paths, and digest evidence without mutation |
| guarded resolution | rollback/resume only alter files when every precondition matches; later user edits yield conflict refusal |
| compensation | injected resolver failure leaves current/export facts truthful and an explicit next recovery state |
| identity | safe recovery preserves/returns the Registry ID only through verified hint rules |
| adapter parity | Command Registry, CLI, MCP, project-open diagnostics, and any UI hook share transaction Module facts |
| isolation | all private recovery artifacts stay absent from Index/export/Player payload |
| architecture | no PyQt/ProjectManager/editor-global/CommandRegistry import in the transaction Module |

## 7. Explicit deferrals

- Referenced-delete replacement/removal migration and recursive folder operations.
- Automatic crash recovery or background/watcher-based recovery.
- Cross-process locking, generic global undo, UI conflict-resolution workflow beyond the explicitly proven command contract.
- Unity/Godot/Electron migration, OpenGL default readiness, and native acceleration completion.

## 8. Completion record

_To be filled after implementation and verification._

## 9. Unique next Gate

_To be named only when Phase 7D is fully closed._


## 6. Completed state/action matrix and evidence

| Journal classification | Digest proof | Phase 7D action | Write boundary |
|---|---|---|---|
| `prepared_before_state` / `redoing_before_state` | Source/reference owners are exactly at the recorded before digests; rename target is absent; any recorded delete backup is either valid or absent before it was recorded. | `rollback` | Journal only: transition to `undone`, attach deterministic `recovery_resolution`; no asset, owner, backup, Registry, or export write. The normal guarded redo receipt remains the only way to reapply. |
| `failed_recoverable_before_state` | Compensation returned the asset/reference owners to recorded before facts and any private backup has not changed. | `acknowledge_failure` | Journal only: transition to terminal `failed_acknowledged`, preserving the receipt/backup for forensic retention. |
| `applied`, `undone`, `failed_acknowledged` | Current facts match the respective terminal receipt state. | None | Existing undo/redo remains responsible for applied/undone receipts. Acknowledged compensation is not added to generic undo history. |
| malformed JSON, unsupported schema, unknown state, mixed current state, or changed source/target/owner/backup digest | Ambiguous or conflicting. | None | Deterministic refusal with paths, expected/current digest evidence, and zero mutation. |

Implemented the Qt-free Authority interface in `asset_reference_transaction.py`:

```python
inspect_asset_reference_transaction(project_root, transaction_id)
list_asset_reference_transaction_recovery(project_root)
resolve_asset_reference_transaction(project_root, transaction_id, *, action)
```

Inspection/listing are JSON-only and deterministic. Project open delegates to the same listing through its existing recovery adapter and remains read-only. The only implemented resolver vocabulary is `rollback` and `acknowledge_failure`; `resume`, inferred "already applied" acknowledgement, automatic cleanup, and any overwrite of a user-changed file remain intentionally unsupported because their byte-level safety was not proved.

The transaction receipts and private delete backups retain their existing no-automatic-cleanup policy. This preserves the already-proven undo/redo contract and keeps the data outside Asset Index inventory, export closure, and Player payload. Delete redo now rejects a changed private backup with `asset_transaction_backup_changed` before changing journal state or project files.

### Verification

- Added `tests/test_asset_reference_transaction_recovery.py`: valid prepared inspection, compensated failure, malformed/unsupported/unknown journals, source and backup conflicts, terminal states, guarded resolution, and backup overwrite refusal.
- Extended transaction-command, project-open, MCP command-discovery, and AI CLI command-list coverage. Project open proves it does not alter a malformed journal's bytes.
- Final relevant regression: **107 passed in 52.88 s** across transaction/recovery/command, Registry/Index/dependency/export, project-open, MCP, AI CLI, and tools smoke tests.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `tools/check_release_consistency.py` all passed; `compileall`, runtime import with the runtime on `PYTHONPATH`, and `git diff --check` passed. The latter reported only pre-existing LF/CRLF warnings.
- Re-ran `tools/benchmark_engine.py --case asset_reference_transaction_scale --repeats 1`: 1,000 assets / 20 scenes / 400 edges; rename plan/apply/undo/redo `953.0136 / 5675.5900 / 811.5918 / 935.0164 ms`, delete `839.3251 / 2053.6236 / 1028.3103 / 1075.0444 ms`; export remained ready after redo and transaction metadata remained absent from export. These are one-run machine-local observations, not performance guarantees.

**Unique next Gate:** Phase 7E ? referenced-asset retirement/replacement policy and Authority decision. It must first retain current hard-block delete behavior, audit type/reference semantics, and establish a read-only policy/impact decision model before any replacement or referenced-delete mutation is contemplated.
