# 2026-07-18 Downstream Extension Operator Inspection and Failed-Lifecycle Recovery Authority

## Purpose

Continue the user-confirmed nested framework topology without promoting UI adapters into architecture authority:

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and downstream plugin-host framework
      -> versions/<version>/runtime (versioned runtime boundary)
          -> L2 vitalloom.* capability/domain packages
          -> L3 engine extension plugins/adapters
          -> L4 project addons scoped to one Project World
```

Phase E5 made downstream-extension discovery and lifecycle planning deterministic and Qt-free, but its reports are only raw Adapter fields. Operators cannot inspect one canonical host snapshot, list current recovery work, reject stale recovery requests, or invoke one explicitly confirmed normal lifecycle retry through the shared command registry.

## Starting truth

- `PluginLoader.last_project_addon_discovery_report` and `last_lifecycle_report` are JSON-safe but have no shared operator inspection Interface or stable report identity.
- blocked discovery can preserve the previous Project World's embedded catalog, so the requested Project World and the retained catalog are distinct facts that must not be collapsed.
- failed activation/deactivation callbacks may have partial third-party side effects; no generic rollback exists.
- `plugin.list` and `plugin.resolve` inspect project manifest/package resolution, not the live L1 downstream plugin Host.
- package transaction recovery already proves the project/id/action confirmation-binding pattern, but lifecycle recovery is in-memory Host state and must reject stale snapshots before any callback.
- CLI/MCP may run without a live editor Host. Commands must then fail explicitly rather than importing PyQt or fabricating state.

## Decisions

### 1. Qt-free operator Module

Add `core/VitaLoom/project/plugin_host_operator.py` as the authority Module. Its Interface owns:

- deterministic live Host inspection snapshots;
- exact catalog, active, failed, discovery and lifecycle facts;
- requested Project World versus retained embedded-catalog Project World facts;
- derived `settled / blocked / failed / partial / not_run` operator status;
- stable SHA-256 report identity over canonical JSON facts;
- recovery listing and exact confirmation binding;
- stale project/report/action rejection before mutation;
- a Qt-free weak Adapter binding seam for same-process UI/MCP/command adapters.

The Module imports no PyQt6 and does not call plugin callbacks itself.

### 2. Shared command surface

Register three commands in the existing shared registry:

```text
plugin.host.inspect
plugin.host.recovery.list
plugin.host.recovery.resolve
```

`inspect` and `list` are read-only. `resolve` is mutating, non-undoable, and requires:

- exact current Project World path;
- exact current report id;
- an action currently offered by the authority;
- exact operator confirmation binding project/report/action.

The command Adapter first uses `context["plugin_host_operator"]` when explicitly supplied, then the Qt-free live Adapter binding. No live Host returns `plugin_host_unavailable`; it must not import `EditorContext` or PyQt.

### 3. Narrow recovery action

The only E6 mutation action is:

```text
retry_project_lifecycle
```

It re-runs the normal E5 path only:

1. revalidate that the supplied project/report still matches the current inspection;
2. re-read the current Project World's `project.json` as a JSON object;
3. run normal authoritative L4 manifest discovery;
4. only if discovery is ready, run normal project lifecycle sync;
5. return before/after inspection and exact discovery/lifecycle reports.

It does not force-import, force-unload, bypass protected plugins, edit manifests, clear failures blindly, or invent rollback. For failed/partial callback reports the recovery record explicitly warns that manual repair or process restart may still be required; the exact operator confirmation makes the retry deliberate but does not claim side-effect rollback.

### 4. Project/report identity

The inspection report includes:

- `project_path`: latest requested/opened Project World;
- `embedded_catalog_project_path`: Project World whose L4 catalog is currently retained, if known;
- normalized catalog entries;
- active and failed plugin ids;
- discovery and lifecycle reports;
- derived status and diagnostics;
- `report_id` and offered recoveries.

The report digest excludes generated confirmation strings and is recomputed from canonical facts. Any catalog/report/active/project change invalidates a previously issued recovery request.

### 5. Adapter convergence

`PluginLoader` remains the current Editor/PyQt Host Adapter. It gains a small operator Interface that projects its state into the Qt-free Module and executes only the validated normal retry. PyQt panels may call the shared commands later, but E6 adds no recovery panel and places no rule in UI code.

## Defensive test matrix

- inspection is deterministic and JSON-safe;
- report identity changes when project, catalog, active set, failure, discovery or lifecycle facts change;
- settled/not-run hosts offer no mutation recovery;
- blocked/failed/partial hosts list exactly one narrow retry with risk facts;
- requested Project World and retained embedded-catalog Project World remain distinct;
- project mismatch, stale report id, unsupported action and bad confirmation fail closed;
- stale requests execute zero discovery/sync/plugin callbacks;
- recovery re-reads `project.json`, runs discovery before sync, and stops if discovery blocks;
- command specs are present, read-only flags are correct, and resolve is mutating/non-undoable;
- no live Host returns `plugin_host_unavailable`;
- Qt-free operator Module imports without PyQt6;
- no L3/L4 fact enters the FrameCore L1 manifest or `vitalloom.*` capability catalog.

## Verification

Focused:

```powershell
python -B -m pytest -q tests/test_plugin_host_operator.py tests/test_plugin_host_operator_commands.py tests/test_plugin_loader_operator_recovery.py tests/test_plugin_host_lifecycle.py tests/test_plugin_loader_lifecycle_authority.py tests/test_engine_plugin_host_architecture.py
```

Guardrails:

```powershell
python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B tools/check_gui_boundaries.py
python -B tools/check_release_consistency.py
```

Also run changed-module AST/import smoke, targeted whitespace checks, and `git diff --check`. Record real PyQt/symlink skips without fake Qt or fake filesystem behavior.

## Non-goals

- replacing PyQt6 or selecting a successor app shell;
- a recovery GUI panel;
- durable lifecycle receipt persistence or cross-process lifecycle locks;
- force import/unload/reload;
- generic rollback of arbitrary third-party callback side effects;
- watcher/hot-reload redesign;
- changing `.pond`, AI command registry semantics, Inspector binding, SR2D, package manifests, project manifests, or L0/L1/L2/L3/L4 topology.

## Completion and next gate

E6 completes only when the Qt-free operator Module, command surface, PluginLoader Adapter, stale/confirmation checks, tests, guardrails, `docs/mainline_status.md`, and a fresh-session prompt agree.

After E6 closes, the single next Gate is **Phase E7 — Downstream Extension Hot-Reload / Watcher Lifecycle Authority Audit and Contract Decision**.
