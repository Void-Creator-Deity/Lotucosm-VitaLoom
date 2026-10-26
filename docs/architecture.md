# 莲池织机架构总览

本文解释当前仓库的真实运行结构。完整物理模型见 [suite_architecture.md](suite_architecture.md)。

## 架构裁定：引擎大插件是下层插件框架（2026-07-18）

当前唯一正确的架构解释是“框架 + 可嵌套插件 host”，而不是“一个 PyQt 编辑器项目”：

```text
L0 FrameCore root framework
  └─ L1 lotucosm-vitaloom, the sole engine/product plugin discovered by FrameCore
       └─ versions/<version>/runtime, the versioned engine-runtime boundary
            ├─ L2 `vitalloom.*` capability packages
            ├─ L3 engine extension plugins/adapters
            └─ L4 project addons, discovered and activated only after project-open
```

L1 引擎大插件可以继续作为框架承载下层插件；FrameCore 仅负责发现、选择版本并委托入口。`vitalloom.*` 不得提升为 L1 plugin；项目 addon 不得进入 cold-start capability catalog。现存 PyQt6/QPainter/OpenGL 代码是旧 UI-host adapter，不是引擎根、领域 authority 或下层插件契约。
## 1. 顶层模型

```text
FrameCore
  -> lotucosm-vitaloom
     -> hub
     -> versions/1.0.0/runtime
        -> core/Lotucosm
        -> core/VitaLoom
        -> core/api
        -> builtin
Project World
  -> workspace/projects/samples
  -> workspace/projects/user
Extension World
  -> workspace/extensions/user
  -> workspace/extensions/community
```

`FrameCore` 是最底层 Module。它的 Interface 是插件发现、`plugin_manifest.json`、版本 registry、生命周期、服务注册表和事件交互。它的 Implementation 不知道 `core.*` 或 `builtin`。

`lotucosm-vitaloom` 是莲池织机大插件。它的 Interface 是 Hub、版本 registry、项目 lock 解析和能力包管理。

`versions/1.0.0/runtime` 是具体织机版本。只有这里拥有 `core.*` namespace。

## 2. 三个名字

| 名字 | 是什么 | 当前物理位置 | 不是 |
|---|---|---|---|
| FrameCore | L0 启动架子 | `FrameCore/` | 不是莲池 runtime，不加载能力包 |
| lotucosm-vitaloom | 莲池织机大插件 | `FrameCore/plugins/lotucosm-vitaloom/` | 不是某个项目 |
| Lotucosm | 莲池运行时语义 | `.../runtime/core/Lotucosm/` | 不是 Hub，不是编辑器 UI |
| VitaLoom | 织机宿主、编辑器、Player | `.../runtime/core/VitaLoom/` | 不是 L0 Frame |
| PVAEC | 研究和演化语义 | 产品 runtime 内的 `pvaec_*` 与 `builtin/systems/pvaec_orchestrator.py` | 不是底层框架 |

`suite_id` 是历史 lock 兼容标识。它不代表用户需要理解的第二个安装层。

## 3. 入口

| 命令 | 作用 |
|---|---|
| `python main.py` | 启动 FrameCore，发现 `lotucosm-vitaloom`，打开 Hub |
| `python main.py --version` | 输出大插件与默认 runtime 版本 |
| `python main.py --smoke-hub` | offscreen 构造 Hub |
| `python main.py --smoke-editor` | 委托产品 runtime 构造 EditorKernel |
| `python player.py --project PATH` | 通过产品版本 Player 打开项目 |
| `python tools/run_ps_experiment.py` | bootstrap 后进入产品 runtime 的 PS 实验链 |

## 4. 运行时双轨

当前不合并 SR/PS tick。

| 轨道 | 主入口 | 事实 Interface |
|---|---|---|
| SR_PLAY | GameViewport / SimulationTransport | `.pond` 场景、SceneRuntimeEntity、ScriptBase/PvaecScript、可视化 tick |
| PS_BATCH | PsExperimentService / PsExperimentRunner | `Pond.update`、实验 config、无头指标输出 |

两者通过生态观察快照等只读 Interface 汇合到编辑器面板，但 tick 语义保持分离。

## 5. 能力包与插件

