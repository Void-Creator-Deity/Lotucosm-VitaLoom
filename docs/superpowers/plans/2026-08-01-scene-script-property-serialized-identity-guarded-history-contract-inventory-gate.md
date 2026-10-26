# E184 Scene Script-Property Serialized-Identity Guarded-History Contract Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E183 retained `entity.set_property` as compatibility-only because arbitrary dotted JSON paths, unbounded values, structure materialization, and whole-entity snapshot restoration do not establish a safe field-level history contract.

## Decision

**No migration.** `script.set_property` remains a compatibility command with representative durable history; it is not approved as a guarded scene-owned history domain.

The audit found no stable serialized script identity or bounded field contract:

- A scan of all five workspace `.pond` scenes found 55 entities carrying `scripts` lists and 31 script objects. Every sampled script object used only `name`, `type`, and `properties`; none carried a serialized script `id`. The samples have no duplicate aliases within one entity, but that is sample data rather than a schema or uniqueness invariant.
- The runtime command accepts a caller-supplied `script` selector and selects the **first** script whose `name`, `type`, or `path` equals it. It neither requires a unique match nor records a script index or immutable identifier. Name/type/path are aliases, not serialized identity.
- The active Inspector derives script controls from script names only (`script_<name>_<dotted-path>`). Its UI helper likewise changes the first matching name. A reorder, replacement, duplicate alias, or name/type/path collision has no exact target proof.
- The command schema constrains only scene path, entity id, script selector, and arbitrary dotted property path. `value` is not bounded by a field-specific schema. Both the runtime and Inspector helpers materialize missing `properties` dictionaries and nested dictionaries, replacing malformed non-dictionary structure along the way.
- Registry inverse simply replays `script.set_property` with `old_value` and redo with `new_value`; neither carries an expected-current field, script, list, entity, or full-scene witness. Fresh-Registry durable replay compatibility therefore cannot reject a stale alias/reorder/replacement before write.

## Authority and compatibility retained

- No runtime, Registry, Inspector, `.pond`, manifest, or audit-schema behavior changed.
- Scene-owned script rejection remains terminal: it cannot fall through to a local `CommandStack`, legacy sync, success side effect, or canonical rehydrate.
- E175/E177 non-scene and ownerless local fallback remains unchanged.
- Audit remains schema v4 with `unified_undo_redo_runtime=false`. Representative durable replay is not a global unified-history claim.

## Verification proof

Focused relevant suite:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:PYTHONDONTWRITEBYTECODE = '1'
& '.\.venv\python.exe' -B -m pytest -q `
  tests\test_inspector_property_mapping.py `
  tests\test_ai_command_durable_project_undo.py `
  tests\test_ai_command_audit_status_tool.py `
  tests\test_ai_command_audit_history.py
# 31 passed, 3 subtests passed in 2.57s
```

The suite confirms current active Inspector routing, terminal failure behavior, script-property durable replay compatibility, audit records, and audit-status expectations. The source inventory establishes why that compatibility behavior is not a stale-safe identity contract.

`py_compile` passed for command runtime, Registry, Inspector binding/dock, and relevant test modules. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. Repository-wide pytest was intentionally not run because E184 is a no-runtime-change inventory/decision gate.

## Fallback and concrete unblock path

Keep direct script-property calls compatible, but do not add expected-current guards to the existing alias-plus-dotted-path surface and do not promote it as safe semantic history.

A future migration must first define one separately named script-field command with: a serialized immutable script identity or a schema-enforced unique identity plus stable index semantics; one canonical property location; a bounded value schema and normalization rule; a field-level expected-current inverse; same-process stale/retry proof; fresh-Registry durable stale/retry proof; successful `scene.open` rehydration; and terminal scene-owned rejection. It must prove duplicate aliases, reorders, replacement, and malformed nested state before extending history.

## Completion and next gate

E184 closes with no behavior change: name/type/path alias matching and arbitrary nested script mutation do not meet the serialized-identity standard.

Exactly one next gate: **E185 -- Scene Prefab Placement Durable-History Contract Inventory Gate**.