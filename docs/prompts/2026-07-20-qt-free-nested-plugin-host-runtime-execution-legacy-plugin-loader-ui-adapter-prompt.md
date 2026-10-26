# VitaLoom E20 Fresh-Session Prompt

继续 Phase E20：Qt-free Nested Plugin Host Runtime Execution Authority and Legacy `PluginLoader` UI Contribution Adapter。

先读取 `AGENTS.md`、`CONTEXT.md`、`docs/mainline_status.md`、E19 plan，并以当前工作树为准。保持用户确认的递归框架/插件拓扑：

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom
       FrameCore 中唯一的引擎/产品大插件
       同时是 downstream nested plugin-host framework
       -> versions/1.0.0/runtime（版本实现承载边界，不另升一层）
            -> L2 VitaLoom capability/domain package
            -> L3 engine extension / Host Adapter
            -> L4 Project World addon
```

PyQt6/QPainter/OpenGL 仅是现有或遗留 UI Host Adapter，不是引擎根、插件 authority 或扩展规则来源。不得把 L2/L3/L4 提升为并列 FrameCore 插件，也不得迁移到 Unity、Godot、Unreal、Electron 或其他 app shell。

E19 已完成 Qt-free runtime plugin lifecycle Interface：

- `IRuntimePlugin`、`IEntityTypeProvider`、`IComponentTypeProvider` 位于 Qt-free runtime contract；
- legacy `IEditorPlugin` 保持兼容并只增加 editor-ready；
- discovery/load/unload/hot-reload candidate 已接受 `IRuntimePlugin`；
- Downloader、CellSimulation、PS Replay Overlay 三个 runtime 插件已脱离 `kernel.plugin_interfaces`；
- 完整套件（排除当前缺 `cryptography` 的 signature 文件）为 `1226 passed, 25 skipped, 34 subtests passed`，四项架构门禁通过。

E20 只处理 nested plugin Host 的执行权威：

1. 审计 `core/VitaLoom/kernel/plugin_loader.py`，把职责明确分为：
   - Qt-free Host：discovery/import、实例构造、E17 metadata/activation validation 调用、registry/catalog ownership、activation/deactivation callback、确定性 failure facts；
   - legacy UI Adapter：LayoutManager contribution、Dock/Viewport/Menu/Theme、`on_editor_ready`、kernel signals、具体 Editor context projection。
2. 先写 headless/runtime 红测，再提取最小而深的 Qt-free Module（候选 `core/VitaLoom/core/runtime_plugin_host.py`，最终命名以审计为准）。
3. legacy `PluginLoader` 最终成为 Editor UI contribution / editor-ready / Host signal Adapter，不再是唯一 runtime execution authority。
4. 不复制或替代 E17 `plugin_activation_contract.py`、`project/plugin_host_lifecycle.py`、`project/plugin_host_operator.py` 或 E18 viewport cleanup。
5. 不改变 plugin ID、dependency ordering、official/user/embedded/L4 discovery、protected plugin 规则、activation context、reload/unload report、manifests、Player/export 或 L3/L4 lifecycle。
6. 运行 focused/expanded/full 回归和四项架构门禁；明确记录 signature 环境 blocker；更新 E20 plan、`CONTEXT.md`、`docs/mainline_status.md`、`docs/INDEX.md` 与唯一下一 Gate prompt。

必须诚实区分：已稳定、开发中、未验证、环境阻塞。整个项目尚未完成，不得因 E20 完成而宣称 native/OpenGL/legacy UI Host 替代或全项目完成。
