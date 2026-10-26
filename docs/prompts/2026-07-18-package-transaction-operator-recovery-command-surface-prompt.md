# Phase E3 完成后的接手提示（2026-07-18）

## 已完成且已验证

项目架构保持：

```text
L0 FrameCore
  → L1 lotucosm-vitaloom（唯一引擎/产品大插件，也是下层 extension 的 host framework）
    → versions/<version>/runtime（版本化运行时边界）
      → L2 vitalloom.* capability/domain
      → L3 extension adapter
      → L4 <project>/addons/（只在 project-open 后发现与激活）
```

E3 已将 package receipt recovery 暴露为 Qt-free command registry surface：

- `package.transaction.inspect`、`package.transaction.recovery.list`：只读，不为 clean project 创建 receipt metadata。
- `package.transaction.recovery.resolve`：必须携带 `project_path`、`transaction_id`、合法 `action` 和 `resolve_package_transaction:<transaction_id>:<action>` confirmation。
- install retry 只能委托 `plugin.install` authority；uninstall retry 只能删除已验证的 project-local artifact，不能重放 `plugin.uninstall`。
- relative/external/file/symlink artifact、malformed/prepared/terminal receipt、确认/动作不匹配和 workspace escape 全部 fail closed。

验证：相关 E3 回归 **45 passed, 1 skipped in 1.87s**；project plugin model、core、GUI、release checks 均通过。PyQt6 未安装导致真实 adapter contract skip；不得 fake/stub PyQt。

## 唯一下一 Gate

**Phase E4 — Dedicated package transaction cross-process interlock authority。**

开始 E4 前，先创建/更新 E4 计划。必须新增独立的 `<project>/.vitaloom/package_transaction_interlock.json` authority，覆盖 install、uninstall 与 recovery resolve 的所有 mutation seam，fail closed，并用真实第二进程测试证明拒绝与零项目写入。不得复用或合并 `asset_transaction_interlock.json`；不要把 Qt/PyQt 提升为架构根，也不要提交、回滚、删除或清理既有 dirty/untracked 工作树。