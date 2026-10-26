# Phase E35 Fresh-Session Prompt -- Qt-Free Dock Contribution Contract and Host-Owned Dock Surface Projection

Date: 2026-07-23
Status: closed

Read `AGENTS.md`, `CONTEXT.md`, `docs/mainline_status.md`, ADR-0002, ADR-0003, the completed E34 plan, and the E35 plan before editing code.

## Architecture authority

```text
L0 FrameCore
└─ L1 lotucosm-vitaloom (sole engine/product mega-plugin and recursive downstream Plugin Host)
   └─ versions/1.0.0/runtime
      ├─ L2 capability/domain Modules
      ├─ L3 engine extensions / Host Adapters
      └─ L4 Project World addons
```

The engine is the L1 plugin and itself the derived recursive plugin framework. `NestedPluginHost`, `RuntimePluginHost`, and `ProjectScopedPluginHost` remain the Host authorities. PyQt6/QPainter/Qt OpenGL, `IDockProvider`, `PluginLoader`, `LegacyEditorPluginAdapter`, `EditorKernel`, and `LayoutManager` are current/legacy Host Adapter details. Do not add a second Host, registry, catalog, manifest authority, composition root, Dock/UI framework, widget DSL, renderer framework, peer L1 plugin, or replacement shell. Do not migrate to Unity/Godot/Unreal/Electron.

## E34 closure truth

E34 is complete with Qt-free `toolbar_command` facts, canonical `simulation.transport.status`, Host-owned dynamic action projection, refresh-event deduplication, and the bounded StandardUI simulation toggle/stop slice. Evidence: red `13 failed, 6 passed`; E34 `20 passed`; focused `39 passed`; expanded `94 passed`; complete non-signature `1450 passed, 34 skipped, 34 subtests passed in 162.35s`; Editor smoke `plugins=13/20`; all four guardrails green. Signature-only collection remains blocked by missing `cryptography` in the exact repository `.venv`.

## E35 audit truth

Eight in-scope built-in `IDockProvider` implementations were audited. Stable dock identity/title/area/default visibility/close-float-move/tab facts are currently mixed with Qt widget construction, domain commands/read models, events, capability publication, and concrete layout mechanics.

Inspector is the first bounded slice because its shell facts are minimal while the real `InspectorPanel` Implementation is deep and already exercises canonical command/read-model seams. Hierarchy has a subscribed-but-not-unsubscribed `scene_hierarchy_updated` event; ProjectBrowser directly removes/adds docks on language refresh; Console owns logging/capability lifetime; PackageManager and PS Experiment own broader service lifecycles; SimulationControl has inconsistent dock reference ownership. Do not use these debts to widen the first Interface.

## E35 closure truth

E35 is complete. The existing contribution Interface now supports immutable, deterministic, JSON-safe `dock_surface` facts for the bounded Inspector shell. `LegacyEditorPluginAdapter` is the only current Qt projection authority: it maps portable placement/features, localizes titles in place, owns exact cleanup/reload, preserves delayed tabification and legacy/community fallback, and keeps the Inspector content construction explicitly as a legacy bridge.

Evidence:

- Red baseline: `13 failed, 2 passed`.
- Contract/legacy projection focus: `67 passed`.
- Expanded lifecycle and Inspector focus: `185 passed`.
- Protected regression: `164 passed in 10.30s`.
- Full non-signature suite: `1465 passed, 34 skipped, 34 subtests passed in 160.72s`.
- Editor smoke: `plugins=13/20`, zero discovery errors, layout exercise and deterministic reverse shutdown.
- Guardrails: all four green.
- Signature-only remains blocked by missing `cryptography` in the repository `.venv`; do not install silently.

E35 does not claim a replacement Host, cross-Host Inspector content parity, complete Dock migration, viewport/theme migration, native GPU geometry, OpenGL default readiness, signature verification, or whole-engine completion.

## Unique next Gate

**Phase E36 -- Qt-Free Hierarchy Dock Contribution and Host-Owned Hierarchy Refresh Ownership.** First write red tests around the existing `scene_hierarchy_updated` subscription ownership gap, then reuse the current `dock_surface` contract for the Hierarchy shell. Preserve the current Hierarchy content bridge, scene/entity command/read-model authorities, legacy/community compatibility, and the one-L0/one-L1 recursive framework-plugin topology.
