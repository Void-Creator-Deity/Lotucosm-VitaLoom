# VitaLoom 引擎化重构完成记录

日期：2026-10-23

状态：**已完成**

计划内完成度：**100/100**

## 结论

本次重构把项目从“功能可运行，但跨层边界和运行证据主要依赖约定”推进为：

- 宿主、产品插件、版本 runtime、能力包和 Project World 分层明确。
- 插件、包、项目 lifecycle 和写入事务有统一 authority。
- PyQt6 收回为 UI-host adapter，不再是引擎根。
- WorldBridge 的字段、行为、tick、replay 和 mapping 边界可重验。
- checkpoint、脚本恢复和跨进程重建具备原子性与 quarantine 路径。
- Native SR2D 只有在 build、import、ABI、entropy、parity 和 benchmark 同时成立时才能准入。
- uv 环境、分块回归、入口 smoke 和发行门禁形成可复现闭环。

`100%` 只表示原定引擎化重构交付面完成，不代表所有未来产品功能、跨平台 native parity 或任意第三方扩展能力都已实现。

## 权威记录

| 记录 | 用途 |
|---|---|
| [refactor_progress.md](refactor_progress.md) | 固定 100 分进度口径和 7 个交付面 |
| [refactor_iteration_log.md](refactor_iteration_log.md) | 唯一总迭代记录和根目录审计结论 |
| [mainline_status.md](mainline_status.md) | 长周期阶段、证据、失败模式和边界总账 |
| [archive/test-artifacts/2026-10-23/README.md](archive/test-artifacts/2026-10-23/README.md) | 测试中间文件归档、manifest 和锁定项 |

## 七个交付面

| 交付面 | 权重 | 结果 |
|---|---:|---|
| FrameCore → 大插件 → versioned runtime → capability/extension → Project World | 15 | 完成 |
| Plugin/package/project lifecycle 与事务 authority | 15 | 完成 |
| UI host adapter 隔离与入口可运行性 | 10 | 完成 |
| WorldBridge 字段、行为、tick、replay、mapping authority | 25 | 完成 |
| Portable checkpoint、脚本 rehydration、跨进程 atomicity | 15 | 完成 |
| Native SR2D / OpenGL 与功能、parity、benchmark 证据 | 10 | 完成 |
| 全量回归、可复现环境与发行门禁 | 10 | 完成 |
| **合计** | **100** | **100/100** |

## 最终架构

```text
FrameCore
  → lotucosm-vitaloom 大插件
  → versions/1.0.0/runtime
  → builtin 能力包 / workspace extensions
  → Project World
```

- `FrameCore/` 只承担 L0 宿主职责。
- `lotucosm-vitaloom` 是唯一 L1 产品大插件和递归插件宿主。
- `versions/1.0.0/runtime/` 是产品 runtime。
- `runtime/core` 保持引擎/插件 contract；PyQt6、QPainter 和 OpenGL 属于 UI-host adapter。
- `workspace/projects/` 保存 Project World；项目状态不写回安装目录。
- `.pond`、manifest、公共导入和现有项目/能力包语义保持兼容。

## 已完成的关键能力

### 宿主与生命周期

- 插件发现、激活、依赖、服务、命令和关闭路径统一。
- 包事务、项目锁、资产事务和 Project World 写入接入统一 interlock。
- 支持同线程重入、跨进程拒绝、owner nonce 校验和显式 stale-lock recovery。

### UI host adapter

- Hub、Editor、Player 入口有 offscreen smoke。
- Qt/UI 逻辑不进入核心 runtime authority。
- 不再创建第二套 GameViewport tick、Pond update 或项目生命周期。

### WorldBridge

- 字段 round-trip、行为路由、串行 tick、next-tick replay 和 mapping audit 可复验。
- 输入、共享时钟、pause/reset epoch、SR/PS RNG 流和 draw order 有独立 witness。
- 声明范围内 `silent_loss_cells=[]`，同时保留不可移植字段的永久 do-not-claim。

### Checkpoint 与脚本

