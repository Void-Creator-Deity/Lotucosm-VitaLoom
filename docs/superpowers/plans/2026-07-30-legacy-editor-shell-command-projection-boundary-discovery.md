# Phase E63 -- Legacy Editor Shell Command Projection Boundary Discovery

Date: 2026-07-30
Status: completed

## Previous gate

E62 proved that editor-layout persistence has one safe portable-facts seam:
`EditorLayoutState` carries JSON-safe saved facts while `LayoutManager` remains
the concrete Qt capture, file-I/O, and apply authority. E62 also confirmed that
runtime command ownership remains with `RuntimePluginHost` and the current
`LegacyEditorPluginAdapter` is the only Qt payload projection route.

## Objective

Audit the bounded command projection path from Host-copied editor
contributions through `LegacyEditorPluginAdapter` to `LayoutManager`'s concrete
`QAction`, menu, and toolbar lifecycle. Identify the existing runtime command
authority, callback binding, enablement, and unload cleanup seams. Select at
most one smallest portable fact or regression improvement only if it preserves
the singular runtime command authority and the sole Qt Adapter projection.

## Constraints

Keep `FrameCore` L0, `lotucosm-vitaloom` the sole L1 engine/product mega-plugin,
and `versions/1.0.0/runtime` the product boundary. Preserve `RuntimePluginHost`,
`LegacyEditorPluginAdapter`, `.pond`, Project World, Inspector command binding,
SR2D, SR/PS, Player/export, package/signature behavior, public imports, and
entity/component MRO. Do not create a second Host, command registry, event bus,
widget DSL, renderer, UI framework, app shell, or peer engine root.

## Required evidence before closure

Document source-level command authority and the exact Qt action projection and
unload path. Run focused contribution/Adapter/LayoutManager lifecycle tests plus
full Qt regression, standard/eager Editor smokes, the four guardrails, and the
independent signature collection. Record any extraction as a non-authoritative
portable fact; do not claim a replacement Host or OpenGL default readiness.


## Findings and implementation

`RuntimePluginHost.load_plugin()` publishes command specs before invoking the
Adapter; unload cleans Adapter UI, calls plugin unload, then releases Host-owned
commands. The Adapter only builds QAction callbacks that dispatch to the global
registry with contribution provenance. LayoutManager owns QAction/menu/toolbar
creation and removal. No second command authority exists.

Each QAction trigger now obtains a fresh thawed JSON-safe contribution payload.
A mutating handler therefore cannot leak state into a later click or mutate the
Host-copied contribution facts. A focused regression proves two invocations each
receive the original nested payload and that command ownership remains runtime
Host-owned.

## Evidence

- Focused Adapter/contribution/LayoutManager lifecycle proof: `18 passed in 0.47s`.
- Full Qt regression: `1670 passed, 34 skipped, 34 subtests passed in 198.85s`.
- Standard/eager Editor smokes: `13/20`, `20/20`; four guardrails and diff check
  passed; independent signature-only collection: `2 passed in 0.27s`.

## Closure

E63 is complete. The unique next gate is E64: Legacy Editor Shell Viewport Tab
Projection Boundary Audit. Audit the central viewport/tab fallback projection
without creating a new UI Host or changing rendering policy.
