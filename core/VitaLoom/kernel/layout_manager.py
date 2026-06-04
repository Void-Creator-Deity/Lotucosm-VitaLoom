"""布局管理器：Dock/视口标签/菜单/工具栏与 `~/.vitaloom` 布局持久化。

架构数据流::

    IDockProvider → add_dock → restore_layout / apply_default_workspace_layout

排错: 见 core/VitaLoom/README.md「插件」「布局」
"""

from PyQt6.QtWidgets import (
    QDockWidget, QMenuBar, QToolBar, QWidget, QMenu, 
    QStatusBar, QTabWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QByteArray, QSettings
from PyQt6.QtGui import QAction, QGuiApplication, QIcon
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from core.VitaLoom.core.logger import get_logger


logger = get_logger("LayoutManager")


def _set_action_icon(action: QAction, icon_spec: object) -> None:
    """从文件路径、主题名或 QIcon 为 QAction 设置图标。"""
    if icon_spec is None:
        return
    if isinstance(icon_spec, QIcon):
        if not icon_spec.isNull():
            action.setIcon(icon_spec)
        return
    if isinstance(icon_spec, str):
        s = icon_spec.strip()
        if not s:
            return
        if os.path.isfile(s):
            ic = QIcon(s)
        else:
            ic = QIcon.fromTheme(s)
        if not ic.isNull():
            action.setIcon(ic)


class LayoutManager:
    """职责: 管理主窗口 Dock、中央视口标签、菜单/工具栏及布局 JSON 缓存。
    时机: `EditorKernel.__init__` 创建；插件 `on_load` 注册 UI；关闭时 `save_layout`。
    不变量: Dock `objectName` 等于 config title；`tabbed_with` 可延迟 `_pending_tabify`。
    排错: Dock 叠放失败 → `process_pending_dock_tabify`；视口空白 → `switch_viewport`。
    """
    
    def __init__(self, main_window):
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
        self.main_window = main_window
        self.docks: Dict[str, QDockWidget] = {}
        self.viewports: Dict[str, QWidget] = {}
        self.viewport_providers: Dict[str, Any] = {}  # 存储视口提供者
        self.current_viewport = None
        self._is_switching_viewport = False
        self._plugin_menu_actions: Dict[str, List[tuple[QMenu, QAction]]] = {}
        self._plugin_toolbar_actions: Dict[str, List[QAction]] = {}
        self._pending_tabify: List[Tuple[str, str]] = []
        
        # 布局配置路径
        self.layout_config_path = os.path.join(
            os.path.expanduser("~"), 
            ".vitaloom", 
            "layout_config.json"
        )
        
        # 创建菜单栏和工具栏（空的，由插件填充）
        self.menubar = QMenuBar()
        self.main_window.setMenuBar(self.menubar)
        
        # 工具栏可以移动（参考Unity）
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(True)
        self.toolbar.setFloatable(True)
        self.main_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # 创建状态栏（参考Unity）
        self.statusbar = QStatusBar()
        self.main_window.setStatusBar(self.statusbar)
        self.statusbar.showMessage(self._tr("status.ready", "就绪"))
        
        # 视口标签页容器（用于在中央区域切换多个视口）
        self.viewport_tabs: Optional[QTabWidget] = None
        self._setup_viewport_tabs()
    
    def add_dock(self, dock_widget: QDockWidget, config: Dict[str, Any]):
        """职责: 将插件 Dock 挂到主窗口，支持 tabbed_with 与几何记忆。
        时机: `PluginLoader._register_dock` 在插件 on_load 后调用。
        不变量: 同 title 先 remove_dock；area 默认 LeftDockWidgetArea。
        排错: 面板不可见 → default_visible 与 restore 后状态。
        """
        title = config["title"]
        if title in self.docks:
            self.remove_dock(title)
        dock_widget.setObjectName(title)
        area = config.get("area", Qt.DockWidgetArea.LeftDockWidgetArea)
        visible = config.get("default_visible", True)
        tabbed_with = config.get("tabbed_with", None)
        can_close = config.get("can_close", True)
        can_float = config.get("can_float", True)
        can_move = config.get("can_move", True)

        features = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        if can_move:
            features |= QDockWidget.DockWidgetFeature.DockWidgetMovable
        if can_float:
            features |= QDockWidget.DockWidgetFeature.DockWidgetFloatable
        if can_close:
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        dock_widget.setFeatures(features)
        
        # 标签化：伙伴已存在则立即 tabify；否则先停靠并排队，待伙伴注册后再 tabify
        if tabbed_with and tabbed_with in self.docks:
            self.main_window.tabifyDockWidget(self.docks[tabbed_with], dock_widget)
        else:
            self.main_window.addDockWidget(area, dock_widget)
            if tabbed_with:
                self._pending_tabify = [p for p in self._pending_tabify if p[0] != title]
                self._pending_tabify.append((title, tabbed_with))
        
        dock_widget.setVisible(visible)
        self.docks[title] = dock_widget
        self._process_pending_tabify()
        
        logger.info("已添加 Dock 面板: %s", title)
    
    def remove_dock(self, title: str):
        """移除 Dock 面板。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if title not in self.docks:
            logger.warning("Dock 面板不存在: %s", title)
            return
        
        dock_widget = self.docks.pop(title)
        self._pending_tabify = [p for p in self._pending_tabify if p[0] != title and p[1] != title]
        if dock_widget and hasattr(self.main_window, 'removeDockWidget'):
            self.main_window.removeDockWidget(dock_widget)
            dock_widget.deleteLater()
            logger.info("已移除 Dock 面板: %s", title)

    def _process_pending_tabify(self):
        """尝试完成因伙伴 dock 尚未加载而推迟的 tabify。"""
        if not self._pending_tabify:
            return
        remaining: List[Tuple[str, str]] = []
        for child_title, host_title in self._pending_tabify:
            child = self.docks.get(child_title)
            host = self.docks.get(host_title)
            if child and host:
                try:
                    self.main_window.tabifyDockWidget(host, child)
                except Exception as exc:
                    logger.warning("tabify 失败: %s + %s: %s", host_title, child_title, exc)
            elif child_title in self.docks:
                remaining.append((child_title, host_title))
        self._pending_tabify = remaining

    def process_pending_dock_tabify(self):
        """对外显式刷新延迟 tabify（例如在批量注册 dock 结束后调用）。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self._process_pending_tabify()

    def apply_default_workspace_layout(self):
        """应用更友好的默认编辑器布局。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        # 左侧：Hierarchy
        left = self.docks.get("Hierarchy")
        if left:
            self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left)

        # 右侧：Inspector + Plugin Manager 标签化
        right_primary = self.docks.get("Inspector")
        right_secondary = self.docks.get("Plugin Manager")
        if right_primary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_primary)
        if right_primary and right_secondary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_secondary)
            self.main_window.tabifyDockWidget(right_primary, right_secondary)
            right_secondary.hide()

        # 底部：Project + Console 标签化
        bottom_primary = self.docks.get("Project")
        bottom_secondary = self.docks.get("Console")
        if bottom_primary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_primary)
        if bottom_primary and bottom_secondary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_secondary)
            self.main_window.tabifyDockWidget(bottom_primary, bottom_secondary)

        # 调整分区比例
        dock_list = []
        size_list = []
        for title, size in [("Hierarchy", 280), ("Inspector", 320), ("Project", 300)]:
            dock = self.docks.get(title)
            if dock:
                dock_list.append(dock)
                size_list.append(size)
        if dock_list:
            self.main_window.resizeDocks(dock_list, size_list, Qt.Orientation.Horizontal)

    def _tr(self, key: str, default: str = "") -> str:
        context = getattr(self.main_window, "editor_context", None)
        tr_fn = getattr(context, "i18n_tr", None) if context is not None else None
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key
    
    def _setup_viewport_tabs(self):
        """设置视口标签页容器"""
        # 如果使用标签页系统，将central_stack替换为标签页
        if hasattr(self.main_window, 'central_stack'):
            # 将central_stack包装在标签页中
            self.viewport_tabs = QTabWidget()
            self.viewport_tabs.setTabsClosable(False)
            self.viewport_tabs.setMovable(True)  # 允许拖拽标签页重新排序
            self.viewport_tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 1px solid #404040;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    padding: 8px 16px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 2px solid #0e639c;
                }
                QTabBar::tab:hover {
                    background-color: #3e3e42;
                }
            """)
            # 连接标签页切换信号
            self.viewport_tabs.currentChanged.connect(self._on_viewport_tab_changed)
    
    # === 视口: 标签注册与切换 ==================================================
    def add_viewport(self, viewport_id: str, viewport_widget: QWidget, provider=None):
        """职责: 在中央 QTabWidget 注册视口页。
        时机: `PluginLoader._register_viewport`。
        不变量: viewport_id 唯一；provider 可选存于 viewport_providers。
        排错: 标签无内容 → widget 是否 None；重复 id 覆盖旧页。
        """
        if viewport_id in self.viewports:
            self.remove_viewport(viewport_id)
        self.viewports[viewport_id] = viewport_widget
        if provider:
            self.viewport_providers[viewport_id] = provider
        
        # 获取视口名称
        viewport_name = provider.get_viewport_name() if provider and hasattr(provider, 'get_viewport_name') else viewport_id
        
        # 使用标签页系统（参考Unity）
        if self.viewport_tabs:
            self.viewport_tabs.addTab(viewport_widget, viewport_name)
        else:
            # 回退到旧的堆栈方式
            if hasattr(self.main_window, 'central_stack'):
                self.main_window.central_stack.addWidget(viewport_widget)
        
        # 如果是第一个视口，设为当前视口
        if self.current_viewport is None:
            self.switch_viewport(viewport_id)
        
        logger.info("已添加视口: %s (%s)", viewport_id, viewport_name)
    
    def remove_viewport(self, viewport_id: str):
        """移除视口。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if viewport_id not in self.viewports:
            logger.warning("视口不存在: %s", viewport_id)
            return
        
        viewport_widget = self.viewports.pop(viewport_id)
        
        # 从标签页或堆栈中移除
        if self.viewport_tabs:
            index = self.viewport_tabs.indexOf(viewport_widget)
            if index >= 0:
                self.viewport_tabs.removeTab(index)
        elif hasattr(self.main_window, 'central_stack'):
            self.main_window.central_stack.removeWidget(viewport_widget)
        
        viewport_widget.deleteLater()
        
        if viewport_id in self.viewport_providers:
            del self.viewport_providers[viewport_id]
        
        # 如果移除的是当前视口，切换到其他视口
        if self.current_viewport == viewport_id:
            self.current_viewport = None
            # 切换到第一个可用的视口
            if self.viewports:
                first_viewport_id = next(iter(self.viewports.keys()))
                self.switch_viewport(first_viewport_id)
        
        logger.info("已移除视口: %s", viewport_id)
    
    def switch_viewport(self, viewport_id: str):
        """职责: 激活指定视口并通知 provider（若有 on_viewport_activated）。
        时机: 菜单/快捷键或标签切换回调。
        不变量: `_is_switching_viewport` 防重入。
        排错: 切换无效 → viewport_id 是否在 viewports 字典。
        """
        """切换视口
        
        Args:
            viewport_id: 视口 ID
        """
        if viewport_id not in self.viewports:
            logger.warning("视口不存在: %s", viewport_id)
            return
        
        # 如果已经是当前视口，不需要切换
        if self.current_viewport == viewport_id or self._is_switching_viewport:
            return
        self._is_switching_viewport = True
        
        try:
            # 停用当前视口
            if self.current_viewport and self.current_viewport in self.viewport_providers:
                try:
                    self.viewport_providers[self.current_viewport].on_viewport_deactivated()
                except Exception as e:
                    logger.exception("停用视口失败: %s", e)
            
            # 切换视口
            widget = self.viewports[viewport_id]
            if self.viewport_tabs:
                index = self.viewport_tabs.indexOf(widget)
                if index >= 0 and self.viewport_tabs.currentIndex() != index:
                    self.viewport_tabs.setCurrentIndex(index)
            elif widget and hasattr(self.main_window, 'central_stack'):
                self.main_window.central_stack.setCurrentWidget(widget)
            
            self.current_viewport = viewport_id
            
            # 激活新视口
            if viewport_id in self.viewport_providers:
                try:
                    self.viewport_providers[viewport_id].on_viewport_activated()
                except Exception as e:
                    logger.exception("激活视口失败: %s", e)
            
            # 更新状态栏
            viewport_name = viewport_id
            if viewport_id in self.viewport_providers:
                provider = self.viewport_providers[viewport_id]
                if hasattr(provider, 'get_viewport_name'):
                    viewport_name = provider.get_viewport_name()
            self.statusbar.showMessage(
                self._tr("status.current_viewport", "当前视口: {name}").format(name=viewport_name),
                3000,
            )
            
            logger.info("切换到视口: %s", viewport_id)
        finally:
            self._is_switching_viewport = False
    
    def _on_viewport_tab_changed(self, index: int):
        """视口标签页切换事件处理"""
        if self.viewport_tabs and index >= 0:
            widget = self.viewport_tabs.widget(index)
            # 找到对应的viewport_id
            for vp_id, vp_widget in self.viewports.items():
                if vp_widget == widget:
                    self.switch_viewport(vp_id)
                    break
    
    def get_current_viewport(self) -> Optional[QWidget]:
        """获取当前活动的视口部件。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        if self.current_viewport and self.current_viewport in self.viewports:
            return self.viewports[self.current_viewport]
        return None
    
    def add_menu_items(self, menu_items: List[Dict[str, Any]], plugin_name: Optional[str] = None):
        """添加菜单项。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for item in menu_items:
            # 支持分隔线
            if item.get('separator', False):
                path_parts = item.get('path', '').split('/')
                parent_path = path_parts[:-1] if len(path_parts) > 1 else path_parts
                parent_menu = self._get_or_create_menu(parent_path)
                sep_action = parent_menu.addSeparator()
                if plugin_name:
                    self._plugin_menu_actions.setdefault(plugin_name, []).append((parent_menu, sep_action))
                continue

            path = item["path"].split("/")
            menu = self._get_or_create_menu(path[:-1])

            action_fn = item.get("action", None)
            if action_fn is None:
                # action 为 None 时添加分隔线
                sep_action = menu.addSeparator()
                if plugin_name:
                    self._plugin_menu_actions.setdefault(plugin_name, []).append((menu, sep_action))
                continue

            if not callable(action_fn):
                logger.warning("菜单项回调不可调用，已跳过: %s", item.get("path", ""))
                continue

            action = menu.addAction(path[-1])
            action.triggered.connect(action_fn)
            if plugin_name:
                self._plugin_menu_actions.setdefault(plugin_name, []).append((menu, action))
            
            shortcut = item.get("shortcut", None)
            if shortcut:
                action.setShortcut(shortcut)
            
            if "icon" in item:
                _set_action_icon(action, item["icon"])
    
    def add_toolbar_items(self, toolbar_items: List[Dict[str, Any]], plugin_name: Optional[str] = None):
        """添加工具栏项。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for item in toolbar_items:
            if item.get("separator", False):
                sep_action = self.toolbar.addSeparator()
                if plugin_name:
                    self._plugin_toolbar_actions.setdefault(plugin_name, []).append(sep_action)
            else:
                action_fn = item.get("action")
                if not callable(action_fn):
                    logger.warning("工具栏项回调不可调用，已跳过: %s", item.get("text", ""))
                    continue

                action = self.toolbar.addAction(item["text"])
                action.triggered.connect(action_fn)
                if plugin_name:
                    self._plugin_toolbar_actions.setdefault(plugin_name, []).append(action)
                
                if "icon" in item:
                    _set_action_icon(action, item["icon"])
    
    def _get_or_create_menu(self, path: List[str]) -> QMenu:
        """获取或创建菜单
        
        Args:
            path: 菜单路径
            
        Returns:
            QMenu: 菜单对象
        """
        if not path:
            return self.menubar
        
        current_menu = None
        for name in path:
            # 查找已存在的菜单
            found = False
            if current_menu is None:
                # 在菜单栏中查找
                for action in self.menubar.actions():
                    if action.text() == name and action.menu():
                        current_menu = action.menu()
                        found = True
                        break
                if not found:
                    current_menu = self.menubar.addMenu(name)
            else:
                # 在子菜单中查找
                for action in current_menu.actions():
                    if action.text() == name and action.menu():
                        current_menu = action.menu()
                        found = True
                        break
                if not found:
                    current_menu = current_menu.addMenu(name)
        
        return current_menu
    
    def register_theme(self, name: str, stylesheet: str):
        """注册主题。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        self.main_window.setStyleSheet(stylesheet)
        logger.info("已应用主题: %s", name)

    def remove_plugin_ui(self, plugin_name: str):
        """移除插件通过菜单/工具栏注册的 UI 元素。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        for menu, action in self._plugin_menu_actions.pop(plugin_name, []):
            menu.removeAction(action)
        for action in self._plugin_toolbar_actions.pop(plugin_name, []):
            self.toolbar.removeAction(action)
        self._prune_empty_menus()

    def _menu_has_effective_actions(self, menu: QMenu) -> bool:
        """菜单是否还包含有效动作（非分隔线或非空子菜单）。"""
        for action in menu.actions():
            if action.isSeparator():
                continue
            sub_menu = action.menu()
            if sub_menu:
                if self._menu_has_effective_actions(sub_menu):
                    return True
                continue
            return True
        return False

    def _prune_empty_menus(self):
        """递归删除菜单栏中的空菜单，避免语言切换后残留旧语种菜单壳。"""
        changed = True
        while changed:
            changed = False
            for action in list(self.menubar.actions()):
                menu = action.menu()
                if not menu:
                    continue
                if not self._menu_has_effective_actions(menu):
                    self.menubar.removeAction(action)
                    changed = True
    
    # === 布局: 持久化与恢复 ====================================================
    def save_layout(self):
        """职责: 将主窗口状态与 Dock 几何写入 QSettings / JSON。
        时机: `EditorKernel.closeEvent` 或用户保存布局。
        不变量: 路径 `layout_config_path` 位于用户目录 `.vitaloom`。
        排错: 重启布局丢失 → 检查目录权限与 save 是否被调用。
        """
        """保存当前布局状态（参考Unity的布局保存功能）"""
        try:
            # 保存窗口状态
            window_state = self.main_window.saveState()
            
            # 保存窗口几何信息
            geometry = {
                'x': self.main_window.geometry().x(),
                'y': self.main_window.geometry().y(),
                'width': self.main_window.geometry().width(),
                'height': self.main_window.geometry().height()
            }
            
            # 保存Dock面板状态
            dock_states = {}
            for title, dock in self.docks.items():
                st: Dict[str, Any] = {
                    'visible': dock.isVisible(),
                    'floating': dock.isFloating(),
                    'area': int(self.main_window.dockWidgetArea(dock).value) if not dock.isFloating() else None,
                    'geometry': {
                        'x': dock.geometry().x(),
                        'y': dock.geometry().y(),
                        'width': dock.geometry().width(),
                        'height': dock.geometry().height()
                    }
                }
                if dock.isFloating():
                    try:
                        st['save_geometry_hex'] = bytes(dock.saveGeometry()).hex()
                    except Exception as e:
                        logger.debug("保存 Dock geometry 失败: %s", e)
                dock_states[title] = st
            
            # 保存视口状态
            viewport_state = {
                'current': self.current_viewport,
                'tabs_order': []
            }
            if self.viewport_tabs:
                for i in range(self.viewport_tabs.count()):
                    widget = self.viewport_tabs.widget(i)
                    for vp_id, vp_widget in self.viewports.items():
                        if vp_widget == widget:
                            viewport_state['tabs_order'].append(vp_id)
                            break
            
            # 保存到文件
            layout_data = {
                'window_state': window_state.toBase64().data().decode('utf-8'),
                'geometry': geometry,
                'dock_states': dock_states,
                'viewport_state': viewport_state
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.layout_config_path), exist_ok=True)
            
            with open(self.layout_config_path, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2, ensure_ascii=False)
            
            logger.info("布局已保存: %s", self.layout_config_path)
            self.statusbar.showMessage(self._tr("status.layout_saved", "布局已保存"), 2000)
            return True
        except Exception as e:
            logger.exception("保存布局失败: %s", e)
            return False
    
    def restore_layout(self):
        """职责: 从缓存恢复窗口与 Dock；失败返回 False 供默认布局兜底。
        时机: 插件加载后 QTimer 延迟调用。
        不变量: 无缓存或解析失败时不抛异常，返回 False。
        排错: 每次启动默认布局 → restore 返回 False；见 `apply_default_workspace_layout`。
        """
        """恢复保存的布局状态"""
        try:
            if not os.path.exists(self.layout_config_path):
                logger.info("未找到保存的布局配置，使用默认布局")
                return False
            
            with open(self.layout_config_path, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
            
            # 恢复窗口几何信息
            if 'geometry' in layout_data:
                geom = layout_data['geometry']
                x = int(geom.get('x', 100))
                y = int(geom.get('y', 100))
                width = max(640, int(geom.get('width', 1600)))
                height = max(480, int(geom.get('height', 900)))
                self.main_window.setGeometry(x, y, width, height)
            
            # 恢复窗口状态（包括Dock布局）
            if 'window_state' in layout_data:
                state_data = QByteArray.fromBase64(
                    layout_data['window_state'].encode('utf-8')
                )
                self.main_window.restoreState(state_data)
            
            # 恢复Dock面板状态
            if 'dock_states' in layout_data:
                for title, state in layout_data['dock_states'].items():
                    if title in self.docks:
                        dock = self.docks[title]
                        if 'visible' in state:
                            dock.setVisible(state['visible'])
                        if 'floating' in state and state['floating']:
                            dock.setFloating(True)
                            hex_blob = state.get('save_geometry_hex')
                            if isinstance(hex_blob, str) and hex_blob:
                                try:
                                    dock.restoreGeometry(QByteArray(bytes.fromhex(hex_blob)))
                                except Exception:
                                    hex_blob = None
                            if not hex_blob and 'geometry' in state:
                                geom = state['geometry']
                                x = int(geom.get('x', 100))
                                y = int(geom.get('y', 100))
                                width = max(200, int(geom.get('width', 320)))
                                height = max(120, int(geom.get('height', 240)))
                                dock.setGeometry(x, y, width, height)
                            self._ensure_dock_on_screen(dock)
            
            # 恢复视口状态（只在视口已加载时才切换）
            if 'viewport_state' in layout_data:
                vp_state = layout_data['viewport_state']
                if 'current' in vp_state and vp_state['current']:
                    target_vp = vp_state['current']
                    if target_vp in self.viewports:
                        self.switch_viewport(target_vp)
                    # 否则静默忽略，等插件加载完再切换
            
            logger.info("布局已恢复: %s", self.layout_config_path)
            self.statusbar.showMessage(self._tr("status.layout_restored", "布局已恢复"), 2000)
            return True
        except Exception as e:
            logger.exception("恢复布局失败: %s", e)
            return False
    
    def reset_layout(self):
        """重置为默认布局。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        try:
            # 显示所有Dock面板
            for dock in self.docks.values():
                dock.setVisible(True)
                dock.setFloating(False)
            
            # 重置窗口大小
            self.main_window.setGeometry(100, 100, 1600, 900)
            
            # 切换到第一个视口
            if self.viewports:
                first_viewport_id = next(iter(self.viewports.keys()))
                self.switch_viewport(first_viewport_id)
            
            logger.info("布局已重置为默认")
            self.statusbar.showMessage(self._tr("status.layout_reset", "布局已重置"), 2000)
            return True
        except Exception as e:
            logger.exception("重置布局失败: %s", e)
            return False


    def _dock_geometry_cache_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".vitaloom", "dock_geometry_cache.json")

    def _read_dock_geometry_cache(self) -> Dict[str, Any]:
        path = self._dock_geometry_cache_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_dock_geometry_cache(self, data: Dict[str, Any]):
        try:
            path = self._dock_geometry_cache_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("写入 dock 几何缓存失败: %s", e)

    def _ensure_dock_on_screen(self, dock: QDockWidget):
        """浮动 dock 完全落在所有屏幕之外时，挪到主屏可用区内。"""
        try:
            if not dock.isFloating():
                return
            fg = dock.frameGeometry()
            if fg.isNull():
                return
            for screen in QGuiApplication.screens():
                if screen.availableGeometry().intersects(fg):
                    return
            scr = QGuiApplication.primaryScreen()
            if not scr:
                return
            ag = scr.availableGeometry()
            dock.move(ag.x() + 32, ag.y() + 32)
        except Exception as e:
            logger.debug("校正浮动 Dock 位置失败: %s", e)

    def remember_dock_geometry(self, title: str):
        """LayoutManager.remember_dock_geometry。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        dock = self.docks.get(title)
        if not dock:
            return
        if not dock.isFloating():
            return
        cache = self._read_dock_geometry_cache()
        geo = dock.geometry()
        entry: Dict[str, Any] = {
            "x": int(geo.x()),
            "y": int(geo.y()),
            "width": int(max(200, geo.width())),
            "height": int(max(120, geo.height())),
        }
        try:
            entry["save_geometry_hex"] = bytes(dock.saveGeometry()).hex()
        except Exception as e:
            logger.debug("缓存 Dock geometry 失败: title=%s error=%s", title, e)
        cache[title] = entry
        self._write_dock_geometry_cache(cache)

    def restore_dock_geometry(self, title: str):
        """LayoutManager.restore_dock_geometry。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        dock = self.docks.get(title)
        if not dock:
            return
        cache = self._read_dock_geometry_cache()
        info = cache.get(title)
        if not isinstance(info, dict):
            return
        try:
            hex_blob = info.get("save_geometry_hex")
            if isinstance(hex_blob, str) and hex_blob:
                dock.restoreGeometry(QByteArray(bytes.fromhex(hex_blob)))
            else:
                x = int(info.get("x", 100))
                y = int(info.get("y", 100))
                w = int(max(200, info.get("width", 320)))
                h = int(max(120, info.get("height", 240)))
                dock.setGeometry(x, y, w, h)
            self._ensure_dock_on_screen(dock)
        except Exception:
            return

    def show_dock_with_mode(self, title: str, floating: bool):
        """LayoutManager.show_dock_with_mode。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        dock = self.docks.get(title)
        if not dock:
            return
        if floating:
            dock.setFloating(True)
            self.restore_dock_geometry(title)
        else:
            self.remember_dock_geometry(title)
            dock.setFloating(False)
        dock.setVisible(True)
        dock.show()
        dock.raise_()
        if floating:
            dock.activateWindow()

    def show_dock(self, title: str, *, floating: Optional[bool] = None) -> bool:
        """显示并置前指定 Dock；不存在时返回 False。"""
        dock = self.docks.get(title)
        if not dock:
            logger.warning("Dock 不存在: %s", title)
            return False
        use_float = dock.isFloating() if floating is None else bool(floating)
        self.show_dock_with_mode(title, use_float)
        return True

    def toggle_dock_floating(self, title: str):
        """LayoutManager.toggle_dock_floating。

        
        职责:
            执行本函数声明的对外行为（见实现）。
        
        时机:
            由调用方在对应生命周期内调用。
        
        不变量:
            不破坏模块顶 docstring 与同级契约。
        
        排错:
            异常时见本文件模块说明与子树 README 排错表。
        """

        dock = self.docks.get(title)
        if not dock:
            return
        if dock.isFloating():
            self.remember_dock_geometry(title)
            dock.setFloating(False)
        else:
            dock.setFloating(True)
            self.restore_dock_geometry(title)
            dock.raise_()
            dock.activateWindow()

