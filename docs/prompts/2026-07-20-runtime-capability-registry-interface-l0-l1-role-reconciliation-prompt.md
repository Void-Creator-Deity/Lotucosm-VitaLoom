# 2026-07-20 Runtime Capability Registry Interface and L0/L1 Registry Role Reconciliation — Fresh Session Prompt

继续 VitaLoom 主线，只执行 **Phase E14 — Runtime Capability Registry Interface and L0/L1 Registry Role Reconciliation Authority**。先读 `AGENTS.md`、`CONTEXT.md`、`docs/architecture.md`、`docs/suite_architecture.md`、`docs/adr/0002-first-principles-and-layering.md`、`docs/adr/0003-suite-plugin-architecture.md`、E13 plan 的 completion evidence 与 `docs/mainline_status.md` 的 E13 段，再审计实际代码；不要从 `ServiceRegistry` 同名、PyQt 类名或当前 singleton 反推最终架构。

## 不可变架构

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom sole engine/product plugin and nested plugin-host framework
      -> versions/<version>/runtime (product/runtime boundary)
          -> L2 capability/domain Modules
          -> L3 engine extension / Host Adapters
          -> L4 addons scoped to one Project World
```

- 固定产品 runtime：`FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`。
- L0 只负责 FrameCore/Suite plugin discovery、manifest、版本选择、lifecycle、L0 服务与事件交互；不得 import L1 runtime internals。
- L1 `lotucosm-vitaloom` 是当前唯一引擎/产品大插件，同时可作为下层 plugin-host framework；L2/L3/L4 不得抬成并列 FrameCore 插件。
- PyQt6/QPainter/current OpenGL 是 legacy UI-host Adapter，不是 engine root、registry authority、plugin authority 或 framework authority。
- 不迁移到 Unity/Godot/Unreal/Electron，不选择替代 UI Host。
- 不破坏 `.pond`、AI command registry、Inspector binding、SR2D seams、package/project manifests、L3/L4 lifecycle、Player/export。
- 工作树含大量既有 uncommitted/untracked 迁移内容；不得 stage/commit/reset/restore/clean/delete，不得批量格式化、重编码或清理无关 whitespace。

## E13 已完成事实

- Qt-free `capability_publication.py` 已提供 owner-labelled transactional publication、失败回滚、exact-object unpublication、later replacement 保留、absence evidence 与幂等 release。
- GameViewport、PS、Package Manager、Downloader、Console panel 和 console logging handler 已迁移；未发现残留直接 runtime publisher。
- `GameViewport()` 构造只创建 Adapter；Editor/Player composition 设置 Host context 后才显式发布，卸载/关闭只撤销自己拥有的 exact publication。
- focused `51 passed`；同进程污染回归 `38 passed`；Player/Project World `19 passed`；全量排除 signature 为 `1176 passed, 25 skipped, 34 subtests passed`；四项架构门禁与 `AST OK: 274 files`。
- signature 测试仍因当前 `.venv` 缺少 `cryptography` 无法收集。

## E14 的真实问题

仓库当前有两个同名但尚未正式裁定关系的 Module：

- `FrameCore/service_registry.py::ServiceRegistry`：文档称为 Frame/Suite 之间的最小服务发现接口，但当前 `FrameApi` 只携带 app/resource/suite 与版本/entry 委托行为，没有把它形成明确的 runtime handoff 契约。
- `runtime/core/VitaLoom/core/editor_context.py::ServiceRegistry`：L1 runtime 的 capability publisher/consumer 广泛通过 `EditorContext.services` 使用它；但 `EditorContext` 继承 `QObject`，属于 legacy PyQt Host Adapter 和全局编辑器状态容器。

未来非 Qt Host 要保留 L2–L4 engine-plugin contracts，就需要一个 Qt-free、可由 Editor/Player/headless composition 提供的 registry Interface；但“两个类同名”不是合并依据。L0 registry 应继续服务 FrameCore/Suite 层职责，L1 作为 nested plugin-host framework 也可能拥有独立的 runtime capability registry。E14 必须用真实 owner/scope/lifetime/key 与 handoff 证据决定：保持隔离、建立显式 bridge，或共享一个最小 Protocol。

## 第一动作

1. 在 `docs/superpowers/plans/` 新建 E14 phase plan，先记录 E13 gate、当前 full-suite/signature 限制与唯一范围。
2. 审计并画出 registry ownership/lifetime 表：
   - `FrameCore/service_registry.py`；
   - `FrameCore/lifecycle.py::FrameApi` 与 L1 lifecycle plugin；
   - Hub、runtime editor、Player、CLI/MCP/headless entry handoff；
   - `editor_context.py::ServiceRegistry` 与 `get_editor_context()` singleton；
   - `service_keys.py` 及全部 `get_editor_context().services` / `context.services` publisher、consumer；
   - Project World、L3 extension 与 L4 addon load/unload 对 registry 的依赖。
3. 为两个 registry 分别列出 owner、scope、lifetime、key namespace、process/thread 语义、replacement、unload/disposal 与 absence/error contract；先找真实交集，再决定是否需要 bridge。
4. 先写 headless red tests，要求 L2/L3 consumer 能通过 Qt-free registry Protocol/composition 获取 capability，且 import 不需要 PyQt。至少证明 Editor/Player/headless 中两个真实 Adapter/composition，避免只有一个 Adapter 的假 seam。
5. 保持 E13 publication lease 单一职责：registry Interface 负责 lookup/register/unregister 能力契约；publication lease 继续负责 ownership、事务发布和 exact unpublication。不要重复实现 owner stack 或 release 逻辑。
6. 不预设把 L0 registry 注入所有 runtime，也不预设删除 L1 registry。若选择 bridge，必须是显式、最小、可测试且不让 L0 import runtime keys/implementation；若保持隔离，必须记录为何这是有意的层级隔离而非偶然重复。
7. 分批迁移，不把 `FrameApi` 或 `EditorContext` 扩张成 god context，不创建第三个 process-global singleton，不把 registry Interface 变成 Project World 根。
8. 实现后运行 focused headless/import tests、E13 publication lifecycle、Project World E9–E13、command/Inspector、SR/PS、plugin lifecycle、Player/Hub/export、package/manifest 回归，四项架构门禁、AST 与 changed-region whitespace；更新 `CONTEXT.md`、`docs/mainline_status.md`，只命名一个下一 Gate。

## 不得虚称

不得宣称项目整体完成、PyQt 已移除、替代 UI Host 已选择、两个 registry 必须合并、L0 已成为 runtime capability authority、signature suite 已验证、OpenGL 已 default-ready 或 native acceleration 已完成。
