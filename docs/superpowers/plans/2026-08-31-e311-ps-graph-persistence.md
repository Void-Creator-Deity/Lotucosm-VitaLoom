# E311 — PS component graph persistence round-trip

## 目标

将 PS `Component.connections` 的有序有向边纳入两套现有 organism serializer 的持久化契约，并保持旧 `.pond`/旧 organism payload 缺少该字段时可加载。

## 交付

- `Organism.replace_component_connections()` 校验边 payload、组件 ID 与恢复顺序，并通过 `Component.add_connection()` 建边。
- `PondSerializer` 与 `OrganismSerializer` 写出 `component_connections`：稳定 `source_id`、`target_id` 与局部 `order`，不保存 live object 引用。
- 两套 organism serializer 都改用 `ComponentFactory` 恢复组件，覆盖 `CiliaActuator`、`ReproductionActuator` 等注册类型，并保留未知类型回退行为。
- 新增 `tests/test_e311_component_graph_persistence.py`，覆盖两种 organism round-trip、具体组件类型恢复、旧字段兼容、无效边拒绝与 restored object identity。
- graph corpus 现在真实执行两套 serializer round-trip，并报告 `graph_persistence_round_trip=true`；`cross_lane_replay=false` 仍保持。

## 证据

```text
E311 focused: 24 passed in 0.88s
PS graph corpus: graph_persistence_round_trip=true, legacy_missing_field_compatible=true
admission verifier: all_fields_blocked=true, live_adapter_admitted=false
static boundary: valid=true
```

## 边界

本阶段没有实现 WorldBridge live adapter；没有把本地 graph persistence 当作 SR/PS shared authority 或 replay 证据；保持 `lossless=false`、`default_ready=false`、`live_adapter_admitted=false`、`unified_undo_redo_runtime=false`、`cross_lane_replay=false`。没有修改 `.pond`、`.venv`、`uv.lock`，没有运行包管理器，也没有 stage/commit/reset/clean。

## 下一门

**E312 — 为 membrane/component graph 的 authority 与 shared checkpoint/replay 建立跨 lane 证据；在 replay gate 未关闭前继续阻断 live adapter。**

