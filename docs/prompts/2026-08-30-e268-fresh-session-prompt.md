# E268 fresh-session prompt

继续 VitaLoom 主线重构，不要把目标缩小为“测试通过”。当前工作区已完成并验证：

- E267：Inspector Qt-free CommandRegistry authority migration。
- E268：MemoryEditor 的 `edit_memory(...)` 已经通过 `memory.edit` Registry 命令执行，使用 transient token、JSON-safe guarded snapshots、原子回滚和 undo/redo；`MemoryEditor.close()` 会释放绑定。
- focused chain：42 passed，6 subtests passed；scoped `.venv\python.exe` py_compile、AI command audit status guard、`git diff --check` 均通过。

必须继续遵守：

- runtime 边界保持在 `FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime`。
- 不破坏 `.pond`、AI command registry、Inspector binding、SR2D adapter、package/project manifests、Qt-free L0–L4 contracts。
- 把既有未提交修改视为用户/前序工作；不要 stage、commit、reset、restore、clean 或删除无关改动。
- 环境暂不处理：继续用项目 `.venv\python.exe`，不要重建环境、`uv sync`、重装依赖、切换解释器或修改 `uv.lock`。
- 不要把 `unified_undo_redo_runtime` 提前标为完成。

唯一下一 gate：

**E269 -- inventory remaining non-Registry mutation routes after MemoryEditor migration and select the next structural authority migration**

E269 要求先写/更新 `docs/superpowers/plans/` 下的阶段计划，再对 runtime/UI/adapter 中仍直接修改共享状态的路径做有证据的清单，区分：持久化项目命令、瞬态编辑器目标、运行时 MemorySystem、导入/导出兼容路径和遗留 CommandStack。选择且只选择一个下一结构迁移目标，不要同时扩大多个 gate。更新 `docs/mainline_status.md` 与下一 fresh-session prompt，运行与范围匹配的测试和检查，并记录确切的剩余边界。
