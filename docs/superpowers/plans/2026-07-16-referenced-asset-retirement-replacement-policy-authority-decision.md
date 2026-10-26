# Phase 7E ? Referenced-Asset Retirement / Replacement Policy and Authority Decision

**Date:** 2026-07-16

**Status:** complete

**Previous Gate:** Phase 7D ? asset transaction recovery resolution and operator-control Authority

**Architecture focus:** decide the safe policy and pure Authority boundary for a user who wants to retire an asset that still has canonical live references. Existing `asset.delete` must remain a hard block until this decision has evidence. The transaction Module remains the future mutation Authority; Asset Index/Registry remain fact Authorities; commands/UI stay Adapters.

## 1. Gate objective

Phase 7C intentionally blocks referenced single-file deletion. Phase 7D makes transaction recovery explicit, but neither gate decides what "replace", "remove", or "retire" means for each valid `.pond` reference style. Phase 7E must not bypass that block. It must establish a JSON-only, deterministic, read-only policy/impact model that can answer whether a requested retirement candidate is in scope, what references would need change, what replacement representations are possible, and why an operation remains refused.

Candidate deep interface, subject to red tests and evidence:

```python
analyze_asset_retirement_policy(project_root, *, source_path, replacement_path=None)
```

The final interface must return current Index/Registry facts by reference, not reimplement their scans or identity rules. It may expose potential future mutation prerequisites, but Phase 7E does not itself rewrite references or unlink referenced assets.

## 2. Non-negotiable architecture rules

- Preserve the plugin runtime boundary at `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`, PyQt6 shell, QPainter default viewport, and OpenGL opt-in policy.
- Keep `.pond`, `project.json.active_scene`, manifest/lock semantics, Inspector command binding, SR2D seams, Player export, CLI, and MCP compatible.
- `asset_index.py` owns canonical current-reference/export facts; `asset_registry.py` owns persistent identity/tombstone facts; `asset_reference_transaction.py` owns only a future verified mutation receipt. No Adapter parses raw scenes/journals to invent a policy.
- Do not weaken current `asset.delete` blocking behavior in this phase. Do not add folder recursion, automatic reference removal, default replacement choice, watcher/hot reload/background indexing, cross-process locking, or generic external-filesystem undo.

## 3. Discovery questions that must be answered with tests

1. Which canonical matching references are safely representable as a replacement under the existing structured location-token and style-preservation rules: project-relative paths, scene-relative paths, `active_scene`, script `path`, script `name`, and bare script shorthand?
2. Which source/replacement pairs are invalid before planning: missing, outside-project, protected metadata, same path, folder, target collision, wrong script shorthand location, malformed owner, or unsupported semantic asset type?
3. How should a "remove without replacement" request be represented? The default must remain refused unless every affected reference has a separately proved semantic deletion rule; no empty-string or null rewrite may be guessed.
4. What Index/export and Registry identity facts must be present before a later mutation can be considered, and what must remain true after a hypothetical migration?
5. What is the smallest command/CLI/MCP read-only surface that exposes the same decision facts without creating a UI flow or bypass path?

## 4. TDD sequence

1. Write red tests for deterministic policy/impact results and for every refusal class. Include nested `.pond` locations, `active_scene`, script forms, malformed owners, external/traversal references, and unchanged file bytes after analysis.
2. Implement a Qt-free policy/impact Authority that consumes canonical resolver/Index facts and structured location information. It must sort output and provide paths, current reference style, candidate representability, conflict/refusal codes, and explicit non-goals.
3. Add read-only Command Registry, CLI, MCP, and ProjectManager-safe exposure only after the Module contract passes. No mutation command is added in this phase.
4. Prove export/Registry/Index parity remains unchanged, run project-scale analysis timing if the new planner scans owners, and close with boundary/release/import/diff evidence.

## 5. Exit criteria

- Current referenced `asset.delete` remains a hard block in direct, command, CLI, and MCP paths.
- A deterministic JSON-only analysis explains a replacement candidate or refusal without modifying project files, Registry metadata, journals, backups, export output, or undo history.
- No generic "remove" action exists without a separately proved per-reference semantic policy.
- One future gate, not this gate, is named only after evidence shows whether a narrowly scoped replacement transaction is feasible.


## 6. Implementation record and evidence

