# Phase E59 -- Legacy UI Interface Authority Call-Site Audit and Non-Adapter Quarantine Enforcement

Date: 2026-07-30
Status: completed

## Previous gate

E58 retained and documented the legacy public interface surface. Validation is
complete: the project-local Qt environment passes full non-signature regression
(`1661 passed, 34 skipped, 34 subtests passed in 190.02s`), standard/eager
Editor smoke (`13/20`, `20/20`), and guardrails; package-signature coverage is
independently `2 passed in 0.27s` in the shared interpreter.

## Scope

Audit every runtime and author-facing call site of `IEditorPlugin`,
`IDockProvider`, `IViewportProvider`, and `IThemeProvider`. The only permitted
concrete UI projection authority is `LegacyEditorPluginAdapter`; legacy fallback
must remain bounded structural callable-shape behavior. Add targeted guards only
where audit evidence identifies an authority leak.

## Constraints

Preserve L0/L1/runtime boundaries, public legacy imports, abstract signatures,
and the deliberate `IEntityTypeProvider` / `IComponentTypeProvider` MRO. Do not
create another Host, registry, event bus, widget DSL, renderer, UI framework,
or app shell. Do not alter `.pond`, Project World, Inspector command binding,
SR2D, SR/PS, Player/export, manifests, or package/signature authority.

## Verification

Before closure, run focused audit tests, full non-signature regression,
signature-only coverage in an available cryptography-capable interpreter, four
guardrails, and standard/eager Editor smokes in `.venv`. Record exact proof and
one next gate.
## Completion record (2026-07-30)

- Runtime audit found `IEditorPlugin`, `IDockProvider`, `IViewportProvider`, and
  `IThemeProvider` only in `core/VitaLoom/kernel/plugin_interfaces.py`; no other
  runtime Python module imports, annotates, subclasses, checks, or type-gates
  these legacy UI interfaces.
- Added a source-level regression guard in `tests/test_runtime_plugin_contract.py`
  that fails if any of the four names leaks out of that public compatibility
  module. This is intentionally a quarantine guard, not a public-import removal.
- Targeted audit proof: `3 passed in 0.18s`.
- Full isolated Qt regression:
  `1662 passed, 34 skipped, 34 subtests passed in 165.59s`.
- All four guardrails pass in `.venv\python.exe`.

## Unique next Gate

E60 -- Legacy Editor Host Rendering Boundary Discovery and Migration-Readiness
Audit: map the current PyQt6/QPainter/OpenGL host adapter seams, classify what is
already Qt-free versus host-coupled, and produce an evidence-backed incremental
migration plan without introducing a replacement UI framework or changing
runtime authority.