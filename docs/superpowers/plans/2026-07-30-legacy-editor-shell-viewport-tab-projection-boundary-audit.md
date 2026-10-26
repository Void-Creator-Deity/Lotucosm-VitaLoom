# Phase E64 -- Legacy Editor Shell Viewport Tab Projection Boundary Audit

Date: 2026-07-30
Status: completed

## Previous gate

E63 proved RuntimePluginHost owns commands while LegacyEditorPluginAdapter and
LayoutManager only project QAction/menu/toolbar UI. QAction payloads are freshly
thawed per trigger.

## Objective

Audit the legacy central viewport/tab projection and fallback path. Identify the
smallest safe parity or state-contract improvement without introducing a second
Editor Host, renderer, widget framework, or changing default rendering policy.

## Required evidence

Trace registration, switching, removal, saved state, and concrete offscreen
Editor behavior; run focused tests plus full Qt regression, smokes, guardrails,
and signature collection before closure.


## Findings and implementation

The empty `QTabWidget` wrapper is falsey in this PyQt host. Legacy truthiness
checks therefore left `EditorKernel` on `central_stack` and sent every viewport
through the fallback path despite creating a tab container. All viewport-tab
presence checks now use `is not None`, so EditorKernel installs the real tab
container and LayoutManager consistently registers, switches, removes, saves,
and restores its tabs. Saved tab order is applied before selecting the saved
current viewport. The legacy stack remains only an explicit no-tab fallback.

## Evidence

- Viewport/tab state, switch, removal, save and restore regression: `8 passed in 0.42s`.
- Expanded viewport lifecycle/contribution projection suite: `51 passed in 1.59s`.
- Full Qt regression: `1671 passed, 34 skipped, 34 subtests passed in 199.12s`.
- Standard/eager Editor smokes: `13/20`, `20/20`; all guardrails and diff check
  passed; independent signature-only collection: `2 passed in 0.28s`.

## Closure

E64 is complete. The unique next gate is E65: Legacy Editor Shell Dock Layout
Projection Audit. Audit dock registration/tabification/geometry persistence and
restore parity without introducing another Host or UI framework.
