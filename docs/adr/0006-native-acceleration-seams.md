# ADR-0006: Native Acceleration Seams, Not Big-Bang Runtime Rewrite

Date: 2026-06-19

## Status

Accepted

## Context

莲池织机现在的主体实现是 Python + PyQt6。对照商业游戏引擎岗位要求，明显缺口包括 GPU/多线程调度、native 性能证据、渲染批处理、跨平台移动端和长期稳定性数据。

但当前项目的核心价值不是“立刻变成 C++ 商业引擎”，而是：

- FrameCore 插件框架与 Suite 物理结构已经成型。
- SR/PS/PVAEC 语义在 Python 层迭代速度快。
- AI 原生命令层要求 UI/CLI/MCP/Agent 同构，这需要稳定的 runtime Interface。
- 大迁移会破坏现有测试面和项目创作工作流。

## Decision

第一阶段不整体重写 runtime。只为明确热点设计 native acceleration seam：

- SR 2D 物理：刚体、弹簧、膜拓扑、碰撞 broadphase。
- SR 渲染批处理：sprite batching、可见性裁剪、材质/纹理批处理。
- PS batch：多 run 并行、统计聚合、快照压缩。
- 资源管线：hash、导入、导出闭包扫描的增量索引。

每个 seam 必须先有 Python Interface、benchmark case、行为测试和 fallback Adapter。只有出现第二个 Adapter（例如 Python Adapter + Rust/C++ Adapter）时，seam 才算真实。

## Consequences

好处：

- 保持当前插件架构和项目格式稳定。
- 可以用 `tools/benchmark_engine.py` 找热点，再决定是否 native 化。
- AI 命令层不需要理解 native 内部实现，只调用同一 Command Registry。

代价：

- 短期内不能声称拥有商业级 C++/GPU 引擎能力。
- 深层渲染、动画、移动端优化仍是明确缺口。
- 每个 native Adapter 都要额外维护打包、平台、调试和 fallback。

## Verification

SR 2D uses `SrPhysics2DWorld.step()` as the first adapter boundary. The Python adapter is required as the fallback and behavior oracle; native code is only acceptable after parity tests and benchmark evidence exist.

```bash
python -B tools/benchmark_engine.py --case sr2d --repeats 1
python -B tools/benchmark_engine.py --case all --repeats 1
python -B -m pytest -q -p no:cacheprovider tests/test_ai_isomorphic_scene_commands.py
python -B tools/check_core_boundaries.py
```
