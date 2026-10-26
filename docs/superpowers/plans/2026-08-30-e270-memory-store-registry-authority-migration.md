# E270 -- MemoryEditor Import / MemorySystem.store Registry Authority Migration

## Goal
将 MemoryEditor 的导入 mutation 纳入共享 Qt-free CommandRegistry，使 `MemorySystem.store()` 成为可撤销、可重做且具备 stale guard/失败回滚的唯一编辑器入口，同时保持容量淘汰和 `.pond` 运行时语义不变。

## Scope
- `memory.store` 公共命令及其内部 inverse `memory.restore` 的注册、执行和 undo/redo record。
- MemorySystem 集合快照的 JSON-safe 序列化、恢复、预期状态校验与原子失败回滚。
- MemoryEditor.import_memory() 的 Registry 路由及 transient target 生命周期。
- 覆盖容量淘汰、目标关闭、redo 失败、自定义 MemoryGene/MemorySystem 恢复失败等边界测试。
- 更新主线状态和下一 session prompt。

## Non-goals
- 不命令化 PVAECCycle.update_memory、继承复制、serializer 反序列化、decay/reset 等运行时生命周期 mutation。
- 不删除旧 CommandStack 兼容代码，不改变 `.pond`、AI command registry、Inspector、SR2D adapter 或 manifest 契约。
- 不修复当前 Conda/uv 混合环境，不重建 `.venv`，不运行 `uv sync`，不修改 `uv.lock`。
- 不写 durable project audit，不把对象引用写入 Registry history。

## Implementation
1. 审核现有 `memory.store`/`memory.restore` 注册、helper、undo/redo record 与 transient binding。
2. 补齐回归测试，验证成功路径、容量淘汰后精确 undo/redo、stale guard、关闭目标、redo 失败历史保留、恢复阶段完整回滚。
3. 若测试发现问题，仅在 E270 涉及文件内修复，并保持历史记录只含 token 与 JSON-safe 快照。
4. 运行 focused tests、audit status guard、scoped py_compile、git diff --check。
5. 记录证据、跳过项与唯一下一 gate。

## Evidence required
- E270 focused tests 全部通过，覆盖上述边界。
- `tools/check_ai_command_audit_status.py` 通过。
- scoped `.venv/python.exe -m py_compile` 通过。
- `git diff --check` 通过。
- 文档明确当前 `unified_undo_redo_runtime` 仍未完成。

## Exactly one next gate
E271 -- inventory remaining runtime lifecycle mutation authority and define one bounded next commandization target