`runtime/builtin/package_index.json` 是产品版本内置 capability catalog。里面的 `vitalloom.*` 条目是 Loom Capability Package，不是 FrameCore 插件。

下层扩展 authority 链路：

```text
runtime capability catalog（L2）
  -> official/workspace extension source catalog（L3；workspace 默认只作为 source）
  -> project manifest / lock 计算激活目标
  -> project-open 后校验 <project>/addons/*/plugin.json（L4）
  -> Qt-free lifecycle plan
  -> 当前 Editor/PyQt Host Adapter 执行 on_load/on_unload 与 UI 挂接
```

项目 lock 可以启用、禁用或固定 capability 解析结果，但不能改变 FrameCore 加载哪个大插件。L4 addon 的 manifest 必须声明受约束的入口、插件 id、版本、依赖和目标 `lotucosm-vitaloom` runtime 版本；Addon discovery 失败不得先破坏上一个 Project World 的 embedded catalog。

运行态 operator authority 同样位于 L1 引擎插件的 versioned runtime 内，而不属于 FrameCore 或 PyQt panel。`plugin_host_operator.py` 把当前请求 Project World、保留的 L4 catalog Project World、catalog/active/failure 和 discovery/lifecycle report 归一为带稳定 report id 的 Qt-free inspection；共享命令 `plugin.host.inspect`、`plugin.host.recovery.list`、`plugin.host.recovery.resolve` 只允许 confirmation-bound 的正常 lifecycle retry。stale report 必须在任何 callback 前拒绝，且不存在 force import/unload 旁路。

## 6. 禁止回退

- 根目录不得恢复 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/`。
- 不得增加旧路径导入 shim。
- `FrameCore` 不得 import 产品 runtime。
- Hub 不得放进产品版本 runtime。
- Project World 不得写入 `FrameCore/plugins/lotucosm-vitaloom/`。

## 7. 相关文档

| 目的 | 文档 |
|---|---|
| 完整模型 | [suite_architecture.md](suite_architecture.md) |
| 物理迁移审计 | [suite_refactor_completion_audit.md](suite_refactor_completion_audit.md) |
| 架构决策 | [adr/0003-suite-plugin-architecture.md](adr/0003-suite-plugin-architecture.md) |
| 项目 manifest/lock | [project_manifest.md](project_manifest.md) |
| 能力包体系 | [package_architecture.md](package_architecture.md) |
| 运行时入口 | [runtime_entry_points.md](runtime_entry_points.md) |

## 8. 引擎 Host 与遗留 PyQt 实现边界

VitaLoom 的稳定架构中心是 L0 FrameCore 与 L1 引擎大插件的扩展契约，不是任何一个 GUI 工具包。`lotucosm-vitaloom` 作为 L1 产品插件，同时为版本化 runtime、capability package、安装级 extension plugin 和项目级 addon 提供下层框架能力；项目 addon 仅在项目打开后参与发现与激活，不能污染安装或 FrameCore manifest。

PyQt6 当前仍被 Hub、Editor/Player 启动路径以及部分 editor extension 使用。因此它是**现有 host/UI adapter 实现**，但不是不可替换的产品根边界。后续替换必须先抽出 Qt-free 的 host contract（生命周期、服务、面板贡献、viewport surface、输入和项目切换），再使 PyQt 或新宿主分别作为 adapter；不得仅删除 import 就宣称迁移完成，也不得在 L0 中反向导入 runtime UI。

Real-time SR rendering 仍通过 `GameViewport`、`SimulationDriver`、`ViewportFrameSnapshot` 与 `ViewportBackend` 的语义 seam 工作。当前实现策略如下：

- `QPainterViewportBackend` 仍是当前默认 backend，并可消费 backend-neutral draw commands。
- `OpenGLViewportBackend` 是 opt-in 的近期待验证 bridge；在真实 context-backed pixel、interaction 与 benchmark parity 证据齐备前，`auto` 不切换默认值。
- `VITALOOM_VIEWPORT_BACKEND=qpainter|opengl|rhi|auto` 控制当前 adapter 的 backend 选择；`rhi` 只是未来 Vulkan / Direct3D / Metal 的抽象目标，不是本阶段实现。
- `pygame` 仅允许留在显式 allowlist 的 legacy 路径；`tools/check_gui_boundaries.py` 保护主 GUI/runtime 路径。
