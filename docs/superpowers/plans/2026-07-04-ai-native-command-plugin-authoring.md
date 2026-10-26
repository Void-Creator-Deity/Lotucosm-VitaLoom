# AI-Native Command And Plugin Authoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make VitaLoom package command contributions discoverable, registry-backed, and testable across UI, CLI, MCP, and agent paths.

**Architecture:** Keep the existing FrameCore -> `lotucosm-vitaloom` plugin runtime boundary. The VitaLoom Command Registry remains the single semantic command surface, while `builtin/package_index.json` declares which capability packages expose those commands.

**Tech Stack:** Python, pytest, existing VitaLoom Command Registry, `tools/check_project_plugin_model.py`, JSON package catalog.

---

## Summary

Phase 5 starts after the SR2D native build/import proof gate. The next risk is not renderer or native performance; it is semantic drift between package manifests, UI actions, CLI, MCP, and agent commands.

This phase first turns the documented plugin command contract into a guard: every command declared in `runtime/builtin/package_index.json` must describe successfully through the Command Registry, and every registered command capability must resolve to a catalog package id. This catches cases where the UI or manifest claims a command belongs to a capability that project locking, package checks, or agents cannot resolve.

## Current State

- Phase 0 baseline/tracking gate passed, but the worktree remains intentionally dirty.
- Phase 1 and Phase 2 viewport gates passed with OpenGL still opt-in and QPainter still default.
- Phase 3 Python SR2D broadphase diagnostic gate passed; `bruteforce` remains default.
- Phase 4 native proof-tooling gate passed; C++/Rust extensions remain unavailable on this machine.
- Phase 5 baseline health check passed on 2026-07-04:
  - `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py` -> `41 passed in 6.62s`
  - `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`
  - `python -B tools/audit_worktree_groups.py` -> `total: 953`

## Scope

- Add a registry/catalog consistency test for builtin package command contributions.
- Extend `tools/check_project_plugin_model.py` with the same registry/catalog guard.
- Align any builtin command `capability` values that point at non-catalog ids.
- Update Phase 5 evidence in `docs/mainline_status.md`.
- Add a fresh-session prompt for continuing Phase 5.

## Non-goals

- Do not change the plugin-shaped architecture.
- Do not migrate the GUI shell or renderer.
- Do not merge `CommandStack` and Command Registry in this first gate.
- Do not rewrite Inspector or SceneViewport widgets unless a failing command-binding test requires it.
- Do not install native toolchains or claim native acceleration.

## Files

- Modify: `tests/test_plugin_command_contributions.py`
  - Adds direct pytest/unittest coverage for package catalog command declarations and registry capability ownership.
- Modify: `tools/check_project_plugin_model.py`
  - Adds the same guard to the standalone project/plugin model checker.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
  - Aligns builtin command capabilities only where the test proves they point at a non-catalog package.
- Add: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`
  - Fresh-session continuation prompt for Phase 5.
- Modify: `docs/INDEX.md`
  - Links this plan and prompt under Agent execution material.
- Modify: `docs/mainline_status.md`
  - Records Phase 5 baseline and first gate evidence.
- Modify: `tests/test_mcp_command_adapter.py`
  - Adds representative CLI/MCP scene edit equivalence coverage.
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
  - Adds thin MCP-facing helpers for representative scene edits without duplicating command semantics.

## Step-by-step Tasks

### Task 1: Add the registry/catalog consistency test

**Files:**
- Modify: `tests/test_plugin_command_contributions.py`

- [ ] **Step 1: Write the failing test**

Add imports and this test method to `PluginCommandContributionTests`:

```python
    def test_builtin_package_commands_resolve_to_registry_capabilities(self) -> None:
        from core.VitaLoom.commands.registry import reset_command_registry
        from core.VitaLoom.core.bundle_paths import resource_root

        registry = reset_command_registry()
        catalog_path = resource_root() / "builtin" / "package_index.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        packages = [row for row in catalog.get("packages", []) if isinstance(row, dict)]
        package_ids = {str(row.get("id", "")).strip() for row in packages}
        command_ids = {
            str(command_id).strip()
            for row in packages
            for command_id in row.get("commands", [])
            if str(command_id).strip()
        }

        missing: list[str] = []
        invalid_capabilities: list[str] = []
        for command_id in sorted(command_ids):
            try:
                spec = registry.describe(command_id)
            except KeyError:
                missing.append(command_id)
                continue
            capability = str(spec.get("capability", "")).strip()
            if capability not in package_ids:
                invalid_capabilities.append(f"{command_id}:{capability}")

        self.assertEqual([], missing)
        self.assertEqual([], invalid_capabilities)
