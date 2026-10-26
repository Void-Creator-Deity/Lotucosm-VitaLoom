# Phase E58 -- Legacy Public Plugin Interface Compatibility Contract Audit and Deprecation Documentation

Date: 2026-07-30
Status: completed

## Architecture authority

Preserve `L0 FrameCore -> sole L1 lotucosm-vitaloom engine/product mega-plugin and recursive downstream Plugin Host/derived framework -> versions/1.0.0/runtime L2-L4`. `IRuntimePlugin` / `RuntimePluginHost` remain Qt-free lifecycle and metadata authority; Host-copied `editor_contributions` remain portable editor-shell authority; `LegacyEditorPluginAdapter` remains the sole concrete PyQt payload bridge. This phase must not create another Host, registry, event bus, widget DSL, renderer, UI framework, app shell, composition root, or peer engine root.

## Previous Gate

E57 closed the official author path: all community samples directly use `IRuntimePlugin`, Dock/Viewport shell facts are declarative and Host-copied, PyQt payload imports are lazy, and USER_GUIDE theme authoring uses `theme_profile`. Evidence includes final author/sample `9 passed in 0.81s`, signature-only `2 passed in 0.29s`, prior full non-signature `1640 passed, 50 skipped, 34 subtests passed in 161.41s`, compile, four guardrails, and standard/eager Editor smokes (`13/20`, `20/20`).

## Audited current truth

- `core.VitaLoom.kernel.plugin_interfaces` continues to export `IEditorPlugin`, `IDockProvider`, `IViewportProvider`, `IThemeProvider`, `IEntityTypeProvider`, and `IComponentTypeProvider`. The first four are legacy UI compatibility interfaces over the Qt-free runtime contract; entity/component remain intentional multiple-inheritance adapters and must not be flattened.
- `LegacyEditorPluginAdapter` uses structural, local compatibility fallbacks rather than obsolete type gates: pre-declarative Dock requires callable `create_dock_widget()` + `get_dock_config()`; Viewport requires callable `create_viewport_widget()` + `get_viewport_id()`; Theme requires callable `get_theme_name()` + `get_stylesheet()` when a `theme_profile` is absent. Built-in authority is declarative, not these types.
- The current public interface docstrings are incomplete/generic and do not state the exact supported fallback payloads, preferred replacement contracts, or lifecycle/ownership limits. Some troubleshooting docs still describe legacy provider methods as a normal authoring requirement.
- Existing tests prove inheritance compatibility and broad Adapter behavior, but must explicitly prove that public legacy imports remain Qt-free and that structural fallback continues without `isinstance(..., legacy_interface)` authority.

## Tasks

### Task 1 -- Publish precise compatibility contract

1. Upgrade `plugin_interfaces.py` module/class/method documentation to name the public compatibility guarantee, non-authoritative status, exact legacy payload shape, preferred direct `IRuntimePlugin` replacement, and Adapter/lifecycle ownership boundary.
2. Add a focused author/deprecation guide and correct stale troubleshooting text so official new-author instructions never prescribe legacy UI inheritance while still documenting how existing plugins remain supported.
3. Do not add runtime warnings, remove imports, alter abstract method signatures, or change `IEntityTypeProvider` / `IComponentTypeProvider` inheritance.

### Task 2 -- Prove bounded compatibility behavior

1. Add tests that import public legacy interfaces with PyQt6 blocked and verify exact inheritance/abstract surface stability.
2. Add narrow Adapter tests demonstrating a legacy-shaped plugin projects through structural fallback without subclass/type-gate dependence, and that declarative contributions remain preferred when present.
3. Preserve existing loading, activation context, unload/reload, `.pond`, Project World, Inspector command binding, SR2D, SR/PS, Player/export, package/signature behavior.

### Task 3 -- Verification and closure

1. Run changed-file compileall, focused interface/Adapter/community/contribution/loader compatibility tests, and targeted stale-author-doc scans.
2. Run relevant guardrails and an appropriate Editor smoke if Adapter behavior changes; run complete non-signature regression before claiming E58 complete.
3. Update this plan, a fresh-session prompt, `docs/mainline_status.md`, `CONTEXT.md`, contributor docs, and `docs/INDEX.md`; name exactly one next Gate after a fresh audit.

## Completion boundary

E58 may clarify, prove, and preserve the bounded public legacy compatibility surface only. It must not migrate to a new UI host, remove supported legacy imports, broaden fallback into new runtime authority, change Project World or `.pond` semantics, alter Inspector command binding, SR2D/SR/PS, Player/export, package/signature authority, native/OpenGL scope, or claim engine/editor completion.
## Completion record (2026-07-30)

