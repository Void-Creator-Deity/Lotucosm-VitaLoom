# E183 Scene Entity Generic-Property Guarded-History Contract Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E182 completed stale-safe entity lifecycle history in both directions using full ordered-scene witnesses. It deliberately did not treat `entity.set_property -> entity.restore_snapshot -> redo entity.set_property` as safe merely because an expected-current scene witness could be added.

## Decision

**No migration.** `entity.set_property` remains a compatibility command with representative durable history, but it is not approved as a stale-safe scene-owned semantic-history domain.

The required evidence does not support a field-specific contract:

- The active Inspector routes position axes to `transform.set` and script keys to `script.set_property`, but routes every other non-private entity field through `entity.set_property`. The tested `energy` route is therefore an example of a generic compatibility call, not a declared `energy` domain contract.
- The command schema requires only `scene_path`, `entity_id`, and `property_path`. Its `value` is not bounded by a field-specific JSON schema, and arbitrary dotted paths remain public.
- `_set_nested_property()` materializes missing dictionaries and replaces a non-dictionary intermediate value with a dictionary. Thus paths can alter structural fields such as `id`, `position`, and `scripts`, as well as create or replace nested object structure. The path grammar cannot represent a narrow array/object contract.
- Registry undo stores the complete pre-mutation entity and invokes `entity.restore_snapshot`, which replaces that whole entity. Neither the restore command nor the paired redo payload currently carries an expected-current witness. Fresh-Registry durable replay exists, but it can replay an old whole-entity snapshot over later canonical entity changes.
- A full-scene equality witness would prevent that stale overwrite only by requiring an exact scene match; it would not make the arbitrary path, untyped value, structure-materializing setter, or whole-entity inverse into an evidenced field-level `.pond` contract. Adding that guard to the broad compatibility surface would contradict E179's explicit no-generic-migration rule.

## Authority and compatibility retained

- No runtime, Registry, Inspector, `.pond`, manifest, or audit-schema behavior changed in this decision gate.
- Scene-owned generic Inspector rejection remains terminal: no local `CommandStack` fallback, legacy sync, success signal, or `scene.open` rehydrate happens after a failed semantic command.
- E175/E177 non-scene and ownerless local fallback behavior remains unchanged.
- Audit remains schema version 4 with `unified_undo_redo_runtime=false`. Representative durable undo/redo availability is not a global unified-history claim.

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

The suite confirms the active `energy` compatibility route, terminal scene-owned rejection, fresh-Registry generic replay compatibility, audit history, and status-tool expectations. It is not evidence that the generic route is stale-safe; the source-contract audit above is the reason this gate makes no migration.

`py_compile` passed for the command runtime, Registry, Inspector binding/dock, and relevant test modules. `tools/check_ai_command_audit_status.py`, `tools/check_core_boundaries.py`, and `tools/check_gui_boundaries.py` passed. Repository-wide pytest was intentionally not run because this was a no-runtime-change decision/inventory gate.

## Fallback and concrete unblock path

Keep direct generic calls compatible, but do not advertise them as guarded semantic history and do not repair them by adding a wider generic setter or whole-entity snapshot guard.

A future migration must first extract **one separately named, active-scene field command** with all of the following: a stable canonical JSON location; a field-specific value schema and normalization rule; an identity distinct from mutable entity fields; a field-level expected-current undo/redo inverse; same-process stale/retry proof; fresh-Registry durable stale/retry proof; successful `scene.open` rehydration; and terminal scene-owned rejection. It must leave the existing generic command as compatibility-only unless its full public semantics receive an independently proven contract.

## Completion and next gate

E183 closes with no behavior change: the generic entity-property surface is too broad and structurally unsafe for a guarded-history migration.

Exactly one next gate: **E184 -- Scene Script-Property Serialized-Identity Guarded-History Contract Inventory Gate**.