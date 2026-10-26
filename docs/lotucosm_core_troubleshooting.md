# Lotucosm 核心排错索引

运行 SR/PS 出错时，按现象查下表；编辑器问题见 [README_VITALOOM.md](guides/README_VITALOOM.md)。

## 现象 → 优先查看

| 现象 | 优先查看 | 说明 |
|------|----------|------|
| 莲池 tick 不推进、世代不触发 | `Pond.update`、`EvolutionRunner.apply_generation` | `time` 每帧自增；`iteration` 仅世代边界；`evolution_generation_interval` 须 >0 |
| 生物体未加入模拟 / 重复 ID | `Pond.add_organism`、`organisms` 字典键 | 同 ID 返回 False；成功时同步 `root_entities` |
| 加载 .pond 后实体无 pond 引用 | `Pond._apply_loaded_pond_state` | 加载后须回填 `org.pond = self` |
| 实体位置/子层级错乱 | `EntityBase.world_position`、`add_child` | 子实体 `position` 为局部；绘制目前多用局部坐标 |
| 脚本 `instantiate` 返回 None | `ScriptBase.instantiate`、`runtime_entities.instantiate_entity` | 无 `entity.pond` 时回退 `get_cosmos().get_active_world()` |
| PVAEC 循环恒失败 | `PVAECCycle.run_cycle`、各阶段 `perceive`/`execute_action` | 日志 `PVAEC循环执行失败`；检查组件是否有 `sense`/`act` |
| 感知全零或噪声异常 | `PVAECCycle.perceive`、`PerceptionSystem.fuse_flat_sensor_dict` | `use_legacy_perception_pipeline=True` 才走噪声融合 |
| 记忆检索为空 | `MemorySystem.retrieve`、`MemoryGene.situation` | 当前为字符串子串匹配；情境 `str(perception)` 须可对上 |
| 无活跃世界 / 脚本找不到莲池 | `Cosmos.get_active_world`、`set_active_world` | `active_world_id` 未设时 `get_active_world()` 为 None |
| SR 中枢不动 / 速度封顶异常 | `CentralBrainPvaec.act`、`MindProfile.max_speed` | `bounds` 宽高 ≤0 时 `think` 返回零加速度 |
| MindProfile 与场景不一致 | `MindProfile.from_dict`、`.pond` 中 `mind` 字段 | 见 [sr_mind_profile_fields.md](sr_mind_profile_fields.md) |
| 演化基因未遗传 | `mind_dict_mutate`、`GENE_KEYS` | 仅 `wander_amp`/`gain_high_stress`/`mem_alpha` 三键 |
| 插件 Dock 未出现 | `LegacyEditorPluginAdapter`、`LayoutManager`（VitaLoom） | 新插件检查 `dock_surface` 与 Adapter-local factory；仅旧插件 fallback 需要 `create_dock_widget` + `get_dock_config` |
| 事件订阅无回调 | `core/api/events.EventBus.publish` vs `event_system.EventBus.emit` | 两套总线：字符串 `EventType` 与 `Enum EventType`，勿混用 |
| 用户脚本 `exec` 失败 | `ScriptRuntime.execute`、`get_script_runtime` | 全局注入 `cosmos`/`publish`；异常见日志 `脚本执行失败` |
| 启动器模式打不开 | `main.py` / Hub 启动链路 | GUI 路径依赖 `FRAMECORE_ROOT`、大插件根和 `plugin_manifest.json`；推荐直接运行 `python main.py` |

## 模块速查

| 模块 | 职责摘要 |
|------|----------|
| `pond.py` | 莲池环境：实体、资源、物理子系统、每帧 `update` |
| `entity.py` | 实体基类：运动学、层级、脚本列表 |
| `component.py` | 组件基类：信号、连接、Inspector 属性 |
| `pvaec_cycle.py` | 通用 PVAEC 六步循环（非 SR 脚本管线） |
| `scripts.py` | `ScriptBase` 生命周期与 `instantiate` 工具 |
| `memory.py` | `MemoryGene` / `MemorySystem` 运行时记忆 |
| `perception.py` | 传感器 flat dict 噪声与裁剪 |
| `cosmos.py` | 多世界单例与全局系统注册 |
| `runtime_entities.py` | 按类型字符串在莲池中创建实体 |
| `sr_mind_profile.py` | SR 中枢可调参数 dataclass |
| `sr_mind_gene.py` | MindProfile 子集突变 |
| `workspace/projects/*/scripts/central_brain_pvaec.py` | SR 场景中枢 PVAEC 脚本类（工程内实现） |
| `core/VitaLoom/kernel/plugin_interfaces.py` | 历史编辑器接口兼容表面；新作者应使用 `IRuntimePlugin` + `editor_contributions` |
| `core/api/*` | 装饰器、双事件总线、脚本运行时 |