```

Also add `import json` at the top of the file.

- [ ] **Step 2: Run the test and verify the red failure**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plugin_command_contributions.py::PluginCommandContributionTests::test_builtin_package_commands_resolve_to_registry_capabilities
```

Expected: fail with invalid capabilities for `asset.*` commands pointing at `vitalloom.asset.pipeline`.

### Task 2: Make builtin command capabilities catalog-resolvable

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`

- [ ] **Step 1: Align asset command capabilities**

Change these command specs from:

```python
capability="vitalloom.asset.pipeline",
```

to:

```python
capability="vitalloom.lotuspond.runtime",
```

for:

- `asset.scan`
- `asset.create`
- `asset.import`
- `asset.validate`
- `asset.dependencies`
- `asset.export_closure`

Do not change command ids, handlers, schemas, mutation flags, or public return shape.

- [ ] **Step 2: Run the focused test and verify green**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plugin_command_contributions.py::PluginCommandContributionTests::test_builtin_package_commands_resolve_to_registry_capabilities
```

Expected: pass.

### Task 3: Add the standalone checker guard

**Files:**
- Modify: `tools/check_project_plugin_model.py`

- [ ] **Step 1: Extend the checker**

After loading `catalog`, build `package_ids` and `catalog_command_ids`, then load the Command Registry and verify:

```python
    package_ids = {
        str(pkg.get("id", "")).strip()
        for pkg in catalog.get("packages", [])
        if isinstance(pkg, dict) and str(pkg.get("id", "")).strip()
    }
    catalog_command_ids: set[str] = set()
```

Inside the existing package loop, add each string command id to `catalog_command_ids`.

After the package loop, add:

```python
    from core.VitaLoom.commands.registry import reset_command_registry

    registry = reset_command_registry()
    for command_id in sorted(catalog_command_ids):
        try:
            spec = registry.describe(command_id)
        except KeyError:
            violations.append(f"{command_id} is declared in builtin package_index.json but not registered")
            continue
        capability = str(spec.get("capability", "")).strip()
        if capability not in package_ids:
            violations.append(
                f"{command_id} declares unresolved command capability {capability!r}; "
                "capability must match a builtin package id"
            )
```

- [ ] **Step 2: Verify the checker**

Run:

```bash
python -B tools/check_project_plugin_model.py
```

Expected: `project plugin model OK`.

### Task 4: Update docs and execution material

**Files:**
- Add: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`
- Modify: `docs/INDEX.md`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Add the fresh-session prompt**

The prompt must instruct the next C0dex session to:

- Read `AGENTS.md`, `docs/mainline_status.md`, this plan, `docs/ai_native_command_layer.md`, and `docs/plugin_command_contract.md`.
- Preserve plugin-shaped architecture.
- Continue Phase 5 by checking UI/CLI/MCP/agent parity through Command Registry.
- Distinguish command registry payloads, UI wiring, MCP adapter behavior, undo/redo, and audit history.
- Run the Phase 5 verification commands before claiming progress.

- [ ] **Step 2: Link the plan and prompt**

Add rows under `docs/INDEX.md` Agent execution material:

```markdown
| VitaLoom Phase 5 AI-native command/plugin authoring plan | [superpowers/plans/2026-07-04-ai-native-command-plugin-authoring.md](superpowers/plans/2026-07-04-ai-native-command-plugin-authoring.md) |
| VitaLoom Phase 5 AI-native command/plugin authoring prompt | [prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md](prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md) |
```

- [ ] **Step 3: Update mainline status**

Record:

- Phase 5 baseline test result.
- The new registry/catalog gate.
- Any skipped or unavailable work.
- Next gate: representative scene edit equivalence through CLI and MCP, then UI binding audit for the same command.

### Task 5: Run verification

**Files:**
- No new runtime files beyond the task files.

- [ ] **Step 1: Focused Phase 5 tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py
```

Expected: all pass.

- [ ] **Step 2: Guardrails**

Run:

```bash
python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tests/test_plugin_command_contributions.py tools/check_project_plugin_model.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
```

Expected: all pass. Git may warn about LF/CRLF normalization; whitespace errors must be absent.

### Task 6: Prove representative CLI/MCP scene edit equivalence

**Files:**
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing MCP helper/equivalence test**

