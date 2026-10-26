# 2026-10-26 更新说明

这是一次源码维护更新，不是重新发布的发行包。当前 GitHub 源码对应引擎化架构与真实可用性收尾结果，`dist/` 仍是旧发行快照，不在本次同步范围内。

## 更新内容

### 布局与编辑宿主

- 重建被乱码污染的布局管理器。
- 恢复 Dock/Viewport 生命周期、布局保存与恢复、主题状态、菜单和工具栏贡献清理。
- 保留视口替换失败时 fail-closed 的清理语义。

### PS 实验链路

- 修复同一项目重复绑定时的幂等性问题。
- 项目内容变化后允许重新绑定。
- 修复 runtime projection 下从插件安装目录错误推导应用根的问题。
- PS 预设路径优先使用宿主 `application_root` / `repo_root`，再回退到 `bundle_paths.application_root()`。

### Hub

- 项目位置显示为 `samples/...` 短路径，完整路径放入 tooltip。
- 项目行支持键盘焦点，并显示明确的焦点边框。
- 简化副标题和空状态文案。
- 保持现有字体策略；离屏 Qt 的字体枚举限制不构成运行时字体故障。

### 门禁与文档

- 清理 release consistency 检查器中的乱码和过时仓库引用。
- 更新布局、PS、Dock 生命周期和 Hub smoke 回归测试。
- 更新 README、文档索引、项目元数据和本更新说明。
- 本机 Hub 项目列表、编辑配置和截图状态不进入 Git。

## 验证结果

已执行：

- PS 根路径相关回归：`21 passed`
- Hub smoke：`19 passed`
- `python -B tools/check_core_boundaries.py`：通过
- `python -B tools/check_release_consistency.py`：通过
- `python -B -m compileall -q FrameCore workspace tools main.py player.py`：通过
- `git diff --check`：通过

真实 PVAEC Editor 启动验证：

- 项目：`workspace/projects/samples/pvaec-细胞演化`
- 场景：`12 个节点, 5 个连接`
- PS 预设加载：1 次
- 插件发现：`registered=20 activated=13 discovery_errors=0`
- 无 Traceback、无 `U+FFFD` 乱码、无残留 Editor Python 进程

验证脚本在 25 秒后主动终止 Editor，因此进程返回码为 `1`；这是测试终止方式，不是业务启动失败。

## 升级与验证

```bash
uv sync --frozen
python main.py --version
python main.py --smoke-hub
python main.py --smoke-editor
python tools/check_core_boundaries.py
python tools/check_release_consistency.py
```

## 已知边界

- 本轮没有运行完整全量 pytest、全部样例工程、原生构建和正式发行打包。
- `dist/` 未重建，不能声明已与当前源码一致。
- `workspace/state/` 是本地运行状态，不应作为源码提交。
- 如需正式发行，应重新执行完整回归、原生准入和发行构建后再打新的版本标签。
