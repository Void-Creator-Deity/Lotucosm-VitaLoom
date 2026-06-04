# 🚀 莲池生命织机 · 快速开始

> 织机（引擎/编辑器）入口。PVAEC AI 模拟见 **[README_PVAEC.md](README_PVAEC.md)** · 总索引 **[README.md](README.md)**。

## 环境准备（Clone 后必做）

仓库**不包含**虚拟环境（`.venv/` 已在 `.gitignore` 中）。拉取后请在本机创建：

```bash
# 需要 Python 3.12+
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
# 开发 / 跑测试：pip install -e ".[dev]"
```

## 一分钟启动

```bash
# 激活虚拟环境后
python main.py
```

就这么简单！✨

## 新架构说明

VitaLoom Engine 现在使用**插件化架构**：

- 🎯 **极简内核**：核心只有 ~800 行代码
- 🔌 **完全插件化**：所有 UI 功能都是插件
- 🎨 **高度可定制**：官方/社区插件都可以按项目禁用/替换
- 🔥 **热重载**：开发插件时无需重启

### 插件分层（补充）

- **Core**：仅“窗口/内核框架”（不通过 `builtin/` 或 `plugins/` 目录加载）
- **Official Mods**：官方插件（编辑器基础体验、2D 引擎相关插件、莲池/生命玩法插件等），默认启用，可按项目禁用
- **User/Community Mods**：`plugins/` 目录下的用户/社区插件

项目级禁用通过 `project.json.disabled_plugins` 实现：打开项目会自动卸载对应插件，并在下次启动继续生效。

## 界面预览

启动后你会看到：

```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help     [▶ Play] [⏸] [⏹]    │ ← 菜单栏+工具栏
├──────────┬──────────────────────────────┬───────────────┤
│          │                              │               │
│ Hierarchy│     Scene Viewport           │   Inspector   │
│          │                              │               │
│  Scene   │  (场景编辑区域)               │  (属性面板)    │
│   ├─Cell1│                              │               │
│   └─Cell2│                              │               │
│          │                              ├───────────────┤
│          │                              │               │
│          │                              │   Project     │
│          │                              │               │
│          │                              │  (资源浏览器)  │
├──────────┴──────────────────────────────┴───────────────┤
│ Console                                                 │
│ (控制台输出)                                             │
└─────────────────────────────────────────────────────────┘
```

## 主要功能

### 1. 场景编辑（Scene Viewport）
- 编辑场景中的实体
- 添加/删除/修改对象
- 可视化编辑

### 2. 游戏运行（Game Viewport）
- 点击 **▶ Play** 按钮
- 运行模拟
- 观察生命体行为

### 3. 细胞编辑（Cell Editor）
- 在 Hierarchy 中**双击细胞**
- 进入细胞内部编辑模式
- 编辑传感器、执行器、连接

### 4. 插件管理
- 菜单：**Tools > Plugin Manager**
- 查看所有已加载插件
- 重载插件（开发时）

## 开发自定义插件

### 步骤 1：创建插件文件

```bash
# 在 plugins 目录创建你的插件
mkdir plugins/my_plugin
```

### 步骤 2：编写插件代码

```python
# plugins/my_plugin/my_plugin_plugin.py
from core.plugin.interfaces import IDockProvider
from PyQt6.QtWidgets import QDockWidget, QLabel

class MyPlugin(IDockProvider):
    def get_plugin_info(self):
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "provides": ["dock"]
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
    
    def on_unload(self):
        pass
    
    def create_dock_widget(self):
        dock = QDockWidget("My Panel")
        dock.setWidget(QLabel("Hello from my plugin!"))
        return dock
    
    def get_dock_config(self):
        return {
            "title": "My Panel",
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": True
        }
```

### 步骤 3：重启编辑器

```bash
python main.py
```

你的插件会自动加载！🎉

## 详细文档

- 📖 **完整使用指南**: `USER_GUIDE.md`（包含 Mod 编写指南）
- 📖 **插件开发指南**: `PLUGIN_DEVELOPMENT_GUIDE.md`
- 🏗️ **架构说明**: `ARCHITECTURE_DIAGRAM.txt`

## 示例插件

查看 `plugins/` 目录的示例：

1. **example_custom_viewport** - 自定义视口
2. **example_custom_dock** - 自定义面板

这些示例展示了：
- 如何创建插件
- 如何使用事件总线
- 插件间如何通信

## 常见问题

### Q: 如何切换视口？
A: 使用菜单 **View > Scene View** 或 **View > Game View**

### Q: 如何进入细胞编辑模式？
A: 在 Hierarchy 面板中**双击细胞实体**

### Q: 如何管理插件？
A: 菜单 **Tools > Plugin Manager**

### Q: 如何开发新功能？
A: 创建插件而不是修改核心代码

### Q: 旧代码还能用吗？
A: 可以，但会发出废弃警告。建议迁移到新架构。

## 技术支持

遇到问题？

1. 查看 `USER_GUIDE.md` - 完整使用指南
2. 查看 `PLUGIN_DEVELOPMENT_GUIDE.md` - 插件开发指南
3. 查看示例插件代码

## 项目结构

```
VitaLoom-Engine/
├── main.py                    ← 启动这个！
├── core/
│   ├── VitaLoom/kernel/       ← 核心框架
│   └── plugin/interfaces.py   ← 插件接口
├── builtin/editor_extensions/ ← 官方插件（Official Mods，默认启用，可按项目禁用）
├── plugins/                   ← 你的插件放这里
├── data/                      ← 数据文件
└── projects/                  ← 用户项目
```

## 下一步

1. ✅ 启动编辑器：`python main.py`
2. ✅ 探索界面和功能
3. ✅ 查看示例插件
4. ✅ 开发自己的插件
5. ✅ 享受模块化架构！

---

**欢迎使用 VitaLoom Engine！** 🌌

一个高度模块化的生命模拟引擎平台。
