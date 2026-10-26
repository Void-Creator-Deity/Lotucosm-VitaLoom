# Fresh-session prompt -- E240 WorldBridge Quarantine Diagnostic Provenance and Operator Visibility Decision Gate

## Current position

E239 is complete. The current runtime is quarantined after an E236-labelled `WorldBridgeHandoffFailure`; not only the ordinary tick but every known opt-in SR-to-PS bridge writer is denied before Pond construction/reuse and before mutation:

- `scene_prebridge` -- scene-load `ensure_bridged_organisms`;
- `spawn_bridge` -- dynamic-spawn `bridge_spawned_organism`;
- `tick_handoff` -- tick prebridge and `unified_pond_step*`.

The Qt-free `world_bridge_quarantine_readmission_authority.py` only classifies entry-point admission. It cannot clear quarantine, make a Pond, mutate SR/PS, restart a host, or restore/replay. `GameViewport` stores the last admission decision. `_discard_scene_runtime_state()` and `_stop_simulation()` drop `_unified_pond` before clearing current-lifetime suspension; `_refresh_unified_pond_mode()` never clears suspension. A later normal lifecycle may create fresh instances, but this is not safe same-instance retry or recovery.

E239 evidence: focused 32 passed; wider 268 passed + 5 subtests; full offscreen 2294 passed, 34 skipped, 55 subtests. E234-E239/runtime-status guards and `git diff --check` passed. Retain `.pytest-e239-full-3bf259878aef4c96a3736a94b0584ca4`; do not delete `.pytest-*` directories. Do not stage, commit, reset, restore, clean, or touch unrelated existing changes.

## Only active gate

**E240 -- WorldBridge Quarantine Diagnostic Provenance and Operator Visibility Decision Gate**

Start with an E240 plan, then audit whether the failure receipt and last admission decision can be made consistently visible to host/operator diagnostics without turning the legacy Qt adapter into an engine authority, leaking mutable runtime state, adding persistence/replay semantics, or exposing a user control that clears quarantine. Identify exact UI/log/status consumers and define a Qt-free immutable/copy-isolated diagnostic projection if source evidence supports it. Keep `runtime_mode=dual`, `unified_pond_enabled=false`, `default_ready=false`; preserve `.pond`, manifests, AI command registry, Inspector bindings, and SR2D seams. Close with focused tests, static guard, wider WorldBridge regression, full offscreen regression, mainline evidence, and exactly one next gate.
