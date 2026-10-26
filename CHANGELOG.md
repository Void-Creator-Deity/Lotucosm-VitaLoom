# Changelog

## 2026-10-26

### Engine usability closure

- 恢复并重建布局管理器，覆盖 Dock/Viewport 生命周期、布局保存恢复、主题状态与贡献清理。
- 修复 PS 实验服务的项目绑定幂等性，以及 runtime projection 下的 PS 预设根路径定位。
- 优化 Hub 项目路径显示、完整路径 tooltip、键盘焦点和空状态文案。
- 更新 release consistency、core boundaries 与 Hub/PS 相关回归覆盖。
- 完成一次真实 PVAEC Editor 启动验证，模拟日志无 Traceback、乱码和残留进程。
- 新增 [2026-10-26 更新说明](docs/release_notes_2026-10-26.md)。

### Repository and release documentation

- README、文档索引和项目元数据指向实际 GitHub 仓库。
- 本机 Hub 项目列表和截图状态移出版本控制。
- 本地 `.history/` 快照不再进入 Git，修复干净检出的 release consistency 门禁。
- Windows SR2D 原生构建在 checkout 前启用 Git 长路径支持。
- 明确当前源码可用性验证范围；`dist/` 仍未重建，不作为本次同步产物。

## 2026-10-23

### Repository structure

- 完成根目录逐项审计。
- 删除 62 个历史 E 阶段测试模块。
- 删除 20 个无 CI、测试或最终证据链依赖的历史 checker。
- 删除 `build/`、根目录 recovery 文件、异常空文件、缓存和历史测试 payload。
- 保留 `dist/`、docs、prompts、plans、完整 mainline 和正式入口。
- 根目录收敛为 11 个目录、14 个文件。
- 新增 [Refactor Iteration Log](docs/refactor_iteration_log.md)。

### Test and tool hygiene

- `tools/run_pytest_chunked.py` 的临时目录改为 `artifacts/pytest/`。
- 禁止在仓库根目录生成 `.pytest-chunk-*`。
- 清理 20 个 `workspace/` 测试/调试临时项。
- workspace 内测试工程统一进入 `workspace/state/test_temps/`。
- workspace 根目录只保留 `experiments/`、`extensions/`、`projects/`、`state/`。
- 删除 native build cache 和 native/tests/tools 下全部 `__pycache__`。
- 三目录审计共删除 2774 个生成文件、约 54.8 MiB。
- 更新 Cursor Python 注释规则，退役强制四段式模板并对齐当前架构和目录规范。
- 新增 `docs/repository_layout.md` 根目录和命名规则。
- 当前测试模块：497。
- 当前工具模块：158。
- 当前收集用例：3273。

### Verification

- 分块 runner 单 chunk：393 passed, 1 skipped, 33 subtests passed。
- workspace 临时目录相关测试：24 passed。
- CI 工具引用：60 个，缺失 0。
- core boundaries：通过。
- release consistency：通过。
- compileall：通过。

### Remaining

- 根目录、workspace 和历史归档 payload 已无 ACL 锁定测试残留。

## 2026-10-21

- 引擎化重构完成，7 个交付面合计 100/100。
- Native SR2D E554 admission evidence 修复完成。
- CPython 3.11/3.12 C++ wheel、ABI、120 tick parity 和 benchmark 准入完成。
- WorldBridge、checkpoint、事务锁和统一写锁证据闭环完成。

详细历史见 [docs/mainline_status.md](docs/mainline_status.md) 和 [docs/refactor_iteration_log.md](docs/refactor_iteration_log.md)。
