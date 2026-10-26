# Phase E15 — Qt-Free Runtime Host Context Interfaces and Legacy EditorContext Adapter Isolation Authority

接手日期：2026-07-20。

## 真实架构（不可改写）

`FrameCore` 是 L0 根框架；`lotucosm-vitaloom` 是当前唯一的 L1 引擎/产品大插件，同时是可继续承载 L2/L3/L4 的 nested plugin-host framework。产品运行时边界固定为：

`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`

- L2 capability/domain Module、L3 engine extension/Host Adapter、L4 Project World addon 都留在这个 L1 插件内部，不得抬成并列 FrameCore 插件。
- PyQt6/QPainter/current OpenGL 是 legacy UI-host Adapter，不是 engine root、registry authority、plugin authority 或 framework authority。
- 不迁移到 Unity/Godot/Unreal/Electron；E15 不预选替代 UI Host。
- 不破坏 `.pond`、AI Command Registry、Inspector binding、SR2D seams、package/project manifests、Player/export、L3/L4 lifecycle。
- 工作树包含大量既有 uncommitted/untracked 迁移内容；不得 stage/commit/reset/restore/clean/delete，不得批量格式化或重编码无关文件。

## E14 已完成事实

- Qt-free `runtime_capability_registry.py` 已建立 `RuntimeCapabilityRegistry` Interface 与 `InMemoryRuntimeCapabilityRegistry` Implementation。
- L0 FrameCore registry 与 L1 runtime registry 按 owner、scope、lifetime 和 key namespace 有意隔离；没有隐式 bridge、共享 singleton 或 `FrameApi` 晋升。
- Editor、Player、CLI/headless 均有显式 registry composition seam；行为测试证明传入实例原样转发。
- `EditorContext.services` 只保留为 legacy PyQt Adapter 兼容视图；E13 publication lease 仍是 owner/transaction/exact-release authority。
- Player 已改为先绑定 registry，再构造 nested legacy Project World Host Adapter；导出 Player smoke 通过。
- E14 `15 passed`，combined focused `76 passed`，expanded `178 passed`，最终全量（仅排除 signature 文件）`1191 passed, 25 skipped, 34 subtests passed`；四项架构门禁与 `AST OK: 542 files`。
- `tests/test_package_signature_warn_only.py` 仍因当前 `.venv` 缺少 `cryptography` 无法收集。

## E15 的真实问题

E14 已把 registry 从 PyQt Module 中抽离，但 legacy `EditorContext` 仍同时承载或被当作入口访问：registry 兼容视图、event bus、kernel 引用、当前 Project World、scene、selection、mode、canvas 以及 simulation attachment。当前审计发现约 30 个 runtime 文件直接 import/use `editor_context`。其中一部分确实属于 UI Adapter，另一部分可能是 L2/L3/L4 contract 泄漏；不能把它们粗暴统一成另一个全局 context。

E15 的目标是建立足够窄、Qt-free、可由多个真实 Host Adapter 组合的 runtime Host Context Interfaces，并把 `EditorContext` 明确压回 legacy PyQt Adapter 角色。目标不是一次删除 PyQt，也不是制造新的 god context。

## 第一动作

1. 先在 `docs/superpowers/plans/` 新建 E15 plan，记录 E14 gate、full-suite/signature 证据和唯一范围。
2. 审计全部 direct `editor_context` import/use，逐项分类：
   - L1 capability registry lookup/publication；
   - event publish/subscribe；
   - Project World read/config/session facts；
   - scene/selection/mode state；
   - kernel、widget、signal、canvas 等纯 UI ownership；
   - simulation transport/coordinator attachment。
3. 对每类列出 owner、scope、lifetime、mutation authority、thread/process 语义、absence/error contract 和 Editor/Player/headless 是否真实共享。
4. 先写 Qt-free red tests。只为至少两个真实 Adapter/组合都需要的行为建立 Interface；一个 Adapter 只能证明 hypothetical seam。
5. 优先复用 E14 `RuntimeCapabilityRegistry`、Project World capability catalog、Command Registry 和已有 event/lifecycle Module；不要重新包装成万能 context，也不要复制 E13 publication owner stack。
6. legacy `EditorContext` 可以作为一个 Adapter 实现或兼容 facade，但不得继续成为 L0/L1 framework authority。UI-only state 可保留在 Qt Adapter，不要为了“抽离”把 widget/signal 泄漏进 Qt-free Module。
7. 分批迁移普通 L2/L3/L4 consumer；每批必须有 Editor/Player/headless 或第二 Adapter 的行为/生命周期证据，并保持现有插件-facing context 兼容。
8. 运行 focused、Project World、command/Inspector、SR/PS、plugin lifecycle、Player/Hub/export、package/manifest、完整套件（诚实排除 signature）、四项架构门禁、Qt-blocked import、AST 与 changed-region whitespace。
9. 更新 `CONTEXT.md`、`docs/mainline_status.md`、E15 plan，并只命名一个下一 Gate。

## 不得虚称

不得宣称项目整体完成、PyQt 已移除、替代 UI Host 已选择、`EditorContext` 已完全删除、E15 context 是新的根框架、L2/L3/L4 已变成 FrameCore 插件、signature suite 已验证、OpenGL 已 default-ready 或 native acceleration 已完成。
