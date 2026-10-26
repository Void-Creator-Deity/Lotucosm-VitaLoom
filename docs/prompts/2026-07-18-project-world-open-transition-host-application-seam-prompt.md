# Fresh Session Prompt — Phase E9 Project World Open Transition Authority

继续 VitaLoom 主线。当前日期是 **2026-07-18**。先读取：

- `AGENTS.md`
- `CONTEXT.md`
- `docs/mainline_status.md`
- `docs/superpowers/plans/2026-07-18-host-adapter-independence-project-world-runtime-replay-seams.md`
- `docs/adr/0002-first-principles-and-layering.md`
- `docs/adr/0003-suite-plugin-architecture.md`
- 相关 project open、plugin lifecycle、asset Registry 与 scene tests

## 不可变架构

`FrameCore` 是 L0 根框架。`lotucosm-vitaloom` 是唯一 L1 引擎/产品大插件，同时自身是可继续插入下层插件的 plugin-host framework。`versions/<version>/runtime` 是版本化承载边界；`vitalloom.*` 是 L2 capability/domain；L3 是 engine extension/Host Adapter；L4 addon 只属于一个 Project World。

PyQt 是当前/旧 Host Adapter，不是根架构 authority。不要把项目迁移到 Unity/Godot/Unreal/Electron，不要在未选定后继 Host 前删除 PyQt，也不要把 L2 Module 提升为 FrameCore/L1 插件或把 Project World 提升成并列根框架。

## 已完成 Gate

E8 已闭环：

- Qt-free `project_world_creation.py` 成为 Project World scaffold/manifest/default `.pond` authority；
- `project.create` 不再 import `ProjectManager(QObject)`；
- `ProjectManager.create_project` 只保留 PyQt Host Adapter 的路径、recent state 与 signals；
- `ecology_registry` 从 service registry 结构能力读取 PS snapshot，不再 import concrete PyQt experiment implementation；
- `runtime.replay.status` 可在 PyQt imports 被阻断时运行；
- 最终组合回归 `83 passed in 14.68s`，四项架构/发布门禁与 AST/import checks 通过；未用 fake/stub Qt。

## 唯一当前 Gate

**Phase E9 — Project World Open Transition Authority and Host Application Seam**

先在 `docs/superpowers/plans/` 写 E9 计划和 red tests，再实现。只处理 `project.open -> ProjectManager.open_project` 已确认的 Host/application 混合：

1. 审计旧 Project World flush、manifest read/validation、active scene resolution、EditorContext mutation、SceneManager clear/load、asset Registry recovery/refresh、L4 plugin lifecycle sync、recent-project state 与 Qt/signals 的真实顺序及 failure semantics。
2. 提取 Qt-free deep Module，负责 deterministic Project World open preparation/validation/transition facts 与 canonical report；Interface 必须小，不能只是把现有函数逐行搬家。
3. 让 PyQt `ProjectManager` 成为 Host application Adapter，通过明确 seam 执行 scene/context/recent/signal side effects；不得在 Qt-free Module import EditorContext、SceneManager、PyQt 或具体插件 callback。
4. 让 `project.open` command 不再直接 import concrete `ProjectManager`。若 command 需要应用 Host state，必须通过显式 Host Adapter capability/context seam；无 Host 时要有 truthful deterministic result，不能 fake Qt。
5. 保持 `.pond`、AI command registry、Inspector binding、SR2D seams、project/package manifests、asset Registry、L3/L4 plugin lifecycle 语义与打开项目后的交互顺序。对 partial application/rollback 能力必须如实报告，不得宣称无法证明的事务回滚。
6. 使用仓库 `.venv` 跑真实 PyQt Adapter tests，同时增加 PyQt-blocked headless tests。

## 工作纪律

- 不 stage/commit/reset/restore/clean/delete既有 dirty 工作。
- 不用 fake/stub PyQt 制造 headless green。
- 每个 Gate 先计划、红测、实现、回归、门禁，再更新 `docs/mainline_status.md` 与唯一下一 prompt。
- blocker 必须记录 fallback、unblock path 与一个 next Gate。
- 不得声称整个项目已经彻底完成。
