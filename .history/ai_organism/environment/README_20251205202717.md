# Environment模块 - AI生命体环境系统

## 1. 模块概述

Environment模块是AI生命体模拟系统的环境组件，实现了AI生命体生存的虚拟环境，包括：

- 环境对象管理（食物、光源、障碍物）
- 环境物理规则
- 环境存档管理

## 2. 核心设计理念

### 2.1 环境构成

环境由以下核心元素组成：

| 元素类型 | 功能描述 | 影响因素 |
|---------|---------|---------|
| 食物 | 生物获取能量的来源 | 位置、能量值、再生速率 |
| 光源 | 影响生物的感知和行为 | 位置、强度、颜色 |
| 障碍物 | 阻碍生物移动 | 位置、大小、形状 |
| 地形 | 影响生物移动和感知 | 高度、纹理、摩擦系数 |

### 2.2 环境动态性

- **食物再生**：被消耗的食物会随时间再生
- **光源变化**：光源强度会周期性变化
- **障碍物移动**：部分障碍物可能会缓慢移动
- **天气系统**：模拟天气变化对环境的影响

## 3. 核心类说明

### 3.1 Environment类

**功能**：环境类，实现了环境的核心逻辑

**主要属性**：
- `width`: 环境宽度
- `height`: 环境高度
- `food`: 食物列表
- `light_sources`: 光源列表
- `obstacles`: 障碍物列表
- `time`: 环境时间
- `weather`: 当前天气

**主要方法**：
- `__init__()`: 初始化环境
- `add_food()`: 添加食物
- `add_light_source()`: 添加光源
- `add_obstacle()`: 添加障碍物
- `remove_food()`: 移除食物
- `remove_light_source()`: 移除光源
- `remove_obstacle()`: 移除障碍物
- `get_nearby_food()`: 获取附近的食物
- `get_nearby_light_sources()`: 获取附近的光源
- `get_nearby_obstacles()`: 获取附近的障碍物
- `update()`: 更新环境状态
- `draw()`: 绘制环境

### 3.2 Food类

**功能**：食物类，实现了食物的属性和行为

**主要属性**：
- `position`: 位置坐标
- `energy_value`: 能量值
- `radius`: 半径
- `color`: 颜色

### 3.3 LightSource类

**功能**：光源类，实现了光源的属性和行为

**主要属性**：
- `position`: 位置坐标
- `intensity`: 强度
- `color`: 颜色
- `radius`: 影响范围

### 3.4 Obstacle类

**功能**：障碍物类，实现了障碍物的属性和行为

**主要属性**：
- `position`: 位置坐标
- `radius`: 半径
- `color`: 颜色
- `movable`: 是否可移动

### 3.5 EnvironmentArchiveManager类

**功能**：环境存档管理器，实现了环境的保存和加载

**主要属性**：
- `archive_dir`: 存档目录
- `archives`: 存档列表

**主要方法**：
- `__init__()`: 初始化存档管理器
- `list_archives()`: 列出所有存档
- `save_environment()`: 保存环境
- `load_environment()`: 加载环境
- `delete_archive()`: 删除存档
- `create_new_environment()`: 创建新环境

## 4. 模块依赖关系

```
environment/
├── __init__.py                # 模块初始化
├── environment.py             # 环境类，无外部依赖
├── archive_manager.py         # 存档管理器，依赖: environment
└── __pycache__/               # 编译缓存
```

## 5. 使用示例

### 5.1 创建环境

```python
from ai_organism.environment import Environment

# 创建环境
environment = Environment(width=800, height=600)

# 添加食物
environment.add_food((100, 100), energy_value=20.0)
environment.add_food((300, 200), energy_value=15.0)
environment.add_food((500, 300), energy_value=25.0)

# 添加光源
environment.add_light_source((200, 150), intensity=1.0)
environment.add_light_source((400, 400), intensity=0.7)

# 添加障碍物
environment.add_obstacle((250, 250), radius=30)
environment.add_obstacle((550, 150), radius=25)
```

