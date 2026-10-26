# PS · 基础生态实验

这是从旧根 `examples/` 迁移来的两个 **Headless PS** 示例。它们属于 Project World，但不包含 `.pond` 场景，也不经过 `GameViewport` 的 SR 播放链。

## 运行

在仓库根目录执行：

```powershell
python -B workspace/projects/samples/ps-基础生态实验/tools/component_ecosystem.py --steps 20
python -B workspace/projects/samples/ps-基础生态实验/tools/ps_pacman_demo.py --steps 60
```

两个入口都会先读取本项目的 `project.lock.json`，再通过 FrameCore 安装锁定的产品版本 runtime；不会恢复旧根 `core/`、`builtin/`、`src/` 或手写固定 Runtime 导入路径。

## 语义

- `component_ecosystem.py`：LotusPond 中的初始生物、漂浮 TouchSensor、MuscleActuator 与 HybridComponent。
- `ps_pacman_demo.py`：`builtin.systems.simulation.Simulation` 路径的吃豆实验。

它们只演示现有 PS/LotusPond Interface，不实现第二套 `Pond.update`，也不代表 SR/PS 已统一。
