# Simulation模块 - AI生命体模拟系统

## 1. 模块概述

Simulation模块是AI生命体模拟系统的核心模拟组件，实现了AI生命体在环境中的进化和交互。该模块包含：

- 基础模拟框架
- 继承算法模拟实现
- 可视化绘制系统

## 2. 核心设计理念

### 2.1 模拟流程

1. **初始化**：创建环境、添加初始食物和光源、创建初始生物种群
2. **感知-决策-行动循环**：
   - 生物通过传感器感知环境
   - 基于记忆和AI决策生成控制信号
   - 执行器执行动作，影响环境
   - 从结果中学习，更新记忆
3. **繁殖与进化**：
   - 能量充足的生物繁殖后代
   - 后代继承父辈的记忆和工具结构
   - 记忆在遗传过程中发生变异
4. **环境动态**：
   - 食物随时间再生
   - 光源强度变化
   - 障碍物影响生物移动
5. **可视化**：实时绘制环境、生物和相关信息

### 2.2 模拟类型

| 模拟类型 | 功能描述 | 适用场景 |
|---------|---------|---------|
| 基础模拟 | 简单的生物交互模拟 | 快速测试和开发 |
| 继承算法模拟 | 完整的AI进化模拟 | 研究和演示 |

## 3. 核心类说明

### 3.1 Simulation类

**功能**：基础模拟框架，实现了模拟的核心逻辑

**主要属性**：
- `width`: 环境宽度
- `height`: 环境高度
- `organism_count`: 生物数量
- `organisms`: 生物列表
- `food`: 食物列表
- `light_sources`: 光源列表
- `obstacles`: 障碍物列表
- `time_step`: 时间步长
- `paused`: 模拟是否暂停
- `speed`: 模拟速度

**主要方法**：
- `__init__()`: 初始化模拟环境
- `setup_test_environment()`: 设置测试环境
- `create_test_organism()`: 创建测试生物
- `update()`: 更新模拟状态
- `draw()`: 绘制模拟场景
- `handle_event()`: 处理用户输入事件

### 3.2 InheritanceSimulation类

**功能**：继承算法模拟实现，继承自Simulation类

**主要属性**：
- `generation_count`: 代数计数
- `stats`: 模拟统计信息
- `debug_info`: 调试信息

**主要方法**：
- `__init__()`: 初始化继承算法模拟
- `update()`: 扩展基础更新逻辑，添加繁殖和进化机制
- `draw()`: 扩展基础绘制逻辑，添加统计信息显示
- `calculate_fitness()`: 计算生物适应度

## 4. 模块依赖关系

```
simulation/
├── simulation.py                 # 基础模拟框架，依赖: core, tools, environment
├── inheritance_simulation.py     # 继承算法模拟，依赖: simulation
└── __pycache__/                  # 编译缓存
```

## 5. 使用示例

### 5.1 运行基础模拟

```python
import pygame
from ai_organism.simulation import Simulation

# 初始化Pygame
pygame.init()

# 创建模拟对象
simulation = Simulation(width=800, height=600, organism_count=10)

# 运行模拟循环
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        simulation.handle_event(event)
    
    # 更新模拟状态
    simulation.update()
    
    # 绘制模拟场景
    simulation.draw()
    
    # 控制帧率
    clock.tick(60)

# 退出Pygame
pygame.quit()
```

### 5.2 运行继承算法模拟

```python
import pygame
from ai_organism.simulation import InheritanceSimulation

# 初始化Pygame
pygame.init()

# 创建继承算法模拟对象
simulation = InheritanceSimulation(width=800, height=600, organism_count=20)

# 运行模拟循环
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        simulation.handle_event(event)
    
    # 更新模拟状态
    simulation.update()
    
    # 绘制模拟场景
    simulation.draw()
    
    # 控制帧率
    clock.tick(60)

# 退出Pygame
pygame.quit()
```

## 6. 模拟控制

### 6.1 键盘控制

| 按键 | 功能 |
|------|------|
| `Space` | 暂停/继续模拟 |
| `+` | 增加模拟速度 |
| `-` | 降低模拟速度 |
| `Q` | 退出模拟 |
| `C` | 显示/隐藏调试信息 |
| `F` | 添加食物 |

### 6.2 鼠标控制

| 操作 | 功能 |
|------|------|
| 点击生物 | 查看生物详细信息 |
| 点击空地 | 添加食物 |

## 7. 统计信息

模拟过程中会实时显示以下统计信息：

- 当前代数
- 生物数量
- 平均能量
- 平均年龄
- 平均记忆强度
- 成功行为比例
- 探索行为比例

## 8. 配置参数

### 8.1 环境参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `width` | 环境宽度 | 800 |
| `height` | 环境高度 | 600 |
| `organism_count` | 初始生物数量 | 10 |
| `food_regen_rate` | 食物再生速率 | 0.05 |
| `max_food` | 最大食物数量 | 100 |

### 8.2 生物参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `max_age` | 最大年龄 | 500 |
| `initial_energy` | 初始能量 | 100.0 |
| `memory_decay_rate` | 记忆衰减率 | 0.01 |
| `memory_mutation_rate` | 记忆突变率 | 0.1 |
| `reproduction_energy_threshold` | 繁殖能量阈值 | 100.0 |

## 9. 开发指南

### 9.1 扩展模拟功能

1. **继承Simulation类**：创建自定义模拟类，继承自Simulation或InheritanceSimulation
2. **重写关键方法**：根据需要重写以下方法：
   - `setup_test_environment()`: 自定义环境设置
   - `create_test_organism()`: 自定义生物创建
   - `update()`: 自定义模拟逻辑
   - `draw()`: 自定义绘制逻辑
3. **添加新功能**：添加新的模拟功能，如天气系统、疾病传播等

### 9.2 自定义生物

1. **继承Organism类**：创建自定义生物类，继承自core.Organism
2. **添加新属性和方法**：根据需要添加新的属性和方法
3. **重写关键方法**：
   - `perceive_environment()`: 自定义环境感知
   - `decide_action()`: 自定义决策逻辑
   - `learn_from_experience()`: 自定义学习机制
   - `reproduce()`: 自定义繁殖机制

## 10. 性能优化建议

- **限制生物数量**：根据系统性能调整生物数量
- **优化绘制逻辑**：使用高效的绘制方法，避免不必要的计算
- **优化碰撞检测**：使用空间划分算法（如四叉树）优化碰撞检测
- **减少不必要的更新**：只在必要时更新生物和环境状态
- **使用多线程**：将计算密集型任务（如模拟更新）与绘制分离到不同线程

## 11. 测试

运行测试用例：

```bash
pytest tests/test_simulation.py -v
pytest tests/test_inheritance_simulation.py -v
```

## 12. 常见问题

### 12.1 模拟运行缓慢

**解决方法**：
- 减少生物数量
- 降低模拟速度
- 关闭调试信息显示
- 优化代码性能

### 12.2 生物无法繁殖

**解决方法**：
- 增加初始能量
- 降低繁殖能量阈值
- 增加食物数量

### 12.3 生物行为异常

**解决方法**：
- 检查传感器和执行器的连接
- 调整记忆衰减率和突变率
- 检查生物的决策逻辑

## 13. 未来计划

- [ ] 实现3D可视化
- [ ] 添加神经网络支持
- [ ] 支持多物种模拟
- [ ] 实现复杂生态系统
- [ ] 添加数据分析工具
- [ ] 支持分布式模拟