### 5.2 管理环境存档

```python
from ai_organism.environment import EnvironmentArchiveManager

# 初始化存档管理器
archive_manager = EnvironmentArchiveManager()

# 创建新环境
new_env = archive_manager.create_new_environment()

# 添加一些默认内容
new_env.add_food((100, 100))
new_env.add_food((300, 200))
new_env.add_light_source((200, 150), 1.0)
new_env.add_obstacle((400, 250), 30)

# 保存环境
archive_manager.save_environment(new_env, "test_environment", "测试环境描述")

# 列出所有存档
archives = archive_manager.list_archives()
print("可用存档:")
for archive in archives:
    print(f"- {archive['name']}: {archive['description']}")

# 加载环境
loaded_env = archive_manager.load_environment(archives[0]['file'])
```

### 5.3 使用环境

```python
# 在模拟循环中更新环境
environment.update()

# 获取附近的食物
nearby_food = environment.get_nearby_food((200, 200), 100)

# 移除被吃掉的食物
environment.remove_food(eaten_food)

# 绘制环境
environment.draw(surface)
```

## 6. 环境物理规则

### 6.1 碰撞检测

- 食物与生物的碰撞：生物接触食物时自动吞噬
- 生物与障碍物的碰撞：生物无法穿过障碍物
- 生物之间的碰撞：生物之间可以接触但不会重叠

### 6.2 能量规则

- 生物移动消耗能量
- 生物感知环境消耗少量能量
- 生物繁殖消耗大量能量
- 生物吞噬食物获得能量

### 6.3 感知规则

- 生物只能感知视野范围内的物体
- 感知范围受传感器类型和环境因素影响
- 光源影响生物的感知能力

## 7. 配置参数

### 7.1 环境参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `width` | 环境宽度 | 800 |
| `height` | 环境高度 | 600 |
| `food_regen_rate` | 食物再生速率 | 0.05 |
| `max_food` | 最大食物数量 | 100 |
| `light_intensity_variation` | 光源强度变化幅度 | 0.2 |

### 7.2 食物参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `default_energy_value` | 默认能量值 | 20.0 |
| `default_radius` | 默认半径 | 8.0 |
| `default_color` | 默认颜色 | (255, 100, 100) |

### 7.3 光源参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `default_intensity` | 默认强度 | 1.0 |
| `default_radius` | 默认影响范围 | 100.0 |
| `default_color` | 默认颜色 | (255, 255, 200) |

## 8. 开发指南

### 8.1 扩展环境元素

1. **创建新的元素类**：继承自BaseEnvironmentElement类
2. **实现核心方法**：
   - `__init__()`: 初始化元素
   - `update()`: 更新元素状态
   - `draw()`: 绘制元素
3. **在Environment类中添加管理方法**：
   - `add_new_element()`: 添加新元素
   - `remove_new_element()`: 移除新元素
   - `get_nearby_new_elements()`: 获取附近的新元素

### 8.2 修改环境物理规则

1. **修改碰撞检测逻辑**：更新`check_collision()`方法
2. **修改能量规则**：更新`calculate_energy_cost()`和`calculate_energy_gain()`方法
3. **修改感知规则**：更新`get_visible_objects()`方法

## 9. 性能优化建议

- **空间划分**：使用四叉树或网格系统优化碰撞检测和物体查找
- **对象池**：使用对象池管理频繁创建和销毁的对象（如食物）
- **延迟加载**：只在必要时加载环境元素
- **批量更新**：批量处理环境元素的更新

## 10. 测试

运行测试用例：

```bash
pytest tests/test_environment.py -v
pytest tests/test_archive_manager.py -v
```

## 11. 未来计划

- [ ] 实现3D环境支持
- [ ] 添加更复杂的天气系统
- [ ] 支持地形编辑器
- [ ] 实现环境事件系统
- [ ] 添加环境音效支持