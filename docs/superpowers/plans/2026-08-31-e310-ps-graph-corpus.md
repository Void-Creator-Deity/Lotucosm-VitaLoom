# E310 — PS Membrane/Component graph corpus

## 目标

建立真实 PS `Organism.components`、`Organism.membrane` 与 `Component.connections` 的只读拓扑事实，明确当前 graph persistence 与跨 lane replay 缺口。

## 交付与证据

- 新增 `world_bridge_ps_graph_corpus.py` 与 `check_worldbridge_ps_graph_corpus.py`。
- 通过真实 `ComponentFactory` 创建 Sensor、Actuator、Membrane，并通过真实 `Organism.add_component/set_membrane/connect_tools` 构造短生命周期 probe。
- 记录 owner binding、膜引用、entity-child 关系和有序有向 edge：`e310-sensor -> e310-actuator`。
- 明确 `graph_persistence_round_trip=false`：现有 Pond/Organism serializer 没有持久化 `Component.connections` 的完整顺序与恢复契约。
- 将 graph facts 接入 admission verifier；事实可证明但不会提升为 live adapter 准入。
- CI/release consistency 纳入 graph corpus CLI。

## 证据

```text
E310 graph corpus focused: 3 passed
PS graph corpus CLI: connection_creation=true, ordered_directed_edges=true
admission verifier（含 graph facts）：OK；graph_persistence_round_trip=false 且 shared_runtime_replay_gate 仍阻断
release consistency: OK
```

## 边界

`read_only=true`、`maps_live_objects=false`、`worldbridge_live_authority=false`、`cross_lane_replay=false` 保持；未修改 `.pond`、`.venv`、`uv.lock`，未运行包管理器，未 stage/commit/reset/clean。

## 下一门

**E311 — 为 PS component graph 建立有序边的 persistence round-trip 与兼容恢复契约；在 graph persistence、inheritance 与 shared replay 证据完成前继续阻断 live adapter。**
