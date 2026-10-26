# Phase E1 完成后的接手提示（2026-07-17）

## 已完成

Phase E1 已完成：Package Manager 领域规则不再必须导入 PyQt adapter。架构为：

```text
L0 FrameCore → L1 lotucosm-vitaloom（引擎大插件，也是下层插件框架）
→ versioned runtime → L2 capability/domain → L3 workspace/editor adapter → L4 project addon
```

主要 seam：

- `runtime/builtin/editor_extensions/package_domain/catalog.py`
- `runtime/builtin/editor_extensions/package_domain/project_operations.py`
- `runtime/builtin/editor_extensions/package_manager_plugin.py`（仅 L3 PyQt adapter）

已验证：**26 passed, 1 skipped in 0.30s**，并且 AST、core boundary、GUI boundary、release consistency 与 Qt-free import smoke 全部通过。

## 当前风险

若 local artifact 安装成功而 `plugin.install` 项目命令失败，现状会报告失败且不启用，但保守保留本地 artifact；还没有跨 local storage 与 project state 的可恢复事务/回滚协议。卸载的 project command 失败则已阻止删除本地 artifact。

真实 PyQt adapter 测试必须在安装 PyQt6 的 GUI host 运行；没有 PyQt6 时应明确 skip，禁止 fake Qt。

## 唯一下一 Gate

**Phase E2 — Package local-storage / project-command recoverable transaction authority。**

开始 E2 前，先在 `docs/superpowers/plans/` 写 E2 计划，明确 authority、状态机、receipt/recovery 边界、失败路径、幂等性与“不可自动删除用户 artifact”的安全规则。保持 `.pond`、AI registry、Inspector binding、SR2D、manifests 和 L0–L4 嵌套插件架构；不要提交、回滚或清理现有 dirty/untracked 工作树。
