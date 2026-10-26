# ADR-0007：统一语义命令历史，而非统一 UI 对象栈

> 物理架构：产品运行时边界仍为 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/`；分层与 Suite/产品版本模型遵循 [ADR-0003](0003-suite-plugin-architecture.md)。

## 状态

已接受（架构决定，2026-07-31）；实施中。

## 背景

VitaLoom 已具备 Qt-free `CommandRegistry`、命令事件包络、代表性内存撤销/重做与项目级 JSONL audit 重放，也已将编辑器菜单、工具栏与快捷键接入 `command.undo` / `command.redo`。同时，Inspector 和 SceneViewport 仍各自直接实例化并执行遗留 `CommandStack`；视口 Ctrl+Z/Ctrl+Y 也绕过 Registry。

这使一次用户编辑的撤销路径取决于它来自哪个 UI 表面：菜单操作只看 Registry，视口快捷键只看本地 UI 对象栈。该双权威状态与完整重构目标不兼容，且不能通过把 Qt/画布对象闭包塞入 Qt-free Registry 来伪造统一。

## 决策

### 1. 一个语义历史权威

`CommandRegistry` 是支持项目语义变更的唯一历史权威；若后续为清晰度提取 `CommandHistoryService`，它必须保持 Qt-free、由 Registry 委托或被 Registry 委托，并保留当前公共 command registry 流程。

一个语义历史条目至少包括：稳定 command id、JSON-safe payload、JSON-safe result/inverse 数据、因果顺序、执行/undo/redo 动作、可选 source audit id、项目定位以及失败结果。它不能保存 QWidget、QGraphicsItem、Python callback、OpenGL context 或其他进程内 UI 对象。

### 2. 统一的范围

“统一 undo/redo”指所有**受支持的、改变项目语义的**编辑操作经同一命令历史处理，无论入口是 Inspector、SceneViewport、菜单/工具栏/快捷键、CLI 还是 MCP。

不包含焦点、选择、悬停、临时拖拽预览、布局、渲染缓存和其他无 `.pond` /项目语义的瞬态 UI 状态。此类状态可以继续留在 UI-host，但不得被全局编辑 Undo/Redo 冒充为项目历史。

### 3. 遗留 `CommandStack` 的迁移

`CommandStack` 仅作为 UI-host 迁移适配器保留：

- 已有语义 Registry command 的编辑必须迁移到 Registry，不能继续同时写入 `CommandStack`。
- 旧 stack 中尚无语义建模的节点/连线操作必须先获得稳定 payload、场景读写和 inverse 设计，才可加入全局 Undo/Redo。
- 在该迁移完成前，global `command.undo` / `command.redo` 不得声称覆盖这些遗留操作；遗留 Ctrl+Z/Ctrl+Y 也不能被标记为统一实现的证据。
- 遗留 stack 不进入 `.pond` 或 durable audit，且不能向 L0/L1 反向注入 Qt 生命周期或 GUI authority。

### 4. 持久化与重放

`.pond` 继续保存场景真值，不修改其语义。`project/.vitaloom/command_audit.jsonl` 继续是审计/兼容轨迹；由同一语义 command 产生的持久 undo/redo 可从 fresh registry 重新解析。若新增索引、版本或 checkpoint，只能 append-compatible，并需明确崩溃恢复、部分失败、分支截断和外部文件修改的处理。

本 ADR 不批准将命令历史等同于 SR/PS runtime replay、WorldBridge 映射或 unified Pond。那些边界仍由 ADR-0001/0005 及其只读状态工具约束。

### 5. 失败原子性和测试门槛

语义 handler 失败不得消耗或推进 undo/redo 指针；audit 写入失败必须有明确、可测试的提交策略，不能悄然让场景变更和 history 分叉。每个迁移切片至少证明：入口执行、同一全局 undo/redo、fresh-registry durable undo/redo、逆操作失败回滚、`.pond` 兼容、Qt-free import/boundary 以及 UI parity。

## 后果

- 这是逐条语义迁移，不是把 GUI `Command` 对象塞入 Registry 的大爆炸重写。
- 全局菜单/快捷键可最终对所有支持的语义编辑保持一致，但不能在迁移前夸大覆盖范围。
- Inspector/viewport 需要明确 project/scene context 传递，而非依赖隐式 widget 状态。
- 现有 command registry、Inspector binding、`.pond`、SR2D 和 manifests 维持公共兼容；QPainter 保持默认，OpenGL/native/WorldBridge 就绪度不因本决定而变化。

## 相关

- [ADR-0002：第一性原理与分层依赖](0002-first-principles-and-layering.md)
- [ADR-0003：Suite Plugin Architecture](0003-suite-plugin-architecture.md)
- [ADR-0005：统一 Pond 接缝](0005-unified-pond-bridge.md)
- [E167 plan](../superpowers/plans/2026-07-31-ai-command-unified-undo-redo-runtime-architecture-decision-and-completion-gate.md)
