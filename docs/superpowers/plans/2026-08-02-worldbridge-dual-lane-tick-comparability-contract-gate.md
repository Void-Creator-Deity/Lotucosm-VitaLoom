# E215 WorldBridge Dual-Lane Tick Comparability Contract Gate

Date: 2026-08-02
Status: complete

## Previous gate

E214 established that SR and PS do not share clock, input, checkpoint, or replay authority. The current bridge runs only after SR phases and calls a PS fixed-step update without consuming SR delta, so a tick merge remains prohibited.

## Objective

Define and prove a read-only, deterministic dual-lane comparability trace contract. The trace must make each lane's clock, phase boundary, bridge hand-off, and observable checkpoint explicit so future admission work can compare behavior without pretending that the runtimes are already unified.

## Required work

1. Inventory existing comparability runner and observation/snapshot APIs for reusable, Qt-free seams.
2. Define a compact trace schema with separate SR and PS clock values, an explicit bridge boundary, stable entity identifiers, and declared loss labels.
3. Add deterministic trace construction and regressions that reject any trace claiming shared clocks, lossless mapping, or replay admission.
4. Run focused comparability/WorldBridge checks and the widest practical baseline; record exact evidence, fallback, unblock path, and exactly one next gate.

## Non-goals

No tick merge, no scheduler rewrite, no default runtime change, no scene/Pond checkpoint migration, no claim of replay determinism, and no removal of mapping-loss labels.

## Decision

E215 admits only a Qt-free diagnostic packaging contract. `build_worldbridge_dual_lane_trace(...)` records SR and PS as separate clock domains (`sr_scaled_scene_seconds` and `ps_pond_unit_ticks`), sorts bridge-pair links by stable identifiers, copy-isolates JSON checkpoints, preserves all six mapping-loss labels, and seals the payload with a deterministic SHA-256 digest. The link relation is explicitly `bridge_pair_not_identity_equivalence`.

Validation rejects any trace that claims a shared clock, identity equivalence, lossless mapping, replay admission, or default readiness. The pre-existing comparability runner is identified accurately as `ps_batch_vs_ps_unified_bridge_adapter_not_live_sr_ps_trace`; E215 therefore does not present that runner as live cross-lane evidence.

## Evidence

- Added the Qt-free contract in `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_dual_lane_trace.py`, the guard `tools/check_worldbridge_dual_lane_trace.py`, and regression coverage in `tests/test_worldbridge_dual_lane_trace.py`.
- Nested the contract under `dual_lane_trace_contract` in `runtime_worldbridge_status.py` without changing runtime mode or project defaults.
- Focused WorldBridge/comparability/observation coverage passed **`66 passed, 5 subtests passed in 1.90s`**.
- `check_worldbridge_dual_lane_trace.py`, `check_worldbridge_tick_replay_admission.py`, and `check_runtime_worldbridge_status.py` passed and retained `tick_merge_admitted=false`, `replay_admitted=false`, `default_ready=false`, and runtime mode `dual`.
- Explicit temporary-artifact compilation passed for all three changed Python implementation/tool files.
- Full offscreen regression under repository `.venv\python.exe` passed **`2096 passed, 34 skipped, 55 subtests passed in 223.10s (0:03:43)`**.
- `git diff --check` exited successfully; output contained only pre-existing LF-to-CRLF conversion warnings.

## Fallback and unblock

Retain the dual runtime and treat this schema as read-only diagnostic packaging, not as a common checkpoint or replay record. If a live producer cannot observe both authorities without importing Qt or inventing atomicity, it must expose that limitation explicitly and keep trace production opt-in. Unblocking stronger claims requires a producer anchored to existing Qt-free SR snapshot/observation and PS Pond snapshot authorities, stable bridge-pair identity, deterministic capture-order evidence, and regressions proving that no UI host becomes engine authority.

## Exactly one next gate

**E216 -- WorldBridge Live Dual-Lane Checkpoint Trace Producer Adapter Gate**.

