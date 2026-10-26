# Phase E13 — Runtime Capability Publication Lease, Exact Unpublication and Host Lifecycle Isolation Authority

- **Date:** 2026-07-20
- **Status:** Complete
- **Previous Gate:** E12 Project World Host Adapter factory/ownership/disposal composition is complete.
- **Unique scope:** capability publication ownership and unload isolation inside the existing `lotucosm-vitaloom` version runtime.

## Architecture invariant

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 extension / Host Adapters
          -> L4 addons scoped to one Project World
```

The new Module remains inside `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`. It is not a new FrameCore plugin, registry root, Project World framework, or UI framework. PyQt6/QPainter/current OpenGL remain legacy Host Adapters and must not become capability lifecycle authority.

## E12 gate and current proof limit

E12 stabilized Project World Host ownership, owned-versus-borrowed Editor/Player leases, exact Project World capability cleanup, and concrete singleton encapsulation. Fresh pre-E13 proof is:

```text
40 passed in 1.00s
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
```

The previous full suite excluding signature collection was `1152 passed, 25 skipped, 34 subtests passed, 2 failed`. One failure was load-sensitive asset-index timing. The deterministic architectural failure was process-wide `SR_SELECTED_IDENTITY_HOST` pollution from `GameViewport`. `tests/test_package_signature_warn_only.py` remains uncollectable in the current `.venv` because `cryptography` is absent.

## Publisher audit

| Publisher | Keys | Owner / scope | Current construction and unload truth | E13 action |
|---|---|---|---|---|
| Project World Editor/Player composition | five `project_world.*` keys | Editor/default Player composition root | Already exact-instance cleanup through E11/E12 helpers; replacement-safe | Preserve compatibility; route through the generic publication Module only if public return contracts remain intact |
| `GameViewport` | `simulation.sr_host`, `simulation.sr_selected_identity_host` | one viewport instance, L3 viewport Adapter lifetime | Constructor publishes; plugin publishes again after context assignment; plugin unload only calls `deleteLater()`; no exact unpublication | Must migrate; lease owned by viewport and released before plugin deletion; repeat registration must be deterministic |
| `PsExperimentPlugin` | `ps_experiment`, `simulation.ps_runtime_snapshot_host` | one loaded plugin instance | Two sequential registrations can partially publish; unload removes by key and may delete replacement | Must migrate transactionally and release before PS service teardown |
| `PackageManagerPlugin` | `package.catalog`, `package.operations` | one loaded plugin instance | Registers in `on_load`; unload removes both by key | Migrate to one multi-key lease |
| `DownloaderPlugin` | `downloader` | one loaded plugin instance | Registers in `on_load`; unload removes by key | Migrate to lease |
| `ConsolePlugin` | `ui.console_panel` | one created dock/panel instance | Publishes lazily during dock construction; unload removes by key | Migrate lazy publication to lease; constructor failure leaves no publication |

No other direct version-runtime `services.register()/unregister()` publisher was found at phase start.

## Design decision

Use **replace-with-evidence plus exact unpublication**, not a recoverable global stack:

1. Existing `ServiceRegistry.register(key, value)` replacement semantics and consumer lookup stay unchanged.
2. A small Qt-free `CapabilityPublicationLease` owns one atomic publication batch and records an explicit owner label, keys, and whether each key replaced an existing value.
3. Registration validates the registry Interface and the complete batch before mutation.
4. If registration fails part-way, already-written exact values are rolled back. Pre-existing values are restored only for constructor/registration rollback, because publication never successfully completed.
5. Normal release removes only entries whose current registry value is the exact published object. A later replacement is retained and reported.
6. Normal release does not resurrect the value that was replaced when publication succeeded. This preserves the current registry's last-writer semantics and avoids inventing a hidden global owner stack.
7. Double release is deterministic and side-effect free.

This creates a deep Module: callers provide `registry`, `owner`, and a key/value mapping; all validation, transactional failure cleanup, exact identity checks, evidence, and idempotent release remain local to the Module.

## Implementation sequence

1. Add Qt-free `core/VitaLoom/core/capability_publication.py`.
2. Add focused tests for:
   - owner-labelled publication evidence;
   - atomic multi-key construction and rollback;
   - exact unpublication;
   - later replacement safety;
   - double release;
   - malformed registry and key rejection;
   - PyQt-blocked import smoke.
3. Migrate `GameViewport` and `PsExperimentPlugin` first as the two required real Adapters.
4. Migrate package manager, downloader, and console publishers so no known blind key-unregister remains.
5. Add plugin/viewport lifecycle tests, including producer-before-Inspector isolation in one process.
6. Run focused and expanded regressions, architecture guards, AST/import smoke, and changed-region whitespace checks.
7. Update `CONTEXT.md`, `docs/mainline_status.md`, this plan's completion evidence, and create exactly one next-Gate prompt.

## Compatibility constraints

- Keep all existing service keys and consumer `services.get()` behavior.
- Do not change `.pond`, AI command registry, Inspector command binding, SR2D seams, package/project manifests, Player/export, or L3/L4 discovery semantics.
- Do not make `EditorContext.ServiceRegistry` the framework authority.
- Do not stage, commit, reset, restore, clean, delete, batch-format, re-encode, or normalize unrelated dirty/untracked files.

## Verification matrix

- `tests/test_capability_publication_lease.py`
- GameViewport selected identity + Inspector default-loader ordered reproducer
- PS runtime snapshot and replay tests
- plugin loader/lifecycle tests
- package/downloader/console focused tests where present
- Project World E9–E12 regressions
- command/Inspector collection
- SR/viewport collection
- Player/Hub/export and package/manifest collections
- `tools/check_project_plugin_model.py`
- `tools/check_core_boundaries.py`
- `tools/check_gui_boundaries.py`
- `tools/check_release_consistency.py`

## Completion evidence (2026-07-20)

| Item | Evidence |
|---|---|
| Qt-free publication Module | `core/VitaLoom/core/capability_publication.py` provides owner-labelled transactional publication, pre-mutation validation, rollback after partial write, exact-object unpublication, later-replacement preservation, absence evidence, and idempotent release. |
| Migrated publishers | GameViewport, PS experiment, Package Manager, Downloader, Console panel, and console logging handler use publication leases; a post-migration audit found no direct version-runtime `services.register()/unregister()` publisher. |
| Host composition timing | `GameViewport()` no longer publishes from its constructor. Editor and Player composition assign Host context first and then explicitly call `register_as_sr_host()`. Plugin unload, Player construction failure, and Player close release only their own exact publication. |
| Focused proof | Publication/lifecycle/selected-identity/Inspector focused suite: `51 passed in 0.93s`. |
| Ordered same-process proof | GameViewport producer tests followed by Inspector default-loader tests: `38 passed in 1.25s`; the prior `expected unavailable / actual not_running` pollution no longer reproduces. |
| Player / Project World proof | `19 passed in 5.60s` across Project World Host ownership, Player-mode plugins, and export Player smoke. |
| Full-suite proof | Excluding only the currently uncollectable signature file: `1176 passed, 25 skipped, 34 subtests passed in 123.68s`. The asset-index threshold test separately passed in `8.45s` with a `< 10.0s` threshold; this remains load-sensitive evidence, not a general performance guarantee. |
| Guardrails and static proof | `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, `release consistency OK`; no direct runtime registry publishers found; `AST OK: 274 files`; all E13 changed regions passed whitespace checks. Existing whole-file whitespace debt in the untracked legacy GameViewport Adapter was not batch-cleaned. |
| Environment limit | `tests/test_package_signature_warn_only.py` was not collected because the repository `.venv` lacks `cryptography` (`ModuleNotFoundError`). No network install was performed and no older signature result is reused as current evidence. |

