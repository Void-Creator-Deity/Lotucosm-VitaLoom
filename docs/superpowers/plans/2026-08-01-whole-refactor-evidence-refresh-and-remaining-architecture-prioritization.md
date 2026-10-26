# E204 Whole-Refactor Evidence Refresh and Remaining-Architecture Prioritization Gate

Date: 2026-08-01
Status: complete

## Previous gate

E166 performed the prior whole-refactor evidence audit. E167–E203 subsequently hardened command-history, Project-World persistence, legacy-save provenance, failure atomicity, and cross-runtime caller boundaries. Their focused proof did not by itself establish current whole-worktree readiness.

## Objective and result

E204 refreshed the repository-wide evidence matrix against the current worktree. It exposed one real full-suite performance regression, profiled and corrected it, then re-ran the complete suite and current architecture guards. The result proves the covered runtime boundaries and regressions are currently green; it **does not** prove that the complete refactor is finished.

## Environment and full-suite evidence

- Initial collection was blocked because the project `.venv` lacked the test dependency `cryptography`. A normal sandboxed installation could not reach the package index; after explicit approval, `cryptography 50.0.0`, `cffi 2.1.0`, and `pycparser 3.0` were installed into the existing project `.venv`. This is a local test-environment dependency repair, not a product-source change.
- First full run, `./.venv/python.exe -B -m pytest -q`, reached execution and returned `2057 passed, 34 skipped, 50 subtests passed` plus one failure: `tests/test_asset_index_project_scale.py` measured a 1,000-asset cold rebuild at `15.192s`, above the explicit `10.0s` contract. The failure was treated as a real product regression rather than hidden behind focused results.
- `cProfile` attributed the cold-path cost primarily to sequential `_digest()` file opens in `project.asset_index._inventory()` (one profile recorded `build_project_asset_index=7.212s`, `_inventory=6.200s`, `_digest=5.756s`, and `pathlib.open/io.open=4.672s`). Metadata/cache semantics and deterministic inventory ordering were already correct; opening roughly one thousand small files serially was the bottleneck on Windows.
- `_inventory()` now gathers cache misses first, hashes multiple misses with an order-preserving `ThreadPoolExecutor.map()` (at most 16 workers), and retains the direct path for a single miss. Its caller-owned digest-cache and cache-stat semantics remain unchanged; final rows are still path-sorted and deterministic.
- Focused asset-index evidence after the repair passed: `21 passed in 5.77s` for project-scale/index/registry/incremental/command integration coverage; the isolated 1,000-asset cold-scale test passed in `2.16s`.
- Fresh complete rerun passed: `./.venv/python.exe -B -m pytest -q` -> **`2058 passed, 34 skipped, 50 subtests passed in 231.70s (0:03:51)`**.

## Guard evidence

The following commands all exited `0` after the full-suite repair:

```powershell
./.venv/python.exe -B tools/check_project_plugin_model.py
./.venv/python.exe -B tools/check_release_consistency.py
./.venv/python.exe -B tools/check_core_boundaries.py
./.venv/python.exe -B tools/check_gui_boundaries.py
./.venv/python.exe -B tools/check_ai_command_audit_status.py
./.venv/python.exe -B tools/check_sr2d_native.py
./.venv/python.exe -B tools/check_runtime_replay_status.py
./.venv/python.exe -B tools/check_runtime_worldbridge_status.py
./.venv/python.exe -B tools/check_worldbridge_component_decision.py
./.venv/python.exe -B tools/check_worldbridge_component_projection.py
./.venv/python.exe -B tools/check_worldbridge_component_projection_diagnostics.py
./.venv/python.exe -B tools/check_worldbridge_mapping_audit.py
git diff --check
```

`git diff --check` emitted only pre-existing LF/CRLF warnings. No staging, commit, reset, restore, revert, clean, or deletion was performed.

## Current completion matrix

| Requirement | Current classification | Evidence and claim boundary |
| --- | --- | --- |
| Versioned plugin/runtime, package/project manifests, Qt-free L0–L4 and legacy UI-host boundaries | proven for covered contracts | Full suite plus project-plugin, release, core and GUI guards passed. This is not authorization to make Qt the engine authority. |
| `.pond`, Registry command flows, Inspector binding, persistence/history provenance | proven for covered behavior | E167–E203 regressions are included in the 2058-pass complete suite; explicit Standard UI save, lifecycle flush exclusion, and quarantined legacy Save As retain their established contracts. |
| Asset-index cold rebuild performance | proven for the specified tested scale | The 1,000-asset cold test now passes after deterministic bounded concurrent hashing. It does not claim an unbounded filesystem throughput guarantee. |
| Command-history architecture | incomplete by explicit product status | Audit still reports `schema_version: 4` and `unified_undo_redo_runtime: false`; representative semantic history is not a global unified undo/redo claim. |
| Replay and unified runtime | incomplete / non-default | Replay/WorldBridge guard paths pass their stated status checks, but unified runtime replay and SR/PS tick merging are not proven. |
| WorldBridge mapping | incomplete by explicit ledger | Mapping audit remains `lossless: false` with known losses: `velocity_acceleration`, `active_visible_state`, `render_identity`, `scripts`, `membrane_component_graph`, `hierarchy`, and `memory_genes`. Component projection remains read-only and is not live graph mapping. |
| Native acceleration | incomplete / not default-ready | SR2D native status guard passes its current status contract only; no new extension build/import/parity/benchmark proof was created here. |
| OpenGL acceleration | incomplete / not default-ready | No current-context pixel parity, interaction smoke, and benchmark evidence establishes an OpenGL default-ready adapter. |

## Decision and next gate

The next material gap is WorldBridge’s documented kinematic mapping loss. E205 must first prove whether the shared `EntityBase` velocity/acceleration representation can be synchronized without merging SR/PS ticks, invoking component behavior, changing `.pond` semantics, or upgrading the pilot/default status. It may close only the loss item that its tests demonstrate; it must retain an explicit non-lossless ledger for all remaining gaps.
