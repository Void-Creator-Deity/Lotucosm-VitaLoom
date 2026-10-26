# Phase E15 — Qt-Free Runtime Host Context Interfaces and Legacy EditorContext Adapter Isolation Authority

- **Date:** 2026-07-20
- **Status:** Complete
- **Previous Gate:** E14 runtime capability registry Interface and L0/L1 registry role reconciliation is complete.
- **Unique scope:** identify and extract only the Host seams genuinely shared by multiple VitaLoom compositions, starting with the string runtime event bus, while reducing `EditorContext` to a legacy PyQt UI Host Adapter rather than creating another god context.

## Architecture invariant

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin
       and nested plugin-host framework
      -> versions/<version>/runtime
          -> L2 capability/domain Modules
          -> L3 engine extensions / Host Adapters
          -> L4 addons scoped to one Project World
```

The product runtime boundary remains:

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime
```

E15 Modules must remain inside this single L1 engine plugin. They must not become peer FrameCore plugins, another root framework, a Project World root, or a PyQt-owned extension authority. PyQt6/QPainter/current OpenGL remain legacy UI Host Adapter Implementations. The engine plugin itself remains the framework that hosts L2/L3/L4 extensions.

## E14 gate and proof limit

E14 established:

- a Qt-free `RuntimeCapabilityRegistry` Interface and in-memory Implementation;
- intentional isolation between the L0 FrameCore registry and the L1 runtime capability registry;
- explicit Editor, Player, and CLI/headless composition seams;
- E13 `CapabilityPublicationLease` as the sole owner-labelled publication/release authority;
- Player composition order that binds the L1 registry before constructing nested legacy Project World Host Adapters.

Current proof:

```text
E14 focused: 15 passed
Project World capability/ownership: 14 passed
Combined focused: 76 passed
Expanded runtime/plugin/command/Player set: 178 passed
Full suite excluding signature file: 1191 passed, 25 skipped, 34 subtests passed
project plugin model OK
core boundaries OK
GUI boundaries OK
release consistency OK
AST OK: 542 files; BOM files: 37
```

Environment limitation: `tests/test_package_signature_warn_only.py` is not collectable in the repository `.venv` because `cryptography` is absent. E15 must not claim the signature suite has been verified unless that dependency is available and the test actually runs.

## Direct EditorContext dependency audit

The phase-start AST audit found **29 runtime files** with a direct import of `core.VitaLoom.core.editor_context`. Runtime dynamic attachments also include `event_bus`, `kernel`, `simulation_transport`, `simulation_coordinator`, `repo_root`, `application_root`, project configuration/cache fields, and legacy UI state.

| Concern | Current consumers / evidence | Owner, scope, lifetime | E15 ruling |
|---|---|---|---|
| L1 capability registry | EditorKernel, PlayerShell, Project World/PS/SR/package/command consumers | one composed VitaLoom Editor, Player, or headless Host | Already owned by E14; reuse `RuntimeCapabilityRegistry`, do not wrap it in a new context. |
| String runtime events | about 26 uses of dynamic `event_bus`; plugins call `subscribe/unsubscribe/publish` | one composed L1 Host; synchronous in-process dispatch; released with Host/plugin lifecycle | First extraction candidate: Qt-free narrow Interface plus headless Implementation and legacy Qt signal Adapter. |
| Project World facts/session | project manager, scene manager/switcher, project wizard, assets | one L4 Project World within an L1 Host | Reuse E11/E12 Project World capability/session/ownership Modules; do not duplicate fields in a new Host context. |
| Selection/scene/mode | Inspector, outline, tools, viewports, project/scene legacy managers | legacy editor UI session; mutable and signal-driven | Keep UI-only state and PyQt signals in legacy `EditorContext` until a second non-Qt Host demonstrates a real seam. |
| Kernel/widget/canvas/layout | EditorKernel, Inspector, viewport/layout code | legacy Qt Editor Host only | Explicitly UI-only; never place in a Qt-free runtime Host Interface. |
| Simulation attachment | GameViewport, simulation control, Player/runtime hosts | composed Host / active simulation session | Prefer existing coordinator/transport Modules or registry capabilities; do not keep expanding dynamic context fields. |
| Enum/process-global event systems | `core/api/event_system.py`, `core/api/events.py` | separate legacy global namespaces and semantics | Do not merge with the Host-scoped string runtime event bus in E15. Audit/migration requires a later explicit gate. |
| Plugin load context | `PluginLoader -> plugin.on_load(kernel.get_context())` | plugin activation within Editor/Player Host | Preserve compatibility initially; migrate only concrete non-UI consumers to narrow seams. Do not replace it with another universal context object. |

## Phase-start dependency classification

### Shared runtime event consumers

- Project World open/close and scene switching publish lifecycle events.
- Inspector, library browser, console, viewports, and editor extensions subscribe to or publish string events.
- Editor and Player each construct a Host-scoped event bus.
- No production consumer of the current Qt bus was found to access `event_fired` or `subscribers` directly; those are Adapter internals rather than the shared runtime Interface.

### UI-only consumers retained in the legacy Adapter

