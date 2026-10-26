# Phase 7F ? Referenced Single-File Asset Replacement Transaction Authority

**Date:** 2026-07-17

**Status:** complete

**Previous Gate:** Phase 7E ? referenced-asset retirement / replacement policy and Authority decision

**Architecture focus:** add at most one narrowly scoped, durable transaction operation for a current, freshly revalidated referenced-asset replacement candidate. The operation must preserve the plugin-shaped runtime and deepen the existing transaction Module; it must not turn a read-only policy analysis into a stale approval token or create an alternate delete path.

## 1. Gate objective

Phase 7E proved that a currently referenced source and a currently existing replacement can be described deterministically without writes. Phase 7F decides and, only after red tests, may implement the smallest mutation whose semantics are explicit:

```text
rewrite every currently canonical, representable live source reference to the existing replacement;
retire (unlink) the source single file;
refresh Registry facts so source identity becomes a tombstone;
retain enough guarded private evidence to undo/redo or diagnose recovery.
```

The authoritative plan/apply/undo/redo interface must live in `asset_reference_transaction.py`. A Phase 7E analysis result is advisory only: apply must reproduce/revalidate all source/replacement, owner, reference, Index, and Registry facts at its own point of execution.

## 2. Non-negotiable scope

### In scope only after proof

- One project-contained source file and one already-existing project-contained replacement file.
- Existing canonical reference forms only: structured `.pond` locations, `project.json.active_scene`, and existing representable script `path`/`name`/bare shorthand forms.
- Atomic affected-owner writes plus source file retirement, Registry refresh/tombstone, durable journal/private source backup, guarded undo/redo, and existing recovery inspection compatibility.
- Existing command/CLI/MCP discovery only after the Authority contract passes.

### Explicitly not in scope

- Remove-without-replacement, empty/null reference values, folders, replacement generation/copy/import, automatic replacement choice, UI wizard, Inspector behavior change, watcher/hot reload/background index, cross-process locking, generic external filesystem undo, or semantic content conversion.
- No mutation may trust a cached 7E output, blindly overwrite user-modified owners/source/replacement/backup, or silently change a nonrepresentable reference style.
- Do not weaken `asset.delete` for live references. It remains a separate hard-blocked route.

## 3. Required contract decisions before implementation

1. **Operation name and receipt schema.** Choose one explicit operation distinct from `rename` and `delete` (candidate: `replace_referenced`). Record source/replacement paths, preconditions, exact owner edits, source backup digest/path, Registry before/after facts, and enough state for existing recovery classification.
2. **Source semantics.** On successful apply, the source is unlinked and its persistent Asset Registry identity becomes a tombstone. Replacement bytes and identity are not overwritten or merged. Undo restores source bytes and active identity only if all guards still prove no user conflict.
3. **Compatibility.** The operation is structural, not semantic conversion. It may preserve Phase 7E's explicit `replacement_semantic_compatibility_not_inferred` warning, but must never claim type/content equivalence or fabricate converters.
4. **Stale analysis resistance.** Planning/apply independently re-resolve all locations and digest/current facts. Any changed owner, source, replacement, malformed metadata, new unrepresentable live reference, or Registry conflict must refuse before overwrite/partial mutation.
5. **Export/Index isolation.** Journal/private backup artifacts remain outside Asset Index inventory and Player export. Current export facts after apply/undo/redo must remain truthful.

## 4. TDD sequence

1. Audit the current `plan_asset_reference_mutation`, receipt, apply/undo/redo, private backup, Registry hint, and recovery classifier seams. Write a short implementation note in this plan before code changes.
2. Write red Authority tests for successful image/script/active-scene replacement; source retirement/tombstone; exact style preservation; private backup and receipt facts; undo/redo; modified owner/source/replacement/backup conflicts; stale-plan refusal; malformed/unrepresentable/remove-only refusal; and project-byte atomicity under injected failure.
3. Implement only the Authority extension. Reuse Phase 7E resolver/replacement rules and existing transaction storage/guards; do not duplicate Index/Registry scans or make a policy Adapter mutate.
4. Add the one command Adapter only after Authority green. Prove `mutates=True`, explicit operation payload, CLI/MCP discovery, referenced `asset.delete` still blocks, and no UI path exists.
5. Prove Index/Registry/export/Player parity, recovery inspection/listing behavior, scale timing at 1,000 assets / 20 scenes / 400 edges, and boundary/release/import/diff checks. Document any PyQt environment blocker with fallback and unblock path.

## 5. Exit criteria

- A current candidate replacement applies atomically or leaves project/Registry/export facts unchanged on refusal/failure.
- Source unlink/tombstone and reference edits are explicit, digest-guarded, reversible, and durable; replacement bytes/identity never receive implicit changes.
- Existing recovery Authority classifies the new receipt safely, and user changes are refused rather than overwritten.
- `asset.delete` remains blocked for referenced assets; no generic remove/folder/UI behavior is introduced.
- One subsequent gate is named only after full evidence is recorded.


