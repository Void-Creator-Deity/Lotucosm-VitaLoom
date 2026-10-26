# 莲池织机 FrameCore 插件架构

本文是当前仓库的权威架构说明。物理迁移已经完成：根目录不再保留旧运行时 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/` 或旧根 manifest。旧路径不提供 shim；入口全部通过 `FrameCore`、`plugin_manifest.json` 和产品版本 `version_manifest.json` 定位。

## 1. 第一性原理

| 必须为真 | 架构落点 |
|---|---|
| 最底层必须小而稳定 | `FrameCore/` 只负责发现 FrameCore 插件、生命周期、服务注册表、事件交互和基础启动 |
| 莲池织机必须是一整块可安装能力 | `FrameCore/plugins/lotucosm-vitaloom/` 是内部启动安装包，用户日常只管理项目插件 |
| Hub 要管项目和织机版本 | Hub 位于大插件根 `hub/`，不属于某个具体 runtime 版本 |
| 具体织机版本必须自洽 | `versions/<version>/runtime/` 内拥有自己的 `core.*`、`builtin`、Editor、Player |
| 项目必须独立且可复现 | `workspace/projects/` 保存项目，`project.lock.json` 锁定产品版本和能力包解析结果 |
| 能力包归织机管理 | `runtime/builtin/package_index.json` 是产品版本内的 capability catalog，FrameCore 不直接加载 `vitalloom.*` |

剃刀结论：对外只保留“莲池织机项目 + 项目插件”这套用户模型；不再把 Suite、Product、安装级启动插件做成用户可见层。`suite_id` 只作为历史 lock 字段和兼容标识存在。

## 架构裁定（2026-07-18）

FrameCore 只发现一个 L1 插件：`lotucosm-vitaloom`。该引擎/产品大插件自身是下层 extension 的 host framework；其版本化 runtime 才管理 capability package、engine extension plugin 和项目 addon。`Project World` 是项目 addon 的作用域，不是与 L0/L1 平级的第二套框架。

PyQt6/QPainter/OpenGL 是遗留 UI-host adapter 实现。它们不定义 FrameCore、L1 engine plugin 或下层插件的架构；后续任何 UI-host 演进必须通过 Qt-free engine/plugin contracts，而不是反向让领域或插件规则依赖 GUI。
## 2. 分层模型

```text
L0 · FrameCore
  最底层架子：发现 FrameCore 插件、提供 FrameApi、装配环境变量、委托入口。

L1 · lotucosm-vitaloom FrameCore Plugin
  莲池织机内部启动安装包：Hub、项目索引、版本注册表、模板入口、版本 runtime 集合。

Versioned Runtime Boundary（不另编号）
  versions/<version>/runtime：承载该版本的 Lotucosm、VitaLoom、Player、SR/PS 与下层扩展契约。

L2 · VitaLoom Capability / Domain Package
  `vitalloom.*` 能力、依赖和领域包，由版本 runtime 的 capability catalog 管理。

L3 · Engine Extension Plugin / Adapter
  官方 editor extension、workspace extension source 中的实现，以及具体 UI/Host Adapter。

L4 · Project Addon (Project-scoped Extension)
  `<project>/addons/` 内仅随当前 Project World 生效的扩展，只在 project-open 后发现和激活。```

两个“插件”可以同名但不能混层：

| 名称 | 位置 | 谁加载 | 作用域 |
|---|---|---|---|
| FrameCore 启动插件 | `FrameCore/plugins/lotucosm-vitaloom/` | FrameCore | 内部安装环境，不进项目插件 UI |
| L2 capability/domain package | `versions/*/runtime/builtin/package_index.json` 与实现根 | 莲池织机 runtime capability authority | 当前版本 runtime / 项目解析 |
| L3 engine extension / Adapter | `runtime/builtin/editor_extensions/`、`workspace/extensions/` 来源 | 莲池织机 runtime plugin Host | Host 安装或项目选择；workspace 默认不全局启用 |
| L4 project addon | `<project>/addons/` | 莲池织机 runtime plugin Host | 仅当前 Project World |

## 3. 当前物理目录

```text
FrameCore/
  __init__.py
  suite_registry.py          # 历史名字，读取 plugin_manifest.json
  product_registry.py        # 读取大插件 versions/*
  lifecycle.py
  service_registry.py
  event_bus.py
  plugins/
    lotucosm-vitaloom/
      plugin_manifest.json
      hub/
      versions/
        1.0.0/
          version_manifest.json
          runtime/
            main.py
            player.py
            core/
              Lotucosm/
              VitaLoom/
              api/
            builtin/
workspace/
  projects/
    samples/
    user/
  extensions/
    user/
    community/
  experiments/
  state/
    system/
    experiment_runs/
```

根 `main.py` 是 FrameCore 应用入口：发现 `lotucosm-vitaloom` 大插件，启动 Hub，或按 manifest 委托到选定版本 runtime。根 `player.py` 是开发/打包 CLI 入口，行为同样由 manifest 转发。

## 4. Manifest 契约

| 文件 | 位置 | 职责 |
|---|---|---|
| `plugin_manifest.json` | `FrameCore/plugins/lotucosm-vitaloom/` | 大插件 id、显示名、Hub 入口、默认版本、版本列表、capability catalog |
| `version_manifest.json` | `.../versions/1.0.0/` | 具体版本入口、物理根、内置 capability catalog |
| plugin.json | <project>/addons/<addon>/ | L4 addon id、版本、受约束入口、依赖与目标 L1 runtime 版本 |
| `project.json` | 项目根 | 项目期望使用的织机版本和能力 |
| `project.lock.json` | 项目根 | 实际解析到的产品版本和 capability 版本 |

当前 `plugin_manifest.json` 的关键形状：

```json
{
  "plugin_id": "lotucosm-vitaloom",
  "product_id": "lotucosm-vitaloom",
  "entry": "hub",
  "default_version": "1.0.0",
  "versions": ["1.0.0"],
  "capability_catalog": "versions/1.0.0/runtime/builtin/package_index.json"
}
```

当前 `version_manifest.json` 的关键形状：

```json
{
  "entrypoints": {
    "editor": "runtime/main.py --editor",
    "player": "runtime/player.py",
    "smoke_editor": "runtime/main.py --smoke-editor"
  },
  "physical_roots": [
    "runtime/core/Lotucosm",
    "runtime/core/VitaLoom",
    "runtime/core/api",
    "runtime/builtin"
  ],
  "builtin_capability_index": "runtime/builtin/package_index.json"
}
```

## 5. 启动链路

```text
python main.py
  -> FrameCore 读取 lotucosm-vitaloom/plugin_manifest.json
  -> FrameApi 选择默认或 lock 指定的 versions/<version>
  -> Hub 显示项目索引、版本状态和 lock 状态
  -> Hub 打开项目时解析 project.lock.json
  -> 子进程启动 versions/<version>/runtime/main.py --editor
  -> 产品 runtime 从自身目录加载 core.*、builtin 和 capability catalog
```

关键环境变量：

- `FRAMECORE_ROOT`
- `VITALOOM_SUITE_ROOT`：历史名字，当前含义是 `lotucosm-vitaloom` 大插件根
- `VITALOOM_PRODUCT_VERSION_ROOT`
- `VITALOOM_APP_ROOT`

## 6. 插件与能力加载顺序

固定 authority 顺序：

```text
版本 runtime capability catalog（L2）
  -> official/workspace extension sources（L3；workspace 默认不激活）
  -> 当前项目 required_capabilities / package_state / project.lock.json
  -> project-open 后验证当前项目 addons/*/plugin.json（L4）
  -> Qt-free dependency/lifecycle plan
  -> 具体 Host Adapter 执行生命周期回调
