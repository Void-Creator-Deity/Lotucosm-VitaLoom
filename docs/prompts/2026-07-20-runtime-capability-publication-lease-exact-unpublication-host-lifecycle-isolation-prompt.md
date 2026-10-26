# 2026-07-20 Runtime Capability Publication Lease, Exact Unpublication and Host Lifecycle Isolation — Fresh Session Prompt

继续 VitaLoom 主线，只执行 **Phase E13 — Runtime Capability Publication Lease, Exact Unpublication and Host Lifecycle Isolation Authority**。先读 `AGENTS.md`、`CONTEXT.md`、`docs/adr/0002-first-principles-and-layering.md`、`docs/adr/0003-suite-plugin-architecture.md`、E12 plan 尾部 completion evidence 与 `docs/mainline_status.md` 的 E12 段，再审计代码；不要从 PyQt 类名反推架构。

## 不可变架构

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime (product/runtime boundary)
          -> L2 vitalloom.* capability/domain Modules
          -> L3 engine extension / Host Adapters
          -> L4 addons scoped to one Project World
```

- `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime` 仍是产品 runtime 边界。
- PyQt6/QPainter/current OpenGL 是 legacy UI-host Adapter，不是引擎根、插件 authority 或新 framework。
- 不迁移到 Unity/Godot/Unreal/Electron，不创建与 L1 引擎大插件并列的 Project World、capability-registry 或 UI 插件根。
- 不破坏 `.pond`、AI command registry、Inspector binding、SR2D seams、package/project manifests、L3/L4 lifecycle、Player/export。
- 仓库含大量既有 uncommitted/untracked/deleted 迁移内容；不得 stage/commit/reset/restore/clean/delete，不得批量格式化、重编码或清理无关 whitespace。

## E12 已完成事实

- Qt-free `project_world_host_ownership.py` 已提供 owner-labelled lease、复用、最后释放 disposal、factory-failure cleanup 与 fail-closed retry。
- `project_world_host_composition.py` 是当前 concrete Project World Host 的 legacy composition Adapter；Editor/default Player owned，显式 Player Host borrowed。
- Project World capability cleanup 是 exact unpublication；entry points 不再访问 `ProjectManager._instance`。
- focused `8 passed`；Project World `43 passed`；Editor/Player/Hub/L3-L4 `136 passed, 1 skipped`；command/Inspector `217 passed`；rendering `140 passed, 23 skipped`；package/manifest `100 passed, 1 skipped, 17 subtests`；四项架构门禁通过。
- 排除 signature 文件的整套是 `1152 passed, 25 skipped, 34 subtests passed, 2 failed`，不能宣称全绿。一个是负载 timing 波动；另一个是 process-wide Host capability publication 顺序污染。
- signature 测试当前因 `.venv` 缺少 `cryptography` 无法收集。

## E13 首个真实问题

`GameViewport.register_as_sr_host()` 将 `SIMULATION_SR_HOST` 和 `SR_SELECTED_IDENTITY_HOST` 写入 process-wide `EditorContext.services`，但没有与 viewport 生命周期绑定的 exact unpublication。它可污染后续 Inspector default-loader 行为。其他 extension publishers 也存在按 key 盲目 `unregister()`、可能删除另一 owner replacement 的风险。

这不是“给测试补 fixture cleanup”即可关闭的测试问题，而是 L1 版本 runtime 内 L3 Host Adapter capability publication 缺少 ownership/lifecycle authority。也不要把 legacy PyQt `EditorContext.ServiceRegistry` 直接升级成引擎 framework authority。

## 第一动作

1. 在 `docs/superpowers/plans/` 新建 E13 phase plan；先记录 E12 gate、当前 full-suite 限制和唯一范围。
2. 审计所有 version-runtime `services.register()/unregister()` publisher：Project World composition、GameViewport SR hosts、PS experiment、package manager、console、downloader，以及 plugin load/unload/error/replacement 顺序。列出 owner、scope、构造失败、重复 unload、replacement 和 process restart 语义。
3. 先写 Qt-free red tests，要求一个小而深的 publication Module/lease Interface：
   - owner-labelled registration evidence；
   - exact unpublication，不删除后来 replacement；
   - constructor failure / unload / double release deterministic cleanup；
   - 至少第二个非-GameViewport Adapter 证明 seam 真实；
   - PyQt-blocked import smoke；
   - 同进程先运行 GameViewport producer 再运行 Inspector default-loader 不再污染。
4. 再决定 registration collision 是 reject、replace-with-evidence 还是可恢复 stack；不要在没有测试和生命周期事实时发明另一个 global god registry。
5. 保持现有 service keys 和 consumer lookup 兼容；优先让 legacy registry 作为 Adapter 满足 Qt-free Interface，而不是让 L2/L3 Module import PyQt `EditorContext`。
6. 实现后运行 focused、Inspector/command、SR/PS、plugin lifecycle、Project World E9–E12、Player/Hub/export、package/manifest 回归，四项架构门禁、AST/import/changed-region whitespace，并更新 `docs/mainline_status.md`。只命名一个下一 Gate。

## 不得虚称

不得宣称项目整体完成、PyQt 已移除、替代 UI Host 已选定、capability publication Module 是新 FrameCore 插件、OpenGL 已 default-ready、native acceleration 已完成，或缺少 `cryptography` 的 signature suite 已验证。
