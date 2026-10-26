# E270 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E271 -- inventory remaining runtime lifecycle mutation authority and define one bounded next commandization target**

## 已完成上下文

- E267：Inspector Qt-free CommandRegistry authority migration。
- E268：MemoryEditor 单条 `memory.edit` Registry authority migration。
- E269：盘点剩余 mutation 路线并选择 MemoryEditor import/storage bypass。
- E270：MemoryEditor.import_memory() 已通过 `memory.store` 命令执行；新增内部 inverse `memory.restore`，支持 guarded collection snapshot、容量淘汰后的精确 undo/redo、失败回滚和 transient lifecycle 清理。
- 最新 E270 证据：focused chain **49 passed, 6 subtests passed**；audit status guard passed；scoped `.venv\\python.exe -m py_compile` passed；`git diff --check` passed。
- `unified_undo_redo_runtime` 必须继续保持 `false`。

## 环境约束

继续使用项目解释器：

```text
<repository-root>\\.venv\\python.exe
```

不要重建 `.venv`、不要运行 `uv sync`、不要重装依赖、不要切换解释器、不要修改 `uv.lock`。当前 Conda/uv 混合环境按用户决定暂时保持，重构主线完成后再修复。

## E271 任务边界

1. 先阅读 `AGENTS.md`、`docs/mainline_status.md`、最近 E269/E270 plan 和 prompt。
2. 盘点运行时生命周期 mutation：simulation learning、inheritance copy、serializer hydration、decay、reset/clear，以及任何尚未列出的直接 mutation。
3. 区分：
   - 领域生命周期 API（默认不直接纳入编辑器 undo/redo）；
   - 需要显式 domain command 设计的候选路径；
   - 真正的 editor mutation bypass。
4. 为下一阶段选择**恰好一个**有边界的 commandization/inventory 目标；不要在 E271 中顺手修改多个领域。
5. 写入 `docs/superpowers/plans/`，完成证据盘点，更新 `docs/mainline_status.md`，创建下一 fresh-session prompt。

## 禁止事项

- 不迁移到 Unity/Godot/Unreal/Electron。
- 不破坏 `.pond`、AI command registry、Inspector、SR2D adapter、package/project manifests 或 Qt-free L0-L4 contracts。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不把 `unified_undo_redo_runtime` 标记为完成。
- 不要把运行时生命周期 mutation 直接伪装成编辑器命令；必须先定义 authority、边界和证据。

## 输出要求

完成后说明：本 gate 做了什么、证据是什么、还剩哪些边界，以及唯一下一 gate。使用简体中文。
