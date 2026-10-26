# Phase E74 -- Runtime Plugin Host Catalog-Entry Metadata Completeness Audit

Date: 2026-07-30
Status: complete

## Previous gate

E73 made known-id activation and active manual reload consume one copied,
Host-owned metadata snapshot instead of re-reading a mutable plugin after
registration or reload preflight. Adapter projection and failed-activation
cleanup now receive separate copies.

## Objective

Audit every direct catalog-entry metadata cache route, especially
`RuntimePluginHost.cache_catalog_entry_metadata()`, against the metadata shape
produced by ordinary `cache_plugin_metadata()`. Establish whether a catalog
entry can leave Host-owned metadata incomplete for known-id activation,
activation-context resolution, command publication, or legacy editor
contribution projection. If a defect is reproducible, correct it at the single
Qt-free Host metadata authority while preserving existing public contracts.

## Required evidence

1. Compare normalized `PluginHostCatalogEntry` fields with the cache shape
   produced by `_cache_plugin_metadata()`.
2. Trace all callers of `cache_catalog_entry_metadata()` and direct catalog
   replacement/reconciliation paths.
3. Add a narrow regression only when a reachable incomplete-cache path can
   violate a consumer contract. Cover known-id activation, context lookup,
   command publication, and legacy Adapter contributions as applicable.
4. Run focused Host/reload coverage, relevant Qt-adapter coverage if exercised,
   syntax and architecture/release guardrails, signature proof, and
   `git diff --check`. Record broad-suite status honestly.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
renderer, layout manager, widget DSL, UI framework, or app shell. Do not alter
`.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export,
package/project manifests, public imports, MRO, or the established legacy
activation-context compatibility contract. QPainter remains the default path;
do not claim OpenGL or native acceleration default readiness, nor whole-refactor
completion.

## Initial audit hypothesis

`cache_catalog_entry_metadata()` may currently retain activation, version,
description, and provides facts while omitting facts retained by
`_cache_plugin_metadata()`, such as canonical `name`, `declared_name`, and
normalized `editor_contributions`. This is not yet a defect claim: the audit
must first prove whether such metadata can enter a known-id activation or
observer path without later replacement by a complete plugin metadata cache.

## Completion criteria

- The reachable catalog-entry cache paths and all metadata consumers are traced.
- Any reproduced completeness gap is covered by a deterministic regression and
  repaired with the smallest Host-local change.
- Tests and checks demonstrate the claim; skipped broad proof is recorded.
- `docs/mainline_status.md`, `CONTEXT.md`, `docs/INDEX.md`, and this fresh
  session prompt state the result and name exactly one next Gate.
## Audit result

cache_catalog_entry_metadata() had no production caller at audit time
(g --glob '*.py' 'cache_catalog_entry_metadata\\(' . found only its
definition), but it is a public Host seam for an already-validated replacement
candidate. The seam was materially incomplete: ordinary Host caching retained
canonical 
ame, declared display name, and normalized editor-contribution
facts, while catalog caching retained none of those facts. catalog_entries()
also could not export them, so a direct catalog round trip could activate a
known id with incomplete context and Adapter projection metadata.

The smallest Qt-free repair extends PluginHostCatalogEntry with backward-
compatible defaulted declared_name and editor_contributions fields. Its
normalization and dictionary projection copy those facts. The Host now exports
them from catalog_entries() and caches the complete normalized fact set in
cache_catalog_entry_metadata(). Cached editor-contribution dictionaries are
copied rather than re-parsed: they already contain the Host-assigned owner id,
which is intentionally not a declaration input field.

The deterministic regression begins with a plugin whose second
get_plugin_info() call raises, exports its catalog entry, directly caches that
entry in a second Host, and activates by known id. It proves one initial info
call, declared runtime context, command ownership, and complete normalized
legacy Adapter contribution projection. An adjacent legacy Adapter regression
now explicitly verifies that its observed metadata is an equal but independent
Host snapshot, consistent with E73's snapshot contract.

## Evidence

- Syntax: py_compile passed for plugin_host_lifecycle.py,
  untime_plugin_host.py, and the E74 lifecycle regression.
- Focused direct coverage: 27 passed, 1 skipped in 0.82s.
- Host/reload/catalog coverage: 67 passed, 1 skipped in 1.61s.
- Offscreen Adapter/context projection coverage: 25 passed in 0.83s.
- Project-plugin, core-boundary, GUI-boundary, and release-consistency
  guardrails all passed.
- Independent shared-Python package signature proof: 2 passed in 0.37s.
- A fresh full offscreen Qt suite and application smokes were not rerun because
  this Gate changes only Qt-free Host catalog facts plus focused Adapter
  assertions. E68 remains the latest broad proof: 1678 passed, 34 skipped,
  34 subtests; regular/eager smokes 13/20 and 20/20.

## Next gate

E75 -- Runtime Plugin Host Catalog-Entry Mutation-Isolation Audit. Audit the
nested mutable catalog facts exported and re-cached by this public seam to
prove no caller can mutate Host-owned metadata through a catalog entry or a
subsequent activation snapshot.