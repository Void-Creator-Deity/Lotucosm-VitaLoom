# Refactor Iteration Log

本文件是唯一的总迭代重构记录。阶段细节保留在 `mainline_status.md`、`prompts/`、`superpowers/` 和 `archive/`，不再为每次清理单独生成重复总结。

## Iteration 1：引擎化重构

完成日期：2026-10-21

- 完成 FrameCore → 大插件 → versioned runtime → capability/extension → Project World 分层。
- 完成 lifecycle、包/资产/项目事务和统一写锁。
- 完成 UI-host adapter 隔离、Hub/Editor/Player 入口 smoke。
- 完成 WorldBridge 字段、行为、tick、replay 和 mapping authority。
- 完成 checkpoint、脚本 rehydration、跨进程恢复和 quarantine。
- 完成 Native SR2D ABI、parity、benchmark 和 release 门禁。
- 原定 7 个交付面：**100/100**。

## Iteration 2：Native SR2D admission 修复

完成日期：2026-10-21

- 修复安装 native SR2D 后 E554 witness 被错误 quarantine 的环境漂移。
- 绑定 artifact SHA256、ABI、entropy contract、120 tick parity 和 benchmark evidence。
- E554 live GameViewport：12 个 proof 字段全部为 true。
- 三场景 120 tick：`maximum_delta=0.0`。

## Iteration 3：归档清理与恢复

日期：2026-10-23

- 对测试中间文件建立 manifest、inventory 和 cleanup log。
- 首次尝试把 docs、测试、工具和构建产物移出仓库，用户指出这是错误整理方向。
- 已按 manifest 原路恢复 prompts、plans、archive、完整 mainline、tests、tools、build、dist 和根目录文件。
- 恢复后：559 个测试模块、178 个工具模块。
- 外部临时归档已删除。

## Iteration 4：根目录逐项审计与去冗余

日期：2026-10-23

### 根目录保留

| 根项 | 处理 |
|---|---|
| `.github/` | 保留，CI 和 workflow |
| `.cursor/` | 保留规则；删除生成 `debug.log` |
| `.git/` | 保留 |
| `.venv/` | 保留，本地环境 |
| `dist/` | 保留，正式发行产物 |
| `docs/` | 保留，当前文档和历史材料 |
| `FrameCore/` | 保留，L0 宿主和产品插件 |
| `native/` | 保留，可选原生实现 |
| `tests/` | 保留有效测试 |
| `tools/` | 保留 CI、发布和维护工具 |
| `workspace/` | 保留 Project World |
| `main.py`、`player.py` | 保留入口 |
| `pyproject.toml`、`uv.lock` | 保留依赖和锁 |
| `README.md`、`START_HERE.md`、`CONTEXT.md` | 保留入口和当前上下文 |
| `AGENTS.md`、`.gitignore`、`.pylintrc`、`.python-version` | 保留工程规则 |
| `LICENSE`、`CHANGELOG.md` | 保留 |
| `requirements.txt` | 保留为 pip 兼容入口 |

### 根目录删除

- 空 `.agents/`
- 空 `.codex/`
- `.cursor/debug.log`
- `build/` 中的 PyInstaller 中间产物
- `.recovery_*` 历史恢复文件
- `1`
- `System.Management.Automation.Internal.Host.InternalHost`
- `__pycache__/`
- `lotucosm_vitaloom.egg-info/`

### 测试和工具清理

- 删除 62 个历史 E 阶段测试模块；它们的 manifest 和恢复记录保留在 `docs/archive/`。
- 删除 20 个无 CI/测试/最终依赖的历史 checker；其 manifest 保留。
- 当前有效测试：**497 个模块，3273 个收集用例**。
- 当前工具：**158 个 Python 模块**。
- CI 引用的 60 个工具全部存在。

### 测试运行规则

- `tools/run_pytest_chunked.py` 不再在仓库根目录创建 `.pytest-chunk-*`。
- 临时目录统一位于 `artifacts/pytest/`。
- `artifacts/` 已加入 `.gitignore`。
- 中断产生的 `.pytest-chunk-02-y64qh9xh` 已删除。
- 需要位于 workspace 内的测试临时工程改为 `workspace/state/test_temps/`。
- `workspace/` 根目录只保留 `experiments/`、`extensions/`、`projects/`、`state/`。

### workspace 清理

- 删除 20 个测试/调试临时项。
- 删除记录：`docs/archive/test-artifacts/2026-10-23/repository-restore/workspace-audit-deletions.tsv`。
- 根目录、workspace 和历史归档 payload 当前都没有测试残留。

### native / tests / tools 审计

- 删除 `native/sr2d_cpp/build` 构建缓存。
- 删除 `native/`、`tests/`、`tools/` 下的 `__pycache__`。
- 共删除 10 个生成目录、2774 个文件、57,474,617 bytes。
- 删除记录：`docs/archive/test-artifacts/2026-10-23/repository-restore/native-tests-tools-audit.tsv`。

清理后：

| 目录 | 文件数 | 大小 | 说明 |
|---|---:|---:|---|
| `native/` | 8 | 0.03 MiB | 只保留 C++/Rust 源码和构建配置 |
| `tests/` | 510 | 3.40 MiB | 497 个测试模块 + 测试支持文件 |
| `tools/` | 159 | 1.00 MiB | 158 个 Python 工具模块 + 支持文件 |

### Cursor Python 规则更新

- 更新 `.cursor/rules/lotucosm-comment-standard.mdc`。
- 移除对已不存在的 `docs/comment_standard.md` 的引用。
- 退役强制“职责/时机/不变量/排错”四段式模板。
- 明确注释只解释原因、边界、所有权、顺序和不变量。
- 对齐 `AGENTS.md`、`docs/architecture.md`、`docs/suite_architecture.md` 和 `docs/repository_layout.md`。

