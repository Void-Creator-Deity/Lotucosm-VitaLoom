# Tools模块 - AI生命体工具系统

## 1. 模块概述

Tools模块是AI生命体模拟系统的工具组件系统，实现了AI生命体的各种功能单元，包括：

- 传感器工具：用于感知环境信息
- 执行器工具：用于与环境交互
- 中枢管理器：用于AI控制和决策
- 细胞膜：作为细胞边界和交互接口
- 连接系统：用于工具间信号传递

## 2. 核心设计理念

### 2.1 统一的Tool基类

所有工具都继承自`Tool`基类，确保了系统的高度可扩展性。Tool基类定义了所有工具的通用接口：

```python
class Tool:
    def __init__(self, tool_id: str, position: Tuple[float, float]):
        # 初始化工具
        
    def process(self, input_value: float) -> Optional[float]:
        # 处理输入，返回输出值
        
    def update(self):
        # 每帧更新
        
    def draw(self, surface):
        # 绘制工具
```

### 2.2 工具类型

| 工具类型 | 功能描述 | 输入 | 输出 | 示例 |
|---------|---------|------|------|------|
| 传感器工具 | 感知环境信息 | 环境信息 | 神经信号 | 触觉传感器、光感传感器 |
| 执行器工具 | 执行物理动作 | 控制信号 | 物理力 | 肌肉效应器、纤毛效应器 |
| 中枢管理器 | AI控制和决策 | 传感器信号 | 控制信号 | 中枢大脑 |
| 细胞膜 | 细胞边界管理 | 环境信息 | 控制信号 | 细胞边界 |
| 连接 | 信号传递通道 | 输入信号 | 输出信号 | 单向连接、双向连接 |

## 3. 核心类说明

### 3.1 Tool基类

**功能**：所有工具的基类，定义了通用接口和属性

**主要属性**：
- `tool_id`: 工具唯一标识符
- `position`: 位置坐标
- `connections`: 连接列表
- `activation`: 激活值
- `state`: 状态标识 (idle, active, processing)
- `genetic_strength`: 遗传强度
- `mutation_rate`: 变异率

**主要方法**：
- `process()`: 处理输入，返回输出值
- `update()`: 每帧更新
- `transmit_signals()`: 向所有连接的目标传递信号
- `mutate()`: 变异
- `draw()`: 绘制工具

### 3.2 SensorTool类

**功能**：传感器工具基类，所有传感器的父类

**主要属性**：
- `sense_range`: 感知范围
- `sensed_value`: 感知值
- `sense_time`: 上次感知时间
- `sense_interval`: 感知间隔（毫秒）

**主要方法**：
- `sense()`: 感知环境，返回感知值

### 3.3 ActuatorTool类

**功能**：执行器工具基类，所有执行器的父类

**主要属性**：
- `force_strength`: 力的强度
- `current_force`: 当前力值
- `last_force`: 上次力值
- `force_decay_rate`: 力衰减率

**主要方法**：
- `apply_force()`: 根据控制信号施加力，返回力向量

### 3.4 CentralBrain类

**功能**：中枢管理器 - 实现AI控制和决策的基本功能

**主要属性**：
- `associations`: 传感器-执行器关联
- `learning_rate`: 学习率
- `success_threshold`: 成功阈值
- `exploration_rate`: 探索率

**主要方法**：
- `learn_association()`: 学习传感器和执行器的关联
- `generate_control_signals()`: 根据传感器输入生成控制信号

### 3.5 Membrane类

**功能**：细胞膜 - 作为细胞的边界

**主要属性**：
- `radius`: 细胞膜半径
- `color`: 细胞膜颜色
- `border_color`: 边框颜色
- `border_width`: 边框宽度
- `auto_ingest_threshold`: 自动吞噬阈值
- `ingestion_rate`: 吞噬速率

**主要方法**：
- `is_inside()`: 检查位置是否在细胞膜内
- `auto_ingest()`: 自动吞噬小型物体

### 3.6 Connection类

**功能**：Tool之间的连接

**主要属性**：
- `source`: 信号源Tool
- `target`: 信号目标Tool
- `weight`: 连接权重
- `is_bidirectional`: 是否为双向连接
- `signal_active`: 信号激活状态

**主要方法**：
- `transmit_signal()`: 传递信号，返回传递后的信号值
- `update()`: 更新连接状态
- `draw()`: 绘制连接

## 4. 具体工具实现

### 4.1 传感器工具

#### TouchSensor
- **功能**：触觉传感器，感知物体接触
- **参数**：`tool_id`, `position`, `sense_range`
- **输出**：0.0-1.0之间的值，表示接触强度

#### LightSensor
- **功能**：光感传感器，感知光照强度
- **参数**：`tool_id`, `position`, `sense_range`
- **输出**：0.0-1.0之间的值，表示光照强度

### 4.2 执行器工具

#### MuscleActuator
- **功能**：肌肉效应器，产生推力
- **参数**：`tool_id`, `position`, `force_strength`
- **输出**：力向量

#### CiliaActuator
- **功能**：纤毛效应器，产生微小推力
- **参数**：`tool_id`, `position`, `force_strength`
- **输出**：力向量

## 5. 模块依赖关系

```
tools/
├── base.py           # 工具基类，无外部依赖
├── connection.py     # 连接类，依赖: base
├── membrane.py       # 细胞膜，依赖: base
├── sensors.py        # 传感器工具，依赖: base
├── actuators.py      # 执行器工具，依赖: base
└── central_brain.py  # 中枢管理器，依赖: base
```

## 6. 使用示例

### 创建传感器

```python
from ai_organism.tools import TouchSensor, LightSensor

# 创建触觉传感器
touch_sensor = TouchSensor("touch_1", (10, 10), 50)

# 创建光感传感器
light_sensor = LightSensor("light_1", (-10, 10), 100)
```

### 创建执行器

```python
from ai_organism.tools import MuscleActuator, CiliaActuator

# 创建肌肉效应器
muscle_actuator = MuscleActuator("muscle_1", (10, -10), 5.0)

# 创建纤毛效应器
cilia_actuator = CiliaActuator("cilia_1", (-10, -10), 2.0)
```

### 创建中枢管理器

```python
from ai_organism.tools import CentralBrain

# 创建中枢管理器
central_brain = CentralBrain("brain_1", (0, 0))
```

### 创建连接

```python
from ai_organism.tools import Connection

# 创建单向连接
connection = Connection(touch_sensor, muscle_actuator, weight=1.0, is_bidirectional=False)

# 创建双向连接
bi_connection = Connection(light_sensor, cilia_actuator, weight=0.5, is_bidirectional=True)
```

## 7. 开发指南

### 创建新的传感器

1. 继承`SensorTool`类
2. 实现`sense()`方法
3. 实现`draw()`方法
4. 实现`get_icon()`方法

### 创建新的执行器

1. 继承`ActuatorTool`类
2. 实现`apply_force()`方法
3. 实现`draw()`方法
4. 实现`get_icon()`方法

### 创建新的中枢管理器

1. 继承`CentralBrain`类
2. 重写`learn_association()`方法（可选）
3. 重写`generate_control_signals()`方法（可选）
4. 实现`draw()`方法
5. 实现`get_icon()`方法

## 8. 性能优化建议

- 限制传感器的感知范围，减少计算量
- 调整传感器的感知间隔，避免过于频繁的感知
- 优化连接的信号传递机制，减少不必要的计算
- 使用高效的绘制方法，特别是在大规模模拟场景下

## 9. 测试

运行测试用例：

```bash
pytest tests/test_tools.py -v
pytest tests/test_sensors.py -v
pytest tests/test_actuators.py -v
```