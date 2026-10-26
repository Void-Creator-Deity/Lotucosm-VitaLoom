# Phase E86 -- Hot Reload Plugin Public Reload Call-Failure Containment Audit

Date: 2026-07-30
Status: complete

## Previous gate

E85 contained the public *observation* call outage in
`HotReloadPlugin._observe_plugins()`. A raised `observe_plugins()` call now
creates the helper's existing empty target facts, so choose-reload opens no
dialog and user-mod batch reload has no targets. Capability resolution remains
outside the exception boundary.

The adjacent mutating helper `_reload_plugin_report()` independently calls the
published `reload_plugin(plugin_id)` operation. It normalizes a malformed
*returned* report, but a raised public operation call can still escape once a
valid copied target has been chosen. This is action-operation failure containment,
not observation semantics, and must be audited separately.

## Objective

Audit and, if necessary, minimally contain a thrown public `reload_plugin()`
call in Hot Reload Plugin's existing report helper. Preserve Host authority and
existing command result shapes. A call outage after legitimate target selection
must yield a deterministic failed report/command result, never propagate an
exception or trigger private-state fallback.

## Required evidence

1. Map `_reload_plugin_report()` callers in choose and user-mod batch commands,
including their existing failed/partial result behavior.
2. Reproduce a raised public `reload_plugin()` call with a complete public
capability stub and no Host-private-state access.
3. If correction is required, contain only the operation call after capability
resolution and prove choose returns its existing failed command result while
batch returns its existing partial-failure form without false success.
4. Run focused Qt/offscreen and Hot Reload lifecycle coverage, adjacent
Host/control/reload tests, source-only syntax/whitespace, guardrails, release
consistency, and independent signature proof.
5. Record pre/post evidence, interpreter/offscreen configuration, skips, E68
broad proof, QPainter/OpenGL truth, fallback/unblock facts, and exactly one next
Gate.

## Explicit non-goals

Do not add a second Host, operation/observation cache, catalog, registry, event
bus, serializer, renderer, layout authority, widget DSL, UI framework, or app
shell. Keep PyQt6/QPainter/OpenGL as a legacy UI-host adapter. Preserve `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. QPainter remains default; OpenGL/native
acceleration is not default-ready. Do not claim whole-refactor completion.


## Audit result

- `_reload_plugin_report()` is the single Hot Reload operation seam shared by
  choose-reload and user-mod batch reload. Its pre-existing normalization
  already converts malformed *returned* values into `invalid_reload_report`,
  but a thrown `host.reload_plugin(plugin_id)` call escaped before that branch.
- The minimal correction resolves the public Host first and catches only the
  `reload_plugin()` call. An operation outage becomes the helper's ordinary
  mapping-shaped failed report (`status=failed`,
  `code=plugin_reload_unavailable`, and the requested `plugin_id`), which then
  follows the existing result normalization and command error paths.
  Resolver/interface failures intentionally remain visible.
- Choose-reload now returns its existing `plugin_reload_failed` command error;
  user-mod batch retains `plugin_reload_batch_partial` and continues to process
  every valid selected target. No private Host read, report cache, metadata
  fallback, second authority, or new result protocol was added.

## Verification evidence

- Genuine TDD red: complete public-capability stubs whose `reload_plugin()`
  call raised produced `3 failed in 0.38s`; each failure propagated from the
  direct operation call in `_reload_plugin_report()`.
- Focused E86 regression: `3 passed in 0.23s`.
- E86 plus Hot Reload observation/lifecycle, PluginLoader hot reload, kernel
  capability, legacy consumer, Package Manager/Manager Refresh, and E84
  Runtime Ops observation-outage coverage: `68 passed in 2.38s` under
  `.venv\python.exe -B`, `QT_QPA_PLATFORM=offscreen`, and
  `PYTHONDONTWRITEBYTECODE=1`.
- Source-only syntax/trailing-whitespace checks passed for the changed runtime
  module and E86 test using
  `compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`; no
  `py_compile` was used. Root offscreen smoke passed and printed
  `Editor smoke OK: suite=lotucosm.vitaloom.suite
  product=lotucosm-vitaloom@1.0.0 plugins=13/20`.
- Project plugin model, core boundaries, GUI boundaries, and release
  consistency tools all passed. Independent signature proof used the existing
  `D:\app\anaconda3\python.exe`: `2 passed in 0.18s` for
  `tests/test_package_signature_warn_only.py`. `.venv` lacks `cryptography`;
  use an already provisioned interpreter or obtain user approval before any
  dependency installation if venv-local signature collection becomes required.
- E68 remains the latest broad offscreen Qt proof: `1678 passed, 34 skipped,
  34 subtests`; regular/eager editor smokes were `13/20` and `20/20`.
  QPainter remains default; OpenGL/native acceleration is not default-ready.
  E86 does not claim whole-refactor completion.
- Unique next Gate: E87 Runtime Ops Public Mutation Call-Failure Containment
  Audit.