### Implemented Authority

`core/VitaLoom/project/asset_reference_transaction.py` now exposes the Qt-free, JSON-only:

```python
analyze_asset_retirement_policy(project_root, *, source_path, replacement_path=None)
```

It reuses the existing Asset Index, Registry loader, canonical location traversal, resolver, and replacement-style helper rather than creating a second dependency/reference parser. The result distinguishes `replacement_candidate`, `unreferenced_delete_available`, and `refused`; it returns current Index/Registry facts, live references, proposed representable edits, blocked references, malformed owners, blockers, warnings, and explicit non-goals.

A `replacement_candidate` is only a future-mutation prerequisite: source and replacement must be distinct, project-contained, unprotected single files; every canonical live reference must be representable using existing style rules; and malformed owners/blockers must be absent. The Authority never creates a receipt, journal, backup, Registry record, undo entry, event, or file change.

### Read-only Adapter seam

The Command Registry now exposes `asset.retirement.analyze` with required `project_path` and `source_path`; `replacement_path` is intentionally optional. Its thin Adapter resolves the project through the existing workspace seam, delegates to the Authority, returns structured transaction Authority errors unchanged, and is explicitly `mutates=False`. CLI and MCP discover the command through the existing registry without a second parser, helper, ProjectManager route, or UI flow.

### TDD and parity proof

- The command red test first failed with `unknown_command`; after the Adapter was added, direct Authority and command results are equal, events remain empty, the schema keeps `replacement_path` optional, referenced `asset.delete` still returns `asset_references_blocking`, and project bytes/absent `.vitaloom` remain unchanged.
- Policy tests cover preserved project/scene-relative style, script shorthand, `active_scene`, referenced remove refusal, unreferenced existing-delete route, missing/same/nonrepresentable replacements, malformed owners, absent Registry non-creation, and existing Registry/Index/export parity. `tests/test_asset_retirement_policy.py` passed **7 tests in 0.86 s**.
- Registry/CLI/MCP discovery and command parity checks passed **4 tests in 0.69 s**. The larger transaction/Registry/Index/recovery/command set passed **49 tests in 9.48 s** before the Player smoke test reached its unrelated PyQt6 import requirement.
- `python -B tools/benchmark_engine.py --case asset_retirement_policy_scale --repeats 1` proved deterministic, byte-preserving analysis on 1,000 assets / 20 scenes / 400 dependency edges: Authority analysis was **2,152.2431 ms**; end-to-end one-run fixture plus repeat/parity evidence was **14,956.8290 ms**. The result was `replacement_candidate` with one proposed edit; export readiness stayed true; Registry remained missing rather than being created; no transaction metadata was created.
- `tools/check_core_boundaries.py`, `tools/check_gui_boundaries.py`, and `tools/check_release_consistency.py` passed. Full compileall passed using a temporary `PYTHONPYCACHEPREFIX` because existing repository `__pycache__` files were locked. `git diff --check` passed with pre-existing LF/CRLF warnings only.

### Environment-limited proof

The active Python 3.13 environment has no `PyQt6`, and the repository `.venv` currently has package scripts but no `python.exe`. Therefore the full Player smoke cannot import `core.VitaLoom.player.player_shell`: the combined relevant collection was **49 passed, 1 failed** at that external import. The export test had already created and checked its launch/runtime/project files before that import. This phase does not change the Player shell or export code. Fallback is the headless Authority/command/Index proof above; the unblock path is to restore a Python 3.11+ environment with PyQt6 and rerun the existing Player/complete CLI-MCP collection. No environment repair is hidden inside this gate.

## 7. Exit decision

All Phase 7E exit criteria are met for the read-only policy seam. Referenced `asset.delete` remains hard-blocked; no generic removal behavior or replacement mutation has been introduced; and the future mutation question is now isolated behind a proof-bearing candidate contract.

**Unique next Gate: Phase 7F ? referenced single-file asset replacement transaction Authority.** Before any implementation, write a new plan and red tests for a narrowly scoped operation that may consume only freshly revalidated Phase 7E-style candidates, must decide and prove source-byte/tombstone semantics, preserve canonical reference styles, recheck conflicts at apply time, remain atomic and undoable, and keep remove-only/folder/UI/watcher/cross-process behavior out of scope.
