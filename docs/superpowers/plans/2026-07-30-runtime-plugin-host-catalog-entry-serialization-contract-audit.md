# Phase E76 -- Runtime Plugin Host Catalog-Entry Serialization Contract Audit

Date: 2026-07-30
Status: complete

## Previous gate

E75 proved catalog entry export, normalization, dictionary projection, direct
caching, and later Adapter activation use copied nested facts rather than
aliases of the Host metadata cache. The public catalog route remains a single
Host-owned metadata authority.

## Objective

Audit the serialized public contract of `PluginHostCatalogEntry` and
lifecycle/catalog consumers. Determine whether the complete Host-owned facts
introduced in E74 are rendered deterministically and JSON-safely through
`to_dict()` and lifecycle serialization, without shape drift, non-serializable
values, private Host fields, or accidental loss of activation/projection facts.

## Required evidence

1. Trace all `PluginHostCatalogEntry.to_dict()` consumers and lifecycle plan,
   discovery, reconciliation, and diagnostics serialization paths.
2. Compare the catalog-entry dictionary shape against Host metadata and the
   documented reload/lifecycle inputs, including declared name, activation
   context facts, normalized provides, dependencies, protection, and editor
   contributions.
3. Add a deterministic regression that serializes a complete entry, verifies
   its exact safe shape and ordering assumptions, and round-trips it through
   the relevant public lifecycle path where supported.
4. Repair a reproduced defect at the narrow Qt-free lifecycle/Host seam only.
   Do not establish a second metadata or serialization authority.
5. Run focused Host/lifecycle/Adapter coverage, syntax, guardrails, signature
   proof, and `git diff --check`. Record broad proof status honestly.

## Explicit non-goals

Do not add a new Host, metadata registry, command registry, event bus,
renderer, layout manager, widget DSL, UI framework, or app shell. Preserve
`.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. QPainter remains the default UI path;
OpenGL and native acceleration are not default-ready. Do not claim the entire
refactor complete merely because this gate closes.

## Completion criteria

- Public serialized catalog outputs have an explicit, regression-backed
  contract or a smallest-scope correction.
- No mutable/private/non-JSON-safe Host fact leaks through the documented
  catalog/lifecycle outputs.
- Results, verification evidence, skips, fallback/unblock notes, and exactly
  one next Gate are recorded in mainline docs and the fresh-session prompt.
## Audit result

The public `NestedPluginHost.observe_plugins()` catalog loop used
`_json_safe(entry)`. Because the generic helper serializes dataclasses through
`asdict()`, it omitted the extra public export field
`activation_context_source` supplied by `PluginHostCatalogEntry.to_dict()`.
This caused observable shape drift even though lifecycle reporting already used
`item.to_dict()` correctly.

The narrow Qt-free correction is `row = _json_safe(entry.to_dict())`. It keeps
`PluginHostCatalogEntry.to_dict()` as the sole catalog-entry export authority;
no second serializer, metadata cache, Host, or lifecycle path was introduced.
The added regressions prove the complete explicit-context and default-context
shapes, deterministic JSON-safe output, lifecycle agreement, and consumer
mutation isolation.

## Verification evidence

- `python -m pytest tests/test_plugin_host_control_observation.py -q`:
  `7 passed in 0.18s`.
- Focused Host/lifecycle/reload/catalog coverage:
  `50 passed, 1 skipped in 0.59s`.
- Syntax: `python -m py_compile` for the changed capability module and its
  regression passed.
- Project/architecture guardrails plus warn-only package signature:
  `18 passed in 14.20s`; independent signature rerun: `2 passed in 0.30s`.
- `git diff --check` passed; only pre-existing whole-worktree LF-to-CRLF
  advisories were reported, with no whitespace error.

Qt-dependent Package Manager and other Adapter-consumer collection could not
be rerun in this environment because `D:\app\anaconda3\python.exe` has no
`PyQt6` and the repository has no `.venv\Scripts\python.exe`. No dependency
was installed. The fallback proof is the headless E76 coverage above plus E75
Adapter/context coverage (`25 passed in 0.86s`); the unblock path is to rerun
the relevant offscreen Qt consumer tests in the configured project environment
that provides PyQt6.

E68 remains the latest broad proof: full offscreen Qt `1678 passed, 34
skipped, 34 subtests`; regular/eager smokes `13/20` and `20/20`. QPainter
remains the default UI route, and OpenGL/native acceleration are not
default-ready. Closing E76 does not claim the whole refactor is complete.

## Next gate

**E77 -- Runtime Plugin Host Public Observation Consumer Schema Compatibility
Audit.** Audit legacy capability consumers of public plugin observation for
reliance on documented fields only, tolerance of the complete metadata shape,
and preservation of Host-owned active/protected/reloadable rules without private
registry access or a competing serialization authority.