Add a test that creates two temporary projects under `workspace/`, runs `entity.create` through the CLI for one scene, runs the same edit through `mcp_adapter.create_entity(...)` for the other scene, and compares normalized command results plus normalized `.pond` output. The first run should fail because `mcp_adapter.create_entity` does not exist yet.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_create_entity_matches_cli_scene_edit_output
```

Expected: fail with `AttributeError` for missing `create_entity`.

- [ ] **Step 3: Add the thin MCP wrapper**

Implement:

```python
def create_entity(scene_path: str, entity: Mapping[str, Any]) -> dict[str, Any]:
    return run_command("entity.create", {"scene_path": scene_path, "entity": dict(entity)})
```

Do not duplicate scene mutation logic in the MCP adapter.

- [ ] **Step 4: Run focused green test and UI bridge audit**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_create_entity_matches_cli_scene_edit_output tests/test_scene_viewport_command_bridge.py
```

Expected: pass, proving MCP helper and existing UI bridge both dispatch the same command-layer shape.

### Task 7: Extend CLI/MCP equivalence to transform edits

**Files:**
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing transform equivalence test**

Add a test that creates two temporary scenes with the same `hero` entity, runs `transform.set` through the CLI for one scene, runs `mcp_adapter.set_transform(...)` for the other scene, and compares normalized command results plus normalized `.pond` output. The first run should fail because `mcp_adapter.set_transform` does not exist yet.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_transform_matches_cli_scene_edit_output
```

Expected: fail with `AttributeError` for missing `set_transform`.

- [ ] **Step 3: Add the thin MCP wrapper**

Implement a wrapper that builds the `transform.set` payload from provided fields and delegates to `run_command`. Do not duplicate scene mutation logic in the MCP adapter.

- [ ] **Step 4: Run focused green test and Inspector payload audit**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_transform_matches_cli_scene_edit_output tests/test_inspector_command_binding.py
```

Expected: pass, proving MCP transform editing and Inspector transform payload binding share the same command-layer shape.

### Task 8: Extend CLI/MCP equivalence to script property edits

**Files:**
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing script property equivalence test**

Add a test that creates two temporary scenes with the same `hero` entity and `brain` script, runs `script.set_property` through the CLI for one scene, runs `mcp_adapter.set_script_property(...)` for the other scene, and compares normalized command results plus normalized `.pond` output. The first run should fail because `mcp_adapter.set_script_property` does not exist yet.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_script_property_matches_cli_scene_edit_output
```

Expected: fail with `AttributeError` for missing `set_script_property`.

- [ ] **Step 3: Add the thin MCP wrapper**

Implement a wrapper that builds the `script.set_property` payload from `scene_path`, `entity_id`, `script`, `property_path`, and `value`, then delegates to `run_command`. Do not duplicate scene mutation logic in the MCP adapter.

- [ ] **Step 4: Run focused green test and Inspector script payload audit**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_script_property_matches_cli_scene_edit_output tests/test_inspector_command_binding.py
```

Expected: pass, proving MCP script property editing and Inspector script payload binding share the same command-layer shape.

### Task 9: Record undo/redo and audit-history status

**Files:**
- Create: `tools/check_ai_command_audit_status.py`
- Create: `tests/test_ai_command_audit_status_tool.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing status tool test**

Add a test that runs `python -B tools/check_ai_command_audit_status.py`, parses JSON output, and asserts:

- `entity.create`, `transform.set`, and `script.set_property` all have `mutates=true` and `undoable_metadata=true`.
- `CommandStack` exists but is not integrated into `CommandRegistry.run`.
- Representative scene edit commands currently have event envelopes only, not durable audit history.
- Overall status is `metadata_and_events_only`.

The first run should fail because the tool does not exist yet.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_status_tool.py
```

Expected: fail because `tools/check_ai_command_audit_status.py` is missing.

- [ ] **Step 3: Implement the status tool**

The tool must inspect the current Command Registry and source files. It must not mutate projects or create fake undo/audit behavior. It should return exit code `0` when the status is accurately recorded.

- [ ] **Step 4: Run focused green test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_status_tool.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with JSON clearly distinguishing metadata, events, CommandStack existence, missing registry undo runtime integration, and missing durable audit history.

### Task 10: Add minimal durable audit history for scene edit commands

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- Create: `tests/test_ai_command_audit_history.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `tests/test_mcp_command_adapter.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing durable audit test**

