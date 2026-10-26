# VitaLoom 社区示例迁移 Gate 完成后的续作 Prompt

```text
不要读取、恢复或依赖旧 Codex 任务；从仓库文件和当前命令输出继续。

先确认当前任务工作区根，再读：
- AGENTS.md
- CONTEXT.md
- docs/adr/0003-suite-plugin-architecture.md
- docs/superpowers/plans/2026-07-15-community-example-migration-and-headless-plugin-seam.md
- docs/mainline_status.md 最后的“社区示例迁移与 Headless 插件 Seam 收口”段
- docs/superpowers/plans/2026-07-05-worldbridge-inspector-diagnostics-decision.md
- docs/prompts/2026-07-05-worldbridge-inspector-diagnostics-decision-prompt.md

刚完成的架构事实：
- L0 FrameCore、L1 产品大插件、L2 锁定版本 runtime、L3 Capability Package/Project Plugin、L4 Project World 的五层设定不变。
- 四个社区插件示例已迁入 workspace/extensions/community/，不恢复根 plugins/。
- 纯 service 插件 Interface 可在无 PyQt6 环境导入；Dock/Viewport 插件仍在自身 Module 显式依赖 PyQt6。
- 旧 PS 示例已迁入 workspace/projects/samples/ps-基础生态实验/，通过 project lock 与 FrameApi 安装锁定 runtime 环境，不恢复根 examples/。
- Simulation 保留默认 Pygame 窗口语义，并支持 enable_pygame=False 的 Headless PS 路径。
- 聚焦证据：8 passed；扩大回归：37 passed；core boundaries/release consistency/compileall/diff check 均通过。
- 当前 worktree audit dirty total 约 982，属于整仓迁移快照，不得随意整理或提交。

下一任务（唯一 Gate）：
执行 Phase 6H — WorldBridge Inspector diagnostics decision。
1. 先复核 Phase 6G 只读 diagnostics 的现状和 Phase 6H 计划；
2. 决定 Inspector 是否以及如何显示只读 projection diagnostics；
3. 不把 diagnostics 误升级成 live component mapping 或 .pond mutation；
4. 按计划先测试，再实现、验证并更新 docs/mainline_status.md 和下一 fresh-session prompt；
5. 未完成当前 Gate 前，不切换到 OpenGL、native acceleration、统一 Pond 或其他主题。

起始命令：
python -B tools/audit_worktree_groups.py
python -B tools/check_runtime_worldbridge_status.py
python -B tools/check_worldbridge_component_projection_diagnostics.py
python -B -m pytest -q -p no:cacheprovider tests/test_worldbridge_component_projection_diagnostics.py tests/test_runtime_worldbridge_command_surfaces.py tests/test_inspector_schema.py tests/test_inspector_command_binding.py

环境与声明限制：
- 当前 Python 3.13.5 缺 PyQt6/pygame；完整 GUI/真实视口 smoke 仍需修复环境后执行。
- 不 stage、commit、reset、clean、回退、移动或删除无关改动。
- 不宣称全量 pytest、完整 GUI、OpenGL default-ready、native acceleration、统一 Pond、SR/PS tick merge 或 live component graph mapping 已完成。
```
