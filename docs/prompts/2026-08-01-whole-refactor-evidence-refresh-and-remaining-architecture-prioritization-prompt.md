# E204 Fresh-Session Prompt -- Whole-Refactor Evidence Refresh and Remaining-Architecture Prioritization Gate

E204 is complete. After installing the missing `cryptography` test dependency into the existing project `.venv`, the first full run exposed a real 1,000-asset cold-index performance failure (`15.192s > 10.0s`). `_inventory()` now preserves its cache/order semantics while hashing multiple cache misses through bounded ordered workers. The focused scale regression and the fresh full suite pass: `2058 passed, 34 skipped, 50 subtests passed in 231.70s`.

All current project/plugin, release, core, GUI, audit, SR2D/native-status, replay, WorldBridge, component-projection, and mapping-audit guards pass. This proves covered contracts, not final completion: `schema_version` remains `4`, `unified_undo_redo_runtime=false`, WorldBridge remains non-lossless/non-default-ready, and neither native nor OpenGL default readiness is proven.

The one next gate is E205: evaluate and, only if evidence supports it, implement a bounded WorldBridge kinematic mapping contract for the documented `velocity_acceleration` loss. Preserve the versioned runtime, dual/pilot boundary, `.pond`, Registry/Inspector/SR2D seams, and all remaining loss declarations. Do not merge ticks, invoke component behavior, or claim lossless/default-ready status.