Add a test that runs `entity.create`, `transform.set`, and `script.set_property` through the Command Registry against a temporary project under `workspace/`. The test must assert each successful result includes `audit_id` and `audit_path`, and that `.vitalloom/command_audit.jsonl` contains one JSON entry per command with `command_id`, `events`, `payload`, and `result`.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_history.py
```

Expected: fail because successful scene edit results do not yet include `audit_id` or write `command_audit.jsonl`.

- [ ] **Step 3: Implement registry-level audit append**

After a mutating command succeeds, derive the project root from `scene_path` or `project_path`, append a JSON line to `.vitalloom/command_audit.jsonl`, and add `audit_id` plus `audit_path` to the result object. Do not add undo/redo runtime behavior in this task.

- [ ] **Step 4: Update status tooling**

Update `tools/check_ai_command_audit_status.py` and its test so it reports durable audit history as present, while still reporting `unified_undo_redo_runtime=false` and `undo_redo=metadata_only`.

- [ ] **Step 5: Run focused green tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_history.py tests/test_ai_command_audit_status_tool.py tests/test_mcp_command_adapter.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with durable audit history present and undo/redo runtime still not unified.

### Task 11: Add minimal CommandRegistry undo/redo bridge for representative scene edits

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- Create: `tests/test_ai_command_undo_redo_bridge.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing undo/redo bridge test**

Add a test that runs `entity.create`, `transform.set`, and `script.set_property` through the Command Registry against a temporary project, then calls registry undo/redo helpers and verifies the `.pond` state changes back and forward. The first run should fail because the registry has no undo/redo bridge helpers yet.

- [ ] **Step 2: Run the focused red test**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_bridge.py
```

Expected: fail because the registry does not expose undo/redo bridge methods.

- [ ] **Step 3: Implement the minimal bridge**

Implement a per-registry in-memory undo/redo stack for the representative scene edit commands only:

- `entity.create` undo -> `entity.delete`; redo -> original `entity.create`
- `transform.set` undo -> `transform.set` with old values from command result; redo -> original `transform.set`
- `script.set_property` undo -> `script.set_property` with old value from command result; redo -> original `script.set_property`

Append audit records for undo/redo actions too. Do not migrate the legacy UI `CommandStack` in this task.

- [ ] **Step 4: Update status tooling**

Update `tools/check_ai_command_audit_status.py` and its test so it reports durable audit history and representative registry undo/redo as present, while still distinguishing that the legacy UI `CommandStack` is not the runtime mechanism.

- [ ] **Step 5: Run focused green tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with status showing durable audit history and representative registry undo/redo bridge present.

**Observed 2026-07-04:** `CommandRegistry` exposes `undo_last()` and `redo_last()` with a per-registry in-memory stack for `entity.create`, `transform.set`, and `script.set_property`. Undo/redo operations delegate to registered commands and append durable audit records with explicit `action` values. The status tool reports `durable_audit_with_representative_undo`, `representative_undo_redo_runtime=true`, and `unified_undo_redo_runtime=false` to avoid overstating cross-session replay or legacy UI `CommandStack` integration.

### Task 12: Expose undo/redo through command-facing agent paths

**Files:**
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Create: `tests/test_ai_command_undo_redo_command_path.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `docs/mainline_status.md`

- [ ] **Step 1: Write the failing command-path test**

Add a test proving `command.undo` and `command.redo` are registered, can be invoked through `CommandRegistry.run(...)`, mutate the same registry session's previous representative scene edit, and append audit actions. Add a second check that MCP helpers delegate to the same command ids. The first run should fail because the command ids and MCP helpers do not exist yet.

- [ ] **Step 2: Implement command-facing undo/redo**

Register `command.undo` and `command.redo` in the runtime command catalog, but delegate their handlers back to `CommandRegistry.undo_last()` / `redo_last()` through context. Avoid pushing undo/redo commands into the undo stack themselves. Do not claim CLI cross-process undo, because the current bridge is intentionally in-memory and per-registry.

- [ ] **Step 3: Add thin MCP helpers**

Add `mcp_adapter.undo_last()` and `mcp_adapter.redo_last()` as wrappers over `run_command("command.undo", {})` and `run_command("command.redo", {})`. Do not duplicate stack logic in the adapter.

- [ ] **Step 4: Update status tooling**

Update the audit status tool so it distinguishes:

- representative registry undo/redo bridge
- command-facing undo/redo path
- legacy UI `CommandStack` integration, still false
- durable cross-session replay, still false

- [ ] **Step 5: Run focused green tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with command-facing undo/redo present and full cross-session replay still explicitly false.

## Tests First

