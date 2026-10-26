# VitaLoom E21 Fresh-Session Prompt

继续 Phase E21：Qt-free Project-Scoped Nested Plugin Host Orchestration and Legacy `PluginLoader` Project Adapter。

先读取 `AGENTS.md`、`CONTEXT.md`、`docs/mainline_status.md`、E20 plan 和当前工作树；第一步必须新建或更新 E21 phase plan，不能直接散改。

固定架构：

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       FrameCore 当前唯一的引擎/产品大插件
       同时是可递归扩展的 downstream plugin-host framework
       -> versions/1.0.0/runtime（版本实现承载边界）
            -> L2 VitaLoom capability/domain package
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon（仅 project-open 后发现与激活）
```

不得把 L2/L3/L4 提升为 FrameCore 并列插件。PyQt6/QPainter/OpenGL 是现有或遗留 UI Host Adapter，不是引擎根、插件 authority 或扩展规则来源；不得迁移到 Unity、Godot、Unreal、Electron 或其他 app shell。

E20 已完成：

- Qt-free `core/VitaLoom/core/runtime_plugin_host.py` 拥有 registry/discovery/dependency/callback execution；
- legacy `PluginLoader` 组合 Host，旧 state 使用同对象 alias；
- discovery/catalog/lifecycle/load/unload/candidate import 已委托 Host；
- UI contribution、command bridge、legacy editor-ready、kernel signals 与 cleanup 仍留在 Editor Adapter；
- 初始红测 `5 failed`，focused `11 passed`，expanded `54 passed`，broader `57 passed`，完整非签名套件 `1231 passed, 25 skipped, 34 subtests passed`，四项架构门禁通过；
- signature 仍因当前 `.venv` 缺 `cryptography` 无法收集。

E21 唯一目标：把 Project World 生命周期作用域下的 nested plugin orchestration 从 legacy Loader 提取为 Qt-free deep Module。重点审计并以红测约束：

1. `clear_embedded_plugins`、`scan_project_addons`、`sync_plugins_for_project`；
2. project lifecycle inspection、recovery list/resolve 与 stale-project/revision protection；
3. L4 catalog 在发现失败时保留上一个 Project World、project-open 后才发现/激活、切换时逆序卸载；
4. 与 E20 `RuntimePluginHost` 的组合 Interface，以及 legacy Loader 对外 compatibility delegation；
5. 继续调用 `plugin_host_lifecycle.py`、`plugin_host_operator.py` 等既有 authority，不复制 manifest、ID、dependency、activation 或 recovery rules。

非目标：manual hot reload orchestration、PyQt Host 替代、native acceleration、OpenGL default-ready、signature 依赖安装。保持 `.pond`、AI Command Registry、Inspector command binding、SR2D seams、package/project manifests、Player/export 和现有 L3/L4 lifecycle。

完成时必须运行 focused、expanded、完整非签名套件和四项架构门禁，记录 signature blocker，更新 E21 plan、`CONTEXT.md`、`docs/mainline_status.md`、`docs/INDEX.md`，并只命名一个后续 Gate。整个项目仍未“彻底完善”。
