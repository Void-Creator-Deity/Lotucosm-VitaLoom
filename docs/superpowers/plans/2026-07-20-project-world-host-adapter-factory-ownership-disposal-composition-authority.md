# 2026-07-20 Project World Host Adapter Factory, Ownership and Disposal Composition Authority

## Purpose

Close the remaining concrete Project World Host lifecycle leak without changing the recursive framework/plugin topology. FrameCore remains L0; `lotucosm-vitaloom` remains the sole L1 engine/product plugin and downstream plugin-host framework; the version runtime remains the product boundary. This Gate makes concrete PyQt Host creation, reuse, ownership, release, and isolated-smoke cleanup explicit while preserving the E9 open Host, E10 session Host, and E11 capability catalog Interfaces.

## Starting evidence

- E11 removed concrete `ProjectManager` imports from ordinary L2/L3 consumers, but `runtime/main.py` and `player_shell.py` still assign `ProjectManager._instance = None` directly.
- `EditorKernel` and `PlayerShell` acquire the concrete singleton themselves and do not express whether the Host is owned or borrowed.
- Accepted Editor/Player close paths flush Project World state but do not release the Host through one lifecycle authority.
- Smoke paths reset a private singleton before and after temporary bundle-path/environment overrides, so failed construction and repeated runs depend on private implementation knowledge.
- E11 capability Adapters remain registered in the process-wide `EditorContext.services` registry after a Host is released, retaining concrete Host references and risking stale capabilities on a later partial Host.
- Compatibility tests also reset the private singleton directly because no public concrete-Adapter disposal seam exists.

## Architecture decisions

1. Add a Qt-free, generic `project_world_host_ownership.py` deep Module. Its Interface is only acquire/reuse/release/dispose-if-idle through lease objects; it receives a Host factory and disposer and never imports PyQt or `ProjectManager`.
2. A lease has an explicit owner label, exposes one Host, and releases idempotently. Overlapping leases reuse one Host; only the last release invokes the disposer. Factory failure leaves no retained Host or lease. Final-disposal failure is fail-closed and keeps the lease active so disposal can be retried.
3. Add `project_world_host_composition.py` as the current legacy PyQt Adapter composition authority. It lazily imports `get_project_manager` and the public concrete disposal function, owns one narrow `ProjectWorldHostOwnership`, and is the only runtime Module besides `project_manager.py` allowed to know concrete singleton compatibility.
4. Add a public exact-instance disposal function in `project_manager.py`. It encapsulates `ProjectManager._instance`, refuses to dispose a different current instance, and preserves existing session semantics; it does not silently flush, close, or claim rollback.
5. `EditorKernel` and default `PlayerShell` construction acquire leases from the composition authority. An explicitly injected Player Host remains borrowed and must not be disposed by Player.
6. Accepted Editor/Player shutdown first preserves E10 flush/teardown ordering, then unregisters E11 capabilities that still point to this Host, then releases the lease. Cancelled/failed Editor shutdown keeps the lease and Host alive.
7. Constructor failures after lease acquisition release/unpublish their own lease before re-raising. Repeated close/release is deterministic and harmless.
8. Isolated Editor/Player smoke uses a public idle-disposal/reset seam before temporary-state construction and in finally cleanup. It never writes `ProjectManager._instance`.
9. Entry-point source guards reject private singleton access and concrete manager imports in `runtime/main.py` and `player_shell.py`. Concrete imports remain legal only in `editor_kernel.py` if required by composition (target is none), `project_world_host_composition.py`, `project_manager.py`, and compatibility exports/tests with explicit justification.
10. This Gate does not turn ownership into a Project World business facade. The ownership Module never forwards open/save/config/recent/package methods; callers continue using E9–E11 Interfaces.

## Defensive red tests

- Import `project_world_host_ownership.py` with all PyQt imports blocked and drive it with a second functional test Adapter.
- Prove one factory call for overlapping leases, exact Host reuse, non-final release without disposal, final release disposal, idempotent double release, owner evidence, and fresh Host creation after release.
- Prove factory failure leaves zero leases/no Host and allows a later successful retry.
- Prove final-disposal failure keeps the lease active and retry succeeds rather than leaking an untracked Host.
- Prove borrowed Player Host cleanup never invokes the legacy disposer.
- Prove E11 capability unregistration removes only the exact Adapters registered by the releasing composition root and does not delete replacements installed by another owner.
- Source/AST guards: `runtime/main.py` and `player_shell.py` contain neither `ProjectManager._instance` nor concrete manager imports; Editor/Player acquire/release through the composition seam.
- Real PyQt Adapter compatibility: acquire the legacy Host twice, release in reverse order, verify exact singleton reuse and a fresh instance after last release under an application object.
- Regress Editor shutdown Cancel/Save/Discard ordering, Player close/smoke, E9–E11 Project World transitions, and startup/relaunch paths.

## Verification and completion

1. Run focused E12 ownership/composition/source tests, first red then green.
2. Run E9–E11 Project World capability/open/session and package-receipt regressions.
3. Run Editor shutdown, Player/Hub/export, L3/L4 lifecycle, command/Inspector, SR2D/viewport, and manifest/package compatibility collections.
4. Run project plugin model, core boundary, GUI boundary, and release consistency guardrails.
5. Run PyQt-blocked import smoke, AST checks, and changed-region trailing-whitespace checks without generating/deleting pycache.
6. Record exact proof, skips, and any full-suite limitations in `docs/mainline_status.md`, then name exactly one next Gate and create one fresh-session prompt.

