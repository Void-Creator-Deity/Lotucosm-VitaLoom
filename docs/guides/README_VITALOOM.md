# 莲池织机说明

莲池织机是一个接入 FrameCore 的大插件，物理位置是：

```text
FrameCore/plugins/lotucosm-vitaloom/
```

它包含 Hub、版本 registry、具体版本 runtime、内置能力包入口。项目和用户扩展不放进这个安装包，而是位于 `workspace/`。

## 1. 组成

| 名称 | 位置 | 职责 |
|---|---|---|
| FrameCore | `FrameCore/` | 最底层架子，发现大插件并委托入口 |
| Hub | `FrameCore/plugins/lotucosm-vitaloom/hub/` | 项目门户，管理项目、版本、lock 状态 |
| Lotucosm | `versions/1.0.0/runtime/core/Lotucosm/` | 莲池运行时语义：Cosmos、Pond、实体、组件、系统、`.pond` 场景、脚本契约 |
| VitaLoom | `versions/1.0.0/runtime/core/VitaLoom/` | 编辑器、Dock、视口、项目管理、Player、SR/PS 控制面 |
| builtin | `versions/1.0.0/runtime/builtin/` | 产品版本内置能力包、官方编辑器插件、实体类型和系统 |
| Project World | `workspace/projects/` | 用户项目、示范项目、项目 lock、脚本、资产、addons |

Hub 不属于某个 `versions/<version>/runtime/`。它要管理版本，所以必须位于大插件根。

## 2. 启动链路

```text
python main.py
  -> FrameCore 读取 lotucosm-vitaloom/plugin_manifest.json
  -> 打开 Hub
  -> Hub 解析项目 project.lock.json
  -> 选择 versions/1.0.0
  -> 启动 versions/1.0.0/runtime/main.py --editor
```

发布版入口：

```bash
dist\FrameCore\FrameCore.exe
```

源码开发入口：

```bash
python main.py
```

## 3. 项目

| 项目层 | 位置 |
|---|---|
| 官方示范 | `workspace/projects/samples/` |
| 用户项目 | `workspace/projects/user/` |
| 项目嵌入扩展 | 项目根 `addons/` |

每个项目可以拥有自己的：

- `project.json`
- `project.lock.json`
- `scenes/`
- `scripts/`
- `assets/`
- `addons/`

`project.lock.json` 锁定实际解析到的产品版本和能力包版本，保证项目可复现。

## 4. 能力包和插件

莲池织机内部也有插件，但它们和 FrameCore 大插件不是同一层。

```text
产品 builtin capability
  -> workspace/extensions/user
  -> workspace/extensions/community
  -> project addons
```

| 层 | 谁管理 | 作用 |
|---|---|---|
| FrameCore 插件 | FrameCore | 加载 `lotucosm-vitaloom` 大插件 |
| Loom Capability Package | 莲池织机 runtime | 声明 `vitalloom.*` 能力、依赖、物理根和编辑器插件 |
| 用户/社区扩展 | 莲池织机 runtime | 扩展当前安装环境 |
| 项目 addons | 莲池织机 runtime | 只影响当前项目 |

能力包 catalog 位于：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/package_index.json
```

## 5. 运行时双轨

| 轨道 | 入口 | 用途 |
|---|---|---|
| SR_PLAY | GameViewport / SimulationTransport | 可视化 `.pond` 场景播放 |
| PS_BATCH | PsExperimentService / PsExperimentRunner | 无头批处理演化实验 |

SR/PS tick 暂不合并，继续遵守 ADR-0001。

## 6. 开发约束

1. 不恢复根 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/`。
2. 不添加旧路径 shim。
3. `FrameCore` 不 import 产品 runtime。
4. Hub 不放入 `versions/<version>/runtime/`。
5. 项目和用户扩展不写入 `FrameCore/plugins/lotucosm-vitaloom/`。

## 7. 更多文档

- [完整架构](../suite_architecture.md)
- [当前代码结构](../architecture.md)
- [能力包架构](../package_architecture.md)
- [项目 manifest](../project_manifest.md)
- [插件开发指南](PLUGIN_DEVELOPMENT_GUIDE.md)
