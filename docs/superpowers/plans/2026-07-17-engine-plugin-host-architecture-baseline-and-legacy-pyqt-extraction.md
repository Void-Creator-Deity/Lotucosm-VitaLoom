# 引擎大插件作为可扩展框架：架构基线与旧 PyQt 提取 Gate

**日期：** 2026-07-17  
**状态：** in progress  
**前置 Gate：** Phase 7J 的代码与回归证据已具备，文档闭环尚未完成  
**本 Gate 的唯一目标：** 将真实的“根框架 → 引擎大插件 → 版本化引擎 runtime → capability / extension / project addon”层级写成可验证契约，并界定 PyQt 遗留实现的替换边界；不在尚未决定的新宿主技术前提下进行伪迁移。

## 1. 用户确认的架构意图

VitaLoom 不是以 PyQt 为产品根的桌面编辑器。它是一个类似引擎的、可递归扩展的框架插件体系：

```text
L0 FrameCore（根框架）
  -> L1 lotucosm-vitaloom（唯一引擎 / 产品大插件，亦可充当下层框架）
      -> Hub + versions/<version>/runtime（版本选择与版本化引擎）
          -> L2 capability package（能力与依赖声明）
          -> L3 editor / workspace extension plugin（安装级扩展实现）
          -> L4 project addon（项目内嵌扩展）
```

这里的“插件可以继续作为框架加载插件”不是目录上的口号：L1 必须给 L2–L4 提供受控的发现、解析、激活、隔离、生命周期和兼容接口。PyQt 是历史或迁移中的宿主/UI 实现，不是这套分层的架构中心，也不能再被文档描述为不可替代的永久边界。

## 2. 已审计的事实

1. 仓库根 `main.py` 先经 `load_default_suite_manifest()` 构造 `FrameApi`，再加载 manifest `entry` 所指的 L1 生命周期插件；L0 没有直接导入 `core.*` 或 `builtin` runtime 实现。
2. `FrameCore/plugins/lotucosm-vitaloom/plugin_manifest.json` 声明唯一大插件 `lotucosm-vitaloom`、Hub entry、默认版本 `1.0.0` 与 capability catalog。
3. `versions/1.0.0/version_manifest.json` 将 `command/editor/player` 入口与物理 runtime roots 绑定在 L1 大插件内部；L0 仅按 manifest 执行入口。
4. `runtime/builtin/package_index.json` 声明 `vitalloom.*` capability package。它们不是 FrameCore 插件，不能越级改写 L0/L1 manifest。
5. `PluginLoader` 以 `IEditorPlugin` 实现和 `*_plugin.py` 发现扩展；其 scope 为 `embedded_mod < user_mod < official_mod < core_mod`。项目打开后，`scan_project_addons()` 扫描 `<project>/addons/*/plugin.json` 与 `*_plugin.py`，并把它们按项目的 capability / disabled state 参与激活。
6. PyQt 当前被 Hub、runtime 启动入口、Player、`editor_launcher` 与若干 editor extension 直接使用；这证明它仍是**当前实现依赖面**，但不证明它是上层架构契约。

## 3. 要保护的层级契约

| 层级 | 权责 | 允许知道 | 禁止知道 / 做什么 |
|---|---|---|---|
| L0 FrameCore | suite manifest、L1 发现、生命周期、产品版本选择与入口委托 | L1 manifest 和稳定 lifecycle contract | import L2 runtime/core、能力包实现、编辑器组件、具体 UI 工具包 |
| L1 引擎大插件 | Hub、版本注册、runtime catalog、对下层扩展提供 host/activation context | L0 `FrameApi`、自身版本与产品范围 | 让项目 addon 改写 L0/L1 manifest；把具体 runtime 反向泄漏到 L0 |
| L2 版本化 runtime / capability | 引擎语义、公开 API、capability metadata、依赖解析与运行时服务 | 当前版本 runtime roots、package catalog | 将 `vitalloom.*` 冒充 L0 插件；把 package resolution 写成 UI 私有状态 |
| L3 安装级扩展 | 通过已声明 extension contract 扩展编辑器/工具/能力适配器 | host interfaces、manifest/capability 权限 | 私自创建第二条 SR tick 或越权写项目 lock |
| L4 Project addon | 只扩展当前项目世界，随项目打开后发现和激活 | 项目 manifest、显式 addon contract | 影响其他项目、修改产品安装或 FrameCore manifest |

Capability package、extension plugin、project addon 是不同概念：前者是产品 runtime 的能力/依赖单元；中者是安装范围内的实现扩展；后者是项目范围内的嵌入扩展。任何后续迁移必须保留三者的解析与隔离差异。

## 4. PyQt 的正确迁移边界

### 4.1 当前定位

