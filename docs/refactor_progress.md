# VitaLoom 重构进度口径

更新日期：2026-10-21

## 口径说明

本文件是面向规划和验收的固定进度表。分母不是代码行数、提交数或测试数，因为本次重构包含 legacy 删除、所有权迁移、兼容层、门禁与真实运行证据，单看代码量会严重失真。

总分固定为 100，按 7 个交付面加权。每个交付面只有在其定义的真实 producer、consumer、拒绝路径和验证命令闭合后才能记满分。

| 交付面 | 权重 | 当前 | 依据 | 剩余 |
|---|---:|---:|---|---:|
| FrameCore → 大插件 → versioned runtime → capability/extension → Project World 分层 | 15 | 15 | 边界检查、插件/运行时 smoke、分层文档 | 0 |
| Plugin/package/project lifecycle 与事务 authority | 15 | 15 | 包事务、项目锁、Hub/Editor/Player smoke、定向回归 | 0 |
| UI host adapter 隔离与入口可运行性 | 10 | 10 | Hub/Editor/Player offscreen smoke；toolbar state identity 修复 | 0 |
| WorldBridge 字段、行为、tick、replay、mapping authority | 25 | 25 | E557/E558/E559/E560/E561；field/behavior/tick/replay/lossless scoped witnesses；E554 将共享 RNG 边界绑定到当前 native artifact SHA256、ABI、entropy contract、三组 120 tick zero-delta parity 与 benchmark admission evidence | 0 |
| Portable checkpoint、脚本 rehydration、跨进程 atomicity | 15 | 15 | E562-E566 闭合脚本 round-trip、跨会话 source-bundle rehydration、canonical artifact、SR/PS fresh-process atomic reconstruction 与 Project World 全局写锁；E567 正式声明产品永不嵌入/执行 portable Python source、bytecode、pickle 或 executable blob，仅允许 path+SHA256 source bundle，并验证 source available/missing/drift/trust/external 五条路径 | 0 |
| Native SR2D / OpenGL 与功能、parity、benchmark 证据 | 10 | 10 | OpenGL 路径有测试；CPP ABI v1 在 CPython 3.11 与 3.12 均完成 build/import、隔离 wheel、clean fallback、packaged parity、120 tick 零差异 parity 与 benchmark；admission evidence 与 E554 native entropy boundary 交叉绑定；独立 Windows workflow 覆盖双 Python matrix | 0 |
| 全量回归、可复现环境与发行门禁 | 10 | 10 | uv 0.7.9 + Python 3.11 + `uv.lock` 新建正式 `.venv`，旧 Conda 环境已删除；正式环境完整分块回归 3568 tests（3534 passed、34 skipped），入口 smoke、release gates 与双轨 comparability 全部通过 | 0 |
| **合计** | **100** | **100** |  | **0** |

## 当前结论

- 重构工程完成度：**100%**
- 剩余重构权重：**0%**
- 计划内的 7 个交付面已全部收口。
- 完成摘要：[refactor_completion_record.md](refactor_completion_record.md)
- 总迭代记录：[refactor_iteration_log.md](refactor_iteration_log.md)
- 测试中间文件：[2026-10-23 归档](archive/test-artifacts/2026-10-23/README.md)
- 当前活跃面：497 个测试模块、158 个工具模块；根目录 11 个目录、14 个文件。
- 100% 表示本次重构目标完成，不表示所有产品外延能力都已实现；`docs/mainline_status.md` 中的永久 do-not-claim 仍有效。
- 后续每个阶段必须更新本表，并同时给出增加的权重点、依据和仍缺的证据。

## 已完成收口

1. **Native SR2D**
   - CPython 3.11/3.12 本地均完成 wheel build、ABI import、long-horizon parity 与 benchmark。
   - E554 live GameViewport 已从 `excluded_from_selected_runtime` 收口到 `admitted_native_contract`；artifact、ABI、entropy contract、parity 和 benchmark 任一漂移都会重新 quarantine。
2. **回归与环境**
   - 正式 `.venv` 已由 uv 管理；全量分块回归和入口/Comparability 门禁通过。

