"""Dock、视口标签、菜单和布局持久化。"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Tuple

from PyQt6.QtCore import QByteArray, QSettings, Qt
from PyQt6.QtGui import QAction, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMenu,
    QMenuBar,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.VitaLoom.core.logger import get_logger

from .editor_layout_state import EditorLayoutState


logger = get_logger("LayoutManager")


def _state_home() -> str:
    """Return the writable editor state directory."""
    return os.environ.get(
        "VITALOOM_STATE_HOME",
        os.path.join(os.path.expanduser("~"), ".vitaloom"),
    )

def _set_action_icon(action: QAction, icon_spec: object) -> None:
    """Resolve a path, theme icon name, or ready-made QIcon."""
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
    """Manage editor docks, viewport tabs, menus, and persisted layout."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.docks: Dict[str, QDockWidget] = {}
        self.viewports: Dict[str, QWidget] = {}
        self.viewport_providers: Dict[str, Any] = {}
        self.viewport_display_names: Dict[str, str] = {}
        self._host_named_viewports: set[str] = set()
        self.current_viewport = None
        self._is_switching_viewport = False
        self._plugin_menu_actions: Dict[str, List[tuple[QMenu, QAction]]] = {}
        self._plugin_toolbar_actions: Dict[str, List[QAction]] = {}
        self._pending_tabify: List[Tuple[str, str]] = []
        self.state_home = _state_home()
        self.layout_config_path = os.path.join(
            self.state_home,
            "layout_config.json",
        )
        self.menubar = QMenuBar()
        self.main_window.setMenuBar(self.menubar)
        self.toolbar = QToolBar('Main Toolbar')
        self.toolbar.setObjectName('MainToolbar')
        self.toolbar.setMovable(True)
        self.toolbar.setFloatable(True)
        self.main_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.statusbar = QStatusBar()
        self.main_window.setStatusBar(self.statusbar)
        self.statusbar.showMessage(self._tr('status.ready', '就绪'))
        self.viewport_tabs: Optional[QTabWidget] = None
        self._setup_viewport_tabs()

    def add_dock(self, dock_widget: QDockWidget, config: Dict[str, Any]):
        """Register a dock and defer tabification until its host exists."""
        title = config["title"]
        if title in self.docks:
            self.remove_dock(title)
        dock_widget.setObjectName(title)
        area = config.get("area", Qt.DockWidgetArea.LeftDockWidgetArea)
        visible = config.get("default_visible", True)
        tabbed_with = config.get("tabbed_with")
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
        if tabbed_with and tabbed_with in self.docks:
            self.main_window.tabifyDockWidget(self.docks[tabbed_with], dock_widget)
        else:
            self.main_window.addDockWidget(area, dock_widget)
            if tabbed_with:
                self._pending_tabify = [
                    pair for pair in self._pending_tabify if pair[0] != title
                ]
                self._pending_tabify.append((title, tabbed_with))
        dock_widget.setVisible(visible)
        self.docks[title] = dock_widget
        self._process_pending_tabify()
        logger.info('已添加 Dock 面板: %s', title)

    def remove_dock(self, title: str):
        """Remove a registered dock if present."""
        if title not in self.docks:
            logger.warning('Dock 面板不存在: %s', title)
            return
        dock_widget = self.docks.pop(title)
        self._pending_tabify = [
            pair
            for pair in self._pending_tabify
            if pair[0] != title and pair[1] != title
        ]
        if dock_widget and hasattr(self.main_window, 'removeDockWidget'):
            self.main_window.removeDockWidget(dock_widget)
            dock_widget.deleteLater()
            logger.info('已移除 Dock 面板: %s', title)

    def _process_pending_tabify(self):
        """Retry deferred tabification for docks registered out of order."""
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
                    logger.warning('tabify 失败: %s + %s: %s', host_title, child_title, exc)
            elif child_title in self.docks:
                remaining.append((child_title, host_title))
        self._pending_tabify = remaining

    def process_pending_dock_tabify(self):
        """Explicitly retry deferred dock tabification."""
        self._process_pending_tabify()

    def apply_default_workspace_layout(self):
        """Apply the editor's default dock arrangement."""
        left = self.docks.get('Hierarchy')
        if left:
            self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left)
        right_primary = self.docks.get('Inspector')
        right_secondary = self.docks.get('Plugin Manager')
        if right_primary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_primary)
        if right_primary and right_secondary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_secondary)
            self.main_window.tabifyDockWidget(right_primary, right_secondary)
            right_secondary.hide()
        bottom_primary = self.docks.get('Project')
        bottom_secondary = self.docks.get('Console')
        if bottom_primary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_primary)
        if bottom_primary and bottom_secondary:
            self.main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom_secondary)
            self.main_window.tabifyDockWidget(bottom_primary, bottom_secondary)
        dock_list = []
        size_list = []
        for title, size in [('Hierarchy', 280), ('Inspector', 320), ('Project', 300)]:
            dock = self.docks.get(title)
            if dock:
                dock_list.append(dock)
                size_list.append(size)
        if dock_list:
            self.main_window.resizeDocks(dock_list, size_list, Qt.Orientation.Horizontal)

    def _tr(self, key: str, default: str = "") -> str:
        context = getattr(self.main_window, 'editor_context', None)
        tr_fn = getattr(context, 'i18n_tr', None) if context is not None else None
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _setup_viewport_tabs(self):
        """Create the central viewport tab shell when the host supports it."""
        if hasattr(self.main_window, 'central_stack'):
            self.viewport_tabs = QTabWidget()
            self.viewport_tabs.setTabsClosable(False)
            self.viewport_tabs.setMovable(True)
            self.viewport_tabs.setStyleSheet(
                """
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
                """
            )
            self.viewport_tabs.currentChanged.connect(self._on_viewport_tab_changed)

    def add_viewport(
        self,
        viewport_id: str,
        viewport_widget: QWidget,
        provider=None,
        display_name: str | None = None,
    ):
        """Register a viewport, failing closed if replacement cleanup fails."""
        if viewport_id in self.viewports:
            if not self.remove_viewport(viewport_id):
                discard = getattr(viewport_widget, 'deleteLater', None)
                if callable(discard):
                    discard()
                raise RuntimeError(
                    "cannot replace viewport while its existing runtime cleanup failed: "
                    f"{viewport_id}"
                )
        self.viewports[viewport_id] = viewport_widget
        if provider:
            self.viewport_providers[viewport_id] = provider
        viewport_name = display_name
        if viewport_name is None:
            viewport_name = (
                provider.get_viewport_name()
                if provider and hasattr(provider, "get_viewport_name")
                else viewport_id
            )
        else:
            self._host_named_viewports.add(viewport_id)
        self.viewport_display_names[viewport_id] = viewport_name
        if self.viewport_tabs is not None:
            self.viewport_tabs.addTab(viewport_widget, viewport_name)
        elif hasattr(self.main_window, 'central_stack'):
            self.main_window.central_stack.addWidget(viewport_widget)
        if self.current_viewport is None:
            self.switch_viewport(viewport_id)
        logger.info('已添加视口: %s (%s)', viewport_id, viewport_name)

    def set_viewport_display_name(self, viewport_id: str, display_name: str) -> None:
        """Rename an existing host-owned viewport without recreating it."""
        if viewport_id not in self.viewports:
            raise KeyError(f'viewport does not exist: {viewport_id}')
        name = str(display_name or viewport_id)
        self.viewport_display_names[viewport_id] = name
        self._host_named_viewports.add(viewport_id)
        if self.viewport_tabs is not None:
            widget = self.viewports[viewport_id]
            index = self.viewport_tabs.indexOf(widget)
            if index >= 0:
                self.viewport_tabs.setTabText(index, name)

    def dispose_viewport_runtime_capabilities(self) -> dict[str, tuple[str, ...]]:
        """Release runtime capabilities owned by registered viewport widgets."""
        disposed: list[str] = []
        failed: list[str] = []
        for viewport_id, viewport_widget in tuple(self.viewports.items()):
            disposer = getattr(viewport_widget, 'dispose_runtime_capabilities', None)
            if not callable(disposer):
                continue
            try:
                disposer()
            except Exception:
                failed.append(viewport_id)
                logger.exception('视口运行时能力释放失败: %s', viewport_id)
            else:
                disposed.append(viewport_id)
        return {'disposed': tuple(disposed), 'failed': tuple(failed)}

    def remove_viewport(self, viewport_id: str):
        """Remove a viewport after its runtime cleanup succeeds."""
        if viewport_id not in self.viewports:
            logger.warning('视口不存在: %s', viewport_id)
            return False
        viewport_widget = self.viewports[viewport_id]
        disposer = getattr(viewport_widget, 'dispose_runtime_capabilities', None)
        if callable(disposer):
            try:
                disposer()
            except Exception:
                logger.exception('移除前释放视口运行时能力失败: %s', viewport_id)
                return False
        viewport_widget = self.viewports.pop(viewport_id)
        if self.viewport_tabs is not None:
            index = self.viewport_tabs.indexOf(viewport_widget)
            if index >= 0:
                self.viewport_tabs.removeTab(index)
        elif hasattr(self.main_window, 'central_stack'):
            self.main_window.central_stack.removeWidget(viewport_widget)
        viewport_widget.deleteLater()
        if viewport_id in self.viewport_providers:
            del self.viewport_providers[viewport_id]
        getattr(self, 'viewport_display_names', {}).pop(viewport_id, None)
        getattr(self, '_host_named_viewports', set()).discard(viewport_id)
        if self.current_viewport == viewport_id:
            self.current_viewport = None
            if self.viewports:
                first_viewport_id = next(iter(self.viewports.keys()))
                self.switch_viewport(first_viewport_id)
        logger.info('已移除视口: %s', viewport_id)
        return True

    def switch_viewport(self, viewport_id: str):
        """Activate a viewport and notify its provider."""
        if viewport_id not in self.viewports:
            logger.warning('视口不存在: %s', viewport_id)
            return
        if self.current_viewport == viewport_id or self._is_switching_viewport:
            return
        self._is_switching_viewport = True
        try:
            if self.current_viewport and self.current_viewport in self.viewport_providers:
                try:
                    self.viewport_providers[self.current_viewport].on_viewport_deactivated()
                except Exception as e:
                    logger.exception('停用视口失败: %s', e)
            widget = self.viewports[viewport_id]
            if self.viewport_tabs is not None:
                index = self.viewport_tabs.indexOf(widget)
                if index >= 0 and self.viewport_tabs.currentIndex() != index:
                    self.viewport_tabs.setCurrentIndex(index)
            elif widget and hasattr(self.main_window, 'central_stack'):
                self.main_window.central_stack.setCurrentWidget(widget)
            self.current_viewport = viewport_id
            if viewport_id in self.viewport_providers:
                try:
                    self.viewport_providers[viewport_id].on_viewport_activated()
                except Exception as e:
                    logger.exception('激活视口失败: %s', e)
            viewport_name = self.viewport_display_names.get(viewport_id, viewport_id)
            if (
                viewport_id not in self._host_named_viewports
                and viewport_id in self.viewport_providers
            ):
                provider = self.viewport_providers[viewport_id]
                if hasattr(provider, 'get_viewport_name'):
                    viewport_name = provider.get_viewport_name()
            current_viewport_message = self._tr(
                "status.current_viewport",
                "当前视口: {name}",
            ).format(name=viewport_name)
            self.statusbar.showMessage(current_viewport_message, 3000)
            logger.info('切换到视口: %s', viewport_id)
        finally:
            self._is_switching_viewport = False

    def _on_viewport_tab_changed(self, index: int):
        """Synchronize the active viewport with the tab bar."""
        if self.viewport_tabs is not None and index >= 0:
            widget = self.viewport_tabs.widget(index)
            for vp_id, vp_widget in self.viewports.items():
                if vp_widget == widget:
                    self.switch_viewport(vp_id)
                    break

    def get_current_viewport(self) -> Optional[QWidget]:
        """Return the current viewport widget, if any."""
        if self.current_viewport and self.current_viewport in self.viewports:
            return self.viewports[self.current_viewport]
        return None

    def add_menu_items(
        self,
        menu_items: List[Dict[str, Any]],
        plugin_name: Optional[str] = None,
    ):
        """Add declarative menu items and retain them for plugin teardown."""
        for item in menu_items:
            if item.get('separator', False):
                path_parts = item.get('path', '').split('/')
                parent_path = path_parts[:-1] if len(path_parts) > 1 else path_parts
                parent_menu = self._get_or_create_menu(parent_path)
                sep_action = parent_menu.addSeparator()
                if plugin_name:
                    self._plugin_menu_actions.setdefault(
                        plugin_name, []
                    ).append((parent_menu, sep_action))
                continue
            path = item['path'].split('/')
            menu = self._get_or_create_menu(path[:-1])
            action_fn = item.get('action', None)
            if action_fn is None:
                sep_action = menu.addSeparator()
                if plugin_name:
                    self._plugin_menu_actions.setdefault(
                        plugin_name, []
                    ).append((menu, sep_action))
                continue
            if not callable(action_fn):
                logger.warning('菜单项回调不可调用，已跳过: %s', item.get('path', ''))
                continue
            action = menu.addAction(path[-1])
            action.triggered.connect(action_fn)
            if plugin_name:
                self._plugin_menu_actions.setdefault(plugin_name, []).append(
                    (menu, action)
                )
            shortcut = item.get('shortcut', None)
            if shortcut:
                action.setShortcut(shortcut)
            if 'icon' in item:
                _set_action_icon(action, item['icon'])

    def add_toolbar_items(
        self,
        toolbar_items: List[Dict[str, Any]],
        plugin_name: Optional[str] = None,
    ):
        """Add declarative toolbar items and retain them for plugin teardown."""
        for item in toolbar_items:
            if item.get('separator', False):
                sep_action = self.toolbar.addSeparator()
                if plugin_name:
                    self._plugin_toolbar_actions.setdefault(
                        plugin_name, []
                    ).append(sep_action)
            else:
                action_fn = item.get('action')
                if not callable(action_fn):
                    logger.warning('工具栏项回调不可调用，已跳过: %s', item.get('text', ''))
                    continue
                action = self.toolbar.addAction(item['text'])
                action.triggered.connect(action_fn)
                if plugin_name:
                    self._plugin_toolbar_actions.setdefault(
                        plugin_name, []
                    ).append(action)
                if 'icon' in item:
                    _set_action_icon(action, item['icon'])

    def _get_or_create_menu(self, path: List[str]) -> QMenu:
        """Return a nested menu path, creating missing menus."""
        if not path:
            return self.menubar
        current_menu = None
        for name in path:
            found = False
            if current_menu is None:
                for action in self.menubar.actions():
                    if action.text() == name and action.menu():
                        current_menu = action.menu()
                        found = True
                        break
                if not found:
                    current_menu = self.menubar.addMenu(name)
            else:
                for action in current_menu.actions():
                    if action.text() == name and action.menu():
                        current_menu = action.menu()
                        found = True
                        break
                if not found:
                    current_menu = current_menu.addMenu(name)
        return current_menu

    def capture_theme_style_state(self) -> Dict[str, Optional[str]]:
        """Capture application and main-window styles independently."""
        app = QApplication.instance()
        return {
            "application": app.styleSheet() if app is not None else None,
            "main_window": self.main_window.styleSheet(),
        }

    def _write_theme_style_state(self, state: Mapping[str, Optional[str]]) -> None:
        """Write a captured style state without rolling it back."""
        app = QApplication.instance()
        application_style = state['application']
        if app is not None and application_style is not None:
            app.setStyleSheet(application_style)
        main_window_style = state['main_window']
        if main_window_style is None:
            raise ValueError('main_window theme style state must be a string')
        self.main_window.setStyleSheet(main_window_style)

    def _apply_theme_style_state(self, state: Mapping[str, Optional[str]]) -> None:
        """Apply a style state transactionally and restore the previous one on failure."""
        previous = self.capture_theme_style_state()
        try:
            self._write_theme_style_state(state)
        except Exception:
            try:
                self._write_theme_style_state(previous)
            except Exception:
                logger.exception('回滚主题样式状态失败')
            raise

    def restore_theme_style_state(self, state: Mapping[str, Optional[str]]) -> None:
        """Restore a previously captured application and window style state."""
        self._apply_theme_style_state(state)

    def register_theme(self, name: str, stylesheet: str):
        """Apply a theme atomically to the application and main window."""
        app = QApplication.instance()
        self._apply_theme_style_state(
            {
                "application": stylesheet if app is not None else None,
                "main_window": stylesheet,
            }
        )
        logger.info('已应用主题: %s', name)

    def remove_plugin_ui(self, plugin_name: str):
        """Remove menu and toolbar entries owned by one plugin."""
        for menu, action in self._plugin_menu_actions.pop(plugin_name, []):
            menu.removeAction(action)
        for action in self._plugin_toolbar_actions.pop(plugin_name, []):
            self.toolbar.removeAction(action)
        self._prune_empty_menus()

    def _menu_has_effective_actions(self, menu: QMenu) -> bool:
        """Return whether a menu has a non-separator leaf action."""
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
        """Remove recursively empty top-level menus after plugin teardown."""
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

    def save_layout(self):
        """Persist window, dock, and viewport state as JSON."""
        try:
            window_state = self.main_window.saveState()
            window_geometry = self.main_window.geometry()
            geometry = {
                "x": window_geometry.x(),
                "y": window_geometry.y(),
                "width": window_geometry.width(),
                "height": window_geometry.height(),
            }
            dock_states = {}
            for title, dock in self.docks.items():
                dock_geometry = dock.geometry()
                st: Dict[str, Any] = {
                    "visible": dock.isVisible(),
                    "floating": dock.isFloating(),
                    "area": (
                        int(self.main_window.dockWidgetArea(dock).value)
                        if not dock.isFloating()
                        else None
                    ),
                    "geometry": {
                        "x": dock_geometry.x(),
                        "y": dock_geometry.y(),
                        "width": dock_geometry.width(),
                        "height": dock_geometry.height(),
                    },
                }
                if dock.isFloating():
                    try:
                        st['save_geometry_hex'] = bytes(dock.saveGeometry()).hex()
                    except Exception as e:
                        logger.debug('保存 Dock geometry 失败: %s', e)
                dock_states[title] = st
            viewport_state = {'current': self.current_viewport, 'tabs_order': []}
            if self.viewport_tabs is not None:
                for i in range(self.viewport_tabs.count()):
                    widget = self.viewport_tabs.widget(i)
                    for vp_id, vp_widget in self.viewports.items():
                        if vp_widget == widget:
                            viewport_state['tabs_order'].append(vp_id)
                            break
            layout_data = EditorLayoutState(
                window_state=window_state.toBase64().data().decode("utf-8"),
                geometry=geometry,
                dock_states=dock_states,
                viewport_state=viewport_state,
            ).to_mapping()
            os.makedirs(os.path.dirname(self.layout_config_path), exist_ok=True)
            with open(self.layout_config_path, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2, ensure_ascii=False)
            logger.info('布局已保存: %s', self.layout_config_path)
            self.statusbar.showMessage(self._tr('status.layout_saved', '布局已保存'), 2000)
            return True
        except Exception as e:
            logger.exception('保存布局失败: %s', e)
            return False

    def restore_layout(self):
        """Restore persisted layout state without blocking startup on bad data."""
        try:
            if not os.path.exists(self.layout_config_path):
                logger.info('未找到保存的布局配置，使用默认布局')
                return False
            with open(self.layout_config_path, 'r', encoding='utf-8') as f:
                layout_state = EditorLayoutState.from_mapping(json.load(f))
            if layout_state.geometry:
                geom = layout_state.geometry
                x = int(geom.get('x', 100))
                y = int(geom.get('y', 100))
                width = max(640, int(geom.get('width', 1600)))
                height = max(480, int(geom.get('height', 900)))
                self.main_window.setGeometry(x, y, width, height)
            restored_window_state = False
            if layout_state.window_state:
                state_data = QByteArray.fromBase64(layout_state.window_state.encode('utf-8'))
                restored_window_state = bool(self.main_window.restoreState(state_data))
            if layout_state.dock_states:
                for title, state in layout_state.dock_states.items():
                    if title not in self.docks:
                        continue
                    dock = self.docks[title]
                    if 'visible' in state:
                        dock.setVisible(state['visible'])
                    floating = state.get('floating')
                    if not isinstance(floating, bool):
                        continue
                    if floating:
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
                    elif not restored_window_state:
                        dock.setFloating(False)
                        saved_area = state.get('area')
                        for area in (
                            Qt.DockWidgetArea.LeftDockWidgetArea,
                            Qt.DockWidgetArea.RightDockWidgetArea,
                            Qt.DockWidgetArea.TopDockWidgetArea,
                            Qt.DockWidgetArea.BottomDockWidgetArea,
                        ):
                            if saved_area == int(area.value):
                                self.main_window.addDockWidget(area, dock)
                                break
            if layout_state.viewport_state:
                vp_state = layout_state.viewport_state
                tab_order = vp_state.get('tabs_order')
                if self.viewport_tabs is not None and isinstance(tab_order, list):
                    for target_index, viewport_id in enumerate(tab_order):
                        viewport_widget = self.viewports.get(viewport_id)
                        if viewport_widget is None:
                            continue
                        current_index = self.viewport_tabs.indexOf(viewport_widget)
                        if current_index >= 0 and current_index != target_index:
                            self.viewport_tabs.tabBar().moveTab(current_index, target_index)
                if 'current' in vp_state and vp_state['current']:
                    target_vp = vp_state['current']
                    if target_vp in self.viewports:
                        self.switch_viewport(target_vp)
            logger.info('布局已恢复: %s', self.layout_config_path)
            self.statusbar.showMessage(self._tr('status.layout_restored', '布局已恢复'), 2000)
            return True
        except Exception as e:
            logger.exception('恢复布局失败: %s', e)
            return False

    def reset_layout(self):
        """Restore the default dock and window arrangement."""
        try:
            for dock in self.docks.values():
                dock.setVisible(True)
                dock.setFloating(False)
            self.main_window.setGeometry(100, 100, 1600, 900)
            if self.viewports:
                first_viewport_id = next(iter(self.viewports.keys()))
                self.switch_viewport(first_viewport_id)
            logger.info('布局已重置为默认')
            self.statusbar.showMessage(self._tr('status.layout_reset', '布局已重置'), 2000)
            return True
        except Exception as e:
            logger.exception('重置布局失败: %s', e)
            return False

    def _dock_geometry_cache_path(self) -> str:
        return os.path.join(self.state_home, "dock_geometry_cache.json")

    def _read_dock_geometry_cache(self) -> Dict[str, Any]:
        """Read the floating-dock geometry cache, treating bad data as empty."""
        path = self._dock_geometry_cache_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_dock_geometry_cache(self, data: Dict[str, Any]):
        """Write the floating-dock geometry cache without failing the UI."""
        try:
            path = self._dock_geometry_cache_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning('写入 dock 几何缓存失败: %s', e)

    def _ensure_dock_on_screen(self, dock: QDockWidget):
        """Move an off-screen floating dock onto the primary display."""
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
            logger.debug('校正浮动 Dock 位置失败: %s', e)

    def remember_dock_geometry(self, title: str):
        """Remember the geometry of a floating dock."""
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
            entry['save_geometry_hex'] = bytes(dock.saveGeometry()).hex()
        except Exception as e:
            logger.debug('缓存 Dock geometry 失败: title=%s error=%s', title, e)
        cache[title] = entry
        self._write_dock_geometry_cache(cache)

    def restore_dock_geometry(self, title: str):
        """Restore a dock's cached floating geometry."""
        dock = self.docks.get(title)
        if not dock:
            return
        cache = self._read_dock_geometry_cache()
        info = cache.get(title)
        if not isinstance(info, dict):
            return
        try:
            hex_blob = info.get('save_geometry_hex')
            if isinstance(hex_blob, str) and hex_blob:
                dock.restoreGeometry(QByteArray(bytes.fromhex(hex_blob)))
            else:
                x = int(info.get('x', 100))
                y = int(info.get('y', 100))
                w = int(max(200, info.get('width', 320)))
                h = int(max(120, info.get('height', 240)))
                dock.setGeometry(x, y, w, h)
            self._ensure_dock_on_screen(dock)
        except Exception:
            return

    def show_dock_with_mode(self, title: str, floating: bool):
        """Show a dock in the requested floating or docked mode."""
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
        """Show a dock, returning False when it is not registered."""
        dock = self.docks.get(title)
        if not dock:
            logger.warning('Dock 不存在: %s', title)
            return False
        use_float = dock.isFloating() if floating is None else bool(floating)
        self.show_dock_with_mode(title, use_float)
        return True

    def toggle_dock_floating(self, title: str):
        """Toggle a dock between floating and docked modes."""
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
