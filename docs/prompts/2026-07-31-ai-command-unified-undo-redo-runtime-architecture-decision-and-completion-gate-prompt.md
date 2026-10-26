# Fresh-session handoff: E167 complete

E167 is complete. It selected Path A and delivered the first coherent Qt-free semantic-history vertical slice without claiming a completed global migration.

`CommandRegistry` remains the semantic history authority for supported project mutations. `entity.set_property` now has JSON-safe durable undo/redo via a full entity snapshot and the internal `entity.restore_snapshot` inverse command. Supported generic Inspector entity properties route through the registry before the legacy `CommandStack`; after semantic mutation and global undo/redo, the Qt-host adapter re-opens the returned scene path so the current `SceneManager` rehydrates from canonical `.pond` state.

Evidence: changed modules compile; focused history regressions passed `24 passed in 2.50s`; wider AI-command plus UI-action coverage passed `39 passed in 9.94s`; the AI-command audit, core-boundary, GUI-boundary, and `git diff --check` checks passed. The audit explicitly remains `unified_undo_redo_runtime=false`: SceneViewport node/connection editing and other legacy slices still own local `CommandStack` paths.

Continue only with E168 -- SceneViewport Node/Connection Semantic Command-History Migration and Global Undo/Redo Interaction Proof. Keep the versioned runtime boundary and Qt-free FrameCore L0 intact. Preserve `.pond`, command registry, Inspector binding, SR2D and manifest seams; retain QPainter as default; do not use this work to claim native/OpenGL/WorldBridge readiness. Do not stage, commit, reset, restore, clean, delete, or otherwise disturb unrelated dirty work.
