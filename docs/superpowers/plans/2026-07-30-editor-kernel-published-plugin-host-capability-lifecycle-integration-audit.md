# Phase E90 -- Editor Kernel Published Plugin-Host Capability Lifecycle Integration Audit

Date: 2026-07-30
Status: complete

## Previous gate

E89 closed Package Manager's direct public `unload_plugin()` calls after Project World disable. The UI now records persisted project state separately from an unsettled current-session unload, batch unload follows only command successes, and the explicit package-ID branch unloads its persisted runtime ID. Resolver/interface failures remain visible and no second authority was introduced.

The remaining integration boundary to audit is the Editor Kernel's composition-root publication of the recursive public Plugin Host capability. Existing direct UI consumers now use the published Interface; confirm publishing, replacement, and teardown cannot leak stale Host authority or hide lifecycle errors through the legacy adapter.

## Objective

Audit the Editor Kernel's publication and lifecycle ownership for `PLUGIN_HOST_CONTROL_OBSERVATION`, including registration timing, replacement safety, teardown/unpublication, and legacy `PluginLoader` compatibility seams. Correct only demonstrated integration-boundary defects while keeping the Qt-free L0-L4 contracts and one Host authority intact.

## Required evidence

1. Map capability publication, resolution, replacement, and teardown paths from Editor Kernel through `NestedPluginHost` / `PluginLoader`.
2. Reproduce any stale-publication, duplicate-publication, or teardown failure with public-capability tests; keep resolver/interface errors explicit.
3. Prove normal editor lifecycle, command registry, Project World, and legacy adapter behavior remain unchanged.
4. Run focused/adjacent offscreen tests, source compilation/whitespace, guardrails, root smoke, and independent signature proof.
5. Record evidence, skips/blockers/unblock facts, E68 broad-proof limits, QPainter/OpenGL truth, and exactly one next gate.

## Explicit non-goals

Do not change `.pond`, package manifests, Project World command ownership, Inspector binding, SR2D, SR/PS, Player/export, public imports, or MRO. Do not add a Host, registry, event bus, cache, serializer, renderer, UI framework, or app shell. QPainter remains default; OpenGL/native is not default-ready; do not claim whole-refactor completion.

## Delivery and evidence

- E90 mapped the single composition path: `EditorKernel` constructs the legacy `PluginLoader`, publishes that loader's exact `NestedPluginHost` through `PLUGIN_HOST_CONTROL_OBSERVATION`, then acquires and publishes the Project World Host. All public UI consumers resolve the published capability; they do not read `kernel.plugin_loader` or Host-private state.
- The E13 lease contract is intentionally last-writer-wins plus exact-object unpublication, not an owner/predecessor stack. A Kernel rollback removes only the exact Host it published, preserves a later replacement, and deliberately does not resurrect a value that the Kernel had replaced before initialization. This avoids allowing an old lease to overwrite any later Registry authority.
- No production correction was warranted. Added EditorKernel integration proofs that the published capability resolves to the exact `NestedPluginHost`, initialization failure exact-unpublishes without restoring a predecessor, and a thrown publication release keeps the exact lease and Host publication for a deterministic retry.
- Evidence: focused E90 `6 passed in 0.59s`; adjacent capability/Kernel/Project World/Host suite `85 passed in 1.84s`; root offscreen smoke `plugins=13/20`; project-plugin/core/GUI/release guardrails all `OK`; independent signature proof `2 passed in 0.17s` through `D:\app\anaconda3\python.exe`. The source/test/docs scoped compilation and trailing-whitespace checks are recorded with this closure.
- Environment truth: `.venv` still lacks `cryptography`, so the existing Anaconda interpreter supplied only signature proof and no dependency was installed. E68 remains the older broad proof (`1678 passed, 34 skipped, 34 subtests`; regular/eager smokes `13/20`/`20/20`). QPainter remains the default UI renderer; OpenGL/native acceleration is not default-ready; whole-refactor completion is not claimed.

## Next gate

E91 -- Editor Kernel CloseEvent Plugin-Host Capability Release Failure Semantics Audit. Audit the actual Qt close-event boundary: exact capability release failure, user-visible close rejection, retry ordering after a settled plugin shutdown, and preservation of the single Host authority.
