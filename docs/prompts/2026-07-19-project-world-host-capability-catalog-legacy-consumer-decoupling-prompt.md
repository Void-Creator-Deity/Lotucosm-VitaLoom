# Fresh Session Prompt — Phase E11 Project World Host Capability Catalog and Legacy Consumer Decoupling

继续 VitaLoom 主线。当前日期是 **2026-07-19**。先读取：

- `AGENTS.md`
- `CONTEXT.md`
- `docs/mainline_status.md`
- `docs/superpowers/plans/2026-07-19-project-world-flush-save-close-transition-authority-host-application-seam.md`
- `docs/adr/0002-first-principles-and-layering.md`
- `docs/adr/0003-suite-plugin-architecture.md`
- `EditorKernel` composition root、`EditorContext`、runtime service registry、`ProjectManager` 及所有 direct `get_project_manager` consumers

## 不可变架构

`FrameCore` 是 L0 根框架。`lotucosm-vitaloom` 是唯一 L1 引擎/产品大插件，同时自身是下层 plugin-host framework。`versions/<version>/runtime` 是版本化产品 runtime 边界；`vitalloom.*` 是 L2 capability/domain；L3 是 engine extension/Host Adapter；L4 addon 只属于一个 Project World。

PyQt6/QPainter/OpenGL 是 legacy UI-host Adapter，不是引擎根、extension authority 或新 framework。不得迁移到 Unity/Godot/Unreal/Electron，不得把 L2 Module、Project World 或某个 UI Adapter 提升为 FrameCore/L1 并列插件。

## 已完成 Gate

E10 已闭环：

- Qt-free `project_world_report.py` / `project_world_session.py` 拥有 canonical report、manifest validation、deterministic save/flush/close facts 与 atomic manifest replace；
- legacy PyQt `ProjectManager` 只应用 SceneManager/SceneViewport、EditorContext/cache、L4 teardown 和 signals/events；
- previous-World flush fail-closed，stale removed World 仅在 scene unmodified 时 warning-bearing noop；
- forged manifest target、stale project/scene preparation 在 Host mutation 前被拒绝；
- Editor Save/Discard/Cancel、Player shutdown 与标准 UI Save 消费显式 session Host capability；
- focused `26 passed`，expanded `158 passed, 1 skipped`，compatibility `80 passed`，四项 guardrail、py_compile、PyQt-blocked import/strict JSON 与 changed-region whitespace 全部通过。

## 唯一当前 Gate

**Phase E11 — Project World Host Capability Catalog and Legacy Consumer Decoupling**

先在 `docs/superpowers/plans/` 写 E11 plan 和有效 red tests，再实现。目标是移除 L3/read-model consumer 对 concrete `ProjectManager` 的散落 import，同时避免造一个更大的 god port：

1. 审计并分类所有 direct `get_project_manager` consumer：Standard UI recent/config、`plugin_runtime_ops`、package manager、GameViewport、asset dependency、evolution context、SR feedback、ProjectWizard/组合入口。区分 composition Adapter、mutating lifecycle Host、read-only current-World context、recent-project registry 与 project creation/open Interface。
2. 设计小而深的 capability catalog。至少明确：
   - `project_world_open_host`：应用已准备的 open transition；
   - `project_world_session_host`：flush/save/close；
   - read-only current Project World context/config/path Interface；
   - recent-project registry（若审计证明应独立）。
   不得把所有 `ProjectManager` 方法原样复制成一个巨型 Interface。
3. 由 Editor/Player/必要的 L3 composition root 注入或发布 capability；L2/domain Module 不得 import PyQt 或 concrete manager。one adapter 仍可作为当前默认组合，但 Interface 必须可由第二个 test Adapter 验证，避免只有名义 seam。
4. 分批迁移 consumers，先处理只读和标准 UI/plugin runtime ops，再处理 GameViewport/evolution/feedback/asset/package consumers。每批都要保持行为、错误模式和 current Project World locality，不跨到无关 rendering/native/OpenGL 重构。
5. 增加 source/import guard，防止迁移后的 consumer 回归到 concrete manager import；增加真实 PyQt Adapter test 与 Qt-free/headless capability test。
6. 保持 `.pond`、AI command registry、Inspector binding、SR2D seams、asset/package/project manifests、L3/L4 lifecycle、Hub 单 World 进程模型、Player/export 与 existing signals/events 兼容。
7. 完成相关回归、四项 guardrail、AST/import、strict JSON（若新增 report）与 changed-region whitespace 检查。

## 工作纪律

- 不 stage/commit/reset/restore/clean/delete既有 dirty 工作。
- 不用 fake/stub PyQt 制造绿色；headless tests 只验证真正 Qt-free Interface。
- 不借 consumer migration 选择新 GUI Host，也不扩张旧 PyQt authority。
- 每个 Gate 先计划、红测、实现、回归、门禁，再更新 `docs/mainline_status.md` 与恰好一个下一 prompt。
- 不得声称整个项目已经彻底完成。
