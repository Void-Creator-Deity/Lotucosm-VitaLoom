# Phase E2：Package Local-Storage / Project-Command Recoverable Transaction Authority

**日期：** 2026-07-17  
**状态：** completed  
**前置 Gate：** Phase E1 Package Manager domain / UI-host contract extraction 已完成。  
**唯一目标：** 让 package 安装、卸载与 manifest artifact 对齐在本地 artifact 存储和项目 `plugin.install` / `plugin.uninstall` command authority 之间拥有可审计、可恢复、幂等且不误删用户内容的事务边界。

## 1. 当前缺陷（已审计）

当前 install 的顺序是 `local install(record_project_state=False) → plugin.install`。当本地解包成功而项目命令失败时，本地 artifact 可能留下而 project state 未记录；E1 已确保不会虚报成功，但还不能恢复。

当前 uninstall 的顺序是 `plugin.uninstall → local uninstall(record_project_state=False)`。项目命令会先删除 `package_state.installed`，而旧本地卸载实现从该 state 查找路径，因此真实路径可能丢失并退化为 `not_installed`，留下 orphan artifact。

## 2. authority 与状态机

- 项目 package state 的唯一写入 authority 仍是 project command registry；底层 local-storage 操作不得写 project state。
- 每次跨界操作先创建 durable receipt：`<project>/.vitaloom/package_transactions/<transaction_id>.json`。receipt 是恢复 authority，不是第二套 package state。
- receipt 只允许位于当前 project 的 `.vitaloom/package_transactions`，以原子写入和严格 transaction id/path 校验维护；不跟随 symlink，也不接受目录逃逸。
- install 状态：`prepared → local_applied → project_applied → completed`；项目命令失败进入 `failed_recoverable`，默认只允许重试 project command，绝不自动删除已安装 artifact。
- uninstall 状态：`prepared → project_applied → local_applied → completed`；在 project command 前捕获本地 artifact snapshot。项目命令成功而 local delete 失败时进入 `failed_recoverable`，只允许重试本地清理；不得回写项目安装状态。
- terminal receipt 可保留作审计；recovery list 只返回 `prepared`、`local_applied`、`project_applied`、`failed_recoverable` 等非终态。

## 3. 实施切面

1. 新增 Qt-free package transaction receipt/store 模块：schema、原子 receipt、inspection、recovery listing 和严格状态转换。
2. 为 `PackageOperationService` 增加非破坏的本地 artifact snapshot/probe 与基于已捕获 snapshot 的删除能力；不得通过已被 project command 删除的 package state 重新推断路径。
3. 扩展 `PackageProjectOperations`：install、uninstall、manifest align 均使用 receipt；结果返回 transaction id、stage、recovery action，而不是将失败伪装为完成。
4. 添加显式 recovery API：install 仅 retry project install；uninstall 仅 retry local removal。terminal、错误 action、artifact 缺失或 receipt 损坏均 fail closed。
5. 在 PyQt adapter 中仅接入 transaction store/用户反馈；不将 receipt 规则复制进 UI。

## 4. 不变量

- 保持 L0 FrameCore → L1 `lotucosm-vitaloom` → versioned runtime → L2 domain / L3 adapter / L4 project addon 架构。
- 不迁移 UI 宿主；PyQt 继续是当前 L3 adapter。
- 保持 `.pond`、AI command registry、Inspector command binding、SR2D、package/project manifests。
- 不自动删除 local artifact 以掩盖 `plugin.install` 失败；只有 operator 发起、receipt 验证通过的明确 recovery path 才可删除。
- 不提交、回滚、删除或清理既有 dirty/untracked 工作树。

## 5. 验收证据

- Qt-free tests 覆盖 receipt 创建/原子更新/路径拒绝、install command-failure recovery、uninstall snapshot path preservation、local-delete failure recovery、重复 recovery 幂等性、损坏 receipt fail-closed。
- 现有 package catalog/domain/manifest align/installer pipeline tests 仍通过。
- `check_core_boundaries.py`、`check_gui_boundaries.py`、`check_release_consistency.py` 和 package-domain import smoke 通过。
- 真实 PyQt GUI 测试若当前环境无 PyQt6 必须明确 skip，并记录 unblock path。

## 6. 非目标

- 不做包下载器、自动垃圾回收、后台 watcher/hot reload、跨机器同步、自动删除未知 artifact 或全量 package UI 重写。
- 不把 asset transaction receipt 与 package receipt 混成一个未审计的通用事务框架。

## 7. 完成记录（2026-07-18）

### 已实现

- 新增 `builtin.editor_extensions.package_domain.package_transactions`：project-local、Qt-free durable receipt store，路径为 `<project>/.vitaloom/package_transactions/<transaction_id>.json`。它使用独占创建、原子替换、receipt 结构校验、无 symlink 目录/receipt 拒绝、严格 transaction id，并保留事件历史。
- `PackageProjectOperations.install_package` 在 local install 前创建 receipt；local artifact 已写而 `plugin.install` 失败时标记 `failed_recoverable`，恢复动作只能是 `retry_project_install`。artifact 消失时 fail closed 到 `manual_review`，不会自动删除或伪造项目状态。
- `PackageProjectOperations.uninstall_package` 在 `plugin.uninstall` 前捕获本地 artifact snapshot；项目状态清除后仍使用该 snapshot 删除本地 artifact。local delete 失败时只允许 `retry_local_uninstall`，不会重复项目命令或把项目安装状态写回。
- `PackageOperationService` 增加安全 snapshot/probe/删除接口，删除仅允许当前 project 的 `packages/` 内真实目录；外部路径、symlink/异常路径与文件路径都 fail closed。
- manifest artifact 对齐复用同一 install transaction authority；L3 PyQt adapter 通过既有 domain 调用自动获得真实 project receipt，而没有复制事务规则。
- `prepared` receipt（例如副作用后 receipt 更新无法确认的崩溃窗口）会被列出，但只返回 `manual_review`，绝不猜测并重放 command。terminal receipt 不能重放。

### 验收证据

```text
python -B -m pytest -q <15 个 package/project 相关测试文件>
55 passed, 1 skipped in 2.19s

AST OK
core boundaries OK
GUI boundaries OK
release consistency OK
package transaction domain import OK
```

新测试证明：install 项目命令失败后的 receipt/retry、artifact 丢失 fail-closed、uninstall command 后本地 snapshot 删除、local delete 失败的只本地 recovery、terminal receipt 不重放、损坏 receipt/path escape 拒绝、manifest artifact 对齐 receipt，以及真实 `PackageOperationService` 在 project state 已清除时仍能删除已捕获 artifact。

### 环境边界与未完成项

- 当前 Python 3.13.5 环境缺少 PyQt6；真实 adapter 合同测试仍明确 skip。Qt-free domain 与真实 project-service sequencing 已执行；解阻路径是装有 PyQt6 的 GUI host 运行同一 adapter 测试，不能 fake Qt。
- E2 不实现跨进程 package transaction interlock、自动 artifact 垃圾回收、自动删除 operator 未确认的 orphan artifact、包下载器重写或 UI recovery 面板。receipt 的 prepared 状态刻意要求 manual review，避免在不确定 crash 窗口造成二次破坏。

**本 Gate 结论：** completed。project command registry 仍是 project-state 唯一 authority；local artifact 只经 receipt 证明的本地操作改变。

**唯一下一 Gate：** Phase E3 — Package transaction operator recovery command surface and cross-process interlock decision。
