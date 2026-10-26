# E207 WorldBridge Render-Identity Authority Inventory Gate

Date: 2026-08-01
Status: complete

## Previous gate

E206 established that inherited active/visible names do not create a shared authority contract. E207 applied the same evidence standard to render identity.

## Decision

`render_identity` remains intentionally **not mapped**.

- Legacy `EntityBase.color` is a three-channel value used by the Pygame base `draw()` path.
- The Qt-free viewport does not read that field. Its immutable snapshot copies `sr_visual_state` / `visual_state`, while draw commands select type palettes and optional four-channel `fill`/`stroke` overrides from that mapping.
- `world_bridge.py` has no route for legacy color or either viewport visual-state mapping. Therefore a color copy would neither preserve the current Qt-free viewport contract nor prove a rendered-pixel parity claim.

## Evidence

`tests/test_worldbridge_render_identity_authority_inventory.py` proves that a legacy `color` value is absent from the Qt-free visual-state snapshot, that explicit `visual_state.fill` is the actual draw-command input, and that the bridge/ledger retains no unreviewed render-identity route.

Focused viewport/WorldBridge audit coverage passed **`21 passed in 1.07s`**. The mapping-audit and GUI-boundary tools exited `0`. E207 adds only a decision/inventory regression; the immediately prior runtime-changing full-suite baseline remains **`2062 passed, 34 skipped, 50 subtests passed in 225.92s`**.

## Fallback, unblock path, and next gate

Keep render state lane-local. A future projection must map the explicit four-channel viewport visual state, preserve type-palette fallback and selection overlays, and pass a real current-context renderer/parity gate before any visual-equivalence claim. Legacy Pygame color alone is not an unblock.

E208 is the next material mapping-loss boundary: audit script and command-binding ownership. It must establish whether executable behavior can ever be represented as inert bridge data without importing UI authority, bypassing the Registry, or constructing live script/component objects.
