# Phase E82 -- Hot Reload Plugin Public Observation Display Resilience Audit

Date: 2026-07-30
Status: complete

## Previous gate

E81 closed the legacy Plugin Manager's display-only public-observation path. It
now treats non-mapping snapshots and malformed active-id facts as explicit
unknown rather than crashing or asserting a false loaded/inactive state. The
correction uses the existing public observation mixin, does not issue reload or
unload, and does not create another plugin authority.

`hot_reload_plugin.py` was the remaining legacy adapter consumer with an
observation helper and an apparent reloadable-plugin projection. Unlike a
passive manager list, this surface also owns reload action entry points; its
observation handling must not become authorization for a reload command.

## Result

- The source map shows no passive list/detail/status display refresh in Hot
  Reload Plugin. `_observe_plugins()` feeds the choose-command candidate list
  and the user-mod batch target calculation only. The explicit
  `reload_plugin()` call is the action itself. Thus all observed facts on this
  surface are action-adjacent rather than a separate display-only projection.
- The existing implementation already fails closed: non-mapping snapshots
  become an empty copied fact map; reloadable ids must be a non-string
  `Sequence`; user-mod catalog rows must be mappings in a non-string sequence;
  and target ids are intersected with the validated reloadable set. Invalid
  facts yield no candidates/no targets and cannot reach dialog selection or
  `reload_plugin()`.
- E82 added a public-capability regression for non-mapping observation, `None`
  or string reloadable ids, and `None` or string catalog facts. It proves no
  dialog bridge and no reload call occur. No Hot Reload runtime source change
  was warranted: altering a correct fail-closed action path merely to share a
  display helper would blur the authorization boundary.
- Expanded verification exposed one stale source-level test assertion left by
  E81: it required every legacy adapter to spell `resolve_plugin_host`, even
  though Plugin Manager correctly uses `PluginRuntimeOpsMixin` as its existing
  public seam. The test now recognizes either formal public seam; it still
  rejects all legacy PluginLoader-private-state reads. This is a test contract
  repair, not a new Host access path.

## Evidence

Run with `.venv\python.exe`, `QT_QPA_PLATFORM=offscreen`, and
`PYTHONDONTWRITEBYTECODE=1` unless noted otherwise:

1. The new targeted capability proof in
   `tests/test_legacy_plugin_host_capability_consumers.py` passed
   `13 passed in 0.27s`.
2. Source-only compile (without bytecode) and trailing-whitespace checks passed
   for `hot_reload_plugin.py`, the capability-consumer test, and the public-seam
   source contract. The source map confirms public observation only at the
   documented Hot Reload helper/action sites.
3. Before correcting the stale textual seam assertion, expanded verification
   reported `1 failed, 79 passed, 1 skipped`; the failure was the test's
   obsolete `resolve_plugin_host` spelling requirement for Plugin Manager, not
   a Hot Reload behavior defect. After the narrow assertion repair, Hot
   Reload/menu, legacy-consumer, editor seam, Host control/lifecycle/reload,
   runtime command lifecycle, and activation coverage passed
   `80 passed, 1 skipped in 1.50s`.
4. Adjacent Package Manager regression passed `53 passed, 8 subtests passed in
   2.58s`. Boundary/import/manifest/release guardrails passed `21 passed in
   15.36s`; standalone core, GUI, and release tools all reported `OK`.
   The independent base-interpreter warn-only signature proof passed
   `2 passed in 0.17s`.
5. E68 remains the latest broad offscreen Qt evidence: `1678 passed,
   34 skipped, 34 subtests`; regular/eager editor smoke evidence is `13/20`
   and `20/20`.

## Scope and limits

No reload authorization was relaxed and no display normalization was allowed to
grant action permission. No Host private state, fallback catalog, cache, second
Host, registry, event bus, serializer, renderer, layout manager, widget DSL,
UI framework, or app shell was added. The sole chain remains `FrameCore ->
lotucosm-vitaloom -> RuntimePluginHost -> LegacyEditorPluginAdapter ->
LayoutManager`. `.pond`, Project World, Inspector command binding, SR2D,
SR/PS, Player/export, manifests, public imports, and MRO are unchanged.
QPainter remains default; OpenGL/native acceleration is not default-ready.
This is a bounded audit, not whole-refactor completion.

## Next gate

E83 -- Editor Smoke Public Observation Failure-Semantics Audit. Audit the
`main.py` smoke-only public observation projection: malformed/unavailable Host
facts must report a deterministic smoke failure rather than raise through
`.get()` or nested counts access. Keep it a test/tooling read-model boundary;
do not change Runtime Plugin Host authority or normal editor behavior.
