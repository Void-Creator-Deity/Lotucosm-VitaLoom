# VitaLoom 引擎大插件 Host 架构校准提示（2026-07-18）

继续任何实现前，遵守这份已按真实代码和用户设定校准的层级：

```text
L0 FrameCore root framework
  └─ L1 lotucosm-vitaloom
       唯一的 FrameCore 引擎/产品大插件；自身也是下层 extension 的 plugin-host framework
       └─ versions/<version>/runtime
            版本化 runtime 边界与下层插件 host
            ├─ L2 `vitalloom.*` capability package
            ├─ L3 engine extension plugin / adapter（official、installed 或 workspace source）
            └─ L4 project addon（仅 project-open 后发现并激活）
```

- FrameCore 只发现 L1 `lotucosm-vitaloom`，并通过其 manifest/Hub/version entrypoint 委托产品启动；它不 import runtime capability 或具体 UI。
- `lotucosm-vitaloom` 不是一个普通 PyQt 应用文件夹，而是可继续承载插件的引擎大插件/衍生框架。不要创建第二个平级 FrameCore 引擎插件。
- `vitalloom.*` 是 runtime capability package；即使其贡献 editor extension，也不能把它提升为 FrameCore/L1 plugin。
- project addon 只属于打开后的项目 `<project>/addons/`，不得进入 cold-start catalog 或变成全局自动启用插件。
- PyQt6/QPainter/OpenGL 是旧 UI-host adapter 实现。任何新领域规则、插件生命周期、事务恢复或 command authority 都必须 Qt-free；未来替换 UI host 时以 engine/plugin contract 为不变量。
- 不破坏 `.pond`、AI command registry、Inspector command binding、SR2D seam、package manifest 或 project manifest。
- 不 stage、commit、reset、restore、clean、删除已有 dirty/untracked 工作；每个实质 Gate 先写 plan、实施验证、更新 mainline status 与 fresh-session prompt，并只声明一个下一 Gate。

当前唯一工程 Gate：**Phase E3 — Package transaction operator recovery command surface and interlock decision**。先完成 Qt-free receipt/operator command surface；不要把 package recovery 接入 asset interlock；跨进程互斥留给独立的 Phase E4。