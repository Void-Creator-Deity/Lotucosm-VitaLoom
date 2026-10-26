# E209 WorldBridge Hierarchy Ownership Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E208 established that executable script/component objects are not inert bridge data. The WorldBridge mapping ledger still listed `hierarchy` as a separate unmapped loss.

## Decision

`hierarchy` remains intentionally **not mapped**.

- The shared `EntityBase` hierarchy is live behavior: `add_child()` assigns reciprocal graph state; a child derives `world_position` through its parent; and parent update recursively updates children.
- Pond membership is a distinct, unreconciled concern. Adding both organisms registers both in `pond.root_entities`; attaching one as the other's child does not remove the child root. A pond tick therefore dispatches organisms, then roots, while root traversal dispatches the child again. This is incompatible with a naive parent/child copy or tick-merge claim.
- `PondSerializer` writes independent organism records from `pond.organisms` and does not persist `parent` or `children`. It cannot round-trip a hierarchy graph or establish scene authority for one.
- WorldBridge has no direct or reflective hierarchy route. Copying the shared field names would create an unmanaged mutable graph and potentially change update multiplicity, coordinate semantics, and persistence behavior.

## Evidence

`tests/test_worldbridge_hierarchy_ownership_decision.py` proves that a parent/child relation changes world coordinates and causes recursive updates; proves root membership remains separate and a serialized pond snapshot has no hierarchy fields; and rejects direct/reflection WorldBridge routes while retaining the audit loss. The pond test also makes the double-dispatch risk observable: one pond tick advances the parent age to `4` and its still-rooted child to `8`.

Focused hierarchy/mapping/script/component coverage passed **`13 passed in 1.05s`**. New-test compilation, `tools/check_runtime_worldbridge_status.py`, and `tools/check_worldbridge_mapping_audit.py` passed. `git diff --check` passed with only pre-existing LF/CRLF warnings. E209 changes only a regression and documentation, so the latest runtime-changing full-suite baseline remains **`2062 passed, 34 skipped, 50 subtests passed in 225.92s`**.

## Fallback, unblock path, and next gate

Keep hierarchy lane-local. A future hierarchy contract needs a single graph authority, atomic parent/root reconciliation, explicit local/world coordinate policy, persistence with identity/cycle validation, and tick/render parity proof before it can map any edge. Field-name similarity is not an unblock.

E210 is the next material mapping-loss boundary: audit memory-gene ownership and persistence. It must distinguish SR memory-gene bridge/projection behavior from PS inheritance, serializer, and runtime-memory semantics before any mapping claim.
