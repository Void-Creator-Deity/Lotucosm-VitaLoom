# E314 — shared state transport contract（进行中，2026-08-31）

## 本轮目标

在不开放 WorldBridge live adapter、默认 unified runtime 或 full replay 的前提下，把跨 lane 证据所需的输入、生命周期 epoch、clock/tick provenance、caller-owned RNG snapshot 与 SR↔PS identity links 收敛进一个 Qt-free、版本化、digest-sealed transport envelope。

## 已交付

- 新增 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/runtime/world_bridge_shared_state_transport.py`。
- envelope 强制包含 `schema_version`、`envelope_id`、`capture_epoch`、单调语义的 `sequence`、严格 input event shape、pause/reset lifecycle epoch、可区分的 SR/PS clock provenance、观察型 bridge identity links、caller-owned RNG snapshot、atomicity/failure/quarantine 状态及禁止准入标志。
- 使用 canonical JSON + SHA-256 digest；构造和复制都进行深拷贝隔离；篡改、非法 JSON、重复 identity/event、clock domain 混淆和 RNG snapshot 不通过时拒绝。
- transport 失败生成 `quarantine` fallback envelope，不抛出 live restore/replay/default-ready 结论；没有修改 `Pond.update`、`unified_pond_step` 或默认运行路径。
- runtime status、CI、release consistency 已接入 E314 transport CLI。
- 新增 `tests/test_worldbridge_shared_state_transport.py` 与 `tools/check_worldbridge_shared_state_transport.py`。

## 当前证据

```text
E314 focused: 5 passed
contract_valid=true
copy_isolated=true
digest_tampering_rejected=true
strict_input_clock_validation=true
quarantine_fallback_explicit=true
```

## 边界与未完成

当前 envelope 仍是 opt-in/quarantine evidence contract，不是生产 live shared state。尚未把真实 `unified_pond_step_with_trace()` 的 capture seam 接入该 envelope，也没有真实 SR/PS checkpoint restore、rollback/parity、RNG restore 或 sequence receiver authority。因此保持：

```text
shared_live_state_restore=false
full_unified_replay_admitted=false
cross_lane_replay=false
lossless=false
default_ready=false
live_adapter_admitted=false
unified_undo_redo_runtime=false
```

此外，`sequence` 当前由 envelope schema 严格承载，但跨调用 receiver 的单调 sequence authority 尚未实现；本阶段不应把字段存在误报为 replay admission。

## Exactly one next gate

**E315 — 将 E314 envelope 接入真实 E313 live capture seam，并实现 receiver-side sequence/epoch continuity、partial-failure rollback/fallback 与 fresh-instance parity evidence；仍不得默认接管生产 runtime。**
