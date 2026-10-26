# E269 fresh-session prompt

继续 VitaLoom 主线重构。E269 已完成只读盘点：

- E267：Inspector transient mutation → Registry。
- E268：MemoryEditor.edit_memory → `memory.edit` Registry 命令，42 passed + 6 subtests。
- E269：已审计剩余 MemorySystem mutation 路线，并选择唯一下一 gate。

当前唯一下一 gate：

**E270 -- MemoryEditor import / MemorySystem.store Registry authority migration with guarded collection snapshots**

E270 要求先写阶段计划，再实现一个清晰受限的 Qt-free `memory.store` 命令，仅覆盖显式 MemoryEditor import/storage 操作。需要保留 `PVAECCycle.update_memory()` 的模拟运行时学习、继承系统复制、serializer 反序列化、decay/reset 等领域生命周期路径，不要悄悄全部命令化。为 `MemorySystem.memories` 集合设计 JSON-safe guarded snapshot 和原子失败语义；明确容量淘汰、重复情境、导入失败、undo/redo 失败栈保留、transient target 生命周期和是否写 durable audit。保留既有 MemoryEditor API 兼容性；不修改 `.pond` 语义、MemoryGene identity、环境、uv.lock 或无关未提交改动。完成后更新 `docs/mainline_status.md` 和下一 fresh-session prompt，并运行范围匹配的回归、审计状态、py_compile、diff 检查。
