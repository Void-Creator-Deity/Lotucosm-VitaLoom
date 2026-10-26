# VitaLoom Python 迁移吸收与 FrameCore 收口续作 Prompt

```text
不要读取、恢复或依赖旧 Codex 任务；从仓库文件和当前命令输出继续。

正确项目根：
使用当前任务工作区根目录（先运行 Get-Location 核对），不要在文档中写入本机绝对路径。

先读：
- AGENTS.md
- CONTEXT.md
- docs/adr/0003-suite-plugin-architecture.md
- docs/superpowers/plans/2026-07-15-migration-absorption-and-framecore-completion.md
- docs/mainline_status.md 最后的 2026-07-15 段
- FrameCore/project_lock.py
- FrameCore/lifecycle.py
- FrameCore/plugins/lotucosm-vitaloom/hub/__init__.py
- FrameCore/plugins/lotucosm-vitaloom/hub/hub_launcher.py
- FrameCore/plugins/lotucosm-vitaloom/versions/1.0.0/runtime/core/Lotucosm/sr_central_brain_pvaec.py

当前架构真相：
- FrameCore 是 L0 架子。
- FrameCore/plugins/lotucosm-vitaloom 是唯一对外产品插件，包含 Hub + versions/*。
- Hub 属于产品插件，但不属于某个版本 runtime。
- 不恢复根 core/builtin/plugins/products/projects/data。
- CentralBrainPvaec 的权威 Implementation 已回到产品 runtime；两个样例项目只保留 Adapter。
- FrameCore.project_lock 是唯一权威 Implementation；runtime 同名模块是兼容 Adapter。
- Hub Editor 命令按 project lock/项目约束选择 runtime，不再无条件使用默认版本。
- 根 main.py 通过真实 lifecycle Adapter 委托 Hub，不再硬编码 Hub GUI，也不在显示 Hub 时绑定默认 runtime。
- “激活 13”对应 editor_essentials bootstrap 插件集；不要把发现数大于激活数直接当成迁移缺失。

环境限制：
- .venv 已坏，指向不存在的 Python 3.11。
- 当前 Python 3.13.5 缺 PyQt6/pygame；GUI smoke 要在修复环境后运行，不要因 ModuleNotFoundError 改业务逻辑。

下一任务（唯一 Gate）：
审计 HEAD 旧 `plugins/example_*` 与 `examples/*`，按新架构迁移：
1. 应用级示例插件适配新 manifest/Interface，放入 workspace/extensions/community/ 的清晰示例区；
2. 可运行世界示例转成 workspace/projects/samples/ 的正式 Project World，或在证据充分时记录 intentional drop；
3. 不恢复旧根 plugins/ 或 examples/；
4. 先写新阶段计划和测试，再实现；
5. 更新 docs/mainline_status.md 与新的 fresh-session prompt。

起始命令：
python -B tools/audit_worktree_groups.py
python -B tools/check_core_boundaries.py
python -B tools/check_release_consistency.py
python -B -m pytest -q -p no:cacheprovider tests/test_central_brain_migration.py tests/test_framecore_migration_completion.py tests/test_framecore_plugin_lifecycle.py tests/test_suite_registry.py

工作区约束：
- 当前约 981 个 dirty paths 是正在进行的迁移。
- 不 stage、commit、reset、clean、回退、移动或删除无关改动。
- 报告 GUI 测试跳过与原因，不虚构全量通过。
```
