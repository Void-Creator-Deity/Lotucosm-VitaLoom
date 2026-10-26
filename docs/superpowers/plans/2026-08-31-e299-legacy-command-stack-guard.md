# E299 — Legacy UI CommandStack Usage Guard

## 目标

把 ADR-0007 中“遗留 `CommandStack` 只能作为 UI-host 迁移适配器、不得成为产品语义历史 authority”的约束固化为可重复静态检查。当前产品 runtime 已无生产代码实例化 `CommandStack`，但遗留模块仍需保留以兼容既有公共 import；静态 guard 防止新代码重新依赖它。

## 范围与约束

- 扫描 `runtime` 下 Python 生产代码，排除遗留定义文件 `core/VitaLoom/commands/command.py` 本身。
- 识别 `CommandStack` 名称引用与 `CommandStack(...)` 实例化；定义文件不计入违规。
- 工具只读，不修改源文件，不运行 package manager，不碰 `.venv` / `uv.lock`。
- 这是防回归 guard，不声称 `unified_undo_redo_runtime=true`；该 policy 保持 false。

## 验证

- 纯 Python 测试覆盖排除定义文件、发现生产引用、发现实例化和忽略测试目录。
- 当前 runtime 扫描必须返回零生产引用。
- 运行 AI command audit、相关 focused tests 和 diff check。

## 唯一下一门

继续审计尚未迁移的语义入口（若静态 guard 保持零违规），优先从文档列出的 Inspector/SceneViewport 直连 helper 证据开始；不扩大为 runtime replay 或环境迁移。

## 实施与证据（完成，2026-08-31）

- 新增 `tools/check_legacy_command_stack_usage.py`：使用 Python AST 只读扫描 runtime 生产代码；排除遗留定义文件和测试路径，识别 import、引用、实例化与语法错误。
- 新增 `tests/test_legacy_command_stack_usage.py`：4 个纯 Python 回归测试全部通过（`4 passed in 0.31s`）。
- 当前 runtime 扫描结果：`production_usages=[]`，`status=ok`；说明生产路径没有新的 `CommandStack` 依赖，遗留模块仅保留兼容定义。
- AI command audit 关键结果：`viewport_local_command_stack_retired=true`、`command_registry_undo_bridge=true`、`unified_undo_redo_runtime=false`。
- 语义命令 focused tests：`46 passed in 13.51s`；工具 `py_compile` 与相关文件 `git diff --check` 通过。
- CI 已增加 `Legacy CommandStack usage guard` 步骤，防止后续生产代码回退到遗留 UI 对象栈。

## 结论

ADR-0007 所要求的“遗留 CommandStack 不再作为产品 runtime 语义历史 authority”已被当前代码和静态防回归证据支持。保留兼容定义不等于继续混用；本阶段不宣称 full unified SR/PS runtime replay。

## 唯一下一门

继续对仍有明确证据的未完成能力做 current-state 审计；优先核对 WorldBridge 的 component/membrane/script graph mapping 与 lossless mapping 状态，不能把现有 position/energy/health 试点误称为完整统一 Pond。