## 6. Initial seam audit (2026-07-17, read-only)

The current transaction Module has a useful deep implementation to extend rather than replace:

- `plan_asset_reference_mutation(...)` currently admits only `rename` and `delete`; it already builds sorted canonical edits and owner digest guards. Rename uses `_replacement_for(...)`; delete turns every matching live reference into a hard block.
- `_build_file_records(...)` already preserves exact owner before/after bytes and each digest. `_verify_plan(...)`, `_verify_file_state(...)`, and existing journal states supply the first conflict/atomicity seams.
- `_apply_prepared(...)` has the two relevant primitives but separately: rename moves source then writes owner bytes and Registry rename hints; delete makes a private source backup, unlinks source, and refreshes the Registry into a tombstone. Undo/redo already contain reciprocal source/owner/Registry logic and backup-digest guards.
- The current receipt/recovery validator explicitly recognizes only `rename` and `delete`; Phase 7F will need an additive, carefully tested `replace_referenced` schema path and recovery file-fact classification. It must not loosen malformed-journal rejection.

Therefore the first red tests should demonstrate whether one explicit operation can compose the existing owner-byte rewrite and delete-backup/tombstone primitives while preserving ordering, compensation, conflict refusal, and recovery safety. Do not edit implementation until those tests pin the composition contract.

## 7. Implementation and evidence closure (2026-07-17)

**Result: complete.** The narrow Authority extension was implemented without widening the project into a replacement/import/UI workflow.

### Delivered authority contract

- `asset_reference_transaction.py` now admits the explicit `replace_referenced` operation for two different, project-contained, existing, non-protected single files.
- Planning captures source and replacement SHA-256 facts, canonical exact edits, owner digests, and explicit blocked-reference facts. Apply independently replans/revalidates those facts before any write, so a changed owner/source/replacement, newly introduced reference, malformed `.pond`, nonrepresentable live reference, or Registry conflict refuses instead of creating a dangling source reference.
- Apply rewrites only the current representable canonical references while preserving the original reference style, creates a private source backup, unlinks the source, and refreshes Registry facts into a source tombstone. Replacement bytes and Registry identity remain unchanged.
- Undo/redo guard owner, source, private backup, and replacement bytes. A user modification to the replacement, private backup, owner, or relevant source state is a structured refusal, never an overwrite.
- The durable receipt includes `target_path` and `target_sha256`. Recovery validation recognizes `replace_referenced`, and recovery inspection treats the replacement as an immutable independent file fact; a changed replacement makes a purported applied receipt a `terminal_conflict` rather than a false `terminal_applied` result.
- `asset.referenced.replace` is a thin `mutates=True`, `undoable=True` command adapter. Existing CLI and MCP discovery expose it through the command registry. The command explicitly returns `replacement_semantic_compatibility_not_inferred`; structural replacement does not claim asset/content/type/behavior equivalence.
- Generic and durable command undo/redo now replay this receipt through `asset.transaction.undo`, `asset.transaction.redo`, `command.undo`, `command.redo`, `command.undo_project`, and `command.redo_project`.

### Verification evidence

Focused transaction, Registry/Index parity, CLI, and MCP coverage passed:

```text
63 passed in 11.07s
```

The passed focused suite covered retirement policy; Authority plan/apply/undo/redo; recovery receipts; direct, in-memory, and durable command replay; project Asset Index; incremental Registry parity; CLI list/describe; and MCP registry discovery. Core, GUI, and release boundary checks also passed, and `compileall` passed with a temporary external pycache location. `git diff --check` passed for the Phase 7F code and test set.

The scale benchmark at 1,000 assets / 20 scenes / 400 edges recorded `replace_referenced` plan/apply/undo/redo at 817.7104 ms / 2336.8935 ms / 1097.2144 ms / 1099.8438 ms respectively. Its invariants confirmed unchanged replacement bytes, retired source after redo, export readiness after redo, and no transaction metadata in export.

### Known environment limitation

`tests/test_export_player_smoke.py` produced `1 failed, 2 passed` only because this environment uses Python 3.13 and lacks `PyQt6`; the failure occurs after export creation when the unchanged Player shell imports `PyQt6`. This is not a Phase 7F product failure and was not masked by changing Player code or tests. Unblock path: restore a supported Python environment with PyQt6 installed, then rerun Player/full GUI/CLI/MCP evidence.

### Explicit non-goals retained

This gate does not add remove-without-replacement, folders, replacement generation/copy/import, automatic replacement choice, a UI wizard, Inspector behavior changes, watcher/hot reload/background indexing, cross-process locking, generic external filesystem undo, semantic conversion, native acceleration completion, or OpenGL default readiness. Referenced `asset.delete` remains hard-blocked.

**Phase 7F is complete. Unique next Gate: Phase 7G ? strict durable asset transaction receipt validation.**

