# Fresh-session prompt -- E241 WorldBridge Quarantine Diagnostic Lifecycle Correlation and Fresh-Instance Boundary Evidence Gate

## Current position

E240 is complete.  Current-runtime WorldBridge quarantine facts are now visible through a Qt-free, copy-isolated diagnostic projection:

- `world_bridge_quarantine_diagnostic_provenance.py` accepts only E236 labelled failure receipts, E238 containment decisions, and optional E239 writer-admission decisions;
- `GameViewport.query_worldbridge_quarantine_diagnostic()` only reads retained provenance fields and publishes a query-only capability through `WORLDBRIDGE_QUARANTINE_DIAGNOSTIC_HOST`;
- `runtime.worldbridge.quarantine_diagnostic` and its MCP wrapper are non-mutating/headless; absent host returns explicit `unavailable`, never a globally discovered or newly constructed runtime;
- suspended current-runtime output reports phase, partial-mutation possibility, containment action, last opt-in bridge writer admission, and requires a fresh lifecycle before later opt-in admission;
- after suspension is cleared while receipt/containment records remain retained, output is explicitly `historical_or_unverified_after_current_quarantine_cleared`.  This is historical diagnostic evidence only, not recovery, same-instance retry, re-admission, restore, replay, or proof that later instances are fresh.

E240 evidence: focused 37 passed in 7.38s; 8 E240/predecessor/runtime-status guards passed; wider 284 passed + 5 subtests in 31.05s; full offscreen 2299 passed, 34 skipped, 55 subtests in 224.51s.  The initial full run exposed a stale exact capability-lease test expectation; it was corrected to include the third, diagnostic host capability and the complete rerun passed.  Retain `.pytest-e240-full-20260813-a` and `.pytest-e240-full-20260813-b`; do not delete `.pytest-*` directories.  Do not stage, commit, reset, restore, clean, or alter unrelated pre-existing work.

## Only active gate

**E241 -- WorldBridge Quarantine Diagnostic Lifecycle Correlation and Fresh-Instance Boundary Evidence Gate**

Start by writing an E241 plan under `docs/superpowers/plans/`, then audit the actual GameViewport/scene-stop/discard/reload lifecycle and determine whether a diagnostic record can be correlated to a demonstrably new adapter/SR/Pond lifetime without treating retained records as restoration authority.  Define explicit lifecycle identifiers or boundary evidence only if existing ownership can support them, and make any projection Qt-free/copy-isolated/read-only.  A result must distinguish: current quarantined runtime, historical retained evidence, host unavailable, and demonstrably fresh instance boundary.  Do not create a control to clear quarantine, retry handoffs, reuse a failed Pond, restart automatically, restore/replay, or persist mutable runtime state.

Preserve `.pond`, package/project manifests, AI command registry flows, Inspector command binding, SR2D public seams, and the Qt-free L0-L4 engine/plugin contracts.  Keep `runtime_mode=dual`, `unified_pond_enabled=false`, and `default_ready=false`.  Close E241 only with focused tests, a mechanical guard, wider WorldBridge regression, full offscreen regression, `docs/mainline_status.md`, and exactly one next gate.
