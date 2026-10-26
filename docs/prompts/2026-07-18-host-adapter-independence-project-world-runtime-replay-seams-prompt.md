# Fresh Session Prompt — Phase E8 Host Adapter Independence

继续 VitaLoom 主线。先读取：

- `AGENTS.md`
- `docs/mainline_status.md`
- `docs/superpowers/plans/2026-07-18-downstream-extension-hot-reload-watcher-lifecycle-authority.md`
- 相关 `docs/adr/`、`CONTEXT.md` 与架构文档

## 不可变架构

`FrameCore` 是 L0 根框架。`lotucosm-vitaloom` 是唯一 L1 引擎/产品大插件，同时自身是可继续插插件的下层 plugin-host framework。`versions/<version>/runtime` 是版本化承载边界；`vitalloom.*` 属于 L2 capability/domain；L3 是引擎 extension Adapter；L4 addon 只属于一个 Project World。

PyQt 是当前/旧 Host Adapter，不是根架构 authority。不得把项目迁移到 Unity/Godot/Unreal/Electron，不得在未裁定后继 Host 前粗暴删除 PyQt，也不得把 L2 Module 提升成 FrameCore/L1 插件。

## 已完成 Gate

E7 已闭环：

- Qt-free `plugin_host_reload.py`；
- candidate-first L3 hot reload；
- active dependent closure 的反向卸载与依赖优先激活；
- L3 direct reload 与 L4 Project World refresh 分离；
- canonical reload/lifecycle report；
- UI candidate/report convergence；
- project disable 回归 normal lifecycle sync；
- hot reload failure 不再错误获得 E6 project-lifecycle recovery；
- 没有新增自动 watcher；reload inspect/resolve commands 仍有意未注册。

证据：初始 `17 failed`；聚焦 `32 passed`；扩展 `49 passed, 1 skipped`；四项架构/发布门禁通过。

## 唯一当前 Gate

**Phase E8 — Host Adapter Independence for Project World and Runtime Replay Application Seams**

先写 `docs/superpowers/plans/` 下的 E8 计划和 headless 红测，再实现。只处理两条已经证实的 Host/domain 泄漏：

1. `project.create -> project_manager.ProjectManager(QObject) -> PyQt6`
2. `runtime.replay.status -> ecology_registry -> ps_experiment_service -> PyQt6`

目标是把 application/domain authority 提取为 Qt-free deep Module，并让 PyQt 成为一个 Adapter；不是选择新 GUI shell。保持 `.pond`、AI command registry、Inspector binding、SR2D seams、package/project manifests 与插件拓扑不变。

## 工作纪律

- 不 stage/commit/reset/restore/clean/delete既有 dirty 工作。
- 不 fake/stub PyQt 来制造 headless green。
- 每个 Gate 先计划、红测、实现、回归、门禁，再更新 `docs/mainline_status.md` 和下一 prompt。
- 真实 blocker 必须记录 fallback、unblock path 和唯一 next Gate。
