# VitaLoom 引擎插件宿主架构基线（2026-07-17）

继续任何迁移、重构或功能开发前，必须把 VitaLoom 视为分层、可嵌套的框架/插件系统，而不是“一个 PyQt 编辑器项目”。

```text
L0 FrameCore（根框架）
  └─ L1 lotucosm-vitaloom（唯一一级引擎/产品大插件；自身也是下层扩展的框架）
      └─ versions/<version>/runtime（版本化运行时边界）
          ├─ L2 capability package / 纯领域能力
          ├─ L3 official/workspace/editor extension plugin（可替换宿主 adapter）
          └─ L4 project addon（只在 project-open 后发现与激活）
```

- `lotucosm-vitaloom` 是唯一 L1 引擎大插件，同时可以承载下层引擎插件。
- `vitalloom.*` 是 capability package，不得错误提升为 FrameCore/L1 plugin。
- PyQt6 是当前旧 UI-host adapter，不得作为 L0/L1 根架构或领域规则权威；不得擅自迁移到 Unity、Godot、Unreal、Electron 或其他 app shell。
- 保持 `.pond`、AI command registry、Inspector command binding、SR2D adapter、package manifest 与 project manifest。
- project addon 仅 project-open 后发现/激活，不得移入 package catalog 冷启动层。
- 每个实质 Gate 先写 `docs/superpowers/plans/`，后实施、验证、更新 `docs/mainline_status.md` 与 `docs/prompts/`；每次只命名一个下一 Gate。
- 不提交、删除、回滚或清理既有未提交迁移工作，除非用户明确要求。
