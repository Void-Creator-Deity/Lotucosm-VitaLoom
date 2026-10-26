# E176 Inspector Legacy Local-Mutation Owner-Contract Design Gate

Date: 2026-07-31
Status: complete

## Previous gate

E175 retained all non-scene Inspector mutation fallbacks on the local `CommandStack` because none had a proven durable owner, identity, serialized representation, inverse and canonical rehydration contract.  It also prevented a legacy object with a coincidentally similar ID from syncing against an unrelated active `.pond`.

## Objective

Turn the most constrained remaining Inspector connection edit into a real, reviewable semantic-command candidate **only when** every ownership and history invariant is demonstrated.  The candidate is the sole editable connection field currently exposed by Inspector: `ConnectionLine.weight`.  The work must distinguish a selected, scene-owned viewport connection from a transient or otherwise non-scene connection; non-scene fallbacks remain intentionally local.

This gate does not claim whole-refactor completion, unified runtime-wide undo/redo, WorldBridge completion, native readiness, or OpenGL default readiness.

## Evidence-led contract design

### Current facts

- `ConnectionLine.to_dict()` serializes only `{start, end, weight}`; Inspector exposes `start`/`end` as readonly and `weight` as the only editable connection field.
- `.pond.connections` is an ordered list.  Existing `connection.create` / `connection.delete` already use a JSON snapshot plus its exact list index, and reject an index/snapshot mismatch.
- A `ConnectionLine` does not carry a globally durable ID.  Endpoint pair alone is not unique, so it cannot identify duplicated parallel connections.
- `SceneViewport` canonical rehydration replaces canvas instances after `scene.open`; object identity therefore cannot be included in command payloads or durable history.

### Required owner contract

A semantic Inspector connection mutation is applicable only when all conditions hold:

1. `prop_name == "weight"` and the requested value is a finite numeric value;
2. the active `SceneManager` scene path is a real `.pond` and `get_scene_data()` yields an ordered `connections` list;
3. the selected `ConnectionLine` is owned by the current SceneViewport connection collection, not merely endpoint-equivalent to one;
4. its collection index identifies a canonical row equivalent to `connection.to_dict()`; and
5. the canonical row passes the runtime connection validation (both endpoints exist and the stored weight is numeric).

The GUI adapter may use object identity only to prove item 3 during this invocation.  The Qt-free payload is JSON-only: `{scene_path, connection_index, connection: expected_snapshot, weight}`.  It contains no widget/canvas/object reference.

### Authority, schema, inverse and rehydration

- Add a Qt-free `connection.set_weight` command; it accepts no arbitrary property path.
- The handler validates the expected exact row at the requested list slot, validates the new finite weight, replaces only the `weight` member, preserves `start`/`end`, writes `.pond`, and returns `old_connection`, `new_connection`, and `connection_index`.
- Registry history is a pair of guarded `connection.set_weight` calls.  Undo expects `new_connection` and writes `old_connection.weight`; redo expects `old_connection` and writes `new_connection.weight`.  If a concurrent/reordered edit changes the exact slot, history rejects rather than overwriting a different connection.
- Inspector refreshes with canonical `scene.open` only after Registry success; it must not build or execute a local command in the applied/rejected semantic cases.  On rejection, no success signal or local mutation may occur.

### Non-candidate families

The following remain local until separately proven: an unowned connection, non-weight connection attributes, legacy nodes outside the active `.pond`, positional/script holders, arbitrary Python objects and dictionaries.  A coincidental endpoint/weight match is insufficient; no fake Registry setter is allowed.

## Implementation plan

1. Make the SceneViewport-to-Inspector ownership witness explicit and nonserialized, so the Inspector can verify that a selected connection actually belongs to the current viewport collection.
2. Implement and register `connection.set_weight` in the Qt-free runtime command layer and add a guarded durable-history recipe in `CommandRegistry`.
3. Add an Inspector semantic connection route before `ModifyConnectionPropertyCommand`, with three outcomes: `not_applicable`, `applied`, `rejected`.
4. Add regression coverage for command validation, fresh-registry undo/redo, scene rehydration, successful Inspector mapping, and rejection/non-owner local-fallback behavior.
5. Run focused offscreen tests, compilation, audit/boundary checks and scoped whitespace validation; record evidence, skips, fallback and exactly one next gate.

## Completion criteria

- A scene-owned Inspector weight edit has a Qt-free JSON payload, durable inverse and canonical rehydration proof.
- A non-scene or unowned connection remains one local compatible command and performs no Registry / `SceneManager` mutation.
- Registry rejection leaves the connection unchanged and emits no success side effects.
- The command is included in durable project undo/redo eligibility only after fresh-registry evidence passes.
- `unified_undo_redo_runtime=false` remains true until all unrelated local families are migrated with equivalent contracts.

## Execution evidence (completed 2026-07-31)

- `ConnectionLine` now carries a nonserialized SceneViewport owner witness, and every SceneViewport-created or canonical-rehydrated connection is bound to that owner. Inspector accepts the semantic route only for the exact object present in that owner's `connections` collection and, when present, only if the editor canvas is the same owner.
- The Qt-free `connection.set_weight` command accepts a JSON-only scene path, list index, expected snapshot and requested weight. It validates finite numeric weights in the handler (rejecting `bool`, `NaN`, and infinities with a stable domain error), requires an exact canonical slot match, preserves legacy endpoint key spelling, and updates only `weight`.
- The Registry now builds guarded inverse recipes for this command. Its durable execute-state selection also treats a local `command.undo` followed by `command.redo` as reapplied, so a fresh Registry can still perform a later project undo instead of falsely reporting the original execute as permanently consumed.
- Inspector has explicit `not_applicable` / `applied` / `rejected` connection-route outcomes before the legacy property command. An applied mutation rehydrates via `scene.open`; a rejected semantic mutation neither constructs nor executes a local command and emits no success side effect. Unowned connections retain exactly one local fallback command.
- Proof: offscreen focused suite passed `29 passed, 3 subtests passed in 2.17s` for Inspector mapping, connection semantic history, durable project undo, audit status, and command-path undo/redo. `py_compile` passed for all five changed runtime modules. `tools/check_ai_command_audit_status.py` reported schema v4 and representative durable history for `connection.set_weight`; core and GUI boundary checks passed; scoped `git diff --check` passed (only the existing Git LF/CRLF warning for the Inspector test was printed).
- The full test suite was intentionally not run in this narrow gate. No environment blocker remains. The fallback remains the E175 local `CommandStack` path for unowned/non-scene connections and other unproven legacy families; the unblock condition for each remaining family is a demonstrable durable owner, schema, inverse and canonical rehydration contract.

## Next gate

Exactly one next gate: **E177 ? Inspector Remaining Legacy Mutation Owner-Contract Inventory Gate**. Inventory positional/script holders, legacy nodes, dictionaries and remaining connection fields; select at most one next family only if its durable owner, serialized identity, typed mutation schema, inverse and canonical rehydration can be proved.

## Risks and fallback

If the current adapter cannot prove a selected connection belongs to the canonical viewport, preserve the E175 local fallback and document this as a blocker.  Do not infer ownership from endpoint values or use `connection.create` / `connection.delete` as a property setter.
