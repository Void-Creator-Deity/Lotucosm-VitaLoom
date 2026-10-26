# Fresh Session Prompt — Phase E10 Project World Flush/Save/Close Transition Authority

继续 VitaLoom 主线。当前日期是 **2026-07-19**。先读取：

- `AGENTS.md`
- `CONTEXT.md`
- `docs/mainline_status.md`
- `docs/superpowers/plans/2026-07-18-project-world-open-transition-authority-host-application-seam.md`
- `docs/adr/0002-first-principles-and-layering.md`
- `docs/adr/0003-suite-plugin-architecture.md`
- `ProjectManager.flush_current_project/save_project/close_project`、EditorKernel shutdown、PlayerShell shutdown 及相关 tests

## 不可变架构

`FrameCore` 是 L0 根框架。`lotucosm-vitaloom` 是唯一 L1 引擎/产品大插件，同时自身是下层 plugin-host framework。`versions/<version>/runtime` 是版本化产品 runtime 边界；`vitalloom.*` 是 L2 capability/domain；L3 是 engine extension/Host Adapter；L4 addon 只属于一个 Project World。

PyQt6/QPainter/OpenGL 代码是 legacy UI-host Adapter，不是引擎根或 extension authority。不得迁移到 Unity/Godot/Unreal/Electron，不得在没有新 Host parity/rendering evidence 时删除旧 Host，也不得把 L2 Module 或 Project World 提升为 FrameCore/L1 并列插件。

## 已完成 Gate

E9 已闭环：

- Qt-free `project_world_open.py` 成为 Project World open preparation/validation authority；
- blocking manifest 与非法 scene path 在任何 Host mutation 前失败；missing scene 保持打开空场景并显式 warning；
- `ProjectManager` 只作为 concrete legacy PyQt open application Adapter；
- `project.open` 只消费显式 `project_world_open_host` capability，不再 import concrete manager；
- CLI/MCP 无 GUI Host 时返回 `project_host_adapter_unavailable` 与 truthful preparation evidence；
- application report strict JSON-safe 且有 canonical identity；
- expanded regression `114 passed, 1 skipped in 17.02s`，四项 guardrail、AST、changed-region 和 PyQt-blocked smoke 全部通过。

## 唯一当前 Gate

**Phase E10 — Project World Flush/Save/Close Transition Authority and Host Application Seam**

先在 `docs/superpowers/plans/` 写 E10 计划和有效 red tests，再实现。只处理已经确认的 Project World session persistence/close Host 混合：

1. 审计 `flush_current_project`、`_flush_before_project_switch`、`save_project`、`close_project`、EditorKernel `_flush_project_before_shutdown`、PlayerShell `closeEvent` 的真实顺序、scene modified/save、active_scene write、manifest timestamp、L4 addon teardown、EditorContext clear、signal/event 与 failure semantics。
2. 提取 Qt-free deep Module，拥有 deterministic persistence/close preparation facts、路径/manifest validation、canonical strict JSON report 与明确 error modes。不要把每个旧函数逐行包一层，也不要把 SceneManager、EditorContext、PyQt 或 plugin callback 放进 Qt-free Module。
3. 让 concrete PyQt `ProjectManager` 只作为 Host application Adapter 执行 viewport merge、SceneManager save/clear、L4 lifecycle callback、context/signal side effects；发布 truthful completed/partial/failed action report，不宣称第三方 callback 或文件系统副作用的通用 rollback。
4. Editor 与 Player shutdown 不应继续把 concrete manager 当 domain authority。通过明确的 Host capability/seam 消费 flush/close 行为；若某入口必须保留 concrete Adapter construction，需把原因和生命周期写入证据。
5. 修复审计中已确认的真实生命周期缺陷，但不得散修无关 UI：例如 manifest write 原子性、无 current World、missing/invalid manifest、scene save failure、plugin teardown unsettled、context 是否应清空 `current_project_config`、以及 project_saved/project_closed signal 的真实发布语义，都必须由测试裁定。
6. 保持 `.pond`、AI command registry、Inspector binding、SR2D seams、project/package manifests、asset Registry、L3/L4 plugin lifecycle、Hub 单 World 进程模型和 Player 行为兼容。
7. 使用仓库 `.venv` 跑真实 PyQt Adapter tests，同时增加 PyQt-blocked headless tests；完成四项 guardrail、AST/import、strict JSON 与 changed-region whitespace 检查。

## 工作纪律

- 不 stage/commit/reset/restore/clean/delete既有 dirty 工作。
- 不用 fake/stub PyQt 制造 headless green。
- 每个 Gate 先计划、红测、实现、回归、门禁，再更新 `docs/mainline_status.md` 与唯一下一 prompt。
- blocker 必须记录 fallback、unblock path 与一个 next Gate。
- 不得声称整个项目已经彻底完成。
