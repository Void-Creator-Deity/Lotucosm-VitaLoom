# E309 — PS component persistence 与生命周期闭环

## 目标

为每个 ComponentFactory 类型建立可执行的本地 persistence round-trip 与 owner lifecycle 证据；不把本地 PS 证据升级为 WorldBridge live authority 或跨 lane replay。

## 交付

- ComponentFactory 注册 `CiliaActuator`、`ReproductionActuator` 等具体实现，并保留 `Actuator`/`TouchSensor` 等旧别名。
- 新增稳定的 `canonical_component_type()`；PondSerializer 与 ComponentSerializer 不再写出无法反解的 `MuscleActuator`。
- `MuscleActuator` 通过 canonical `Actuator` 反序列化回同一 concrete class。
- `Organism.add_component/remove_component` 现在拥有 attach/detach hook，并在 attach 失败时回滚组件图。
- corpus 对 10 个注册类型执行真实短生命周期 owner probe，记录绑定、attach、detach 和事件顺序。
- 每种组件执行真实 `PondSerializer.serialize_component → deserialize_component → restore_persistent_state` round-trip。临时 `organism_id` 明确属于宿主回绑上下文，不作为组件 persistence mismatch。

## 证据

```text
E309 focused corpus + legacy persistence: 19 passed
PS corpus CLI: component_type_count=10, lifecycle_ownership=true
PS corpus CLI: all_round_trip_ok=true, lossy_or_failed_types=[]
admission verifier（含本地 PS persistence/lifecycle evidence）：OK（shared_runtime_replay_gate 仍阻断 live adapter）
static boundary: OK
release consistency: OK
py_compile: OK
```

## 边界

- `read_only=true`、`maps_live_objects=false` 保持。
- `cross_lane_replay=false`、`persistence_authority_admitted=false` 保持。
- 未修改 `.pond`、`.venv`、`uv.lock`；未运行包管理器；未 stage/commit/reset/clean。

## 下一门

**E310 — 补齐字段级 lifecycle/inheritance/persistence 缺口与真实 Membrane/Component graph connection corpus；继续保持 live adapter blocked。**
