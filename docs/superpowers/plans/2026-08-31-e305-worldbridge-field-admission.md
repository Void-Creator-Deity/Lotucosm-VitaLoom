# E305 — WorldBridge field-level mapping admission matrix

## 目标

基于 E300–E304 证据，为所有 WorldBridge mapping 字段建立明确的 authority、方向、当前状态和 live adapter 准入前置条件。

## 结果

- `world_bridge_field_admission.py` 提供只读矩阵。
- `check_worldbridge_field_admission.py` 提供可执行一致性检查。
- 所有字段当前 `live_adapter_admitted=false`；没有把 descriptor/projection 伪装成 live mapping。

## 下一门

E306：执行 admission blocker verifier。
