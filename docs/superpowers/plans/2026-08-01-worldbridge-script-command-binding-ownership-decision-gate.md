# E208 WorldBridge Script and Command-Binding Ownership Decision Gate

Date: 2026-08-01
Status: complete

## Previous gate

E207 found that render identity has incompatible active representations and no bridge-facing visual authority, so it remains unmapped. The mapping ledger still listed executable `scripts` as a separate loss.

## Decision

`scripts` remains intentionally **not mapped**.

- A `.pond`/legacy scene descriptor can contain JSON-shaped script configuration, but that descriptor is not the same authority as an already-attached runtime script object.
- `EntityBase.add_script()` invokes a script's live `on_attach()` callback, and `EntityBase.update()` invokes its live `update()` callback. The object therefore owns executable lifecycle behavior, not inert bridge metadata.
- PS components likewise own executable sensing, signaling, ingestion, force, and connection behavior. The existing component projection is deliberately JSON-safe and read-only; it explicitly reports `maps_live_components=false` and must not be relabeled as script mapping.
- WorldBridge must not construct, transfer, bind, or execute scripts/components. That boundary also prevents a bridge shortcut from bypassing the existing `.pond` descriptor, command registry, or Inspector command-binding authorities.

## Evidence

`tests/test_worldbridge_script_binding_ownership_decision.py` proves that attached scripts receive live attach/update callbacks, the ledger retains `scripts` as `not_mapped`, and the bridge has no direct or reflective route to script/component lifecycle or behavior names.

Focused script/component/mapping-audit coverage passed **`11 passed in 0.95s`**. `tools/check_worldbridge_component_decision.py`, `tools/check_worldbridge_component_projection.py`, and `tools/check_worldbridge_mapping_audit.py` all exited `0`. E208 is test/document-only, so the latest runtime-changing full-suite baseline remains **`2062 passed, 34 skipped, 50 subtests passed in 225.92s`**.

## Fallback, unblock path, and next gate

Keep executable scripts and components lane-local. A future read-only diagnostic must originate from explicit JSON-safe descriptor facts, preserve the Registry/Inspector ownership path, and prove that it neither instantiates live objects nor invokes lifecycle/behavior callbacks. It is not a live script or component mapping.

E209 is the next material mapping-loss boundary: audit hierarchy ownership. It must determine whether legacy `parent`/`children` traversal, pond root registration, and PS organism inheritance have an authority-preserving mapping contract; until then hierarchy remains a documented loss.
