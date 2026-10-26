# Phase E65 -- Legacy Editor Shell Dock Layout Projection Audit

Date: 2026-07-30
Status: completed

## Previous gate

E64 restored the actual QTabWidget projection: explicit presence checks replace
falsey widget checks, and tab registration/switch/removal/order persistence now
follow one concrete Qt path.

## Objective

Audit dock registration, tabification, visibility/floating geometry persistence,
and restore behavior in the legacy Editor shell. Make only the smallest verified
projection/parity repair; retain LayoutManager and LegacyEditorPluginAdapter as
the sole concrete Qt host path.

## Audit and implementation

- Confirmed `LayoutManager.add_dock()` is the only concrete registration path:
  it applies the configured Qt features, tabifies immediately when the peer is
  available, otherwise records one deferred `(child, host)` relationship, then
  resolves it after each registration.
- Confirmed `remove_dock()` owns concrete projection cleanup: it removes the
  dock from the local map, removes pending relationships in either direction,
  detaches it from `QMainWindow`, and schedules deletion. Adapter unload tests
  continue to exercise this path; no extra dock registry or lifecycle authority
  was introduced.
- Found and repaired one partial-layout gap. `save_layout()` already persisted
  `floating` and dock `area`, but a JSON layout with an absent or unusable Qt
  `window_state` only restored the `floating=True` branch. Thus a mutated
  floating dock could not be restored to docked state, and its persisted area
  was unused.
- `restore_layout()` now records whether `QMainWindow.restoreState()` succeeded.
  Full Qt state remains authoritative for topology/tab order. Only when that
  state is absent or invalid does the existing JSON-safe per-dock fallback set
  `floating=False` and re-add a dock to one of the four validated dock areas.
  The existing floating geometry fallback remains unchanged.
- Added offscreen regressions for deferred tabification/removal cleanup and for
  restoring visibility, docking, and the saved area from a deliberately partial
  layout. The latter fails on the previous behavior and passes with the repair.

## Evidence

- Dock/layout regression: `10 passed in 0.50s`.
- Expanded dock contribution and adapter lifecycle regression: `56 passed in
  1.79s`.
- Full project-local Qt non-signature regression: `1673 passed, 34 skipped,
  34 subtests passed in 200.51s`.
- Offscreen Editor smoke: standard discovery `plugins=13/20`; eager discovery
  `plugins=20/20`. Both save the layout and unload projected docks/viewports
  cleanly.
- Guardrails: project-plugin model, core boundaries, GUI boundaries, and release
  consistency all passed. `git diff --check` exited 0 (existing CRLF warnings
  only). The project-local `.venv` lacks `cryptography`; the independent shared
  Python 3.13 signature collection passed: `2 passed in 0.28s`.

## Non-goals and boundary retained

This phase does not replace the PyQt host, make OpenGL default-ready, alter the
RuntimePluginHost command/lifecycle authority, or create a second layout,
registry, renderer, widget DSL, UI framework, or app shell. `.pond`, Project
World, Inspector command binding, SR2D, SR/PS, Player/export, package/signature,
and public import contracts remain outside the change.

## Next gate

E66 -- Legacy Editor Shell Restore-Timing and Deferred Plugin Projection Audit.
