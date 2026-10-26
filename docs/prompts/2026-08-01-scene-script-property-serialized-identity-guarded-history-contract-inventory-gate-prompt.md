# E184 Fresh-Session Prompt — Scene Script-Property Serialized-Identity Guarded-History Contract Inventory Gate

E184 is complete with **no migration**. `script.set_property` stays compatibility-only rather than a guarded scene-history contract.

## Recorded outcome

- The workspace sample `.pond` scripts have `name`, `type`, and `properties`, but no serialized script `id`.
- Runtime selection uses the first script matching caller-supplied `name`, `type`, or `path`; Inspector selection uses name. Neither proves a unique stable script target after reorder, replacement, or duplicate aliases.
- Property paths and values remain broad; missing/malformed nested structures can be materialized or replaced.
- Undo/redo replays the same alias/path command with old/new values and has no expected-current witness. Fresh durable replay compatibility is not stale-safety.
- No production behavior changed. Scene-owned rejection remains terminal and E175/E177 fallback remains unchanged. Audit is schema v4 with `unified_undo_redo_runtime=false`.

## Next work boundary

Proceed only with E185: inventory the currently undoable `prefab.place` command, its actual UI/command callers, ownership, inverse availability, `.pond` effects, and potential durable-history contract. Do not broaden generic entity or script setters.

Read:

- `docs/superpowers/plans/2026-08-01-scene-script-property-serialized-identity-guarded-history-contract-inventory-gate.md`
- `docs/superpowers/plans/2026-08-01-scene-prefab-placement-durable-history-contract-inventory-gate.md`
- `docs/mainline_status.md`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/runtime_commands.py`
- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/commands/registry.py`

Do not touch `CONTEXT.md`, unrelated dirty work, manifests, `.pond` semantics, WorldBridge, native acceleration, OpenGL-default readiness, or Qt-free L0-L4 contracts. A rejected scene-owned semantic command must never return to local history.