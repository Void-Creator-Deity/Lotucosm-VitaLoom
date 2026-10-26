# Phase E85 -- Hot Reload Plugin Public Observation Call-Failure Containment Audit

Date: 2026-07-30
Status: complete

## Previous gate

E84 repaired the one shared Runtime Ops read boundary. A raised public
`RuntimePluginHost.observe_plugins()` call now becomes an unknown (`{}`)
projection for Package Manager and legacy Plugin Manager consumers; their
existing catalog-evidence checks deny reload, unload, and project mutation.
The resolver remains outside that containment scope so a missing Host capability
is not disguised as an observation outage.

A source audit now leaves one separate runtime call site:
`HotReloadPlugin._observe_plugins()`. Its copied facts feed the choose-reload
candidate list and the `user_mod` batch-target selection. E82 proved malformed
*returned* facts already fail closed at these action-adjacent paths, but did not
exercise an exception raised by the public observation call itself. This is a
distinct failure mode and must not be folded into E84.

## Objective

Audit and, if necessary, minimally contain a thrown public `observe_plugins()`
call at Hot Reload Plugin's existing observation helper. Preserve the Runtime
Plugin Host as the only plugin-state authority. An outage must not open a
selection dialog, choose targets, reload plugins, or invent fallback metadata.

## Required evidence

1. Map `_observe_plugins()` to choose-reload and user-mod batch command flows;
distinguish capability-resolution errors from the public call outage.
2. Reproduce a raised `observe_plugins()` call with a complete public-capability
stub and no Host-private-state access.
3. If correction is needed, contain only the public call at the existing helper
and prove empty/unknown facts result in no dialog, no targets, and no reload.
4. Run focused Qt/offscreen and Hot Reload lifecycle coverage, adjacent
Host/control/reload tests, source-only syntax/whitespace, guardrails, release
consistency, and independent signature proof.
5. Record pre/post evidence, interpreter and offscreen configuration, skips,
E68 broad proof, QPainter/OpenGL truth, fallback/unblock facts, and exactly one
next Gate.

## Explicit non-goals

Do not add a second Host, observation cache, catalog, registry, event bus,
serializer, renderer, layout authority, widget DSL, UI framework, or app shell.
Keep PyQt6/QPainter/OpenGL as a legacy UI-host adapter. Preserve `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. QPainter remains default; OpenGL/native
acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- `HotReloadPlugin._observe_plugins()` is action-adjacent rather than passive
  display: `_reloadable_plugins()` supplies choose-reload candidates, and
  `_user_mod_targets()` intersects copied catalog scope with copied reloadable
  ids for batch targets.
- E82 already made malformed returned facts fail closed, but a raised public
  observation call escaped before those validators ran. The minimal correction
  resolves the Host first, catches only `host.observe_plugins()`, logs a generic
  availability warning, and returns the helper's existing empty target facts.
  Resolver/interface errors are intentionally not masked.
- Empty facts preserve the existing no-op command behavior: choose returns
  `no_candidates` before the Qt dialog bridge; user-mod batch returns
  `no_targets`; neither path reloads. No Host private read, target cache,
  metadata fallback, second authority, or normal Host behavior was added.

## Verification evidence

- Genuine TDD red: complete public-capability stubs whose observation call
  raised produced `3 failed in 0.43s`, all with the public exception propagating
  from `HotReloadPlugin._observe_plugins()`.
- Focused E85 regression: `3 passed in 0.29s`.
- E85 plus Hot Reload lifecycle, PluginLoader hot reload, kernel capability,
  legacy consumer, Package Manager/Manager Refresh, and E84 Runtime Ops
  outage coverage: `65 passed in 2.16s` under `.venv\python.exe -B`,
  `QT_QPA_PLATFORM=offscreen`, and `PYTHONDONTWRITEBYTECODE=1`.
- Source-only syntax/trailing-whitespace check passed for the changed runtime
  module and E85 test, using
  `compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`; no
  `py_compile` was used. Root offscreen smoke passed and printed
  `Editor smoke OK: suite=lotucosm.vitaloom.suite
  product=lotucosm-vitaloom@1.0.0 plugins=13/20`.
- Project plugin model, core boundaries, GUI boundaries, and release
  consistency tools all passed. Independent signature proof used the existing
  `D:\app\anaconda3\python.exe`: `2 passed in 0.26s` for
  `tests/test_package_signature_warn_only.py`. `.venv` lacks `cryptography`;
  use an already provisioned interpreter or obtain user approval before any
  dependency installation if venv-local signature collection becomes required.
- E68 remains the latest broad offscreen Qt proof: `1678 passed, 34 skipped,
  34 subtests`; regular/eager editor smokes were `13/20` and `20/20`.
  QPainter remains default; OpenGL/native acceleration is not default-ready.
  E85 does not claim whole-refactor completion.
- Unique next Gate: E86 Hot Reload Plugin Public Reload Call-Failure
  Containment Audit.
