"""插件加载器：扫描 `*_plugin.py`、解析依赖、注册 Dock/视口/菜单/主题。

架构数据流::

    layered_dirs → _scan_directory → _discover_plugin → _load_all_plugins → LayoutManager

历史坑::

    - core_mod 插件默认受保护，卸载需 scope 非 core_mod

排错: 见 core/VitaLoom/README.md「插件」
"""

import importlib
import importlib.util
import inspect
import sys
import time
from pathlib import Path
from typing import Dict, List
from core.plugin.interfaces import (
    IEditorPlugin, IDockProvider, IViewportProvider, 
    IMenuProvider, IThemeProvider
)
from core.VitaLoom.core.logger import get_logger


logger = get_logger("PluginLoader")


class PluginLoader:
    """职责: 发现、排序、实例化 `IEditorPlugin` 并挂接到 LayoutManager。
    时机: `EditorKernel.load_plugins*` 构造后；运行期 `reload_plugin` / `unload_plugin`。
    不变量: `loaded_plugins` 键为插件类名；依赖须无环；Dock 经 `_register_dock` 唯一 title。
    排错: `failed_plugins` 字典；Dock 未出现 → `IDockProvider` 两方法是否实现。
    """
    SCOPE_CORE = "core_mod"
    SCOPE_OFFICIAL = "official_mod"
    SCOPE_USER = "user_mod"
    SCOPE_UNKNOWN = "unknown"

    _SCOPE_PRIORITY = {
        SCOPE_UNKNOWN: 0,
        SCOPE_USER: 1,
        SCOPE_OFFICIAL: 2,
        SCOPE_CORE: 3,
    }
    
    def __init__(self, editor_kernel):
        """构造并初始化实例。

        职责:
            建立本对象运行所需字段与子系统引用。

        时机:
            宿主创建对象时单次调用。

        不变量:
            子类须完整 super().__init__ 链。

        排错:
            属性缺失 → 查 super 与模块顶 docstring。
        """
        self.kernel = editor_kernel
        self.loaded_plugins: Dict[str, IEditorPlugin] = {}
        self.plugin_dependencies: Dict[str, List[str]] = {}
        self.plugin_order: List[str] = []
        self.failed_plugins: Dict[str, str] = {}
        self.plugin_scopes: Dict[str, str] = {}
        self.plugin_files: Dict[str, str] = {}
        self.protected_plugins: set[str] = set()
        self.scope_overrides: Dict[str, str] = {}
    
    def load_from_directories(self, dirs: List[str]):
        """职责: 扁平目录列表扫描，scope 记为 unknown。
        时机: 非分层启动或测试入口。
        不变量: 目录不存在仅 warning，不中断其余目录。
        排错: 零插件 → 路径与 `*_plugin.py` 命名。
        """
        logger.info("开始扫描插件目录: %s", dirs)
        
        # 扫描所有目录
        for dir_path in dirs:
            path = Path(dir_path)
            if path.exists():
                self._scan_directory(path, self.SCOPE_UNKNOWN)
            else:
                logger.warning("插件目录不存在: %s", dir_path)

        self._finalize_loading()
    
    def load_from_layered_directories(self, layered_dirs: Dict[str, List[str]]):
        """职责: 按 scope 优先级扫描多目录并统一 `_finalize_loading`。
        时机: 生产启动推荐路径。
        不变量: scope 未知时降级为 unknown；core_mod 写入 `protected_plugins`。
        排错: 用户插件被覆盖 → scope 与 `_SCOPE_PRIORITY` 冲突策略。
        """
        logger.info("开始按分层策略扫描插件目录: %s", layered_dirs)

        for scope, dirs in layered_dirs.items():
            normalized_scope = scope if scope in self._SCOPE_PRIORITY else self.SCOPE_UNKNOWN
            for dir_path in dirs:
                path = Path(dir_path)
                if path.exists():
                    self._scan_directory(path, normalized_scope)
                else:
                    logger.warning("插件目录不存在: scope=%s path=%s", normalized_scope, dir_path)

        self._finalize_loading()

    def set_scope_overrides(self, overrides: Dict[str, str]):
        """设置按插件名覆盖 scope 的规则。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        normalized: Dict[str, str] = {}
        for plugin_name, scope in overrides.items():
            normalized[plugin_name] = scope if scope in self._SCOPE_PRIORITY else self.SCOPE_UNKNOWN
        self.scope_overrides = normalized

    def _finalize_loading(self):
        """统一执行依赖解析与加载。"""
        # 解析依赖并按顺序加载
        self._resolve_dependencies()
        self._load_all_plugins()
        
        logger.info("插件加载完成，共加载 %s 个插件", len(self.loaded_plugins))
    
    def _scan_directory(self, path: Path, scope: str):
        """扫描目录查找插件
        
        Args:
            path: 目录路径
        """
        # 查找所有 *_plugin.py 文件
        for py_file in path.rglob("*_plugin.py"):
            try:
                self._discover_plugin(py_file, scope)
            except Exception:
                logger.exception("发现插件失败: %s", py_file)
    
    def _discover_plugin(self, file_path: Path, scope: str):
        """发现插件类
        
        Args:
            file_path: 插件文件路径
        """
        # 动态导入模块
        module_name = f"plugin_{file_path.stem}_{id(file_path)}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找 IEditorPlugin 子类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, IEditorPlugin) and 
                    obj != IEditorPlugin and
                    not inspect.isabstract(obj)):
                    
                    try:
                        plugin_instance = obj()
                        info = plugin_instance.get_plugin_info()
                        plugin_name = info.get("name")
                        if not plugin_name:
                            raise ValueError(f"插件 {name} 缺少 name 字段")

                        effective_scope = self.scope_overrides.get(plugin_name, scope)
                        existing_scope = self.plugin_scopes.get(plugin_name, self.SCOPE_UNKNOWN)
                        if plugin_name in self.loaded_plugins:
                            if self._SCOPE_PRIORITY.get(effective_scope, 0) < self._SCOPE_PRIORITY.get(existing_scope, 0):
                                logger.info(
                                    "跳过低优先级同名插件: name=%s scope=%s existing_scope=%s",
                                    plugin_name,
                                    effective_scope,
                                    existing_scope,
                                )
                                continue
                            logger.warning(
                                "同名插件被更高优先级覆盖: name=%s old_scope=%s new_scope=%s",
                                plugin_name,
                                existing_scope,
                                effective_scope,
                            )

                        self.loaded_plugins[plugin_name] = plugin_instance
                        self.plugin_dependencies[plugin_name] = info.get("dependencies", [])
                        self.plugin_scopes[plugin_name] = effective_scope
                        self.plugin_files[plugin_name] = str(file_path)
                        # 受保护插件：用于“官方插件中不可随意卸载”的情况（例如包管理器）
                        if bool(info.get("protected", False)):
                            self.protected_plugins.add(plugin_name)
                        elif effective_scope == self.SCOPE_CORE:
                            self.protected_plugins.add(plugin_name)
                        else:
                            self.protected_plugins.discard(plugin_name)

                        logger.info(
                            "发现插件: %s v%s (scope=%s)",
                            plugin_name,
                            info.get("version", "未知"),
                            effective_scope,
                        )
                    except Exception:
                        logger.exception("实例化插件失败: %s", name)
    
    def _resolve_dependencies(self):
        """解析插件依赖 - 使用拓扑排序"""
        # 构建依赖图
        in_degree = {name: 0 for name in self.loaded_plugins}
        adj_list = {name: [] for name in self.loaded_plugins}
        
        for plugin_name, deps in self.plugin_dependencies.items():
            for dep in deps:
                if dep in self.loaded_plugins:
                    adj_list[dep].append(plugin_name)
                    in_degree[plugin_name] += 1
                else:
                    logger.warning("插件依赖未找到: plugin=%s dep=%s", plugin_name, dep)
        
        # 拓扑排序（Kahn 算法）
        queue = [name for name, degree in in_degree.items() if degree == 0]
        self.plugin_order = []
        
        while queue:
            current = queue.pop(0)
            self.plugin_order.append(current)
            
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查循环依赖
        if len(self.plugin_order) != len(self.loaded_plugins):
            logger.warning("检测到循环依赖，将尽力加载未排序插件")
            # 为了保证可启动，追加未排序成功的插件（尽力加载）
            unresolved = [name for name in self.loaded_plugins if name not in self.plugin_order]
            self.plugin_order.extend(unresolved)
    
    def _load_all_plugins(self):
        """按依赖顺序加载所有插件"""
        for plugin_name in self.plugin_order:
            plugin = self.loaded_plugins[plugin_name]
            try:
                self._load_plugin(plugin)
            except Exception as exc:
                logger.exception("加载插件失败: %s", plugin_name)
                self.failed_plugins[plugin_name] = str(exc)
        lm = getattr(self.kernel, "layout_manager", None)
        if lm and hasattr(lm, "process_pending_dock_tabify"):
            lm.process_pending_dock_tabify()
    
    def _load_plugin(self, plugin: IEditorPlugin):
        """加载单个插件
        
        Args:
            plugin: 插件实例
        """
        info = plugin.get_plugin_info()
        plugin_name = info["name"]
        
        logger.info("加载插件: %s", plugin_name)
        
        # 调用插件的 on_load
        plugin.on_load(self.kernel.get_context())
        
        # 根据插件提供的接口类型注册
        provides = info.get("provides", [])
        
        if "dock" in provides and isinstance(plugin, IDockProvider):
            self._register_dock(plugin)
        
        if "viewport" in provides and isinstance(plugin, IViewportProvider):
            self._register_viewport(plugin)
        
        if "menu" in provides and isinstance(plugin, IMenuProvider):
            self._register_menu(plugin)
        
        if "theme" in provides and isinstance(plugin, IThemeProvider):
            self._register_theme(plugin)
        
        # 通知加载完成
        try:
            plugin.on_editor_ready()
        except Exception:
            logger.exception("插件 on_editor_ready 失败: %s", plugin_name)
        
        self.kernel.plugin_loaded.emit(plugin_name)
    
    def _register_dock(self, plugin: IDockProvider):
        """注册 Dock 面板
        
        Args:
            plugin: Dock 提供者插件
        """
        try:
            dock_widget = plugin.create_dock_widget()
            config = plugin.get_dock_config()
            self.kernel.layout_manager.add_dock(dock_widget, config)
        except Exception:
            logger.exception("注册 Dock 失败")
    
    def _register_viewport(self, plugin: IViewportProvider):
        """注册视口
        
        Args:
            plugin: 视口提供者插件
        """
        try:
            viewport_widget = plugin.create_viewport_widget()
            viewport_id = plugin.get_viewport_id()
            self.kernel.layout_manager.add_viewport(viewport_id, viewport_widget, plugin)
        except Exception:
            logger.exception("注册视口失败")
    
    def _register_menu(self, plugin: IMenuProvider):
        """注册菜单项
        
        Args:
            plugin: 菜单提供者插件
        """
        try:
            if not self.kernel.layout_manager:
                logger.warning("布局管理器未初始化，跳过菜单注册")
                return
                
            menu_items = plugin.get_menu_items()
            self.kernel.layout_manager.add_menu_items(menu_items, plugin.get_plugin_info().get("name"))
            
            toolbar_items = plugin.get_toolbar_items()
            self.kernel.layout_manager.add_toolbar_items(toolbar_items, plugin.get_plugin_info().get("name"))
        except Exception:
            logger.exception("注册菜单失败")
    
    def _register_theme(self, plugin: IThemeProvider):
        """注册主题（与 ThemeManager 基座 QSS 合并，保留模拟 HUD / 控制台样式）。"""
        try:
            from core.VitaLoom.ui.theme_manager import get_theme_manager

            theme_name = plugin.get_theme_name()
            stylesheet = plugin.get_stylesheet()
            base = get_theme_manager().DARK_THEME
            merged = f"{base}\n{stylesheet}"
            self.kernel.layout_manager.register_theme(theme_name, merged)
        except Exception:
            logger.exception("注册主题失败")
    
    def unload_plugin(self, plugin_name: str):
        """职责: 调用 `on_unload`、清理 UI 并从 `loaded_plugins` 移除。
        时机: 插件管理器或内核关闭时。
        不变量: `protected_plugins` 内插件拒绝卸载。
        排错: UI 残留 → `_cleanup_plugin_ui` 与 `LayoutManager.remove_plugin_ui`。
        """
        """卸载插件（热重载支持）
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning("插件未加载: %s", plugin_name)
            return False
        
        if plugin_name in self.protected_plugins:
            logger.warning("核心插件受保护，禁止卸载: %s", plugin_name)
            return False
        
        plugin = self.loaded_plugins[plugin_name]
        
        try:
            # 1. 清理 UI 元素
            self._cleanup_plugin_ui(plugin, plugin_name)
            
            # 2. 调用插件的卸载回调
            plugin.on_unload()
            
            # 3. 从已加载列表中移除
            del self.loaded_plugins[plugin_name]
            if plugin_name in self.plugin_dependencies:
                del self.plugin_dependencies[plugin_name]
            if plugin_name in self.plugin_order:
                self.plugin_order.remove(plugin_name)
            
            # 4. 发送卸载信号
            self.kernel.plugin_unloaded.emit(plugin_name)
            logger.info("已卸载插件: %s", plugin_name)
            return True
        except Exception:
            logger.exception("卸载插件失败: %s", plugin_name)
            return False
    
    def _cleanup_plugin_ui(self, plugin: IEditorPlugin, plugin_name: str):
        """清理插件注册的 UI 元素
        
        Args:
            plugin: 插件实例
            plugin_name: 插件名称
        """
        try:
            info = plugin.get_plugin_info()
            provides = info.get("provides", [])
            layout_manager = self.kernel.layout_manager
            
            # 清理 Dock 面板
            if "dock" in provides and isinstance(plugin, IDockProvider):
                config = plugin.get_dock_config()
                dock_title = config.get("title", plugin_name)
                layout_manager.remove_dock(dock_title)
            
            # 清理视口
            if "viewport" in provides and isinstance(plugin, IViewportProvider):
                viewport_id = plugin.get_viewport_id()
                layout_manager.remove_viewport(viewport_id)
            
            # 注意：菜单和工具栏项的清理比较复杂，需要记录每个插件添加的菜单项
            if hasattr(layout_manager, "remove_plugin_ui"):
                layout_manager.remove_plugin_ui(plugin_name)
            
        except Exception as e:
            logger.exception("清理插件 UI 元素失败: plugin=%s error=%s", plugin_name, e)
    
    def _invalidate_plugin_bytecode(self, file_path: Path) -> None:
        """清除插件 .pyc，确保热重载读取最新源码。"""
        cache_dir = file_path.parent / "__pycache__"
        if not cache_dir.is_dir():
            return
        stem = file_path.stem
        for pyc in cache_dir.glob(f"{stem}*.pyc"):
            try:
                pyc.unlink()
            except OSError:
                pass
        importlib.invalidate_caches()

    def _instantiate_plugin_from_file(self, file_path: Path) -> tuple[str, IEditorPlugin]:
        """从磁盘重新导入插件模块并实例化（每次使用唯一 module 名以绕过 import 缓存）。"""
        self._invalidate_plugin_bytecode(file_path)
        module_name = f"vitaloom_plugin_{file_path.stem}_{int(time.time() * 1000)}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise RuntimeError(f"无法加载插件模块: {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, IEditorPlugin)
                and obj != IEditorPlugin
                and not inspect.isabstract(obj)
            ):
                plugin_instance = obj()
                info = plugin_instance.get_plugin_info()
                plugin_name = info.get("name")
                if not plugin_name:
                    raise ValueError(f"插件类 {name} 缺少 name 字段")
                return plugin_name, plugin_instance
        raise RuntimeError(f"未在 {file_path} 中找到 IEditorPlugin 实现")

    def reload_plugin(self, plugin_name: str):
        """卸载并从磁盘重新加载插件（user_mod / official_mod 开发热重载）。"""
        if plugin_name not in self.loaded_plugins and plugin_name not in self.plugin_files:
            logger.warning("插件未加载: %s", plugin_name)
            return False

        if plugin_name in self.protected_plugins:
            logger.warning("核心插件受保护，禁止重载: %s", plugin_name)
            return False

        file_path_str = self.plugin_files.get(plugin_name)
        if not file_path_str:
            logger.warning("未记录插件文件路径，无法热重载: %s", plugin_name)
            return False
        file_path = Path(file_path_str)
        if not file_path.is_file():
            logger.warning("插件文件不存在: %s", file_path)
            return False

        scope = self.plugin_scopes.get(plugin_name, self.SCOPE_UNKNOWN)
        if plugin_name in self.loaded_plugins and not self.unload_plugin(plugin_name):
            return False

        try:
            discovered_name, plugin_instance = self._instantiate_plugin_from_file(file_path)
            if discovered_name != plugin_name:
                logger.warning(
                    "插件名不一致，跳过热重载: expected=%s actual=%s",
                    plugin_name,
                    discovered_name,
                )
                return False
            info = plugin_instance.get_plugin_info()
            self.loaded_plugins[plugin_name] = plugin_instance
            self.plugin_dependencies[plugin_name] = info.get("dependencies", [])
            self.plugin_scopes[plugin_name] = scope
            self.plugin_files[plugin_name] = str(file_path)
            if plugin_name not in self.plugin_order:
                self.plugin_order.append(plugin_name)
            if bool(info.get("protected", False)) or scope == self.SCOPE_CORE:
                self.protected_plugins.add(plugin_name)
            self._load_plugin(plugin_instance)
            logger.info("插件热重载成功: %s", plugin_name)
            return True
        except Exception:
            logger.exception("热重载插件失败: %s", plugin_name)
            return False

    def get_plugin_scope(self, plugin_name: str) -> str:
        """PluginLoader.get_plugin_scope。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return self.plugin_scopes.get(plugin_name, self.SCOPE_UNKNOWN)

    def is_plugin_protected(self, plugin_name: str) -> bool:
        """PluginLoader.is_plugin_protected。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        return plugin_name in self.protected_plugins