## Compatibility and non-goals

- Do not delete PyQt6/QPainter/OpenGL or select a successor UI Host.
- Do not migrate to Unity, Godot, Unreal, Electron, or another shell.
- Do not move code outside `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`.
- Do not alter `.pond`, AI command registry, Inspector binding, SR2D seams, package/project manifests, Project World transition ordering, or L3/L4 lifecycle.
- Do not expand into rendering, native acceleration, OpenGL-default, watcher/hot reload, or unrelated package refactoring.
- Do not replace the concrete singleton with another god Host facade.

## Worktree discipline

The repository contains extensive user/prior migration work. Do not stage, commit, reset, restore, clean, delete, re-encode, broadly format, or whitespace-clean unrelated files. Change only E12-owned files/regions and inspect them explicitly.

## Completion evidence（2026-07-20）

### Implemented Modules and lifecycle semantics

- Added Qt-free `project_world_host_ownership.py` with `ProjectWorldHostOwnership` and idempotent `ProjectWorldHostLease`. Overlapping leases reuse one Host; only the final release disposes; factory failure retains nothing; disposal failure is fail-closed and retryable.
- Added `project_world_host_composition.py` as the only current legacy composition Adapter that lazily connects the generic ownership Module to `get_project_manager()` and `release_project_manager_instance()`.
- Added exact-instance `release_project_manager_instance(expected=...)` in `project_manager.py`. Runtime private-singleton access is now confined to that concrete Module.
- Editor and default Player now own composition leases. An explicitly injected Player Host is borrowed and is never disposed by Player.
- Constructor failure and accepted shutdown paths unpublish only exact E11 capability Adapters owned by that composition root, then release only their owned lease. Cancelled/failed Editor close keeps the Host alive.
- `runtime/main.py` editor smoke now uses the public idle-disposal seam and no longer writes the private singleton.

### Test and guardrail proof

| Verification | Result |
|---|---|
| Initial E12 defensive red tests | `6 failed` before implementation |
| Final E12 focused ownership/composition suite | `8 passed in 0.42s` |
| Project World session/capability/package-receipt focused set | `43 passed in 2.37s` |
| E12 + Project World + Editor/Player/Hub/L3-L4 regression | `136 passed, 1 skipped in 11.50s` |
| Command / Inspector collection | `217 passed in 19.11s` |
| SR2D / QPainter / OpenGL / viewport collection | `140 passed, 23 skipped in 12.88s` |
| Package / manifest collection excluding unavailable signature dependency | `100 passed, 1 skipped, 17 subtests passed in 6.01s` |
| Architecture guardrails | `project plugin model OK`; `core boundaries OK`; `GUI boundaries OK`; `release consistency OK` |
| Static checks | `AST OK: 8 files`; E12 changed-region trailing whitespace OK; entrypoint private-singleton/concrete-import guard OK |

The existing whole-file trailing-whitespace debt in untracked legacy `editor_kernel.py` and `project_manager.py` was deliberately not normalized. Only E12-touched regions were checked, preserving unrelated migration work and file encoding/line endings.

### Full-suite truth and current blockers

The current environment full suite, excluding `tests/test_package_signature_warn_only.py`, completed as:

```text
1152 passed, 25 skipped, 34 subtests passed, 2 failed in 139.86s
```

This is not claimed as all-green:

1. `tests/test_asset_index_project_scale.py` exceeded its cold timing threshold once under full-suite load (`14.23s > 10.0s`), then passed three independent reruns (`7.80s`, `7.36s`, `7.82s`). Record this as load-sensitive timing variance, not a reproducible E12 product regression.
2. `tests/test_inspector_sr_selected_component_projection.py` passed independently but is order-polluted by `tests/test_game_viewport_sr_selected_identity.py`, whose `GameViewport` publishes `SR_SELECTED_IDENTITY_HOST` into process-wide `EditorContext.services` without lifecycle restoration. Running the producer before the default-loader test reproduces the leak. This is an existing Host capability publication/disposal debt and is intentionally not patched as a scattered E12 fix.
3. `tests/test_package_signature_warn_only.py` cannot collect in the current `.venv` because `cryptography` is absent. No network install was performed, so prior-session signature results are not reused as current proof.

### Gate conclusion

E12 is complete. The stable result is concrete Project World Host factory/reuse/ownership/disposal composition, owned-versus-borrowed Editor/Player semantics, exact capability cleanup, and removal of entrypoint private-singleton manipulation. The recursive architecture remains:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 extension / Host Adapters
          -> L4 Project World addons
```

This Gate does **not** claim that the whole project is complete, PyQt is removed, a replacement UI Host is selected, OpenGL is default-ready, or native acceleration is complete.

**Unique next Gate: Phase E13 — Runtime Capability Publication Lease, Exact Unpublication and Host Lifecycle Isolation Authority.** The first action is to audit every current version-runtime capability publisher against its real lifecycle, then write Qt-free red tests for ownership-labelled publication leases, replacement-safe exact unpublication, constructor/unload cleanup, and process-isolated restart. The first concrete reproducer is the `GameViewport` SR Host publication that currently leaks into `EditorContext.services`; the Gate must solve it through a runtime capability publication Module usable by more than one Adapter, not by test-only cleanup or by promoting the legacy PyQt `EditorContext` into framework authority.

