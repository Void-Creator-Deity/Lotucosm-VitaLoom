# Phase E99 -- Editor Launcher Project-Path Canonicalization and Type Boundary Audit

Date: 2026-07-31
Status: complete

## Previous gate

E98 consumed a successfully opened explicit project at the existing Kernel boundary and retained a failed request for retry. Launcher still passes an absolute explicit path through `set_startup_project()` without mutating process environment.

## Objective

Audit public `launch_editor(..., project_path=...)` input acceptance and canonicalization for strings, PathLike values, empty/relative paths, and unsupported values. Correct only a proven boundary defect; leave descriptor validation, project opening, fallback, and recovery with Kernel/Project World.

## Required evidence

1. Map callers, annotation, and exact normalization timing.
2. Prove values delivered to `set_startup_project()` for supported inputs with no environment mutation.
3. Prove unsupported-input error timing/identity or correct a real contract defect.
4. Preserve E95 error/splash behavior, singular Kernel/Host/registry authority, and all project/plugin contracts.
5. Run focused tests, adjacency, smoke, guardrails, source hygiene, signatures, and record one next gate.

## Explicit non-goals

Do not move project validation or lifecycle into Launcher; do not add a Host, registry, event bus, fallback Kernel, recovery owner, shell, renderer, or global environment flag. QPainter remains default; OpenGL/native is not default-ready; do not claim whole-refactor completion.

## Audit result and evidence

- Caller map: the production runtime entry point in `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/main.py` supplies `str(resource_root())` and `_parse_cli_project_path()` supplies an absolute string or `None`. The public launcher annotation previously advertised `Optional[str]`, while the `os.path.abspath()` implementation happened to accept some `PathLike` values.
- Defect reproduced: unsupported values were not rejected until after splash display and Kernel construction. A bytes-returning `PathLike` was passed through as bytes despite the Kernel's string contract. New boundary tests were red: `3 failed in 0.41s`.
- Narrow correction: `editor_launcher.py` now declares `project_path: str | os.PathLike[str] | None`, normalizes it with a private Launcher-only helper before importing or starting lifecycle participants, treats `None` and `""` as no explicit request, accepts string-returning `PathLike`, and raises a direct `TypeError` for unsupported or bytes-returning values. Errors raised by `__fspath__()` preserve their original object identity. Launcher still only calls `kernel.set_startup_project()` with an absolute string; it does not inspect `project.json`, open a project, choose fallback, mutate `VITALOOM_SKIP_AUTO_OPEN`, or own Project World recovery.
- Deterministic tests prove relative-string and relative-`PathLike` canonicalization, no-request handling for `None`/empty string, rejection before splash/Kernel side effects, and exact propagation of a `PathLike` normalization error. Green focused boundary proof: `6 passed in 0.24s`; full launcher/registry interface file: `30 passed in 0.63s`; adjacent offscreen lifecycle set: `141 passed in 2.99s`.
- Root editor smoke passed: `Editor smoke OK: suite=lotucosm.vitaloom.suite product=lotucosm-vitaloom@1.0.0 plugins=13/20`. Project-plugin, core, GUI, and release guardrails all passed. Independent Anaconda signature proof: `2 passed in 0.17s`. Scoped UTF-8-sig compilation, CRLF checks, trailing-whitespace checks, and `git diff --check` passed for the production/test paths. `.venv` still lacks `cryptography`; no dependency was installed. E68 (`1678 passed, 34 skipped, 34 subtests`) remains historical only. QPainter remains default; OpenGL/native is not default-ready; whole refactor is not claimed complete.

## Next gate

Exactly one next gate: **E100 -- Editor Launcher Repository-Root Plugin-Layer Boundary Audit**. Audit the public `repo_root` argument and `default_plugin_layers()` handoff for explicit type/canonicalization and authority semantics, without moving plugin discovery, layer ownership, or recovery into Launcher.