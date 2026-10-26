# Phase E16 Fresh Session Prompt

继续保持 `L0 FrameCore -> L1 lotucosm-vitaloom 唯一引擎/产品大插件兼 nested plugin-host framework -> versioned runtime -> L2/L3/L4`。E15 已完成 Qt-free Host-scoped string event Interface，legacy PyQt EventBus 只是 signal Adapter；完整套件（排除缺少 cryptography 的 signature 文件）为 `1200 passed, 25 skipped, 34 subtests passed`。

唯一下一 Gate 是 **Plugin Activation Context Projection and Legacy UI Context Compatibility Authority**。先写 E16 plan，再审计每个真实 `plugin.on_load(editor_context)` 对 registry、event bus、Project World、commands、selection、kernel/widget 的实际需求。只为至少两个真实非 UI 插件共同需要的能力建立窄 Qt-free projection；Dock/viewport/editor-only 插件继续获得显式 legacy UI context Adapter。不得创建万能 RuntimeHostContext，不得改变插件层级，不得破坏 .pond、AI Command Registry、Inspector binding、SR2D、manifest、Player/export 或 L3/L4 lifecycle。
