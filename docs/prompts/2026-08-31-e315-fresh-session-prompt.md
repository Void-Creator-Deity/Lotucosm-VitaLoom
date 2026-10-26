# E314 fresh-session prompt

继续 VitaLoom 重构主线。E313 已证明隔离 replay witness 与真实 dual-lane capture seam；E314 已新增 Qt-free、opt-in/quarantine-only 的 `world_bridge_shared_state_transport.py`，将 input events、pause/reset epoch、SR/PS clock provenance、caller-owned RNG snapshot、bridge identity links 放入 digest-sealed versioned envelope，并通过 5 个 focused tests、CLI、CI/release 接入。

下一门只做 E315：把该 envelope 接到真实 `unified_pond_step_with_trace()` capture seam，实现 receiver-side sequence/epoch continuity、partial-failure rollback/fallback、fresh-instance parity evidence。禁止修改 `Pond.update` 签名或直接开放默认 live adapter。保持 `shared_live_state_restore=false`、`full_unified_replay_admitted=false`、`cross_lane_replay=false`、`lossless=false`、`default_ready=false`、`live_adapter_admitted=false`、`unified_undo_redo_runtime=false`。不修改 `.pond`、`.venv`、`uv.lock`，不运行 uv/Conda 包管理器，不切换解释器，不 stage/commit/reset/clean 无关内容。完成后更新 `docs/mainline_status.md`，并只指定一个下一 gate。
