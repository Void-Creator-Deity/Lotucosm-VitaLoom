# E293 — Simulation Mutation Owner API Convergence

## 目标

审计 PS simulation systems 的直接状态写入，区分 integrator 对自身局部临时向量的计算与对实体/组件 owner state 的实际 mutation；只收敛后者。

## 分类

- `inheritance_simulation.py` 的 position 赋值位于 pygame legacy demo 的点击/热键入口；产品 launcher 指向另一个 `lotucosm.simulator.inheritance_simulation` 模块，因此此文件不是当前 product runtime handoff。保留兼容代码，不在本阶段把旧 demo 当 engine authority 扩张。
- `physics_engine.py` 是注册 PS body 的外部 simulation system，之前直接替换或原地写入 EntityBase motion 字段，属于真实跨-owner mutation。
- `floating_system.py` 对 ComponentBase（继承 EntityBase）的漂浮积分与边界碰撞同样直接写入 owner motion state，属于真实跨-owner mutation。
- food-particle dict 是 FloatingSystem 私有数据模型，不属于 EntityBase/ComponentBase authority，保留其内部 dict mutation。

## 实施

- PhysicsEngine 以 detached/validated motion snapshots 计算力、积分、限速和边界反弹，并通过 `set_position`、`set_velocity`、`set_acceleration` 写回；legacy double 才走明确 fallback。
- FloatingSystem 对 component motion 做相同收敛；漂浮 velocity/acceleration 的缺字段初始化也优先走 owner API。
- 不改变 simulation lifecycle/CommandRegistry 边界；`unified_undo_redo_runtime=false` 维持不变。

## 证据

```text
.venv\\python.exe -m pytest tests/test_physics_engine_owner_api.py tests/test_floating_system_owner_api.py tests/test_component_state_hydration_authority.py tests/test_pvaec_tick_physics_chain.py tests/test_pond_serializer_roundtrip.py tests/test_legacy_p2_persistence.py -q --basetemp .pytest-e293-focused2
=> 28 passed in 1.71s
```

新增证据覆盖 physics force/integration/boundary owner API、floating component motion/boundary owner API、malformed motion 无半更新。

```text
tools/check_core_boundaries.py => core boundaries OK
tools/check_gui_boundaries.py => GUI boundaries OK
tools/check_project_plugin_model.py => project plugin model OK
tools/check_release_consistency.py => release consistency OK
```

## 下一步

E294 对 PS/SR state ownership 做一次静态 inventory，明确剩余直接字段写入各自属于 constructor、owner internals、legacy demo、private dict model 还是待修复的跨-owner mutation；以 inventory 结果决定是否需要最后一轮实现。
