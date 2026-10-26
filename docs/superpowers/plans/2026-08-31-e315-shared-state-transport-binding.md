# E315 — shared state transport binding（完成，2026-08-31）

## 本轮目标

把 E314 的 Qt-free、opt-in/quarantine-only envelope 接到真实 E313 `unified_pond_step_with_trace()` capture seam，验证 receiver 连续性、篡改拒绝、部分失败后的状态保持与 fallback；不开放默认 live adapter 或跨 lane replay。

## 已交付

- 新增 `core/Lotucosm/runtime/world_bridge_e315_shared_state_transport_binding.py` 与对应 CLI/test。
- 两次真实 E313 capture 被映射为 sequence 0/1 envelope，并由 `WorldBridgeSharedStateReceiver` 接收。
- receiver 强制 sequence 从 0 开始连续递增，阻断 sequence gap、capture epoch 回退与 pause/reset epoch 回退；拒绝路径不改变已接受状态。
- 增加 `state_fingerprint()` 审计接口，仅用于证明 rollback/failure isolation，不提供 live restore；删去未使用的 event normalization 临时变量。
- E315 binding 已接入 runtime status、CI 与 release consistency。

## 当前证据

```text
E315 focused: 6 passed
protocol_valid=true
real_e313_capture_seam_exercised=true
accepted_count=2
sequence_continuity_enforced=true
digest_mismatch=true
partial_failure_rollback.receiver_state_preserved=true
quarantine.artifact_valid=true
default_ready=false
```

## 边界与未完成

当前只证明真实 capture → sealed envelope → receiver quarantine boundary，不证明 live object restore、shared checkpoint apply、RNG restore、lossless mapping 或默认 adapter readiness。`bridge_identity_links` 在 E313 的 identity relation 被明确转换为 transport 的 `observation_link`，不能解释为 object identity。保持：

```text
shared_live_state_restore=false
full_unified_replay_admitted=false
cross_lane_replay=false
lossless=false
default_ready=false
live_adapter_admitted=false
unified_undo_redo_runtime=false
```

未修改 `.pond`、`.venv`、`uv.lock`，未运行包管理器，未切换解释器，未 stage/commit/reset/clean 无关内容。

## Exactly one next gate

**E316 — 设计真实跨 lane checkpoint/restore 与 rollback 证据；继续保持 opt-in/quarantine，不接管默认 runtime。**
