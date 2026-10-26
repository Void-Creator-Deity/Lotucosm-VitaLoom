# E202 Fresh-Session Prompt -- Latent SceneManager Save-As Failure-Atomicity and Quarantine Gate

E202 is complete. Public legacy `SceneManager.save_scene_as(scene_path)` is now failure-atomic: it creates a detached candidate with a target-derived name, persists through the existing shared scene-save adapter, and changes the current path only after success. Failed persistence leaves legacy data/name/path/editor-context reference/modified state and signals untouched. The helper is still runtime-unreferenced and excluded from Registry history and command audit; schema v4 and `unified_undo_redo_runtime=false` remain required.

The one next gate is E203: inventory any cross-runtime, package, or extension-layer references to the two public legacy SceneManager save seams before promoting or migrating either one. Do not infer user intent from a raw persistence call; classify provenance, writer/host ordering, and history/audit eligibility first.