- PyQt 目前只是 Hub / 编辑器 / Player 的一个已存在 host/UI 实现及部分扩展的直接依赖。
- CLI、MCP、资产事务、项目 manifest、capability 解析、核心 simulation / command Authority 必须继续可以 Qt-free 地被导入和验证。
- `PackageManagerPlugin` 等“领域解析逻辑与 QWidget plugin 类耦合”的位置是待拆分对象；不得为了 headless 测试而伪造 PyQt 或把产品逻辑塞回测试 shim。

### 4.2 本 Gate 不做的事

- 不预先选定 Unity、Godot、Unreal、Electron 或任何新的 app shell。
- 不整体删除 PyQt、QPainter 或现有 GUI 文件。
- 不把“删除 import”当作迁移完成。
- 不改变 `.pond`、AI command registry、Inspector command binding、SR2D public seams、项目/包 manifest 或 project addon 语义。

### 4.3 后续真正的 host 抽取完成条件

在选择新宿主前，必须先出现稳定、Qt-free 的 host contract：启动生命周期、窗口/面板贡献、viewport surface、输入、服务注册、项目切换、错误与可观测性边界均有明确所有者。每个 PyQt adapter 只能依赖该 contract；核心/包解析不得依赖 QWidget。迁移主张需要 headless import、接口契约、现有 PyQt adapter 回归以及真实新宿主像素/交互证据（如选定）共同证明。

## 5. 实施顺序

1. **完成事实基线。** 把本文档的层级契约同步到 `docs/architecture.md`、`docs/suite_architecture.md`、`docs/package_architecture.md` 和主线状态；修正“PyQt 永久 editor shell”的过时陈述。
2. **建立可重复证明。** 运行 FrameCore / manifest / package / plugin activation 的 Qt-free 回归与边界检查；记录 PyQt 缺失造成的真实 GUI-only test skip/block，不改测试掩盖它。
3. **PyQt 依赖面分类。** 按 L0、L1 Hub、runtime host、UI extension、被 UI 耦合的领域逻辑、CLI/Player 污染风险，形成精确清单和优先级。
4. **闭环 Phase 7J。** 将已通过的 asset mutation interlock 证据、已知 GUI 环境限制和唯一下一 Gate 写回状态文件；该可靠性 Gate 与宿主替换决策保持分离。
5. **唯一下一开发 Gate。** 在不选定新 app shell 的情况下，先将一个明确的领域服务从 PyQt editor plugin 中提取为 Qt-free contract，并用现有 PyQt adapter 保持兼容。首选审计目标是 Package Manager 的 domain/UI 耦合；若实际依赖图显示风险更低的对象，则以审计记录替换该候选。

## 6. 验收证据

### 已取得

```text
python -m pytest -q \
  tests/test_framecore_plugin_lifecycle.py \
  tests/test_framecore_migration_completion.py \
  tests/test_frozen_package_roots.py \
  tests/test_hub_frozen_discovery.py \
  tests/test_package_governance.py \
  tests/test_package_import_side_effects.py \
  tests/test_package_index_architecture.py \
  tests/test_package_migration.py \
  tests/test_plugin_activation.py \
  tests/test_plugin_command_contributions.py \
  tests/test_plugin_id_consistency.py \
  tests/test_plugin_loader_failure_isolation.py \
  tests/test_project_manifest.py \
  tests/test_project_plugin_model_gate.py \
  tests/test_runtime_packages.py
# 49 passed in 1.70s
```

### 已知环境边界

当前解释器为 Python 3.13.5（Anaconda），未安装 PyQt6。下列 package-manager architecture tests 目前因它们在 collection 时导入 PyQt-bound `PackageManagerPlugin` 而被阻断，而不是因 L0/L1/plugin activation 契约失败：

```text
tests/test_manifest_align.py
tests/test_package_conflict_checks.py
tests/test_package_dependency_checks.py
tests/test_package_registry_merge.py
```

它们是第 5 步 domain/UI 抽取 Gate 的直接证据输入；禁止通过删测试、假模块或在 core 中反向引入 UI 来获得虚假的绿色结果。

## 7. 完成定义与交接

本基线 Gate 只有在以下内容同时完成时才可标记 complete：架构文档无“PyQt 是永久根壳”的错误承诺；层级契约和 extension 范围可被测试验证；PyQt 依赖分类清楚；Phase 7J 的文档回路独立闭合；并生成 fresh-session handoff prompt。

**唯一下一 Gate：** `Phase E1 — Package Manager domain / UI host contract extraction decision and minimal implementation`。它只处理一个可审计的耦合面，保持 L0/L1/L2/L3/L4 契约与现有 PyQt adapter 兼容；不选择新引擎壳，不做全量 UI 重写。
