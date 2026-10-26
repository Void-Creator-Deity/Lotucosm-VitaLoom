# Phase E84 -- Runtime Ops Public Observation Call-Failure Containment Audit

Date: 2026-07-30
Status: complete

## Previous gate

E83 repaired the editor-smoke-only read model. Its public `observe_plugins()`
call now turns a thrown, unavailable, non-mapping, incomplete, or malformed
snapshot into a deterministic non-zero smoke result without false counts or
Host-private-state fallback. Normal editor startup remains unchanged.

The remaining shared Qt-free consumer seam is
`PluginRuntimeOpsMixin._runtime_plugin_observation()`. It validates a returned
non-mapping snapshot, but directly invokes the public capability. A raised
`observe_plugins()` call may therefore escape into Package Manager or legacy
Plugin Manager display/action-adjacent callers. This must be audited separately
from E78-E83: it concerns call-outage containment at the one shared adapter
seam, not schema normalization of a returned snapshot.

## Objective

Map every `PluginRuntimeOpsMixin` consumer of the public observation call and
make a thrown or unavailable public observation deterministic at the existing
read-model boundary. A display must render unknown/empty facts as its existing
contract requires; actions which require catalog evidence must remain denied.
Preserve Runtime Plugin Host as the only plugin-state authority.

## Required evidence

1. Trace `_runtime_plugin_observation()` and its Package Manager / legacy Plugin
   Manager consumers; distinguish display projections from action authorization.
2. Reproduce a public `observe_plugins()` exception using a capability stub with
   no RuntimePluginHost private state and determine the current propagation.
3. If correction is required, contain the exception at the existing mixin seam,
   preserve the documented unknown/empty display semantics, and prove catalog-
   dependent actions do not dispatch, reload, unload, or mutate project state.
4. Run focused offscreen Qt tests, adjacent Host/control/lifecycle/reload and
   manager coverage, source-only syntax/whitespace checks, guardrails, release
   consistency, and independent signature proof.
5. Record exact interpreter/offscreen configuration, pre/post evidence, skips,
   E68 broad proof, QPainter/OpenGL status, fallback/unblock facts, and exactly
   one next Gate.

## Explicit non-goals

Do not add a second Host, observation cache, metadata registry, command
registry, event bus, serializer, renderer, layout manager, widget DSL, UI
framework, or app shell. Keep PyQt6/QPainter/OpenGL as a legacy UI-host adapter.
Preserve `.pond`, Project World, Inspector command binding, SR2D, SR/PS,
Player/export, manifests, public imports, and MRO. QPainter remains default;
OpenGL/native acceleration is not default-ready. Do not claim whole-refactor
completion.

## Audit result

- `PluginRuntimeOpsMixin._runtime_plugin_observation()` is the shared public
  read seam for Package Manager and legacy Plugin Manager. Its returned facts
  drive display projections and supply catalog evidence for reload, unload, and
  project-disable authorization.
- The original helper already returned `{}` for a non-mapping snapshot, but a
  public `observe_plugins()` exception escaped into every mixin consumer. The
  minimal correction catches only that call after Host resolution, logs a
  generic availability warning, and returns `{}`. Resolver/interface failures
  remain visible contract failures rather than being relabeled as observation
  outages.
- Existing display semantics consume `{}` as unknown Package Manager memory or
  an empty legacy list. Existing action checks find no matching catalog row and
  deny without calling reload, unload, project command, or refresh. No Host
  private state, cache, second authority, or normal Host behavior was added.

## Verification evidence

- Genuine TDD red: after the test stub implemented the complete runtime
  capability protocol, a raised public observation call propagated as
  `4 failed in 0.61s`. The earlier incomplete-interface `TypeError` was a test
  fixture defect, corrected before evaluating the target behavior.
- Focused E84 regression: `4 passed in 0.40s`.
- E84 plus E83, suite bootstrap, legacy consumers, kernel capability, Package
  Manager/Manager Refresh, Host control/lifecycle/reload, and activation:
  `96 passed, 1 skipped in 2.27s` under `.venv\python.exe -B`,
  `QT_QPA_PLATFORM=offscreen`, and `PYTHONDONTWRITEBYTECODE=1`.
- New adjacent Runtime Ops/Package Manager/Manager Refresh/Hot Reload/kernel
  capability/legacy consumer slice: `61 passed in 1.06s` with the same
  offscreen/no-bytecode configuration.
- Source-only syntax and trailing-whitespace checks passed for the changed
  runtime module and E84 regression, using
  `compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`; no
  `py_compile` was used.
- Root entry offscreen smoke (`.venv\python.exe -B main.py --smoke-editor`)
  passed and reported `Editor smoke OK: suite=lotucosm.vitaloom.suite
  product=lotucosm-vitaloom@1.0.0 plugins=13/20`.
- Project plugin model, core boundaries, GUI boundaries, and release
  consistency tools all passed. Independent signature proof used the existing
  `D:\app\anaconda3\python.exe`: `2 passed in 0.30s` for
  `tests/test_package_signature_warn_only.py`. `.venv` lacks `cryptography`,
  so a venv-local signature collection remains unavailable without an already
  provisioned interpreter or user-approved dependency installation.
- E68 remains the latest broad offscreen Qt proof: `1678 passed, 34 skipped,
  34 subtests`; regular/eager editor smokes were `13/20` and `20/20`.
  QPainter remains default; OpenGL/native acceleration is not default-ready.
  E84 does not claim whole-refactor completion.
- Unique next Gate: E85 Hot Reload Plugin Public Observation Call-Failure
  Containment Audit.
