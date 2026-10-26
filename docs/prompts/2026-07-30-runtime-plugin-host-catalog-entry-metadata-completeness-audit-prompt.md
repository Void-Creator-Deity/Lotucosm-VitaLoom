# Fresh-session handoff: E74 complete

Repository root:

```text
<repository-root>
```

## Completed result

E74 -- **Runtime Plugin Host Catalog-Entry Metadata Completeness Audit** is
complete. `cache_catalog_entry_metadata()` had no production caller, but its
public direct-cache seam could receive an already-validated replacement
candidate. It previously discarded canonical name, declared name, and
normalized editor-contribution facts retained by normal Host metadata caching.

`PluginHostCatalogEntry` now round-trips backward-compatible defaulted
`declared_name` and `editor_contributions`; `catalog_entries()` projects copied
facts and `cache_catalog_entry_metadata()` restores the complete Host metadata
shape. A regression proves known-id activation, runtime context, command
ownership, and legacy Adapter projection still work when later live metadata
access fails. Cached contribution facts are copied rather than re-parsed,
because they already carry the Host-assigned owner id.

## Evidence

- Direct focused coverage: `27 passed, 1 skipped in 0.82s`.
- Host/reload/catalog coverage: `67 passed, 1 skipped in 1.61s`.
- Offscreen Adapter/context coverage: `25 passed in 0.83s`.
- Syntax, four architecture/release guardrails, and shared-Python signature
  proof (`2 passed in 0.37s`) are green.
- E68 remains the latest broad offscreen Qt and smoke proof: `1678 passed,
  34 skipped, 34 subtests`; regular/eager smokes `13/20` and `20/20`.

## Next gate

Execute exactly E75 -- **Runtime Plugin Host Catalog-Entry Mutation-Isolation
Audit**. First create a dated E75 plan and fresh-session prompt. Audit whether
nested mutable data in a `PluginHostCatalogEntry`, its `to_dict()` result, or
its direct catalog-cache round trip can alias and mutate Host-owned metadata or
later activation snapshots. Add a minimal deterministic regression only if the
seam leaks ownership. Keep the fix Qt-free and Host-local; preserve the single
path `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager`.

Do not create a second Host, metadata registry, command registry, event bus,
renderer, layout manager, widget DSL, UI framework, or app shell. Preserve
`.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. The worktree contains extensive user/prior
migration changes: never stage, commit, reset, restore, clean, delete, or
overwrite unrelated work. Do not rewrite untracked `layout_manager.py`
wholesale; it has mojibake risk.