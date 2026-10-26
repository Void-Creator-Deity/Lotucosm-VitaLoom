# Phase E14 — Runtime Capability Registry Interface and L0/L1 Registry Role Reconciliation Authority

- **Date:** 2026-07-20
- **Status:** Complete
- **Previous Gate:** E13 runtime capability publication ownership, exact unpublication, and Host lifecycle isolation is complete.
- **Unique scope:** establish the Qt-free L1 runtime capability registry Interface and explicitly reconcile it with the separate L0 FrameCore Suite-service registry.

## Architecture invariant

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 engine extensions / Host Adapters
          -> L4 addons scoped to one Project World
```

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` remains the product runtime boundary. The E14 Module stays inside that boundary. It must not become a second L0 registry, a peer FrameCore plugin, a Project World root, or a PyQt-owned extension authority. PyQt6/QPainter/current OpenGL remain legacy UI-host Adapters.

## E13 gate and current proof limit

E13 stabilized owner-labelled transactional capability publication, partial-failure rollback, exact-object unpublication, replacement preservation, idempotent release, and Editor/Player Host publication timing. Current proof includes:

```text
51 focused tests passed
38 ordered same-process tests passed
19 Player / Project World tests passed
1176 passed, 25 skipped, 34 subtests passed (signature file excluded)
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
AST OK: 274 files
```

`tests/test_package_signature_warn_only.py` is still uncollectable in the repository `.venv` because `cryptography` is absent. E14 must not reuse an older signature result or silently claim that suite as verified.

## Registry role audit to complete

| Registry Module | Expected owner | Scope / lifetime | Key authority | Current evidence | E14 question |
|---|---|---|---|---|---|
| `FrameCore/service_registry.py::ServiceRegistry` | L0 FrameCore composition | Frame/Suite lifecycle | L0 Suite service names only | Qt-free `register/get/has`; no established `FrameApi` handoff found at phase start | Remain isolated, or share only a structural Protocol without importing L1 keys/Implementation? |
| `core/VitaLoom/core/editor_context.py::ServiceRegistry` | currently constructed by legacy `EditorContext` singleton | process-wide editor/player Host state | L1 runtime capability keys | runtime publishers/consumers use `context.services`; class definition is trapped in a PyQt Module | Extract L1 registry Implementation and Interface into a Qt-free runtime Module and compose it explicitly without creating another global singleton |

The audit must cover `FrameApi`, L1 Hub lifecycle, editor entry, Player entry, CLI/command/headless paths, `EditorKernel`, `PlayerShell`, plugin loader, Project World capability composition, L3 extensions, L4 addon activation/deactivation, and every direct or indirect registry publisher/consumer.

## Initial design hypothesis, not yet completion evidence

1. Keep L0 and L1 registry instances and key namespaces intentionally isolated because they have different owner, scope, lifetime, and framework depth.
2. Define a minimal Qt-free L1 runtime registry Interface plus one concrete in-memory Implementation under the version runtime.
3. Preserve compatibility by letting legacy `EditorContext.services` receive or create that Implementation, while moving the registry definition out of the PyQt Module.
4. Provide explicit composition seams for Editor/Player/headless command execution. At least two real compositions must use the Interface; one Adapter alone would be only a hypothetical seam.
5. Keep E13 `CapabilityPublicationLease` as the owner/transaction/exact-release authority. E14 registry lookup/mutation must not duplicate lease ownership stacks.
6. Do not inject all L1 runtime keys into `FrameApi`, do not make `FrameApi` or `EditorContext` a god context, and do not create a third process-global registry singleton.

This hypothesis must be revised if the complete call-chain audit disproves it.

## Implementation sequence

1. Complete owner/scope/lifetime/key/thread/process/unload audit for both registries and all L1 compositions.
2. Add headless red tests for a Qt-free runtime registry Module, strict key contract, `register/get/has/unregister` compatibility, E13 publication compatibility, and L0/L1 key isolation.
3. Add explicit runtime registry composition and migrate legacy `EditorContext` to import/use it rather than define it.
4. Migrate Editor, Player, and headless/command seams incrementally; preserve existing plugin-facing `context.services` compatibility and avoid broad call-site churn where the context itself is still the correct Host state Adapter.
5. Prove at least two real compositions use the same Interface without requiring the same registry instance or a process-global authority.
6. Run focused E14 tests, E13 publication regressions, Project World E9–E13, command/Inspector, SR/PS, plugin lifecycle, Player/Hub/export, package/manifest tests, architecture guards, AST/import smoke, and changed-region whitespace checks.
7. Update `CONTEXT.md`, `docs/mainline_status.md`, this plan with completion evidence, and create exactly one fresh-session prompt for the next Gate.

## Compatibility constraints

- Preserve `.pond` scene semantics, AI Command Registry flows, Inspector command binding, SR2D seams, package/project manifests, Player/export, and L3/L4 lifecycle.
- Preserve plugin-facing `editor_context.services` behavior during migration unless a tested compatibility Adapter replaces it.
- Do not make the L0 registry import `core.VitaLoom`, L1 service keys, or L1 implementations.
- Do not assume two classes with the same name should share one instance or one lifecycle.
- Do not stage, commit, reset, restore, clean, delete, batch-format, re-encode, or normalize unrelated dirty/untracked files.

## Verification matrix

