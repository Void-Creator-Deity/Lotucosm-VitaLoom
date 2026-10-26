# E313 — bounded cross-lane replay protocol evidence (进行中)

## 本轮目标

在不触碰生产 SR/PS live authority 的前提下，先建立可执行的、Qt-free、版本化 replay protocol witness：输入序列、固定 phase order、caller-owned RNG state、checkpoint digest、controlled restart 与 post-checkpoint trace 比较必须能在 fresh harness instances 上重现。

## 已交付

- `core/Lotucosm/runtime/world_bridge_e313_bounded_replay_corpus.py`：隔离 harness，生成版本化 checkpoint 与 deterministic replay corpus。
- `tools/check_worldbridge_e313_bounded_replay_corpus.py`：CLI 门禁。
- `tests/test_worldbridge_e313_bounded_replay_corpus.py`：checkpoint digest/phase/RNG 篡改拒绝与 controlled restart 测试。
- runtime status、CI、release consistency 已接入该 evidence corpus。

## 当前证据

```text
E313 bounded corpus: 3 passed
protocol_valid=true
input_sequence_monotonic=true
input_cursor_restored=true
random_state_captured=true
tick_order_fixed=true
controlled_restart_reproduced=true
post_checkpoint_trace_equal=true
final_state_equal=true
```

## 重要边界

这一步只证明一个与生产对象隔离的 protocol harness，不能证明真实 `GameViewport`、真实 `Pond`、SR script/component state、bridge identity、native/plugin state 或跨 lane live restore 已实现。保持：

```text
harness_only=true
production_live_adapter_admitted=false
full_unified_replay_admitted=false
cross_lane_replay=false
lossless=false
default_ready=false
live_adapter_admitted=false
unified_undo_redo_runtime=false
```

## 下一门

**E313-B — 将 protocol witness 绑定到真实 SR observation 与 PS Pond capture seam，补齐同一 tick 的输入/clock/RNG provenance；失败时必须产出 quarantine/fallback 证据，仍不得直接开放 live adapter。**
