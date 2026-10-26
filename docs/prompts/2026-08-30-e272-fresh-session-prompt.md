# E272 fresh-session prompt

继续 VitaLoom 主线重构，当前唯一下一 gate 是：

> **E273 -- Route one persistence hydration path through `MemorySystem.adopt_memory` without changing `.pond` semantics**

## 已完成上下文

- E270：MemoryEditor.import_memory() 走 `memory.store` Registry 命令，具备 guarded collection snapshot、容量淘汰精确 undo/redo 和失败回滚。
- E271：完成运行时 lifecycle mutation authority 盘点，确认 simulation、inheritance、serializer、decay/reset、SR memory genes 不是编辑器 undo/redo。
- E272：新增 `MemorySystem.adopt_memory(MemoryGene)`，`store()` 复用该 API；runtime inheritance 已不再直接 `child.memory_system.memories.append(clone)`。
- 最新 E272 证据：focused chain **25 passed**；audit guard passed；scoped py_compile passed；`git diff --check` passed；`unified_undo_redo_runtime=false`。

## E273 边界

1. 阅读 `AGENTS.md`、E271/E272 plans、`organism_serializer.py`、`pond_serializer.py`、`MemorySystem` 及相关 persistence tests。
2. 只选择一个 persistence hydration 路线（建议先处理 organism serializer 或明确理由），用 `MemorySystem.adopt_memory()` 替换直接列表 append。
3. 保持原有字段、顺序、strength/age、错误处理和 `.pond` schema 完全兼容；不得把 hydration 写入 CommandRegistry history。
4. 添加反序列化回归测试和直接 append 搜索证据；运行 focused tests、audit guard、scoped py_compile、`git diff --check`。
5. 更新 `docs/mainline_status.md` 与下一 fresh-session prompt，并只命名一个下一 gate。

## 禁止事项

- 不同时修改 organism serializer 和 pond serializer；本 gate 只处理一条 persistence route。
- 不接入 editor undo/redo，不修改 `unified_undo_redo_runtime`（必须保持 `false`）。
- 不破坏 `.pond` scene semantics、AI command registry、Inspector、SR2D adapter、manifest 或 Qt-free contracts。
- 不 stage、commit、reset、restore、clean 或删除既有无关修改。
- 不修复 Conda/uv 混合环境；继续使用项目 `.venv\\python.exe`，不运行 `uv sync`，不修改 `uv.lock`。

## 输出要求

使用简体中文，说明实现、证据、边界和唯一下一 gate。