```

解释：

- 产品内置 capability 随具体织机版本发布。
- `workspace/extensions/user` 和 `workspace/extensions/community` 是插件源、缓存和开发区；默认不会作为全局插件自动启用。
- 项目 `addons/` 是项目嵌入扩展，只随该 Project World 生效。
- 项目插件管理器只修改当前项目：启用、禁用、安装、解析和导出闭包都写入当前项目的 `project.json` / `project.lock.json`。
- 项目 lock 可以启用、禁用或固定 capability 解析结果，但不能改变 FrameCore 加载哪个内部启动插件。

## 7. 禁止事项

1. `FrameCore` 不得 import `core.VitaLoom`、`core.Lotucosm`、`builtin` 或 `projects`。
2. 不得恢复根 `core/`、`builtin/`、`products/`、`plugins/`、`projects/`、`data/`。
3. 不得添加旧路径 shim。
4. Hub 不得放入 `versions/<version>/runtime/`。
5. 用户项目不得写入 `FrameCore/plugins/lotucosm-vitaloom/` 安装包。
6. SR/PS 双 tick 不在本次物理迁移中合并，继续遵守 ADR-0001。

## 8. 验收命令

```bash
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
python -m compileall -q FrameCore workspace tools main.py player.py
python -m pytest -q
python tools/run_routine_maintenance.py --skip-audit
python tools/build_exe.py --console
dist\FrameCore\FrameCore.exe --version
dist\FrameCore\FrameCore.exe --smoke-hub
dist\FrameCore\FrameCore.exe --smoke-editor
```

## 9. 行业参考

本架构只吸收成熟工具链的原则，不照搬目录：

- Unity Hub 证明“项目门户”和“具体 Editor 版本”应分离。
- Unity lockfile 证明包解析结果需要可复现。
- Unreal Plugin 证明扩展包可以包含更细的模块。
- VS Code extension manifest 证明入口、兼容版本和激活信息应由 manifest 声明。
- Godot `addons/` 证明项目级嵌入扩展是合理模型。
## 10. 引擎大插件 Host / Extension Boundary

`lotucosm-vitaloom` 不是被 FrameCore 直接展开的 runtime 文件夹；它是 L1 引擎/产品大插件，并可作为下层扩展的 host framework。FrameCore 只发现它、选择产品版本并委托 entrypoint，绝不 import viewport、Inspector、SR entity、capability implementation 或任何具体 UI toolkit。

L1/L2 对下层扩展的真实链路是：

```text
package_index.json capability declaration
  -> package dependency / project manifest + lock resolution
  -> PluginLoader discovery of IEditorPlugin / *_plugin.py
  -> official_mod / user_mod / embedded_mod scope isolation
  -> project-open scan_project_addons(<project>/addons)
  -> capability + disabled-plugin activation target
```

- Capability package 是版本 runtime 内的能力/依赖单元；它不是 FrameCore plugin。
- Workspace extension 是安装范围内的扩展实现；其作用域不能写入项目 lock。
- Project addon 只属于当前 Project World，项目打开后才被扫描和激活，不能影响其他项目或改写 L0/L1 manifest。
- PyQt6 是当前 Hub/Editor/Player 的 host adapter 实现，而非 FrameCore 或 engine-plugin 架构契约。不得预设下一宿主技术；先建立 Qt-free host interface，再以各 UI 技术实现 adapter。
- `GameViewport`、`SimulationDriver` 与 `ViewportBackend` 的 SR semantic seam 保持不变。QPainter 仍为当前默认实现，OpenGL 仍为 opt-in，直到真实 context、像素、交互与 benchmark parity 证明其可默认启用。
- `tools/check_gui_boundaries.py` 继续禁止主 GUI path 的直接 `pygame` 依赖。

