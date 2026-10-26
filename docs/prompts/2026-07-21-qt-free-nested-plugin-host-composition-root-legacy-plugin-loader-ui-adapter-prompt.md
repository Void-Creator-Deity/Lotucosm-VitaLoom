# Phase E23 -- Qt-free Nested Plugin Host Composition Root and Legacy PluginLoader UI Adapter

## Resume point

E20, E21, and E22 have extracted three Qt-free deep Modules inside the one L1 engine/product plugin version runtime:

- `RuntimePluginHost`: registry, discovery/import, dependency order, lifecycle callback execution;
- `ProjectScopedPluginHost`: L4 Project World discovery/switching/lifecycle/operator recovery;
- `ManualPluginReloadHost`: candidate-first L3 manual hot reload and truthful reports.

The architecture remains:

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom (single engine/product plugin and recursive downstream plugin-host framework)
       -> versions/1.0.0/runtime
            -> L2 capability/domain
            -> L3 engine extension / host adapter
            -> L4 Project World addon
```

The remaining composition friction is that legacy `PluginLoader` still constructs the three Hosts, aliases shared state, synchronizes lifecycle/reload observations, and performs non-UI startup/bootstrap target orchestration. This makes the PyQt-era Adapter the practical composition root even though it is no longer the rule authority.

## E23 single objective

Create one Qt-free L1 **nested plugin Host composition root** under the same version runtime. The Module should construct and expose the existing three Host Modules over exactly one `RuntimePluginHost` registry and own their shared non-UI composition/report/bootstrap rules. It must be deep enough that a headless Host and the legacy Editor Adapter can use the same Interface without understanding sub-Host wiring.

A likely path is:

```text
core/VitaLoom/core/nested_plugin_host.py
```

Choose the final name in the E23 plan after auditing existing domain language. Do not create a second registry, second root framework, or replacement manifest model.

## Required first actions

1. Write the E23 phase plan before production edits.
2. Audit every remaining `PluginLoader` method and classify it as:
   - Qt-free nested Host composition/bootstrap authority;
   - narrow compatibility delegation/observation alias;
   - concrete legacy UI contribution/command/signal/editor-ready cleanup Adapter duty.
3. Add red tests proving a headless composition can construct the three existing Hosts over one registry, publish coherent lifecycle/reload facts, discover/bootstrap extensions, switch L4 Project Worlds, and hot reload without importing PyQt or legacy plugin interfaces.
4. Add static tests proving Loader delegates composition/bootstrap and no longer constructs the sub-Hosts directly.

## Composition requirements

- Exactly one `RuntimePluginHost` owns registry/loaded/dependency/source/scope/protection facts.
- `ProjectScopedPluginHost` and `ManualPluginReloadHost` must compose that exact object.
- Shared lifecycle and reload reports must remain strict-JSON facts and stay visible through preserved Loader compatibility seams.
- Bootstrap target selection must preserve eager mode, Player/bootstrap package behavior, manifest authorization, activation-context rules, dependency expansion, and project-open L4 timing.
- `PluginLoader` must continue to satisfy `RuntimePluginHostAdapter` for concrete UI contributions, command bridge, kernel signals, legacy editor-ready behavior, cleanup, and layout settling.
- Preserve existing public Loader methods/attributes unless a tested compatibility property/delegate provides the same behavior.
- Require at least two real compositions: headless and legacy Editor Adapter. One adapter alone is not sufficient evidence for a reusable seam.

## Forbidden directions

- no Unity/Godot/Unreal/Electron migration;
- no new UI framework or PyQt replacement in E23;
- no Qt types, EditorKernel, LayoutManager, `kernel.plugin_loader`, or `kernel.plugin_interfaces` in the Qt-free composition root;
- no duplicated registry, plugin ID rules, activation schema, lifecycle planner, reload planner, Project World operator, or manifest authority;
- no changes to `.pond`, AI command registry, Inspector command binding, SR2D, package/project manifests, Player/export semantics, or L0-L4 topology;
- no dependency installation for the known `cryptography` signature blocker;
- no Git reset/clean/stage/commit/revert of unrelated existing work.

## E22 evidence to preserve

- headless E22 suite: `12 passed`;
- compatibility focus: `48 passed`;
- expanded regression: `131 passed, 1 skipped`;
- final full non-signature suite: `1250 passed, 25 skipped, 34 subtests passed in 99.20s`;
- project/core/gui/release guardrails all passed;
- signature-only collection remains blocked by missing `cryptography`.

Close E23 with targeted tests, architecture guardrails, a full non-signature run, truthful blocker recording, status/index/context updates, and exactly one next Gate.