- `selection_changed`, `project_changed`, `project_modified_changed`, and `mode_changed` are PyQt signals.
- `kernel`, widgets, docks, canvas, layouts, selection UI, and most viewport interaction remain legacy Qt Host ownership.
- E15 does not select a replacement UI toolkit and does not delete PyQt.

### Separate event systems that must not be conflated

`core/VitaLoom/kernel/event_bus.py` currently provides Host-scoped string events with `subscribe/unsubscribe/publish` and a Qt signal bridge. `core/api/event_system.py` is an Enum/Event process-global singleton with `register/unregister/emit`; `core/api/events.py` is another global string bus. Their owner, lifetime, key namespace, duplicate-subscription rules, payload type, and lifecycle differ. Similar names are not sufficient reason to merge them.

## Initial Interface hypothesis

1. Add a Qt-free `RuntimeEventBus` Protocol and `InMemoryRuntimeEventBus` Implementation under `core/VitaLoom/core/`.
2. The Interface is only `subscribe(event_name, callback)`, `unsubscribe(event_name, callback)`, and `publish(event_name, data=None)`.
3. Event names must be non-empty strings and callbacks must be callable. Invalid Interface use fails explicitly before state mutation.
4. Dispatch is synchronous and subscription-ordered. One callback failure is logged and does not stop later callbacks.
5. Duplicate subscriptions preserve current legacy behavior unless migration evidence requires a deliberate contract change.
6. The legacy PyQt `kernel.event_bus.EventBus` becomes an Adapter/decorator over the Qt-free Implementation and adds only the `event_fired` signal.
7. EditorKernel and PlayerShell receive an explicit optional event-bus composition seam. They may use the Qt Adapter by default, while tests/headless composition can inject the Qt-free Implementation.
8. `EditorContext.event_bus` remains a compatibility view during E15; it is not the Interface owner.
9. No process-global singleton and no new universal `RuntimeHostContext` is introduced.

This is a hypothesis until red tests and compatibility checks prove it.

## Implementation sequence

1. Freeze the phase plan and dependency classification before production changes.
2. Add Qt-blocked import tests proving the new event Module does not import PyQt.
3. Add red tests for strict validation, duplicate behavior, ordered dispatch, callback failure isolation, exact unsubscribe, and per-instance isolation.
4. Add behavior tests for two real Adapters/compositions: the headless in-memory Implementation and the legacy Qt signal Adapter; verify Editor and Player preserve an explicitly injected event bus instance.
5. Implement the Qt-free event Module and refactor the Qt EventBus to delegate without changing plugin-facing method names.
6. Add explicit Editor/Player composition parameters and preserve existing defaults/lifecycle.
7. Run focused event, plugin lifecycle, Project World, command/Inspector, SR/PS, Player/export, package/manifest, and architecture checks.
8. Run the full suite while honestly excluding only the unavailable signature file, then run Qt-blocked import, AST, BOM, and changed-region whitespace checks.
9. Update `CONTEXT.md`, `docs/mainline_status.md`, this plan, and create exactly one fresh-session prompt for the next Gate.

## Acceptance evidence required

- New event Interface imports with PyQt imports blocked.
- Headless and Qt Adapters satisfy the same behavioral Interface.
- Editor and Player preserve explicitly supplied bus identity.
- Existing plugin `on_load(editor_context)` compatibility remains operational.
- Event callback errors remain isolated and observable through logging.
- No L0 imports of L1 runtime code and no promotion of L2/L3/L4 into peer FrameCore plugins.
- `.pond`, AI Command Registry, Inspector command binding, SR2D seams, manifests, Player/export, and L3/L4 lifecycle regressions remain green.

## Explicit non-goals

- Do not remove PyQt or choose a new UI Host.
- Do not make `EditorContext` disappear in one batch.
- Do not introduce a universal Host context, process-global event singleton, or hidden bridge to L0.
- Do not merge the three existing event namespaces merely because they are named “EventBus”.
- Do not move nested engine plugins out of the single `lotucosm-vitaloom` L1 plugin.
- Do not claim OpenGL default readiness, native acceleration completion, signature verification, or whole-project completion.

## Completion evidence

- Red state: `9 failed` before the Module and composition seams existed.
- E14/E15 plus plugin/Project World focused regression: `73 passed`.
- Full suite excluding only the unavailable signature file: `1200 passed, 25 skipped, 34 subtests passed in 123.71s`.
- Architecture gates: `project plugin model OK`, `core boundaries OK`, `GUI boundaries OK`, `release consistency OK`.
- Changed Python AST: `6 files OK`; changed-region `git diff --check` passed.
- The signature limitation remains unchanged: `cryptography` is absent, so `tests/test_package_signature_warn_only.py` was not collected.

## Unique next Gate

**Phase E16 — Plugin Activation Context Projection and Legacy UI Context Compatibility Authority.** Audit every real `plugin.on_load(editor_context)` consumer, introduce only the narrow runtime/event/capability projection proven by non-UI plugins, retain an explicit legacy UI context view for Dock/viewport Adapters, and do not create another universal Host context or move nested plugins outside the L1 engine plugin.
