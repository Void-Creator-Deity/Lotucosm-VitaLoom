# VitaLoom E19 Fresh-Session Prompt

继续 Phase E19：Qt-free Runtime Plugin Lifecycle Interface and Legacy `IEditorPlugin` Adapter Compatibility Authority。

先读取 `AGENTS.md`、`CONTEXT.md`、`docs/mainline_status.md`、E18 plan，并以当前工作树为准。保持固定拓扑：

```text
L0 FrameCore
  -> L1 lotucosm-vitaloom 唯一引擎/产品大插件兼 nested plugin-host framework
      -> versions/1.0.0/runtime
          -> L2 capability/domain
          -> L3 extension / legacy UI Host Adapter
          -> L4 Project World addon
```

E18 已完成 Editor/Player viewport capability cleanup。E19 只处理 plugin lifecycle contract：

1. 审计所有 `IEditorPlugin` 子类、`PluginLoader` 的 `issubclass`/实例化/metadata/`on_load`/`on_unload`/reload 假设。
2. 区分非 UI runtime plugin lifecycle 与 Dock/Viewport/Menu/Theme 等 legacy PyQt provider interfaces。
3. 先写 Qt-free red tests，再提取最小 runtime plugin lifecycle Interface；现有 `IEditorPlugin` 必须继续兼容。
4. 不改变 manifest、plugin ID、dependency ordering、activation_context、L4 discovery、hot reload、operator report。
5. 不创建 god context，不迁移到其他 app shell，不把 L2/L3/L4 提升为并列 FrameCore 插件。
6. 跑 focused/expanded/full（明确 signature blocker）和四项架构门禁，更新计划、状态、CONTEXT 和下一 prompt。

必须诚实区分：已稳定、开发中、未验证、环境阻塞。完成 E19 后只命名一个下一 Gate。
