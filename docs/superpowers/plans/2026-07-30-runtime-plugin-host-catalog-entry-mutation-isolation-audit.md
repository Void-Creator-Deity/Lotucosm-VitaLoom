# Phase E75 -- Runtime Plugin Host Catalog-Entry Mutation-Isolation Audit

Date: 2026-07-30
Status: complete

## Previous gate

E74 completed the direct catalog-entry metadata round trip. A
`PluginHostCatalogEntry` now carries the copied declared-name and normalized
editor-contribution facts required by known-id activation and legacy Adapter
projection; the direct cache seam restores the complete Host metadata shape.

## Objective

Audit whether a consumer can mutate Host-owned or later activation metadata
through nested mutable values exposed by `RuntimePluginHost.catalog_entries()`,
`PluginHostCatalogEntry.normalized()`, `PluginHostCatalogEntry.to_dict()`, or
`RuntimePluginHost.cache_catalog_entry_metadata()`. Confirm that catalog facts
are snapshots, not an alternate mutable metadata authority.

## Required evidence

1. Trace ownership/copy behavior for `provides`, nested editor contributions,
   normalized entries, dictionary projection, and direct catalog caching.
2. Add a deterministic regression that mutates nested catalog facts at each
   public hand-off boundary and proves the original Host cache, a catalog entry,
   and a destination Host activation snapshot remain isolated.
3. If a leak exists, repair it at the smallest Qt-free Host/lifecycle boundary;
   do not add another metadata owner or registry.
4. Run focused Host/catalog and Adapter coverage, syntax and architecture/
   release guardrails, signature proof, and `git diff --check`. Record broad
   proof status honestly.

## Explicit non-goals

Do not add a Host, metadata registry, command registry, event bus, renderer,
layout manager, widget DSL, UI framework, or app shell. Preserve `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, MRO, and the legacy activation-context contract.
QPainter remains default; neither OpenGL nor native acceleration is
default-ready. Do not claim whole-refactor completion.

## Completion criteria

- The public catalog hand-off boundaries have explicit ownership findings.
- A reproducible nested-mutation scenario proves isolation or has a minimal
  regression-backed fix.
- Evidence and skips are recorded in the mainline docs and fresh-session
  prompt, with exactly one next Gate named.
## Audit result

The public catalog hand-off boundaries are isolated already. `catalog_entries()`
deep-copies cached nested contributions into a `PluginHostCatalogEntry`; the
entry's `normalized()` and `to_dict()` paths copy nested values again; and
direct caching normalizes then deep-copies those facts into the destination
Host cache. `provides` is normalized into an immutable tuple. No secondary
metadata authority or mutation leak was found, so the Gate requires no runtime
behavior change.

The deterministic regression exercises every mutable boundary: it mutates a
nested contribution obtained from a source catalog entry, from that entry's
normalized form, and from its dictionary projection; then it directly caches
the entry in a destination Host, mutates the original entry again, and activates
by known id. It proves the source Host cache, catalog entry, destination Host
cache, and Adapter activation snapshot do not alias one another. The plugin's
second live metadata access raises, proving activation consumes the copied Host
facts.

## Evidence

- Syntax and direct catalog mutation regression: `13 passed in 0.34s`.
- Focused Host/reload/catalog coverage: `68 passed, 1 skipped in 1.65s`.
- Offscreen Adapter/context projection coverage: `25 passed in 0.86s`.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency
  guardrails all passed.
- Independent shared-Python package signature proof: `2 passed in 0.22s`.
- A fresh full offscreen Qt suite and application smokes were not rerun because
  this Gate adds only a headless catalog ownership proof. E68 remains the
  latest broad proof: `1678 passed, 34 skipped, 34 subtests`; regular/eager
  smokes `13/20` and `20/20`.

## Next gate

E76 -- Runtime Plugin Host Catalog-Entry Serialization Contract Audit. Audit
whether `PluginHostCatalogEntry.to_dict()` and lifecycle/catalog serialization
preserve a deterministic, JSON-safe public contract for the complete Host-owned
metadata shape without exposing mutable aliases.