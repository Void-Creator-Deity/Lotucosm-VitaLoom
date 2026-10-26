# Phase E100 -- Editor Launcher Repository-Root Plugin-Layer Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E99 made `launch_editor(..., project_path=...)` an explicit public boundary: string and string-returning `PathLike` inputs become absolute strings before any splash or Kernel side effect; invalid/bytes path forms fail directly; no project descriptor or lifecycle authority moved from Kernel/Project World.

## Objective

Audit `launch_editor(..., repo_root=...)` and `default_plugin_layers(repo_root)` for their actual public type, canonicalization, and plugin-layer handoff contract. Establish whether the apparently unused `_repo_root` parameter is deliberate product-boundary behavior or a real misleading/unsafe boundary defect, then make only the smallest correction proven necessary.

## Required evidence

1. Map every production/test caller and the source of the effective plugin-layer paths.
2. Prove supported `str` and `PathLike` repo-root inputs' exact handoff or intentionally documented non-use.
3. Prove invalid-input timing, error identity, and splash/Kernel/plugin-loader side-effect boundaries, or correct a real defect at Launcher only.
4. Preserve the singular nested Plugin Host, runtime bundle-path authority, plugin discovery/loading semantics, capability registry, Project World authority, E95 splash behavior, and E96 environment neutrality.
5. Run deterministic focused tests, adjacency, smoke, four guardrails, scoped source hygiene, independent signature proof, and document exactly one next gate.

## Explicit non-goals

Do not make Launcher discover plugins, construct another Plugin Host/registry/event bus/Kernel, synthesize layer directories, move bundle-path policy out of core, add recovery/fallback ownership, change manifests/public imports/MRO, or alter `.pond`, AI-command, Inspector, SR2D, renderer, Player, or application-shell semantics. QPainter remains default; OpenGL/native acceleration is not default-ready; do not claim whole-refactor completion.
## Audit result and evidence

- Caller and authority map: product `runtime/main.py` passes `str(resource_root())` to `launch_editor()`. Launcher hands the value only to `default_plugin_layers()`. The default resolver deliberately ignores its `_repo_root` parameter and delegates to `core.bundle_paths.default_plugin_layer_dirs()`, whose `application_root()`/`resource_root()` determine official and user layer directories. Existing `tests/test_bundle_paths.py` proves that intentional non-use. Launcher therefore remains outside plugin directory policy and discovery authority.
- Defect reproduced: the public `repo_root: str` annotation did not state the effective `PathLike` acceptance, relative `str`/`PathLike` values reached a custom resolver without canonicalization, and invalid or bytes-returning values were not rejected until after splash/Kernel startup work. New deterministic boundary cases were red: `4 failed, 30 deselected in 0.40s`.
- Narrow correction: `launch_editor(..., repo_root=...)` now declares `str | os.PathLike[str]`, canonicalizes supported values to an absolute text path before dynamic core imports, splash display, Kernel construction, or layer resolution, and directly rejects unsupported or bytes-returning forms with `TypeError`. A `PathLike.__fspath__()` exception still propagates as the same object. The shared private helper also keeps E99 `project_path` behavior unchanged: `None`/empty string still mean no explicit project request.
- Authority remains unchanged: `default_plugin_layers(normalized_repo_root)` remains the sole Launcher seam; its default implementation deliberately resolves paths through `bundle_paths`, not the supplied repository root. No Launcher-owned layer synthesis, discovery, Host, registry, fallback, recovery, project inspection, or environment mutation was added.
- Evidence: focused red/green proof `4 failed, 30 deselected in 0.40s` -> `4 passed, 30 deselected in 0.28s`; complete interface file `34 passed in 0.60s`; adjacent offscreen lifecycle suite `145 passed in 3.47s`; root editor smoke passed with `suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`; project-plugin, core, GUI, and release guardrails all passed; independent Anaconda signature proof `2 passed in 0.19s`; scoped UTF-8-sig compilation, CRLF/no-bare-LF, trailing-whitespace checks, and `git diff --check` passed for production/test paths. `.venv` still lacks `cryptography`; no dependency was installed. E68 remains historical broad proof only. QPainter remains default; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

Exactly one next gate: **E101 -- Editor Launcher Injected Runtime-Service Boundary Audit**. Audit the public optional `capability_registry` and `event_bus` handoff parameters for validation timing, error identity, and singular runtime-authority preservation, without moving registry/event-bus ownership or lifecycle into Launcher.