- new E14 Qt-free registry/interface/composition tests
- `tests/test_capability_publication_lease.py`
- `tests/test_runtime_capability_publication_lifecycle.py`
- command registry / runtime command / Inspector tests
- SR selected identity and PS runtime snapshot tests
- plugin loader/lifecycle and community example tests
- Project World Host capability/ownership/composition/session/open tests
- Player-mode plugin and export Player smoke tests
- package/manifest/runtime bootstrap tests
- `tools/check_project_plugin_model.py`
- `tools/check_core_boundaries.py`
- `tools/check_gui_boundaries.py`
- `tools/check_release_consistency.py`
- Qt-blocked import smoke and Python AST parse

## Completion rule

E14 is complete only when the L1 runtime registry Interface and Implementation are Qt-free; Editor plus at least one of Player/headless are explicitly composed through that seam; legacy plugin `context.services` compatibility remains tested; L0 and L1 registry roles and key isolation are documented and enforced; E13 publication remains the sole owner/exact-release Module; focused and expanded regressions are recorded honestly; and exactly one next Gate is named. This phase does not complete the overall engine migration or select a replacement UI Host.


## Completion evidence (2026-07-20)

| Item | Evidence |
|---|---|
| L0/L1 role reconciliation | L0 `FrameCore.service_registry.ServiceRegistry` remains Frame/Suite-scoped and owns only L0 service names. L1 `RuntimeCapabilityRegistry` belongs to one composed VitaLoom Editor, Player, or headless Host and owns only L1 runtime capability keys. No implicit bridge, shared singleton, or `FrameApi` promotion was introduced. |
| Qt-free L1 Module | `core/VitaLoom/core/runtime_capability_registry.py` defines the runtime-checkable `RuntimeCapabilityRegistry` Interface, strict key/error contract, `InMemoryRuntimeCapabilityRegistry` Implementation, explicit validation, and narrow resolution from an explicit registry, command context, legacy `editor_context`, or legacy Host Adapter `.services`. Import is proven without PyQt. |
| Explicit compositions | `launch_editor`, `EditorKernel`, `run_player_shell`, `PlayerShell`, `run_player_smoke`, and CLI `main` expose the registry composition seam. Behaviour tests prove Editor, Player, and CLI/headless forward the exact supplied registry instance. Each composition may own a distinct instance; no process-global registry authority was added. |
| Legacy compatibility and consumer migration | `EditorContext.services` imports/uses the Qt-free Implementation and rejects replacement after first binding. Project World, PS/SR lookup, ecology/replay Adapter paths, package Adapter tests, and command contexts resolve through the formal Interface. Incomplete dictionary/get-only test Adapters were replaced rather than weakening the production seam. |
| Publication ownership | E13 `CapabilityPublicationLease` remains the sole owner-labelled transactional publication and exact-unpublication Module. E14 did not add an owner stack or duplicate release semantics inside the registry. |
| Player ordering fix | Player now binds the L1 registry before constructing the nested legacy Project World Host Adapter. This prevents `ProjectManager` from creating `EditorContext` with an unrelated default registry and restores exported Player smoke. |
| Focused proof | E14 Interface/composition tests: `15 passed`. Project World capability/ownership: `14 passed`. Combined E14/E13/Project World/PS/SR focused set: `76 passed`. Expanded command/plugin/Player/Hub/pond/runtime set: `178 passed`. |
| Full-suite proof | Excluding only `tests/test_package_signature_warn_only.py`, the final repository suite is `1191 passed, 25 skipped, 34 subtests passed in 121.42s`. An earlier loaded run exposed one asset-index timing miss plus two incomplete registry test Adapters; the Adapter failures were fixed and the load-sensitive asset-index case separately passed inside `18 passed in 9.73s` before the final full green run. This is not a general performance guarantee. |
| Guardrails and static proof | `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, `release consistency OK`; tokenize-aware parse reports `AST OK: 542 files; BOM files: 37`; changed tracked test regions pass `git diff --check`. |
| Environment limit | The repository `.venv` still lacks `cryptography`, so `tests/test_package_signature_warn_only.py` cannot collect. No network installation was performed and no prior-session signature result is reused as current proof. |
| Stable vs unfinished | Stable: L0/L1 registry role isolation, Qt-free L1 Interface/Implementation, explicit Editor/Player/headless composition, strict Adapter validation, E13 publication ownership, Player/export composition order. Still unfinished: broader isolation of legacy `EditorContext` responsibilities, a replacement UI Host decision/implementation, signature dependency availability, native acceleration proof, and OpenGL default-ready pixel/parity/interaction/benchmark evidence. |

## Phase conclusion and unique next Gate

E14 is complete. The registry seam is now a real multi-Adapter L1 engine-plugin contract rather than a class trapped inside the PyQt `EditorContext`, while FrameCore retains its separate L0 role. This does not complete the overall engine migration and does not select or implement a replacement UI Host.

**Unique next Gate: Phase E15 — Qt-Free Runtime Host Context Interfaces and Legacy EditorContext Adapter Isolation Authority.** First write the E15 plan, then audit the current 30 runtime files that directly import/use `editor_context` and classify each dependency: L1 registry access, event publication/subscription, Project World facts, scene/selection/mode state, kernel/UI ownership, or simulation attachment. Define only the narrow Qt-free Interfaces and composition seams actually shared by Editor, Player, and headless execution; keep `EditorContext` as a legacy PyQt Adapter, do not create another global singleton or a god context, and require at least two real Adapters plus parity/lifecycle evidence before migrating consumers.
