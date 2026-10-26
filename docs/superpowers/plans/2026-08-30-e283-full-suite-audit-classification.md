# E283 全量测试质量门

日期：2026-08-30

## 目标

修复全量测试发现的确定性审计分类缺口，并在隔离 pytest 临时目录下重新执行全量测试，区分真实代码问题与工作区临时目录权限噪声。

## 范围

- 将 `memory.restore` 纳入 E190 non-undoable mutation inventory 的唯一分类。
- 保持其作为 `memory.store` inverse 的语义，不把 runtime memory lifecycle 改造成统一编辑器 undo/redo。
- 使用工作区外隔离 basetemp 完成完整 pytest 运行。
- 记录首轮失败与复跑证据，避免把历史噪声误报成代码回归。

## 非目标

不重建 `.venv`，不运行 `uv sync`，不修改 `uv.lock`，不清理既有临时目录，不改变命令实现、不扩张 runtime undo/redo，也不在本门处理新的架构边界。

## 验证门

项目现有 `.venv\\python.exe`：审计 inventory 与 memory editor focused tests；隔离 basetemp 全量 pytest；scoped compile 与 `git diff --check`。完成后继续下一个真实重构 gate。
