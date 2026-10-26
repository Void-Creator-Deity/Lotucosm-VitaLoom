# Phase E83 -- Editor Smoke Public Observation Failure-Semantics Audit

Date: 2026-07-30
Status: complete

## Previous gate

E82 established that Hot Reload Plugin has no independent passive display
projection: every observation fact is action-adjacent and already validated
fail-closed before dialog selection or reload. Its malformed-fact regression
proves no dialog/reload occurs. No Hot Reload runtime change was warranted.

The `main.py` editor smoke helper is the sole remaining non-Host runtime caller
of `observe_plugins()` outside the public adapter helper. It is a tooling
read-model path, but currently assumes the snapshot is a mapping and assumes
nested discovery/failed/count facts have mapping shape.

## Objective

Audit and, if needed, minimally repair editor-smoke public-observation failure
semantics. An unavailable, non-mapping, partial, or malformed observation must
produce a deterministic smoke failure/report, not a Python exception or false
healthy result. Preserve the Runtime Plugin Host as the only authority and keep
normal editor runtime behavior unchanged.

## Required evidence

1. Map exactly how `main.py` consumes Host observation and prove it is smoke
   tooling/read-model only, never editor command authorization.
2. Add a bounded test seam that reproduces malformed top-level and nested
   public facts without Host-private-state access.
3. If a correction is needed, prove it fails deterministically, reports no
   false successful counts, and does not create a second observation cache or
   Host.
4. Run focused smoke/bootstrap, Host/control/lifecycle/reload, legacy consumer,
   source-only syntax/whitespace checks, guardrails, release checks, and
   independent signatures.
5. Record interpreter/offscreen configuration, pre/post evidence, skips, E68
   broad evidence, QPainter/OpenGL status, fallback/unblock facts, and exactly
   one next Gate.

## Explicit non-goals

Do not add a second Host, metadata registry, command registry, event bus,
serializer, renderer, layout manager, widget DSL, UI framework, or app shell.
Keep PyQt6/QPainter/OpenGL as a legacy UI-host adapter. Preserve `.pond`,
Project World, Inspector command binding, SR2D, SR/PS, Player/export,
manifests, public imports, and MRO. QPainter remains default; OpenGL/native
acceleration is not default-ready. Do not claim whole-refactor completion.

## Audit result

- `main.py` consumes `resolve_plugin_host(kernel.editor_context).observe_plugins()`
  only inside `_run_editor_smoke()`, after suite bootstrap and before smoke
  shutdown. It is neither a normal editor command nor an authorization path.
- The original projection assumed mapping-shaped top-level and nested facts;
  malformed facts could raise on `.get()`/subscript access and a thrown public
  call could escape. `main.py` now has smoke-local validation/report helpers
  that use only the published Host seam. They reject non-mappings, unavailable
  or invalid status, malformed error maps, and absent/invalid/negative counts.
- A public call exception becomes the same deterministic unavailable/malformed
  smoke failure. Valid ready/degraded snapshots retain existing error reporting
  and the healthy `active/catalog` message. No Host, cache, command path, or
  normal editor behavior changed.

## Verification evidence

- Genuine TDD red: the new bounded observation cases initially failed `8 failed
  in 0.37s`; after extracting the reporting read model, `3 failed, 8 passed in
  0.34s`; before public-call containment, `1 failed, 11 passed in 0.34s`.
- Focused E83 regression: `12 passed in 0.22s`.
- Source-only syntax/trailing-whitespace check using
  `compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")`: passed.
- E83 plus suite bootstrap, legacy consumers, Host control/lifecycle/reload,
  and activation: `103 passed, 1 skipped in 2.56s` under `.venv\python.exe -B`,
  `QT_QPA_PLATFORM=offscreen`, and `PYTHONDONTWRITEBYTECODE=1`.
- Root entry offscreen smoke (`.venv\python.exe -B main.py --smoke-editor`):
  passed and printed `Editor smoke OK: suite=lotucosm.vitaloom.suite
  product=lotucosm-vitaloom@1.0.0 plugins=13/20`, followed by reverse unload.
- Adjacent Package Manager / Manager Refresh: `36 passed in 0.58s`.
  Architecture/release guardrail suite: `20 passed in 14.94s`; project plugin
  model, core boundaries, GUI boundaries, and release consistency tools: OK.
- Signature environment: `.venv\python.exe` cannot collect the signature test
  because `cryptography` is absent. The independent existing base interpreter
  `D:\app\anaconda3\python.exe` ran
  `python -B -m pytest tests/test_package_signature_warn_only.py -q` and passed
  `2 passed in 0.22s`. No dependency installation was needed. Fallback is the
  recorded base-interpreter proof; unblock, if venv-local signature execution is
  later required, is to use an already provisioned environment or obtain user
  approval to install its missing dependency.
- E68 remains the latest broad offscreen Qt proof: `1678 passed, 34 skipped,
  34 subtests`; regular/eager editor smokes are `13/20` and `20/20`.
  QPainter remains default; OpenGL/native is not default-ready. Whole-refactor
  completion is not claimed.

## Next gate

**E84 -- Runtime Ops Public Observation Call-Failure Containment Audit.** Audit
and, only if necessary, contain a thrown public `observe_plugins()` call at the
existing `PluginRuntimeOpsMixin` seam. Preserve its existing unknown-display
and action-denial behavior, with no new authority or observation cache.