### Delivered

- Published the bounded public compatibility contract in
  `core.VitaLoom.kernel.plugin_interfaces`: imports remain Qt-free; public
  legacy names, abstract methods, and the entity/component dual-adapter MRO are
  explicitly retained; the new authoring authority remains direct
  `IRuntimePlugin` plus copied `editor_contributions`.
- Added `docs/guides/LEGACY_PLUGIN_INTERFACE_COMPATIBILITY.md` and corrected
  troubleshooting guidance so declarative `dock_surface`, `viewport_surface`,
  and `theme_profile` are the new author path while legacy factories remain
  Adapter-local fallback payloads.
- Added regression proof for Qt-free public-interface import, stable abstract
  surface/MRO, authoring guidance, and structural Dock/Viewport/Theme fallback
  from an `IRuntimePlugin` that does not subclass the legacy provider types.
  The test also proves that `get_viewport_name()` remains public interface
  surface but is not a structural fallback gate.

### Evidence

- Syntax compilation with `compile(..., 'exec')` passed for the changed runtime
  interface and focused test modules. `compileall` could not replace an existing
  locked `__pycache__` output (`WinError 5`), so no bytecode-write claim is made.
- `python -m pytest -q --basetemp .pytest-e58-core6 tests/test_runtime_plugin_contract.py tests/test_legacy_editor_plugin_adapter.py tests/test_community_example_migration.py`
  -> `26 passed in 0.96s`.
- `python -m pytest -q --basetemp .pytest-e58-signature2 tests/test_package_signature_warn_only.py`
  -> `2 passed in 0.16s`.
- `check_project_plugin_model.py`, `check_core_boundaries.py`,
  `check_gui_boundaries.py`, and `check_release_consistency.py` all report OK.

### Environment-limited checks and unblock path

- The current interpreter is `D:\app\anaconda3\python.exe` (Python 3.13) and
  has no installed `PyQt6`. A fresh full non-signature run stops during
  collection with 48 `ModuleNotFoundError: PyQt6` errors; real standard/eager
  Editor smokes cannot be executed in this environment. These are dependency
  collection failures, not failures of the E58 focused contract tests.
- Fallback proof is the headless focused suite above; the Adapter test isolates
  its stylesheet composition behind a test double and never changes product
  runtime behavior.
- Unblock by using an approved isolated project environment with the locked
  PyQt6 dependency installed, then rerun the complete non-signature suite and
  standard/eager Editor smokes. The attempt to install an unpinned package into
  the shared Anaconda interpreter was not permitted and was not retried.

## Unique next Gate

E59 -- Reproducible Qt Validation Environment and Legacy Adapter Full Regression:
provision or select an approved isolated Qt-capable environment, run the full
non-signature regression plus standard/eager Editor smoke evidence, and record
only the validation result. Do not change plugin authority, introduce a new UI
Host, or claim native/OpenGL/default-ready or whole-engine completion.
## Superseding validation update (2026-07-30)

An approved project-local isolated environment was found at `.venv\python.exe`
(Python 3.11.15, PyQt6 6.11.0). It supersedes the shared-Anaconda UI limitation
for this phase:

- `.venv\python.exe -m pytest -q --ignore=tests/test_package_signature_warn_only.py --basetemp .pytest-e58-full-qtenv`
  -> `1661 passed, 34 skipped, 34 subtests passed in 190.02s`.
- Standard and eager offscreen Editor smokes pass with `plugins=13/20` and
  `plugins=20/20`, respectively.
- The four guardrails pass in the isolated environment. The package-signature
  test remains independently proven in the shared Anaconda environment
  (`2 passed in 0.27s`); the isolated Qt environment lacks `cryptography`, so it
  cannot independently collect that signature-only test.

The temporary shared-Anaconda PyQt6 collection limitation remains recorded as an
interpreter-specific observation, but is no longer a blocker for E58 closure.

## Superseding unique next Gate

E59 -- Legacy UI Interface Authority Call-Site Audit and Non-Adapter Quarantine
Enforcement: audit all runtime use of `IEditorPlugin`, `IDockProvider`,
`IViewportProvider`, and `IThemeProvider`; prove no non-Adapter type gate or
new-author authority survives, add narrowly scoped regression guards if needed,
and preserve public imports and entity/component MRO.