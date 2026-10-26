# Phase E79 -- Qt Package Manager Public Observation Fail-Closed Action Boundary Audit

Date: 2026-07-30
Status: complete

## Previous gate

E78 hardened the Qt-free Runtime Ops action seam: non-mapping, unavailable,
and malformed public observations cannot authorize reload, unload, or project
disable. It also mapped the remaining consumers. Static inspection identified
Qt Package Manager selected-plugin and package-disable paths that could treat
missing public catalog facts as unprotected.

## Objective

Reproduce and correct only Qt Package Manager destructive behavior that could
proceed when the Runtime Plugin Host public observation is unavailable,
malformed, or lacks an authoritative row for the target plugin. Keep Runtime
Plugin Host ownership singular: the legacy Qt adapter must not infer protection,
scope, or availability from private Host state or create a fallback registry.

## Audit result

The repository's configured test interpreter was found at `.venv\python.exe`
(not `.venv\Scripts\python.exe`): Python 3.11.15 with PyQt6 6.11.0 and
PyQt6-Qt6 6.11.1. All Qt evidence below ran with `QT_QPA_PLATFORM=offscreen`
and `PYTHONDONTWRITEBYTECODE=1`.

A public-capability stub with no RuntimePluginHost internals reproduced a real
fail-open/fail-crash defect. Before the correction, `None` observation raised
`AttributeError` in selected-plugin disable. Unavailable, invalid, malformed,
and target-absent catalog facts could still dispatch `plugin.disable`, call
`unload_plugin`, refresh, and present the action as successful. The package
branch similarly treated plugin members absent from the public catalog as
unprotected.

The smallest correction is adapter-local and reuses the existing
`PluginRuntimeOpsMixin._runtime_plugin_row(plugin_id)` public capability reader.
Selected-plugin disable now requires a trustworthy matching public row. For a
package containing plugin members, every member must have a trustworthy row;
for an empty-member package fallback, the package id itself must have one.
Missing facts warn and deny the destructive action, with no command, unload,
refresh, selection refresh, or success UI. No Host private state, second Host,
registry, serializer, or parallel command authority was introduced.

## Verification evidence

- New offscreen regressions cover `None`, unavailable empty catalog, invalid
  catalog type, and malformed/target-absent rows for both selected-plugin and
  package disable. The pre-fix run was `8 failed, 6 passed`; after the fix the
  targeted Package Manager/manager-refresh run was `17 passed in 0.57s`.
- E79 plus Host/control/lifecycle/reload/activation coverage: `88 passed,
  1 skipped in 2.12s`.
- Adjacent Package Manager dock/menu/adapter/filter/project-operation/
  transaction/import coverage: `53 passed, 8 subtests passed in 3.08s`.
- Changed source and regression compiled through
  `compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`, avoiding
  pycache writes.
- Boundary/import/manifest/release guardrails: `21 passed in 20.48s`; the
  three standalone boundary/release tools also reported `OK`.
- Warn-only package-signature regression used the existing base interpreter,
  which has `cryptography`: `2 passed in 0.27s`. The Qt venv lacks that optional
  package; no dependency was installed.
- `git diff --check -- docs/INDEX.md` completed without whitespace errors; it
  reported only an existing LF-to-CRLF advisory. Most migration files are
  untracked, so syntax and runtime regression are the primary evidence there.

## Scope and next gate

E68 remains the latest broad offscreen Qt proof: `1678 passed, 34 skipped,
34 subtests`; regular/eager application smoke remains `13/20` and `20/20`.
QPainter remains the default path. OpenGL/native acceleration is not
default-ready. This gate does not claim whole-refactor completion.

The unique next Gate is E80 -- Qt Package Manager Public Observation Display
Resilience Audit. It must audit the remaining display-only direct
`observe_plugins()` reads without changing action authority.