### 本轮删除统计

- 删除顶层项：101
- 删除文件：116
- 删除大小：23,375,557 bytes，约 22.3 MiB
- 删除记录：`docs/archive/test-artifacts/2026-10-23/repository-restore/root-audit-deletions.tsv`

### 当前结构

- 根目录：11 个目录、14 个文件
- `tests/`：497 个测试模块
- `tools/`：158 个工具模块
- `docs/`：782 个文件，prompts/plans/archive 保留
- `dist/`：保留正式发行产物
- `build/`：已删除
- `native/`：8 个源码文件
- `tests/`：510 个文件
- `tools/`：159 个文件

### 验证

- pytest collection：`3273 tests collected`
- 分块 runner 单 chunk：`393 passed, 1 skipped, 33 subtests passed`
- workspace 临时目录相关测试：`24 passed`
- CI 工具引用：60 个，缺失 0
- `check_core_boundaries.py`：通过
- `check_release_consistency.py`：通过
- `compileall tools tests FrameCore main.py player.py`：通过
- docs 本地链接：31 个顶层文档通过

## 当前唯一未清项

历史归档 payload 中的 68 个路径已通过管理员 ACL reset 删除，空 payload 树也已移除。

管理员清理脚本：

`docs/archive/test-artifacts/2026-10-23/finish_locked_cleanup.ps1`

执行前请确认脚本只处理 `cleanup-actions.tsv` 中的锁定路径。

## Iteration 5：真实可用性收尾

完成日期：2026-10-26

本轮不扩大重构范围，只修复“能启动但真实使用仍有断点”的问题，并完成一次真实 Editor 启动验证。

### 本轮修改

| 文件 | 修改 |
|---|---|
| `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/kernel/layout_manager.py` | 重建被乱码污染的布局管理器；恢复 Dock/Viewport 生命周期、布局保存/恢复、主题状态与菜单/工具栏贡献清理，保留 fail-closed 的视口替换语义。代码中替换字符数为 0。 |
| `tools/check_release_consistency.py` | 发布门禁清理乱码与过时仓库引用，继续校验产品/套件/manifest、样例项目锁、插件与项目目录边界、CI 原生链和 Python 版本一致性。 |
| `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/VitaLoom/simulation/ps_experiment_service.py` | 修复 PS 实验服务的项目绑定幂等性：同一项目内容未变化时重复绑定被安全接受，项目内容变化后重新绑定。 |
| `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/builtin/editor_extensions/ps_experiment_plugin.py` | PS 预设根路径不再从插件安装目录推导；优先使用宿主 `application_root` / `repo_root`，缺失时回退 `bundle_paths.application_root()`。修复 runtime projection 下的 `workspace/experiments` 定位。 |
| `FrameCore/plugins/lotucosm-vitaloom/hub/hub_window.py` | 项目位置显示为 `samples/...` 短路径，完整路径放入 tooltip；项目行增加键盘焦点状态与可见边框；简化副标题和空状态文案。 |
| `FrameCore/plugins/lotucosm-vitaloom/hub/hub_style.py` | 增加项目行焦点样式，保持 Hub 暗色视觉基线。 |
| `tests/test_layout_manager_behavior.py` | 覆盖布局持久化、Dock 恢复、视口切换/替换、插件 UI 清理和 fail-closed 清理失败。 |
| `tests/test_ps_experiment_service.py` | 覆盖同项目幂等绑定、项目内容变化重绑和 runtime projection 根路径。 |
| `tests/test_ps_experiment_dock_contribution_lifecycle.py` | 覆盖 Dock 贡献生命周期及无宿主路径字段时的 runtime projection。 |
| `tests/test_hub_smoke.py` | 覆盖短路径显示、完整 tooltip、键盘焦点状态和 Hub 基本可用性。 |

### 真实启动验证

工程：`workspace/projects/samples/pvaec-细胞演化`

日志：`artifacts/editor-real-pvaec-cell-final.log`

- 项目打开成功，活动场景为 `challenge_scene.pond`。
- 场景加载为 `12 个节点, 5 个连接`。
- `PsExperimentService` 与 PS Runtime Snapshot Host 注册成功。
- PS 实验预设加载 1 次：`workspace/experiments/pvaec_homeostasis_loop.json`。
- `PsExperimentPlugin` 加载成功，插件发现 `registered=20 activated=13 discovery_errors=0`。
- 日志无 Traceback，无 `U+FFFD` 乱码；退出后无残留 Editor Python 进程。
- 启动由验证脚本在 25 秒后主动终止，因此进程返回码为 1；这是测试终止方式，不是业务启动失败。

### 测试与门禁

- PS 根路径相关回归：`21 passed`。
- Hub smoke：`19 passed`。
- `python tools/check_core_boundaries.py`：`core boundaries OK`。
- `python tools/check_release_consistency.py`：`release consistency OK`。
- `python -B -m compileall -q FrameCore workspace tools main.py player.py`：通过。

### Hub 视觉说明

原生 Windows 平台截图 `artifacts/hub-after-final.png` 已确认中英文、项目列表、详情面板和按钮显示正常。离屏 Qt 插件的 `QFontDatabase.families()` 为空，离屏截图会出现整屏方框；这是截图后端限制，不是 Hub 运行时字体故障，因此没有为它引入虚假的字体修复。

### 边界与未完成项

- `dist/` 仍是旧发行快照，可能包含旧布局管理器；本轮未重建发行包，不能声明 `dist/` 已与源码同步。
- 本轮验证集中在 Hub 与单个真实 PVAEC 编辑工程，未替代完整回归、原生构建或全部样例工程验证。