## Gate result

E13 is complete. The runtime now has one lifecycle-owned publication Interface used by multiple real Adapters, and the deterministic same-process capability pollution is closed without promoting PyQt `EditorContext` to framework authority. This does not mean the overall engine migration is complete.

**Unique next Gate: Phase E14 — Runtime Capability Registry Interface and L0/L1 Registry Role Reconciliation Authority.** First write the E14 plan, then audit `FrameCore/service_registry.py`, `FrameCore/lifecycle.py::FrameApi`, L1 entry handoff, `editor_context.py::ServiceRegistry`, `service_keys.py`, all runtime registry consumers, and Editor/Player/headless composition. Decide owner, scope, lifetime, key authority, thread/process semantics, unload responsibility, and whether the two registries remain isolated, gain an explicit bridge, or share only a minimal Qt-free Protocol. Do not assume a merge, create a third global singleton, turn `FrameApi`/`EditorContext` into god contexts, or duplicate publication-lease ownership semantics.

## Completion rule

E13 is complete only when every known version-runtime publisher either uses the publication lease or has stronger, evidenced exact lifecycle semantics; ordered GameViewport-to-Inspector pollution is closed through real unload/disposal; at least two real Adapters use the Module; focused and expanded regressions are recorded honestly; and exactly one next Gate is named.