- checkpoint 使用 project identity、source bundle digest、project lock 和 `fsync + os.replace` 原子写入。
- 独立子进程可重建 SR 结构、PS Pond、bridge identity、输入、RNG 和下一 tick。
- source missing、digest/trust drift、路径逃逸和 tamper 均整体 quarantine。
- portable artifact 只允许 relative path + SHA256，不嵌入或执行 Python source、bytecode、pickle 或 executable blob。

### Native SR2D

- C++ ABI v1 在 CPython 3.11 和 3.12 完成真实 wheel build/import。
- default、dense、sparse 三场景各 120 tick，Python oracle 与 native 的 `maximum_delta=0.0`。
- E554 将 shared randomness 边界绑定到当前 artifact SHA256、ABI、entropy contract、parity 和 benchmark admission evidence。
- 证据缺失或漂移时保持 quarantine；Python reference path 始终是 fallback。

### 环境与回归

- 正式 `.venv` 由 uv 管理，`conda_meta_present=false`，`uv.lock` 无 drift。
- Windows Qt 全量回归使用分块 runner，避免单进程 native 崩溃影响整体结果。
- 历史正式全量结果为 `3568 collected / 3534 passed / 34 skipped`。

## 最终审计修复

安装 native SR2D 后，旧 E554 witness 曾因环境变化进入 quarantine。最终修复增加了可重验的 native admission evidence：

- 绑定当前 extension module。
- 绑定 artifact SHA256。
- 绑定 ABI v1 和 entropy contract `none`。
- 绑定三组 120 tick zero-delta parity。
- 绑定 benchmark 收益和 Python fallback 身份。

修复后的 live GameViewport 结果为 `native_closure_mode=admitted_native_contract`，12 个 proof 字段全部为 true；tick merge、full replay 和 default ready 仍保持 false。

## 最终验证

| 验证 | 结果 |
|---|---|
| Native admission / entropy / E554 定向测试 | `29 passed` |
| E554 live GameViewport checker | 退出 `0`，proof 全 true |
| E560-E567 checker 级联 | 全部 PASS |
| Native strict admission，`--repeats 3` | 三场景 120 tick `maximum_delta=0.0` |
| Native benchmark | default `31.23x`、dense `5.47x`、sparse `6.15x` |
| `check_core_boundaries.py` | `core boundaries OK` |
| `check_release_consistency.py` | `release consistency OK` |
| environment provenance | uv 环境、无 Conda metadata、无 lock drift |
| compileall / diff check | 通过 |

## 测试中间文件归档

- 归档目录：[archive/test-artifacts/2026-10-23/](archive/test-artifacts/2026-10-23/)
- 已移动：`111` 个顶层项，`1674` 个文件，`32,278,634` bytes。
- 保持原位：`69` 个 Windows ACL 锁定项。
- 移动失败：`0`。
- 逐项来源、目标、大小、文件数、时间和状态见 [manifest.tsv](archive/test-artifacts/2026-10-23/manifest.tsv)。
- 汇总统计和锁定项清单见 [inventory.json](archive/test-artifacts/2026-10-23/inventory.json)。
- 根目录审计后，不可复用载荷文件已清零；当前清理事实见 [cleanup-record.md](archive/test-artifacts/2026-10-23/cleanup-record.md)。
- 已删除 62 个历史 E 阶段测试模块和 20 个无最终依赖的历史 checker。
- 当前活跃测试为 497 个模块、3273 个收集用例；工具为 158 个模块。
- 当前根目录、workspace 和历史归档 payload 都没有活动测试残留。

归档只保存测试/checker 中间载荷，不作为当前架构、实现或运行入口的权威依据。

## 永久边界

- 不声明任意外部 executable source 可安全执行。
- 不声明任意第三方绕过正式 API 的无锁写入会被拦截。
- 不声明跨平台 native parity；当前正式证据是 Windows CPython 3.11/3.12。
- 不声明未配置能力、未来产品功能和所有编辑器 UI 外延已经完成。
- 远端 Windows CI workflow 尚未获得实际运行回执；本机双 Python matrix 已完成真实验证。

## 工作树说明

仓库保留大量既有未提交改动和历史文件。本次记录整理没有 stage、commit、revert、clean 或格式化无关文件。
