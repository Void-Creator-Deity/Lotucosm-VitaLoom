# 2026-07-18 VitaLoom Fresh-Session Prompt — Phase E7

## 接手目标

继续“彻底完善”主线。Phase E6 已闭环；不要重做 E5/E6，也不要把 PyQt6 当成根架构。下一阶段只进入：

> **Phase E7 — Downstream Extension Hot-Reload / Watcher Lifecycle Authority Audit and Contract Decision**

## 用户确认的不可变架构

```text
L0 FrameCore root framework
  -> L1 lotucosm-vitaloom
       唯一引擎/产品大插件，同时是可继续插插件的下层 plugin-host framework
      -> versions/<version>/runtime
           版本化承载边界，不另编号
          -> L2 vitalloom.* capability/domain packages
          -> L3 engine extension plugins/adapters
          -> L4 project addons scoped to one Project World
```

- 项目自身要做类似 Unity/Godot 的引擎，不迁移到 Unity/Godot。
- PyQt6/QPainter/OpenGL 是当前或遗留 Host Adapter，不是 authority；未选定后继 Host 前不得粗暴删除 PyQt。
- 不得把 `vitalloom.*` 提升为 FrameCore/L1 插件。
- Project World 只是 L4 addon 生命周期作用域，不是并列根框架。
- 不破坏 `.pond`、AI command registry、Inspector binding、SR2D public seams、package/project manifests。
- 不 stage/commit/reset/restore/clean/delete 既有 dirty/untracked 工作。

## Phase E6 已稳定的事实

新增 Qt-free Module：

```text
FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/
  core/VitaLoom/project/plugin_host_operator.py
```

其 Interface 已负责：

- deterministic、strict-JSON-safe live Host inspection；
- requested Project World 与 retained embedded-catalog Project World 分离；
- catalog、active、failed、discovery、lifecycle 的 canonical facts；
- `settled / blocked / failed / partial / not_run` 派生状态；
- SHA-256 `report_id`；
- project/report/action/confirmation fail-closed validation；
- Qt-free weak same-process Adapter binding。

共享命令已注册：

```text
plugin.host.inspect
plugin.host.recovery.list
plugin.host.recovery.resolve
```

唯一 E6 mutation action：

```text
retry_project_lifecycle
```

它只会：重新校验当前 report → 重新读取 `project.json` → 正常 L4 manifest discovery → discovery ready 后正常 lifecycle sync。它不会 force import/unload、绕过 protected plugin、自动改 manifest 或宣称回滚第三方 callback 副作用。

当前 `PluginLoader` 仍是 Editor/PyQt Host Adapter，但 operator/lifecycle 规则位于 Qt-free Module。新 Project World discovery 失败时，inspection 会保留“请求的新 Project World”和“仍承载旧 catalog 的 Project World”两个事实。

## E6 证据

- 初始 TDD red：`11 failed`（Module/command/Adapter Interface 尚不存在）。
- strict JSON 补强 red：`1 failed`（NaN/Infinity 未归一化）。
- 聚焦最终：`30 passed, 1 skipped in 1.00s`。
- 扩展最终：`57 passed, 1 skipped, 1 deselected in 2.07s`。
- 唯一 skip：当前 Windows 会话不能创建 L4 addon directory symlink；没有 fake filesystem。
- `project plugin model OK`
- `core boundaries OK`
- `GUI boundaries OK`
- `release consistency OK`
- `AST OK: 9 files`
- `E6 import smoke OK`
- `strict JSON smoke OK`
- targeted E6 trailing whitespace OK
- `git diff --check` exit 0，仅既有 LF/CRLF warning。

## 已知但未在 E6 散修的问题

当前环境没有 PyQt6。扩展探针明确暴露两条既有 headless Host Adapter 泄漏：

1. `runtime.replay.status -> ecology_registry -> ps_experiment_service -> PyQt6`，导致 `test_mcp_command_adapter.py::test_runtime_replay_status_helper_uses_registry_command` 失败；E6 最终集合精确 deselect 这一条并记录。
2. `project.create -> project_manager.ProjectManager(QObject) -> PyQt6`，导致 `test_ai_command_cli.py` 中 7 条既有 headless CLI 场景失败（该次探针为 `55 passed, 1 skipped, 7 failed`）。

不要用 fake/stub PyQt 掩盖。它们是后续 Host/domain seam 深化债务，不是 E6 operator 回归。

## E7 开始方式

必须先在 `docs/superpowers/plans/` 新建 E7 计划，再实现。审计重点：

- `reload_plugin`、文件 watcher、extension source refresh、project switch、`on_load/on_unload` 与 E5 lifecycle authority 是否存在并行规则；
- hot reload 是否可能绕过 manifest discovery、dependency plan、protected retention、stale report 或 callback failure isolation；
- watcher 的作用域究竟是 L3 source、L4 Project World addon，还是 UI Adapter；不得混为一个全局目录监听器；
- 是否应先只做 contract/decision，还是能安全实现最小 Qt-free watcher event Module；
- 必须保留普通生命周期作为唯一 mutation authority，除非新计划用测试证明更深 Module 的 Interface。

E7 结束时仍需：更新 `docs/mainline_status.md`、创建下一 fresh-session prompt、运行相关 tests/guardrails，并只指定一个下一 Gate。
