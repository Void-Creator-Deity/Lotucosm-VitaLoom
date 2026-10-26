# VitaLoom Phase 7I closure / Phase 7J cross-process mutation-interlock handoff

**Date:** 2026-07-17

## Resume point

Phase 7I — explicit operator-confirmed durable transaction artifact prune execution Authority — is complete. This does **not** mean the whole product, all asset operations, GUI/Player proof, native acceleration, or OpenGL is complete.

Keep the plugin-shaped runtime boundary at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. Preserve the PyQt6 editor shell, QPainter default viewport, opt-in OpenGL, `.pond` semantics, package/project manifests, Asset Index/Registry, SR2D public seams, Player export, Command Registry, CLI and MCP. Do not migrate to Unity, Godot, Unreal, Electron or another application shell. Treat every pre-existing dirty/untracked/deleted worktree item as user/prior migration work: do not stage, commit, reset, clean, revert or delete unrelated files.

## Stable Phase 7I facts

- `asset_reference_transaction.py` owns a narrow Authority: `plan_asset_transaction_artifact_prune`, `apply_asset_transaction_artifact_prune`, inspection, receipt listing, recovery listing and receipt-scoped recovery. It only permits one exact complete durable artifact bundle, not generic cleanup.
- Plan/apply require strict receipt integrity, journal/backup linkage, project-contained paths, SHA-256, policy snapshot, source command-audit provenance and an exact operator confirmation. Apply fresh-revalidates, stages before unlink, and has limited compensation/recovery for only its own staged bytes.
- Terminal authentic `pruned` receipts revoke durable undo/redo; malformed/forged/nonterminal receipts never do. `asset.transaction.prune.plan` is read-only; `.apply` is mutating and intentionally non-generic-undoable; only successful apply emits `asset_transaction_pruned`.
- `project/command_audit.py` is a Qt-free compatibility seam. New audit writes go only to `.vitaloom/command_audit.jsonl`; historical `.vitalloom/command_audit.jsonl` remains read-only. Union replay is deterministic; duplicate same-content IDs de-duplicate; conflicting IDs and malformed nonempty entries cannot become strict prune provenance.
- Registry uses canonical write plus dual-read replay. Authority does not import Registry.

## Phase 7I evidence and current limitation

- Focused prune/retention/command/audit suite: 29 passed in 5.11s.
- Audit namespace/durable replay/CLI-MCP discovery: 16 passed in 1.42s.
- Expanded Qt-free asset/transaction/registry/project suite: 137 passed in 24.82s.
- Plugin non-GUI suite: 46 passed, 1 deselected in 4.82s.
- Core/GUI/release boundary checks, external-cache compileall, 302-file memory syntax compilation, and Qt-free import smoke passed.
- Active interpreter is Python 3.13.5 and `import PyQt6` fails. GUI/project-open/package-manager/hub smoke/Player and complete CLI/MCP GUI-dependent evidence are environment-blocked. Do not alter tests, Player or GUI code to disguise it. Switch to a supported Python environment, install compatible PyQt6, then rerun the blocked evidence.

## Unique next Gate: Phase 7J — durable asset-transaction mutation cross-process interlock Authority

Before implementation, write a Phase 7J plan under `docs/superpowers/plans/`. First audit every transaction mutation and recovery entry point (rename/delete/replace, guarded undo/redo, prune apply and prune recovery) plus project root/manifest ownership. Decide a single project-local lock/lease Authority that does not live in GUI adapters and does not silently delete stale/foreign lock evidence.

Required proof direction:

1. Exact deterministic lock identity and project containment; no lock access outside the active project.
2. Contended mutation rejects with zero data mutation and structured reason; read-only inspection/policy/index/export paths remain unaffected.
3. Stale, malformed, foreign-owner, replaced or interrupted lock evidence is conservative: no automatic unlink or ownership takeover without explicit proof-safe recovery policy.
4. Transaction, durable undo/redo, prune apply and prune recovery cannot interleave across processes into mixed receipt/backup states.
5. No degradation of `.pond`, Asset Index/Registry, export closure, manifests, command registry, CLI or MCP seams; no background cleanup, UI lock wizard, batch cleanup or unrelated asset operations.

After the Gate, run focused plus expanded regression, record PyQt6 skips accurately in `docs/mainline_status.md`, update the roadmap/INDEX and write the next fresh-session prompt. Name exactly one subsequent Gate.