The first production change is blocked until `tests/test_plugin_command_contributions.py::PluginCommandContributionTests::test_builtin_package_commands_resolve_to_registry_capabilities` fails for the expected unresolved `asset.*` capability reason.

## Verification Commands

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_plugin_command_contributions.py::PluginCommandContributionTests::test_builtin_package_commands_resolve_to_registry_capabilities
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_create_entity_matches_cli_scene_edit_output tests/test_scene_viewport_command_bridge.py
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_transform_matches_cli_scene_edit_output tests/test_inspector_command_binding.py
python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_script_property_matches_cli_scene_edit_output tests/test_inspector_command_binding.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_status_tool.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py
python -B tools/check_project_plugin_model.py
python -B tools/check_core_boundaries.py
python -B -m compileall -q FrameCore tools main.py player.py
git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tests/test_plugin_command_contributions.py tools/check_project_plugin_model.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py
```

## Evidence Ledger

| Item | Evidence |
|---|---|
| Phase 5 starting tests | `41 passed in 6.62s` before edits |
| Project plugin model baseline | `project plugin model OK` before edits |
| Worktree state | `tools/audit_worktree_groups.py` reported `total: 953`; no cleanup, stage, commit, revert, or delete |
| New red test | `python -B -m pytest -q -p no:cacheprovider tests/test_plugin_command_contributions.py::PluginCommandContributionTests::test_builtin_package_commands_resolve_to_registry_capabilities` failed as expected: six `asset.*` commands pointed at unresolved capability `vitalloom.asset.pipeline`. |
| New green test | After aligning six `asset.*` command specs to `vitalloom.lotuspond.runtime`, the same focused test passed: `1 passed in 0.14s`. |
| Final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py` -> `42 passed in 9.18s`. |
| Guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; `git diff --check -- docs/INDEX.md docs/mainline_status.md docs/prompts docs/superpowers/plans tests/test_plugin_command_contributions.py tools/check_project_plugin_model.py FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| CLI/MCP scene edit red test | `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_create_entity_matches_cli_scene_edit_output` failed as expected with `AttributeError` for missing `mcp_adapter.create_entity`. |
| CLI/MCP scene edit green test | After adding thin `mcp_adapter.create_entity(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_create_entity_matches_cli_scene_edit_output tests/test_scene_viewport_command_bridge.py` -> `5 passed in 0.43s`. |
| Second-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py` -> `43 passed in 7.15s`. |
| Second-gate guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| CLI/MCP transform red test | `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_transform_matches_cli_scene_edit_output` failed as expected with `AttributeError` for missing `mcp_adapter.set_transform`. |
| CLI/MCP transform green test | After adding thin `mcp_adapter.set_transform(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_transform_matches_cli_scene_edit_output tests/test_inspector_command_binding.py` -> `5 passed in 0.40s`. |
| Third-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py` -> `44 passed in 7.12s`. |
| Third-gate guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| CLI/MCP script red test | `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_script_property_matches_cli_scene_edit_output` failed as expected with `AttributeError` for missing `mcp_adapter.set_script_property`. |
| CLI/MCP script green test | After adding thin `mcp_adapter.set_script_property(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_mcp_command_adapter.py::McpCommandAdapterTests::test_set_script_property_matches_cli_scene_edit_output tests/test_inspector_command_binding.py` -> `5 passed in 0.37s`. |
| Fourth-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py` -> `45 passed in 7.22s`. |
| Fourth-gate guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| Undo/audit status red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_status_tool.py` failed as expected because `tools/check_ai_command_audit_status.py` was missing. |
| Undo/audit status green test | After adding `tools/check_ai_command_audit_status.py`, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_status_tool.py` -> `1 passed in 0.20s`; `python -B tools/check_ai_command_audit_status.py` reported `metadata_and_events_only`. |
| Fifth-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py` -> `46 passed in 7.76s`. |
| Fifth-gate guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| Durable audit red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_history.py` failed as expected because scene edit command results lacked `audit_id` and no `command_audit.jsonl` was written. |
| Durable audit green test | After adding registry-level audit append, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_audit_history.py tests/test_ai_command_audit_status_tool.py tests/test_mcp_command_adapter.py` -> `10 passed in 0.99s`; `python -B tools/check_ai_command_audit_status.py` reported `durable_audit_without_unified_undo`. |
| Sixth-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py` -> `47 passed in 6.59s`. |
| Sixth-gate guardrails | `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| Undo/redo bridge red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_bridge.py` failed as expected with missing `CommandRegistry.undo_last` / `redo_last`. |
| Undo/redo bridge green test | After adding the representative in-memory registry bridge, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py` -> `5 passed in 0.60s`; `python -B tools/check_ai_command_audit_status.py` reported `durable_audit_with_representative_undo`, `representative_undo_redo_runtime=true`, and `unified_undo_redo_runtime=false`. |
| Seventh-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_ai_command_undo_redo_bridge.py` -> `50 passed in 7.67s`. |
| Seventh-gate guardrails | `python -B tools/check_ai_command_audit_status.py` passed; `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| Command-facing undo/redo red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_command_path.py` failed as expected because `command.undo` / `command.redo` were not registered and `mcp_adapter.undo_last()` was missing. |
| Command-facing undo/redo green test | After adding `command.undo`, `command.redo`, and thin MCP helpers, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py` -> `15 passed in 1.53s`; `python -B tools/check_ai_command_audit_status.py` reported `command_undo_redo_path=true`, `representative_undo_redo_runtime=true`, and `unified_undo_redo_runtime=false`. |
| Eighth-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_undo_redo_command_path.py` -> `52 passed in 7.56s`. |
| Eighth-gate guardrails | `python -B tools/check_ai_command_audit_status.py` passed; `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| UI undo/redo action binding red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py` failed as expected when `core.VitaLoom.ui.command_actions` was missing, then failed on missing `EditorKernel._register_core_command_actions`. |
| UI undo/redo action binding green test | After adding `ui/command_actions.py` and the `EditorKernel` hook, `python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py` -> `8 passed in 0.59s`. |
| Ninth-gate final focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py tests/test_ai_command_cli.py tests/test_mcp_command_adapter.py tests/test_plugin_command_contributions.py tests/test_inspector_command_binding.py tests/test_scene_viewport_command_bridge.py tests/test_project_plugin_model_gate.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_undo_redo_command_path.py tests/test_ui_command_actions.py` -> `54 passed in 7.69s`. |
| Ninth-gate guardrails | `python -B tools/check_ai_command_audit_status.py` passed; `python -B tools/check_project_plugin_model.py` -> `project plugin model OK`; `python -B tools/check_core_boundaries.py` -> `core boundaries OK`; `python -B -m compileall -q FrameCore tools main.py player.py` passed with no output; scoped `git diff --check` passed with only the existing LF/CRLF warning for `docs/INDEX.md`. |
| Durable project undo red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py` failed as expected: `command.undo_project` was unknown and `mcp_adapter.undo_project` did not exist. |
| Durable project undo green test | After adding explicit `command.undo_project`, `CommandRegistry.undo_project(...)`, and `mcp_adapter.undo_project(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py` -> `2 passed in 0.25s`. |
| Durable project undo focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py` -> `17 passed in 1.85s`. `python -B tools/check_ai_command_audit_status.py` reports `representative_durable_project_undo=true`, `durable_project_redo=false`, and `unified_undo_redo_runtime=false`. |
| Durable project redo red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py` failed as expected after adding redo assertions: `command.redo_project` was unknown and `mcp_adapter.redo_project` did not exist. |
| Durable project redo green test | After adding explicit `command.redo_project`, `CommandRegistry.redo_project(...)`, and `mcp_adapter.redo_project(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py` -> `4 passed in 0.32s`. |
| Durable project redo focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py` -> `19 passed in 1.94s`. `python -B tools/check_ai_command_audit_status.py` reports `representative_durable_project_undo=true`, `representative_durable_project_redo=true`, and `unified_undo_redo_runtime=false`. |
| Live menu/toolbar undo-redo red test | `python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py::UiCommandActionTests::test_live_menu_and_toolbar_actions_trigger_command_registry` failed as expected because `register_editor_command_actions(...)` did not accept `layout_manager`. |
| Live menu/toolbar undo-redo green test | After wiring `register_editor_command_actions(...)` into real `LayoutManager.add_menu_items(...)` and `add_toolbar_items(...)`, `python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py` -> `3 passed in 0.26s`. |
| Live menu/toolbar undo-redo focused suite | `python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_undo_redo_command_path.py` -> `6 passed in 0.49s`. `python -B tools/check_ai_command_audit_status.py` reports `ui_menu_toolbar_undo_redo_binding=true` and `unified_undo_redo_runtime=false`. |

### Task 13: Bind editor UI undo/redo actions to the command path

**Files:**
- Create: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/ui/command_actions.py`
- Create: `tests/test_ui_command_actions.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`

- [ ] **Step 1: Write the failing UI action binding test**

Add a test with fake shortcut manager and fake registry proving `register_editor_command_actions(...)` registers `edit.undo` and `edit.redo`, and that triggering those callbacks calls `registry.run("command.undo", {})` and `registry.run("command.redo", {})`.

- [ ] **Step 2: Implement the narrow UI binder**

Add a small module that registers editor-level undo/redo actions with `ShortcutManager`-compatible APIs. It must delegate through `CommandRegistry.run(...)`, not legacy `CommandStack`, and it must not create a second undo stack.

- [ ] **Step 3: Verify focused UI/command tests**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py
```

Expected: pass, proving the UI action layer calls the existing command path while full durable replay remains out of scope.

### Task 14: Add representative durable project undo replay

**Files:**
- Create: `tests/test_ai_command_durable_project_undo.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`

- [ ] **Step 1: Write the failing durable project undo test**

Add a test proving a fresh `CommandRegistry` instance can undo the latest representative project-scoped edit from `.vitalloom/command_audit.jsonl`.

The test must:

- Run a representative command such as `transform.set` with one registry.
- Create a fresh registry with `reset_command_registry()`.
- Call `command.undo_project` with `project_path`.
- Assert the scene is restored, an audit entry with `action: durable_undo` is appended, and the result identifies the source audit id.

The first run should fail because `command.undo_project` is not registered.

- [ ] **Step 2: Keep session undo semantics unchanged**

`command.undo` and `command.redo` must remain current-registry-session commands. Do not silently make existing UI shortcuts or MCP `undo_last()` replay durable history.

- [ ] **Step 3: Implement narrow durable replay**

Add a registry method that reads `.vitalloom/command_audit.jsonl`, finds the latest `action=execute` entry for one of the representative commands, derives the same undo payload used by in-memory undo, then executes that undo command with `audit_action="durable_undo"` and `source_audit_id`.

Keep scope narrow:

- Support `entity.create`, `transform.set`, and `script.set_property`.
- Do not implement durable redo yet.
- Do not claim legacy UI `CommandStack` integration.
- Return clear errors when `project_path` is invalid, audit history is missing, or no supported command is replayable.

- [ ] **Step 4: Expose explicit command and MCP helper**

Register `command.undo_project` with required `project_path`, and add `mcp_adapter.undo_project(project_path)`. This command is separate from `command.undo` so existing session behavior remains visible and testable.

- [ ] **Step 5: Update status tooling and docs**

Update the audit status tool so it distinguishes:

- current-registry session undo/redo
- command-facing session path
- UI shortcut action binding
- representative durable project undo
- durable redo, still false
- full unified undo/runtime replay, still false

- [ ] **Step 6: Run focused verification**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with representative durable project undo present and full unified undo/runtime replay still explicitly false.

### Task 15: Add representative durable project redo replay

**Files:**
- Modify: `tests/test_ai_command_durable_project_undo.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/mcp_adapter.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`

- [ ] **Step 1: Write the failing durable project redo test**

Extend the durable project replay tests so a command can be executed, undone by a fresh registry through `command.undo_project`, and then redone by another fresh registry through `command.redo_project`.

The test must assert:

- scene state is restored to the original edited value,
- audit actions become `execute`, `durable_undo`, `durable_redo`,
- the redo result references both the durable undo audit and the original execute audit,
- `mcp_adapter.redo_project(project_path)` delegates to the command path.

The first run should fail because `command.redo_project` and the MCP helper do not exist.

- [ ] **Step 2: Keep session redo semantics unchanged**

`command.redo` must remain current-registry-session redo. Durable redo must be exposed only through explicit `command.redo_project`.

- [ ] **Step 3: Implement narrow durable redo replay**

Read `.vitalloom/command_audit.jsonl`, find the latest replayable `action=durable_undo` entry, find the original `action=execute` entry from its `source_audit_id`, derive the same redo payload used by in-memory redo, then execute that redo command with `audit_action="durable_redo"`.

Keep scope narrow:

- Support `entity.create`, `transform.set`, and `script.set_property`.
- Do not merge with legacy UI `CommandStack`.
- Do not claim complete linear history replay, branching history, conflict resolution, or full unified undo.
- Return clear errors when no durable redo is available or the original execute audit cannot be found.

- [ ] **Step 4: Expose explicit command and MCP helper**

Register `command.redo_project` with required `project_path`, and add `mcp_adapter.redo_project(project_path)`. This command is separate from `command.redo` so existing session behavior remains visible and testable.

- [ ] **Step 5: Update status tooling and docs**

Update the audit status tool so it reports `representative_durable_project_redo=true` while still reporting `unified_undo_redo_runtime=false` and `command_stack.registry_integrated=false`.

- [ ] **Step 6: Run focused verification**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ai_command_durable_project_undo.py tests/test_ai_command_undo_redo_command_path.py tests/test_ai_command_undo_redo_bridge.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_audit_history.py tests/test_mcp_command_adapter.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, with representative durable project undo and redo present while full unified undo/runtime replay remains explicitly false.

### Task 16: Add live menu/toolbar undo-redo smoke for editor actions

**Files:**
- Modify: `tests/test_ui_command_actions.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/ui/command_actions.py`
- Modify: `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/kernel/editor_kernel.py`
- Modify: `tools/check_ai_command_audit_status.py`
- Modify: `tests/test_ai_command_audit_status_tool.py`
- Modify: `docs/mainline_status.md`
- Modify: `docs/prompts/2026-07-04-ai-native-command-plugin-authoring-prompt.md`

- [ ] **Step 1: Write the failing live UI action smoke**

Extend `tests/test_ui_command_actions.py` with a Qt offscreen smoke that creates `QApplication`, `QMainWindow`, `QStackedWidget`, and the real `LayoutManager`, then calls `register_editor_command_actions(...)` with a fake registry.

The test must assert:

- `edit.undo` / `edit.redo` shortcuts are registered,
- real menu actions under `Edit/Undo` and `Edit/Redo` exist,
- real toolbar actions for undo and redo exist,
- triggering menu actions and toolbar actions calls `registry.run("command.undo", {})` and `registry.run("command.redo", {})`.

The first run should fail because `register_editor_command_actions(...)` does not yet accept or use `layout_manager`.

- [ ] **Step 2: Implement narrow menu/toolbar registration**

Update `register_editor_command_actions(...)` so it can receive `layout_manager` explicitly or infer `context.layout_manager`. Register the same command callbacks into existing `LayoutManager.add_menu_items(...)` and `LayoutManager.add_toolbar_items(...)`.

Do not create a second action system, do not bypass Command Registry, and do not change session undo/redo semantics.

- [ ] **Step 3: Wire `EditorKernel` through the real layout manager**

Update `EditorKernel._register_core_command_actions()` so it passes `layout_manager=self.layout_manager` to the helper after the layout manager is constructed.

- [ ] **Step 4: Update status tooling and docs**

Update `tools/check_ai_command_audit_status.py` so it distinguishes:

- shortcut action binding,
- menu/toolbar action binding,
- representative durable project undo/redo,
- full unified undo/runtime replay still false.

- [ ] **Step 5: Run focused verification**

Run:

```bash
python -B -m pytest -q -p no:cacheprovider tests/test_ui_command_actions.py tests/test_ai_command_audit_status_tool.py tests/test_ai_command_undo_redo_command_path.py
python -B tools/check_ai_command_audit_status.py
```

Expected: pass, proving real menu/toolbar actions consume the shared command path while full unified undo/runtime replay remains explicitly false.

## Fallback/Unblock Path

If a command capability is intentionally not a package id, add a documented resolver concept before changing the checker. Do not silently allow unresolved capability ids, because project lock, package discovery, and agent explanations need a stable package target.

If a UI binding test fails while this gate is being implemented, keep this gate scoped to registry/catalog consistency, record the UI failure in `docs/mainline_status.md`, and make it the next Phase 5 gate.

## Phase-End Report Template

- Phase: Phase 5 - AI-native command and plugin authoring
- Status: complete | partially complete | blocked
- Implemented: registry/catalog command contribution gate and any capability alignment
- Verified: exact commands and results
- Skipped/Unavailable: UI/manual smoke, MCP live server, native builds, or GUI context if not run
- Evidence: test output, checker output, docs paths
- Architecture impact: plugin-shaped architecture unchanged; Command Registry remains the shared semantic surface
- Remaining risks: UI/CLI/MCP equivalence gaps, undo/redo audit history, remaining SceneViewport/Inspector migrations
- Next phase: one concrete Phase 5 follow-up gate with first command or file to inspect

## Next Phase Gate

Continue Phase 5 by adding a deeper live toolbar/menu smoke around the existing `edit.undo` / `edit.redo` actions or by designing the next history boundary beyond representative durable project undo/redo. Durable audit history, representative registry undo/redo, command-facing MCP/agent paths, tested UI shortcut action binding, and representative durable project undo/redo are present; full unified undo/runtime replay is not.
