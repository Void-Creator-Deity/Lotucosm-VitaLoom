# Phase E77 -- Runtime Plugin Host Public Observation Consumer Schema Compatibility Audit

Date: 2026-07-30
Status: complete

## Previous gate

E76 restored the complete public catalog-entry serialization contract. The
`NestedPluginHost.observe_plugins()["catalog"]` route now passes
`PluginHostCatalogEntry.to_dict()` through the existing JSON-safety helper, so
it includes `activation_context_source` just like lifecycle reporting. The
correction kept one Host-owned metadata and serialization authority.

## Objective

Audit every legacy capability consumer of public Runtime Plugin Host observation
for schema compatibility. Verify consumers use documented public facts rather
than private Host registries, tolerate the complete catalog metadata shape
without reconstructing it, and preserve the active/protected/reloadable rules
owned by the Runtime Plugin Host.

## Required evidence

1. Locate consumers of `observe_plugins()`, the plugin-host control capability,
   lifecycle report catalog output, and related Package Manager/reload/menu
   projections. Classify each as headless or Qt-dependent.
2. Trace consumer field access. Confirm it is limited to public observation or
   catalog fields and that no consumer reaches into a private registry to
   recreate metadata, serializer behavior, active state, protection, or
   reloadability.
3. Add a narrowly scoped regression for a real compatibility risk found by the
   audit. Prefer a headless seam; if no behavior change is needed, add only
   durable regression proof appropriate to the existing public contract.
4. Run focused Host/control/lifecycle/reload and consumer coverage, plus
   syntax, project guardrails, signature proof, and `git diff --check`.
   Explicitly separate unavailable Qt evidence from headless results.
5. Record exact evidence, skipped/blocked Qt coverage, fallback and unblock
   paths, E68 broad proof status, and exactly one next Gate in the mainline
   documentation and fresh-session prompt.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
serializer, renderer, layout manager, widget DSL, UI framework, or app shell.
Do not expand the legacy PyQt6/QPainter/OpenGL editor adapter into engine or
extension authority. Preserve `.pond`, Project World, Inspector command
binding, SR2D, SR/PS, Player/export, manifests, public imports, and MRO.
QPainter remains the default UI path; OpenGL/native acceleration are not
default-ready. Do not claim the whole refactor is complete when this gate
closes.

## Completion criteria

- Public observation consumers are mapped and have regression-backed evidence
  of schema-compatible, Host-owned behavior, or any reproduced defect receives
  a minimal correction at the existing seam.
- No consumer creates competing metadata/serialization state or relies on
  private Host registry details for public observation behavior.
- Results, verification evidence, skips, fallback/unblock notes, and exactly
  one next Gate are recorded in the plan, status/context/index docs, and
  fresh-session prompt.
## Audit result

The mapped public-observation consumers remain on the exact published
capability. The Qt-free `PluginRuntimeOpsMixin` reads only `catalog` row
`plugin_id`, `scope`, and `protected`; `HotReloadPlugin` reads only catalog
`plugin_id`/`scope` and `reloadable_plugin_ids`. The legacy Plugin Manager uses
`plugin_ids`, `active_plugin_ids`, and `failed_plugin_ids`. The Qt Package
Manager consumes public `active_plugin_ids` plus catalog `plugin_id`,
`version`, `description`, `provides`, and `protected`. The application smoke
uses only public error maps and counts. Project Manager uses the separate
published scan/sync lifecycle methods rather than observation.

No consumer recreates catalog metadata or serialization, and the source audit
found no consumer-side direct access to Runtime Plugin Host metadata,
loaded-plugin, protection, catalog, or reloadability internals. E77 adds a
Qt-free regression supplying the complete E76 catalog row (including declared
name, activation provenance, normalized provides, contributions, active, and
reloadable facts) through a fake capability that exposes no Host internals.
Runtime operations and Hot Reload continue to use only their documented public
facts and preserve the Host-owned reload/protection behavior. No production
change was needed.

## Verification evidence

- Consumer regression plus E76 control, Hot Reload, and focused Host/lifecycle/
  reload/catalog coverage: `68 passed, 1 skipped in 1.28s`.
- The new direct consumer slice: `25 passed in 0.48s`.
- Four changed/related Qt-free sources were syntax-compiled without bytecode
  writes. A normal `py_compile` retry could not replace an existing
  `editor_extensions/__pycache__/hot_reload_plugin...pyc` artifact because of
  `WinError 5`; this is an environment/pycache permission issue, not a syntax
  failure, and no cache file was changed.
- Project/architecture/release guardrails plus warn-only package signature:
  `18 passed in 15.09s`; independent signature rerun: `2 passed in 0.28s`.
  `git diff --check` passed with only existing whole-worktree LF-to-CRLF
  advisories and no whitespace error.

The direct Qt Package Manager consumer tests
`tests/test_package_manager_plugin_host_capability.py` and
`tests/test_manager_refresh.py` could not collect because the current
`D:\app\anaconda3\python.exe` lacks `PyQt6`; the repository has no
`.venv\Scripts\python.exe`. No dependency was installed. The static source
mapping and headless regression are the fallback; rerun those tests in the
configured offscreen PyQt6 project environment to unblock direct Qt proof.

E68 remains the latest broad proof: full offscreen Qt `1678 passed, 34
skipped, 34 subtests`; regular/eager smokes `13/20` and `20/20`. QPainter
remains default, and OpenGL/native acceleration are not default-ready. E77 does
not claim the whole refactor is complete.

## Next gate

**E78 -- Runtime Plugin Host Public Observation Fail-Closed Consumer Boundary
Audit.** Audit whether each legacy consumer handles unavailable, malformed, or
partial public observation snapshots deterministically and fails closed without
falling back to private Host state, while preserving the existing Host authority
and Qt-free boundary.