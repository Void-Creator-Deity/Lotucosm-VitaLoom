# E194 Fresh-Session Prompt -- Project Active Scene Canonical-Only and Terminal-Rejection Authority Repair Gate

Status: complete on 2026-08-01.

E194 separated active-scene manifest authority from host loading. `project.set_active_scene` is canonical-only and ignores legacy load context; `ProjectPanel` explicitly calls `scene.open` only after manifest success. Focused evidence proves no host/fallback side effects on canonical success or rejection. Evidence: focused `20 passed in 1.69s`; wider `60 passed, 10 subtests passed in 4.54s`; audit/core/GUI checks passed with schema v4 and `unified_undo_redo_runtime=false`.

Next is E195: audit whether guarded history can remain manifest-only without generic history rehydration accidentally dispatching a host `scene.open`. Do not add undo merely because E194 completed.
