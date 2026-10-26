# Fresh-session handoff: E73 complete; E74 next

E73 -- **Runtime Plugin Host Activation Metadata Snapshot Consistency Audit**
is complete. It proved and fixed two repeated-live-metadata hazards: planned
activation now passes its known canonical id into `RuntimePluginHost.load_plugin`
and uses one copied Host snapshot for validation, context, commands, and
projection; manual reload reuses a deep-copied preflight candidate metadata
record for replacement and known-id activation. Adapter projection and failed
activation cleanup receive independent copies. Direct regressions, Host/reload
coverage, the relevant offscreen Qt retry, syntax, all four guardrails, diff,
and shared-Python signature checks are green. The latest full Qt/smoke evidence
remains E68; QPainter is default and OpenGL is not default-ready.

Execute exactly E74: **Runtime Plugin Host Catalog-Entry Metadata Completeness
Audit**. Before implementation, create a dated E74 plan and prompt. Trace every
reachable path that calls or can rely on `cache_catalog_entry_metadata()` or any
direct catalog replacement. Establish by regression whether the cached record
contains every declarative fact required by known-id activation,
`activation_context_for`, command ownership, and legacy editor-contribution
projection. If a repair is proven necessary, keep it small, Qt-free, and within
the singular RuntimePluginHost metadata authority. Do not add a Host, registry,
event bus, renderer, layout manager, widget DSL, UI framework, app shell, or
peer engine root; preserve `.pond`, Project World, Inspector command binding,
SR2D, SR/PS, Player/export, manifests, public imports, and MRO. Close E74 with
specific test evidence, recorded skips/fallbacks, and exactly one next Gate.
