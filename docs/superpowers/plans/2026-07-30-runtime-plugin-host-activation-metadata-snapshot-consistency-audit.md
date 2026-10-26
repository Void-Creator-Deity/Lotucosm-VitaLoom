# Phase E73 -- Runtime Plugin Host Activation Metadata Snapshot Consistency Audit

Date: 2026-07-30
Status: complete

## Previous gate

E72 made deactivation metadata Host-owned: Adapter lifecycle mutation cannot
contaminate Host cache facts, present-empty cache entries are authoritative, and
staged retry never re-reads mutable live metadata merely to clean up an active
plugin.

## Objective

Audit the complementary activation route:

```text
registered Host metadata -> activation validation/context -> command publication
-> Adapter projection -> activation rollback
```

Determine whether activation or reactivation of an already registered plugin
wrongly depends on a mutable or failing later `plugin.get_plugin_info()` call,
or exposes Host-owned metadata to mutation during the activation/rollback
sequence. Preserve the live activation-context compatibility contract unless a
reproducible regression proves that Host-owned declarative facts must be used
at a narrower boundary.

## Required evidence

Trace `register_plugin()`, direct registry replacement/cache paths,
`load_plugin()`, activation-context resolution, Adapter publication, rollback,
and manual reload. Add a direct Host regression only for behavior proven unsafe:
for example, register stable metadata, make later live metadata change/fail,
then demonstrate whether activation must use the registered snapshot and that
rollback cleanup receives an isolated equivalent snapshot. Run focused Host,
reload, and relevant Qt-adapter coverage plus syntax, boundary, release, diff,
and signature checks. Record any unrun broad suite explicitly.

## Explicit non-goals

Do not introduce a second Host, metadata registry, command registry, event bus,
renderer, layout manager, widget DSL, UI framework, or app shell. Do not break
`.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export,
package/project manifests, public imports, or the established legacy
activation-context contract. Do not claim native/OpenGL default readiness or
whole-refactor completion.

## Findings and implementation

The audit reproduced two unsafe reads after metadata had already been accepted
by the Host:

1. `execute_lifecycle_target()` knew the canonical registry key but called
   `load_plugin(plugin)` without it. `load_plugin()` then queried live
   `get_plugin_info()` again before context resolution, so a registered plugin
   could fail or drift during a later activation.
2. Manual active reload queried candidate metadata during preflight, removed the
   old active closure, then queried the candidate a second time while replacing
   the registry, and a third time during activation. A later metadata failure
   could therefore interrupt an already-destructive reload.

The minimal Qt-free correction keeps `RuntimePluginHost.plugin_metadata` as the
only registered-metadata authority. Known lifecycle activation supplies its
canonical `plugin_id` to `load_plugin()`, which obtains one copied Host snapshot
for validation, context resolution, command publication, and projection.
Adapter projection and activation-rollback cleanup each receive independent
copies. The compatibility direct-call path still obtains its identity from the
plugin object before following the same snapshot sequence. Manual reload now
deep-copies its once-validated candidate metadata during preflight, uses that
copy to replace the registry cache, and activates by the known canonical id.

## Evidence

- New direct Host regression proves a registered plugin whose later
  `get_plugin_info()` raises still reaches load/projection rollback solely from
  Host facts; Adapter mutation cannot affect rollback cleanup metadata.
- New active manual-reload regression proves candidate metadata is read exactly
  once before old active closure removal and the replacement converges.
- Focused Host lifecycle, shutdown, and manual reload suite: `33 passed in
  0.76s`.
- Reload integration pack under offscreen Qt: `53 passed in 1.50s`.
- Existing real Qt retry regression: `1 passed, 13 deselected in 0.37s`;
  core Host suite: `5 passed in 0.24s`.
- Changed-file `py_compile`, project-plugin-model, core-boundary, GUI-boundary,
  and release-consistency guardrails passed; shared-Python package signature:
  `2 passed in 0.22s`; `git diff --check` passed with only pre-existing CRLF
  conversion advisories.

No new full offscreen Qt run or application smoke was necessary for this
Qt-free Host/reload metadata boundary. E68 remains the newest broad proof:
`1678 passed, 34 skipped, 34 subtests`; regular/eager smokes `13/20` and
`20/20`. QPainter remains default and OpenGL is not default-ready.

## Unique next Gate

E74 -- Runtime Plugin Host Catalog-Entry Metadata Completeness Audit. Audit
whether every direct catalog-entry cache path supplies all declarative facts
needed by known-identity activation, context selection, commands, and legacy
Adapter projection, without live fallback or a parallel metadata authority.
