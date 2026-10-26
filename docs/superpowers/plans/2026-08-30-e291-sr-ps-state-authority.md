# E291 — SR/PS Runtime State Authority 收敛

## 目标

在不改变 `.pond` 语义、SR2D public seams 或 `unified_undo_redo_runtime=false` 的前提下，将真实 SR runtime entity 的桥接写入统一经由 owner API；仅对明确的 legacy/simple double 保留字段写入回退。

## 实施

- 为 `GameViewport._SceneRuntimeEntity` 增加 position、velocity、acceleration、motion snapshot、radius/size、energy、generation owner API。
- owner API 对数值做有限性、半径正值、generation 非负校验；motion state 先完整校验再写入，避免半更新。
- `world_bridge` 的位置、向量、energy、health、size/radius 写入优先调用 owner API，兼容对象才使用旧字段回退。
- SR spawn hydration 改用 energy/generation owner API。

## 证据

```text
.venv\\python.exe -m pytest tests/test_game_viewport_sr_runtime_snapshot_authority.py tests/test_worldbridge_motion_authority.py tests/test_worldbridge_kinematic_mapping_contract.py tests/test_plasticity_and_world_bridge.py tests/test_game_viewport_unified_bridge.py -q --basetemp .pytest-e291-focused2
=> 36 passed in 1.86s
```

## 下一步

继续审计其它 spawn/hydration/simulation 路径，区分构造初始化、持久化恢复、simulation authority 与 UI projection；下一门优先检查 `organism_serializer.py` 与 `pond_serializer.py` 的恢复边界。
