# ADR-0001：双运行时（SR/PS）通过接缝分阶段统一

> 物理架构更新：本 ADR 的核心决策仍有效；旧根 `core/`、`builtin/`、`plugins/`、`projects/` 等路径表述已由 [ADR-0003](0003-suite-plugin-architecture.md) 更新为 FrameCore / Suite / Product Version / Workspace 模型。

- **状态**：已接受
- **日期**：2026-06-04
- **决策者**：莲池织机架构（文档 + L0 运行时接缝）

## 背景

莲池生命织机同时存在：

- **SR 播放轨**：`GameViewport` + 场景实体 + `SimulationTransport`
- **PS 批处理轨**：`Pond` + `Organism` + `PsExperimentService`

PVAEC 示范工程与整个织机引擎需要**指标可比、工具链一致**，但不能在 v1 用一次重构合并 tick（回归面过大，与 Unity/UE Play/Batch 分叉惯例冲突）。

## 决策

1. **不**在短期将 PS tick 并入 `SimulationTransport` 或 `GameViewport` 主循环。
2. **采用分阶段统一策略**（见 [runtime_unification_roadmap.md](../runtime_unification_roadmap.md)）：
   - 先统一**读模型**（`EcologySnapshot` / `collect_ecology_snapshots`）
   - 再统一**配置契约**、**只读视口叠加**、**会话协调器**
   - 最后可选 **单 Pond 驱动**（`runtime_mode: unified_pond`）
3. 产品 runtime 内的 Lotucosm 提供语言无关接缝（`runtime/core/Lotucosm/runtime/`）；**L2 官方扩展包** 提供适配器与 Dock；**社区 `workspace/extensions/`** **不得**实现第二套 tick。分层术语见 [architecture.md](../architecture.md)。
4. 大型 **Project Settings** Dock 不作为前置；工程级字段写入 `project.json` + 实验 Dock。

## 后果

### 正面

- 官方插件（生态、实验、模拟控制）与社区扩展有稳定观测 API。
- SR ▶ 与 PS 实验可继续并行，产品路径清晰。
- Phase C.4 有明确前置（C.1–C.3），可评审后立项。

### 负面

- 在 C.4 之前，遗传/繁殖在 SR 与 PS 仍可能数值不一致，需在文档标明。
- 维护者需同时理解两条 tick（直到 unified 模式）。

## 备选方案（已否决）

| 方案 | 否决原因 |
|------|----------|
| 立即合并 tick | 实体模型、线程、Transport 回归不可控 |
| 仅在 PVAEC 工程内 hack 同步 | 无法服务织机教程与其他官方包 |
| 仅文档、无缝接代码 | 插件仍会直接依赖 GameViewport 私有字段 |

## 参考

- [runtime_entry_points.md](../runtime_entry_points.md)
- [package_architecture.md](../package_architecture.md)
