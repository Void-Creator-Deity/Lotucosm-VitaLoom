# E281 生命周期状态权威边界

日期：2026-08-30

## 目标

收敛 Entity/Organism 的 age、generation、offspring_count 等生命周期与统计写入，区分 runtime lifecycle 与持久化 hydration，不改变编辑器历史边界。

## 范围

- `EntityBase.set_age()` / `advance_age()` 统一年龄校验与推进。
- `Organism.set_generation()` / `increment_offspring_count()` 统一代际和繁殖统计写入。
- 迁移 Organism update、reproduction、PondSerializer 与 OrganismSerializer。
- 保留公开字段 seam、原有默认值、繁殖计数和持久化数值语义。

## 非目标

不处理 editor viewport 自有 runtime doubles 的 generation 字段，不把 memory age 混入 organism age，不迁移 UI tool active 状态，不 commandize simulation/inheritance/persistence lifecycle。

## 验证门

使用项目现有 `.venv\\python.exe` 运行 PS/SR/persistence/lifecycle 聚焦测试、AI command audit、scoped py_compile 与 git diff --check。完成后记录唯一下一 gate。
