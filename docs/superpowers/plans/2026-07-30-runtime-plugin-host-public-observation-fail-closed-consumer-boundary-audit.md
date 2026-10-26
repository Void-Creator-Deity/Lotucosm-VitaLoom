# Phase E78 -- Runtime Plugin Host Public Observation Fail-Closed Consumer Boundary Audit

Date: 2026-07-30
Status: complete

## Previous gate

E77 confirmed that mapped public-observation consumers use the exact published
capability and documented fields only. A full E76 catalog row reaches Qt-free
Runtime Ops and Hot Reload without private Host access or a duplicate metadata
or serialization authority.

## Objective

Audit whether public-observation consumers behave deterministically and fail
closed when the published capability is unavailable or returns partial/malformed
snapshot data. Preserve the Runtime Plugin Host as the authority: consumers
must not infer missing facts from private Host state, bypass protection/reload
rules, or create fallback registries.

## Required evidence

1. Enumerate unavailable, partial, and malformed observation behavior for
   Runtime Ops, Hot Reload, legacy Plugin Manager, Package Manager, and the
   application smoke. Distinguish documented Host output from defensive handling
   needed at legacy capability seams.
2. Reproduce any consumer crash, unsafe action, or incorrect fallback using a
   capability stub that exposes no private Host state.
3. Add the smallest Qt-free correction and regression only where a real
   fail-closed defect exists; otherwise add durable negative-path proof.
4. Run focused consumer/control/lifecycle coverage, source syntax, guardrails,
   signature, and diff check. Record inaccessible Qt tests separately with
   fallback and unblock details.
5. Close the gate with exact proof, broad E68 status, QPainter/OpenGL status,
   and exactly one next Gate.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
serializer, renderer, layout manager, widget DSL, UI framework, or app shell.
Preserve the existing `FrameCore -> lotucosm-vitaloom -> RuntimePluginHost ->
LegacyEditorPluginAdapter -> LayoutManager` path, `.pond`, Project World,
Inspector command binding, SR2D, SR/PS, Player/export, manifests, public
imports, and MRO. QPainter remains default; OpenGL/native acceleration are not
default-ready. Do not claim whole-refactor completion.

## Audit result

The Qt-free `PluginRuntimeOpsMixin` had a real authority-boundary defect. It
assumed `observe_plugins()` was a mapping with mapping catalog rows. A `None`
snapshot or malformed row crashed; an unavailable or empty catalog produced an
empty row that was treated as unprotected and could still reload, unload, or
persist a project disable for the selected plugin.

The minimal correction keeps the public capability as the only source of
permission facts. Runtime Ops now accepts only a mapping snapshot and a
non-string sequence catalog, skips non-mapping rows, returns a copied matching
public row, and denies reload, unload, and project disable when no trustworthy
row authorizes the selected plugin. It neither reads Host internals nor creates
a fallback registry or metadata cache. The E78 regression covers a non-mapping
snapshot, an unavailable empty catalog, and malformed catalog rows; each case
has no action, project command, sync, refresh, or exception.

The remaining consumer map is explicit: Hot Reload already converts a
non-mapping snapshot to empty public facts, validates its ID/catalog sequences,
and yields no candidates/targets rather than reloading. Legacy Plugin Manager
uses observation only for display refresh and still assumes a mapping; that is
a contained availability/display concern, not an action authorization path.
Static inspection of the Qt Package Manager identifies a real follow-up risk:
its selected-plugin disable branch reads `snapshot["catalog"]` without a
mapping boundary and can persist a disable then call `unload_plugin` when the
selected row is absent. Its package branch also treats a missing catalog as no
protected plugins. This requires real Qt regression before changing the
legacy adapter, so it is isolated as E79 rather than masked with untested code.

## Verification evidence

- E78 direct consumer regression: `8 passed in 0.15s`.
- Focused consumer/control/Hot Reload/Host/lifecycle/reload/activation coverage:
  `71 passed, 1 skipped in 1.29s`.
- Changed source and regression compiled with `compile(..., "exec")` using
  `utf-8-sig`, without writing bytecode: `2` source files.
- Project/architecture guardrails plus warn-only signature: `18 passed in
  14.97s`; independent signature rerun: `2 passed in 0.22s`.
- `git diff --check` passed. It reported only pre-existing whole-worktree
  LF-to-CRLF advisories, not a whitespace error.

Direct Qt Package Manager/manager-refresh collection remains blocked in this
environment: `D:\app\anaconda3\python.exe` has no `PyQt6`, and there is no
repository `.venv\Scripts\python.exe`. The attempted collection stopped with
`ModuleNotFoundError: No module named 'PyQt6'`; no dependency was installed.
The fallback is the source mapping and Qt-free Runtime Ops/Hot Reload proof.
The unblock path is the configured offscreen PyQt6 project environment running
`tests/test_package_manager_plugin_host_capability.py` and
`tests/test_manager_refresh.py` with E79's negative-path regressions.

E68 remains the latest broad proof: full offscreen Qt `1678 passed, 34
skipped, 34 subtests`; regular/eager Editor smokes `13/20` and `20/20`.
QPainter remains the default UI route; OpenGL/native acceleration is not
default-ready. Closing E78 does not claim the whole refactor is complete.

## Next gate

**E79 -- Qt Package Manager Public Observation Fail-Closed Action Boundary
Audit.** Reproduce and correct only the Qt Package Manager action paths that
could act on unavailable, malformed, or missing public catalog facts, using a
configured offscreen PyQt6 test environment.