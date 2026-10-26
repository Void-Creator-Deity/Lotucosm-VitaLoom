# E294 — PS/SR State-Write Static Inventory

## 目标

对产品 runtime 内实体与组件的关键状态写入建立可复查的语义 inventory。审计范围为 `position`、`velocity`、`acceleration`、`energy`、`health`、`radius`、`size`、`generation`、`dead`；目标是找到真实跨-owner bypass，而非以字符串匹配替代架构判断。

## 搜索与覆盖范围

- 以产品 boundary `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` 为根，审计 Python attribute assignment、in-place assignment，以及动态 `setattr`。
- 初次 attribute search 命中 79 项；收敛后保留 68 项。差额包括 PhysicsEngine 碰撞 separation/impulse、GameViewport hydration/spawn、CellSimulationPlugin position 写入的真实路径；另补上 Inspector transient property 的动态 `setattr` 路径。
- 搜索结果不等同于缺陷；以下分类结合 owner 类型、调用入口和 fallback 语义完成。

## 分类结论

| 分类 | 路径 | 结论 |
| --- | --- | --- |
| constructor initialization / owner internal | `core/Lotucosm/entity.py`、`builtin/entity_types/organism.py`、`builtin/systems/food.py`、`builtin/systems/obstacle.py` | EntityBase、Organism、Food、Obstacle 对自己的 state 初始化或生命周期/integrator 更新。不是外部 bypass。 |
| owner internal SR adapter | `core/VitaLoom/viewports/game_viewport.py::_SceneRuntimeEntity`、`core/Lotucosm/sr_physics2d/game_contacts.py` | 内部实体/接触对象的 constructor 与 setter 实现。hydration/spawn 外部写入已改为 owner setters。 |
| persistence/aggregate owner | `core/Lotucosm/pond.py` | Pond 对自身 aggregate size 的加载合并；不写 EntityBase/ComponentBase owner state。 |
| private UI/runtime model | `core/VitaLoom/viewports/scene_viewport.py`、`builtin/editor_extensions/scene_viewport_plugin.py`、`core/VitaLoom/tools/selection_tool.py` | Node / selection-tool 私有 UI state，不是 PS/SR entity authority。 |
| explicit simple-double compatibility fallback | `core/Lotucosm/runtime/world_bridge.py`、`builtin/editor_extensions/cell_simulation_plugin.py` | setter 不存在时才赋值；真实 EntityBase/Organism/_SceneRuntimeEntity 优先调用 owner API。 |
| private bridge/demo model | `builtin/systems/ps_experiment_runner.py`、`builtin/systems/inheritance_simulation.py` | `_BridgeEnt` 是 runner 本地 simple double；后者是非产品 launcher 的 pygame legacy demo。 |
| Inspector transient compatibility | `core/VitaLoom/inspector/transient_property.py` | dict、x/y simple object 与一般 transient property 保留 fallback；所有命名 owner state 及 `position_x/y` 现优先调对应 owner setter，Registry history 不变。 |
| **真实跨-owner bypass（已修复）** | `builtin/systems/physics_engine.py` | `resolve_collision` 原先直接就地改两个对象的 `position`/`velocity`；现在先读取 detached validated snapshots，再通过 `set_position` / `set_velocity`（或明确 legacy fallback）写回。 |
| **真实跨-owner bypass（已修复）** | `core/VitaLoom/viewports/game_viewport.py` | scene hydration 和 SR spawn 的 energy/generation 现在经 `set_energy` / `set_generation` 进入 `_SceneRuntimeEntity`。 |

## 实施

- `PhysicsEngine.check_collision` 与 `resolve_collision` 读取 detached motion snapshot；碰撞分离和冲量均经 `_set_motion_vector` 回写，后者优先 owner API。
- `CellSimulationPlugin.on_create_entity` 对已具备 `set_position` 的 runtime entity 使用 setter；无 setter 的 legacy double 才保持字段回退。
- `_SceneRuntimeEntity` 的 serialized-scene hydration 与 evolution spawn 使用现有 `set_energy` / `set_generation`，统一其有限性/范围不变量。
- Inspector transient property 写入为命名 owner state 增加 setter dispatch；`position_x/y` 同样优先 `set_position`。这保持 `inspector.set_property` 的 CommandRegistry history/guard/inverse 路径，不把 simulation lifecycle 纳入 undo/redo。

## 证据

```text
.venv\python.exe -m pytest \
  tests/test_inspector_transient_property_command.py \
  tests/test_physics_engine_owner_api.py \
  tests/test_worldbridge_motion_authority.py \
  tests/test_worldbridge_kinematic_mapping_contract.py \
  tests/test_game_viewport_unified_bridge.py \
  -q --basetemp .pytest-e294-focused3
=> 23 passed in 1.76s

.venv\python.exe -m pytest -q --basetemp .pytest-e294-full
=> 2462 passed, 34 skipped, 55 subtests passed in 357.68s

tools/check_core_boundaries.py => core boundaries OK
tools/check_gui_boundaries.py => GUI boundaries OK
tools/check_project_plugin_model.py => project plugin model OK
tools/check_release_consistency.py => release consistency OK
tools/check_ai_command_audit_status.py => unified_undo_redo_runtime=false
```

新增回归覆盖 PhysicsEngine collision separation/impulse 的 owner API 回写，以及 Inspector transient `position_x`、`energy` 经 Registry execute/undo/redo 调用 owner setter。

## 边界

- `unified_undo_redo_runtime=false` 继续保持；只保留编辑器/Inspector command history。
- 未改变 `.pond` scene 语义、SR2D seams、package/project manifests；没有重建或切换 `.venv`，没有运行 `uv sync`，没有修改 `uv.lock`。
