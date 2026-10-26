# Fresh-session handoff: E72 completed, E73 next

E72, **Runtime Plugin Host Deactivation Metadata Snapshot Consistency Audit**,
is complete. It found that the Host supplied its cached metadata dictionary
straight to Adapter callbacks, enabling mutation of Host facts; it also treated
a present but empty Host metadata record as absent and fell back to live plugin
metadata during deactivation. The Qt-free Host now creates an independent deep
copy for every callback, uses membership instead of truthiness for Host-cache
selection, and only calls the live fallback lazily when the Host has no record.
`plugin_metadata` remains the sole registered-metadata authority.

Evidence is complete for this narrow change: direct metadata regressions `2
passed, 8 deselected`; lifecycle/shutdown `18 passed`; the E70 real Qt retry
`1 passed, 13 deselected`; reload coverage `52 passed`; core Host `5 passed`;
`py_compile`, four guardrails, `git diff --check`, and shared-Python signature
proof `2 passed` are green. No new full Qt/application smoke was run; E68
remains the latest broad proof (`1678 passed, 34 skipped, 34 subtests`; regular
/eager smokes `13/20` and `20/20`).

Execute exactly E73: **Runtime Plugin Host Activation Metadata Snapshot
Consistency Audit**. Audit registration, activation validation/context
resolution, reload/reactivation, and activation rollback boundaries. Use a
real regression to establish whether mutable or failing live
`get_plugin_info()` can override or block Host-owned declarative activation
facts, and whether rollback callback metadata must be isolated consistently.
Do not assume code must change: preserve the current live activation-context
contract unless a concrete failing regression proves a minimal Host-local
repair. Maintain the singular architecture: FrameCore -> lotucosm-vitaloom ->
RuntimePluginHost -> LegacyEditorPluginAdapter -> LayoutManager. QPainter is
default; OpenGL is not default-ready; do not claim whole-refactor completion.