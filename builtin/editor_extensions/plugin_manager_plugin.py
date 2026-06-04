"""插件管理 Dock：启用/禁用 builtin 与外部插件。

排错: 见 `builtin/README.md`（插件未加载）。
"""

from core.plugin.interfaces import IDockProvider, IMenuProvider
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, List

from core.VitaLoom.core.logger import get_logger

logger = get_logger("PluginManagerPlugin")


class PluginManagerPlugin(IDockProvider, IMenuProvider):
    """插件管理器插件 - 管理其他插件的插件"""
    
    DOCK_ID = "Plugin Manager"
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "PluginManager",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "插件管理器，用于管理、启用、禁用和重载插件",
            "dependencies": [],
            "provides": ["dock", "menu"],
            "protected": True,
        }
    
    def on_load(self, editor_context):
        self.context = editor_context
        self.kernel = None
        self.dock = None
        self.plugin_list = None
        self.info_text = None
        
        # 获取内核引用
        if hasattr(editor_context, 'kernel'):
            self.kernel = editor_context.kernel
            
            # 订阅插件加载/卸载事件
            self.kernel.plugin_loaded.connect(self.on_plugin_loaded)
            self.kernel.plugin_unloaded.connect(self.on_plugin_unloaded)
        if hasattr(self.context, "event_bus"):
            self.context.event_bus.subscribe("language_changed", self._on_language_changed)
    
    def on_unload(self):
        if hasattr(self, "context") and self.context and hasattr(self.context, "event_bus"):
            try:
                self.context.event_bus.unsubscribe("language_changed", self._on_language_changed)
            except Exception:
                pass
        if self.kernel:
            try:
                self.kernel.plugin_loaded.disconnect(self.on_plugin_loaded)
                self.kernel.plugin_unloaded.disconnect(self.on_plugin_unloaded)
            except Exception as e:
                logger.warning("PluginManager 断开信号失败: %s", e)
        if self.dock:
            self.dock.deleteLater()
    
    def create_dock_widget(self) -> QDockWidget:
        """创建插件管理器 Dock 窗口"""
        # 注意：Dock 的内部标识必须稳定（用于默认布局/持久化），显示标题再做 i18n
        self.dock = QDockWidget(self._t("plugin_manager.title", "插件管理器"))
        self.dock.setObjectName(self.DOCK_ID)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 标题
        title_label = QLabel(self._t("plugin_manager.title", "插件管理器"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 分割器：左侧插件列表，右侧详情
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：插件列表
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.plugin_list = QListWidget()
        self.plugin_list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.plugin_list)
        
        # 按钮行
        button_layout = QHBoxLayout()
        
        reload_btn = QPushButton(f"🔄 {self._t('plugin_manager.reload', '重载')}")
        reload_btn.clicked.connect(self.reload_selected)
        reload_btn.setToolTip(self._t("plugin_manager.reload_tip", "重载选中的插件"))
        button_layout.addWidget(reload_btn)

        unload_btn = QPushButton(f"🗑️ {self._t('plugin_manager.unload', '卸载')}")
        unload_btn.clicked.connect(self.unload_selected)
        unload_btn.setToolTip(self._t("plugin_manager.unload_tip", "卸载选中的插件"))
        button_layout.addWidget(unload_btn)

        disable_btn = QPushButton(f"🚫 {self._t('plugin_manager.disable_project', '项目禁用')}")
        disable_btn.clicked.connect(self.disable_in_project)
        disable_btn.setToolTip(self._t("plugin_manager.disable_project_tip", "在当前项目中禁用该插件（持久化）"))
        button_layout.addWidget(disable_btn)

        enable_btn = QPushButton(f"✅ {self._t('plugin_manager.enable_project', '项目启用')}")
        enable_btn.clicked.connect(self.enable_in_project)
        enable_btn.setToolTip(self._t("plugin_manager.enable_project_tip", "在当前项目中启用该插件（持久化）"))
        button_layout.addWidget(enable_btn)
        
        refresh_btn = QPushButton(f"🔃 {self._t('plugin_manager.refresh', '刷新')}")
        refresh_btn.clicked.connect(self._refresh_plugin_list)
        refresh_btn.setToolTip(self._t("plugin_manager.refresh_tip", "刷新插件列表"))
        button_layout.addWidget(refresh_btn)
        
        list_layout.addLayout(button_layout)
        
        # 右侧：插件信息
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText(self._t("plugin_manager.placeholder", "选择插件以查看详情"))
        
        splitter.addWidget(list_widget)
        splitter.addWidget(self.info_text)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 初始刷新插件列表
        self._refresh_plugin_list()
        
        self.dock.setWidget(widget)
        return self.dock
    
    def get_dock_config(self) -> Dict[str, Any]:
        return {
            # title 作为内部 key，保持稳定
            "title": self.DOCK_ID,
            "area": Qt.DockWidgetArea.RightDockWidgetArea,
            "default_visible": False,  # 默认隐藏
            "can_close": True,
            "tabbed_with": "Inspector"
        }
    
    def get_menu_items(self) -> List[Dict[str, Any]]:
        """添加插件管理器菜单项"""
        return [
            {
                "path": f"{self._t('menu.tools', '工具')}/{self._t('plugin_manager.title', '插件管理器')}",
                "action": self.show_plugin_manager,
            }
        ]
    
    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """不添加工具栏项"""
        return []
    
    def show_plugin_manager(self):
        """显示插件管理器"""
        if self.dock:
            self.dock.setVisible(True)
            self.dock.raise_()
    
    def _refresh_plugin_list(self):
        """刷新插件列表"""
        if not self.plugin_list or not self.kernel:
            return
        
        self.plugin_list.clear()
        
        for plugin_name in self.kernel.plugin_loader.loaded_plugins.keys():
            item = QListWidgetItem(plugin_name)
            self.plugin_list.addItem(item)
        
        logger.info(
            self._t("plugin_manager.log.refreshed", "🔄 插件列表已刷新：{count} 个插件").format(
                count=self.plugin_list.count()
            )
        )
    
    def _on_selection_changed(self):
        """选中项变化时更新详情"""
        if not self.plugin_list or not self.info_text or not self.kernel:
            return
        
        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.text()
            plugin = self.kernel.plugin_loader.loaded_plugins.get(plugin_name)
            
            if plugin:
                info = plugin.get_plugin_info()
                unknown = self._t("plugin_manager.unknown", "未知")
                loader = self.kernel.plugin_loader
                scope = loader.get_plugin_scope(plugin_name) if hasattr(loader, "get_plugin_scope") else "unknown"
                protected = loader.is_plugin_protected(plugin_name) if hasattr(loader, "is_plugin_protected") else False
                protected_text = self._t("plugin_manager.core_protected", "是（核心模块）") if protected else self._t("plugin_manager.not_protected", "否")
                
                details = f"""
<h2>{info.get('name', unknown)}</h2>
<p><b>{self._t('plugin_manager.field.version', '版本')}:</b> {info.get('version', unknown)}</p>
<p><b>{self._t('plugin_manager.field.author', '作者')}:</b> {info.get('author', unknown)}</p>
<p><b>{self._t('plugin_manager.field.description', '描述')}:</b> {info.get('description', self._t('plugin_manager.none', '无'))}</p>
<p><b>{self._t('plugin_manager.field.provides', '提供能力')}:</b> {', '.join(info.get('provides', []))}</p>
<p><b>{self._t('plugin_manager.field.dependencies', '依赖')}:</b> {', '.join(info.get('dependencies', [])) or self._t('plugin_manager.none', '无')}</p>
<p><b>{self._t('plugin_manager.field.scope', '插件层级')}:</b> {scope}</p>
<p><b>{self._t('plugin_manager.field.protected', '受保护')}:</b> {protected_text}</p>
                """
                
                self.info_text.setHtml(details)
    
    def reload_selected(self):
        """重载选中的插件"""
        if not self.plugin_list or not self.kernel:
            return
        
        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.text()
            loader = self.kernel.plugin_loader
            if hasattr(loader, "is_plugin_protected") and loader.is_plugin_protected(plugin_name):
                logger.warning(
                    self._t(
                        "plugin_manager.log.protected",
                        "🛡️ 核心插件受保护，禁止重载：{name}",
                    ).format(name=plugin_name)
                )
                return
            logger.info(
                self._t("plugin_manager.log.reloading", "🔄 正在重载插件：{name}").format(
                    name=plugin_name
                )
            )
            self.kernel.plugin_loader.reload_plugin(plugin_name)
            self._refresh_plugin_list()

    def unload_selected(self):
        """卸载选中的插件"""
        if not self.plugin_list or not self.kernel:
            return

        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.text()
            loader = self.kernel.plugin_loader
            if hasattr(loader, "is_plugin_protected") and loader.is_plugin_protected(plugin_name):
                logger.warning(
                    self._t(
                        "plugin_manager.log.unload_protected",
                        "🛡️ 核心插件受保护，禁止卸载：{name}",
                    ).format(name=plugin_name)
                )
                return
            logger.info(
                self._t("plugin_manager.log.unloading", "🗑️ 正在卸载插件：{name}").format(
                    name=plugin_name
                )
            )
            self.kernel.plugin_loader.unload_plugin(plugin_name)
            self._refresh_plugin_list()

    def _get_selected_plugin_name(self):
        if not self.plugin_list:
            return None
        current_item = self.plugin_list.currentItem()
        return current_item.text() if current_item else None

    def disable_in_project(self):
        """在当前项目中持久禁用插件（写入 project.json.disabled_plugins）。"""
        if not self.kernel:
            return
        plugin_name = self._get_selected_plugin_name()
        if not plugin_name:
            return

        loader = self.kernel.plugin_loader
        scope = loader.get_plugin_scope(plugin_name) if hasattr(loader, "get_plugin_scope") else "unknown"
        if scope == "core_mod":
            logger.info(self._t("plugin_manager.log.project_disable_core_skip", "🛡️ Core 仅内核框架，不支持项目级禁用：{name}").format(name=plugin_name))
            return
        if hasattr(loader, "is_plugin_protected") and loader.is_plugin_protected(plugin_name):
            logger.warning(self._t("plugin_manager.log.project_disable_protected", "🛡️ 插件受保护，禁止项目禁用：{name}").format(name=plugin_name))
            return

        from core.VitaLoom.project.project_manager import get_project_manager

        pm = get_project_manager()
        cfg = pm.get_current_project_config()
        if not cfg:
            logger.warning(self._t("plugin_manager.log.no_project", "⚠️ 当前没有打开的项目，无法持久化配置"))
            return

        disabled = cfg.get("disabled_plugins", [])
        if not isinstance(disabled, list):
            disabled = []
        if plugin_name not in disabled:
            disabled.append(plugin_name)

        if pm.update_project_config_fields({"disabled_plugins": disabled}):
            logger.info(self._t("plugin_manager.log.project_disabled", "🚫 已在项目中禁用插件：{name}").format(name=plugin_name))
            # 立即生效
            self.kernel.plugin_loader.unload_plugin(plugin_name)
            self._refresh_plugin_list()

    def enable_in_project(self):
        """在当前项目中持久启用插件（从 project.json.disabled_plugins 移除）。"""
        if not self.kernel:
            return
        plugin_name = self._get_selected_plugin_name()
        if not plugin_name:
            return

        from core.VitaLoom.project.project_manager import get_project_manager

        pm = get_project_manager()
        cfg = pm.get_current_project_config()
        if not cfg:
            logger.warning(self._t("plugin_manager.log.no_project", "⚠️ 当前没有打开的项目，无法持久化配置"))
            return

        disabled = cfg.get("disabled_plugins", [])
        if not isinstance(disabled, list):
            disabled = []
        disabled = [x for x in disabled if x != plugin_name]

        if pm.update_project_config_fields({"disabled_plugins": disabled}):
            logger.info(self._t("plugin_manager.log.project_enabled", "✅ 已在项目中启用插件：{name}（重启后会重新加载）").format(name=plugin_name))
    
    def on_plugin_loaded(self, plugin_name: str):
        """插件加载时的回调"""
        logger.info(
            self._t("plugin_manager.log.loaded", "✅ 插件已加载：{name}").format(name=plugin_name)
        )
        if self.plugin_list:
            self._refresh_plugin_list()
    
    def on_plugin_unloaded(self, plugin_name: str):
        """插件卸载时的回调"""
        logger.info(
            self._t("plugin_manager.log.unloaded", "❌ 插件已卸载：{name}").format(name=plugin_name)
        )
        if self.plugin_list:
            self._refresh_plugin_list()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data):
        # 直接重建面板，避免逐控件维护翻译状态
        if self.dock and self.kernel and hasattr(self.kernel, "layout_manager"):
            lm = self.kernel.layout_manager
            if hasattr(lm, "remove_dock"):
                lm.remove_dock(self.DOCK_ID)
            dock = self.create_dock_widget()
            lm.add_dock(dock, self.get_dock_config())
