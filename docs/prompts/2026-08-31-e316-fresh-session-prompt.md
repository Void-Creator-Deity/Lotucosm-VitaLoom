# E316 fresh-session prompt

继续 VitaLoom 重构主线。E315 已将 E314 digest-sealed shared-state envelope 接入真实 `unified_pond_step_with_trace()` capture seam，并完成 receiver sequence continuity、digest tamper rejection、quarantine fallback 与 rejected-input state preservation 证据。E315 focused 为 6 passed，CLI `protocol_valid=true`，且已接入 runtime status、CI、release consistency。

下一门只做 E316：设计并实现真实跨 lane checkpoint/restore 与 rollback 证据。先审计现有 E313/E314/E315 seam 和已有 checkpoint feasibility contract，明确 restore 前后的 SR/PS state boundary、input cursor、clock、RNG context、lifecycle epoch、failure atomicity；只建设隔离/opt-in/quarantine witness，不修改 `Pond.update`/`unified_pond_step` 签名，不开放默认 live adapter，不把 receiver copy 当作 live restore。

必须保持：`shared_live_state_restore=false`、`full_unified_replay_admitted=false`、`cross_lane_replay=false`、`lossless=false`、`default_ready=false`、`live_adapter_admitted=false`、`unified_undo_redo_runtime=false`。不修改 `.pond`、`.venv`、`uv.lock`，不运行 uv/Conda 包管理器，不切换解释器，不 stage/commit/reset/clean 无关内容。完成后更新 `docs/mainline_status.md`、本阶段 plan，并只指定一个下一 gate。
