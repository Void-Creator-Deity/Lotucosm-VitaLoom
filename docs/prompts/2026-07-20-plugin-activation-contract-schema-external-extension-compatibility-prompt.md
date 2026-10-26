# Phase E17 Fresh Session Prompt

继续保持项目真实架构，不要把它改写成普通应用或把旧 PyQt UI 当引擎根：

```text
L0 FrameCore 根框架
  └─ L1 lotucosm-vitaloom
       FrameCore 唯一的引擎/产品大插件
       同时是 nested plugin-host framework
       └─ versions/1.0.0/runtime
            ├─ L2 capability/domain Module
            ├─ L3 engine extension / Host Adapter
            └─ L4 Project World addon
```

E15 已完成 Qt-free `RuntimeEventBus`；E16 已完成 `plugin_activation_context.py` 与 PluginLoader 的 activation 分流。E16 运行时 projection 只提供 `services` 和 `event_bus`，按 Host/Loader 缓存，不暴露 kernel、scene、selection、mode、canvas、widget、Qt signal、ProjectManager 或动态附件。缺省插件 metadata 仍走 exact legacy UI context；显式 `activation_context: "runtime"` 才获得 runtime projection。Downloader、CellSimulation、PsReplayOverlay 已迁移，明确依赖 UI 的 Dock/viewport/menu/theme/kernel/selection/widget 插件不迁移。

E16 证据：红测 `6 failed`；focused `50 passed`；扩展 E13–E16/plugin lifecycle/PS replay `65 passed`；本轮 loader/lifecycle/operator 回归 `48 passed, 1 skipped`；完整套件（排除当前 `.venv` 缺少 `cryptography` 的 signature 文件）`1207 passed, 25 skipped, 34 subtests passed`；四项架构门禁、6 个 E16 Python 文件 AST 与 changed-region whitespace 检查通过。

唯一下一 Gate：**Phase E17 — Plugin Activation Contract Schema, External Extension Compatibility, and Context-Kind Manifest Validation Authority**。

第一动作：先写 E17 plan 和 red tests，审计插件契约/schema 的所有权与实际消费路径，至少覆盖：

- 版本 runtime 官方插件 metadata；
- 安装级、用户级、workspace/embedded extension；
- L4 `<project>/addons/` manifest 与 project-open discovery；
- legacy 插件缺省 `legacy_ui` 的兼容诊断；
- `activation_context` 未知值、类型错误、缺失值和 reload/discovery/operator report；
- package/plugin/project manifest 与 release consistency 的交叉校验。

要求：

- 不根据 `provides` 自动推断 activation context；
- 未知值 deterministic rejection，并在 `on_load` 前失败；
- 继续保持 legacy default，给第三方/旧插件明确诊断；
- 不把 runtime projection 扩张为 god context；
- 不迁移明确依赖 kernel/widget/selection 的 UI 插件；
- 不改变 `.pond`、AI Command Registry、Inspector binding、SR2D seams、Player/export、L3/L4 lifecycle；
- 不把 L2/L3/L4 提升为并列 FrameCore 插件；
- 不选择或引入 Unity、Godot、Unreal、Electron，也不在本 Gate 选择替代 UI Host；
- 不 stage、commit、reset、restore、clean 或删除既有无关工作树内容；
- 使用仓库 `.venv/python.exe`，未获明确批准不要联网安装 `cryptography`。

阶段闭环必须包括：实现、focused/expanded/full verification、四项架构门禁、静态检查、更新 `CONTEXT.md`、`docs/mainline_status.md`、本 plan，并只命名一个下一 Gate。不要宣称整个项目已经完成。
