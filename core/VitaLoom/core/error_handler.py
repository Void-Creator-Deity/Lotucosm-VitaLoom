# -*- coding: utf-8 -*-
"""错误处理器单例：分级日志、可选弹窗与 error_occurred 信号。

排错: 启动闪退 → 日志文件路径与 ErrorLevel.CRITICAL 处理链。
"""

import sys
import traceback
import logging
from typing import Optional, Callable, Dict
from enum import Enum
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QWidget


class ErrorLevel(Enum):
    """错误级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler(QObject):
    """职责: 统一捕获并展示编辑器异常，写入日志文件。
    时机: 插件或内核调用 handle_error / 全局 excepthook（若安装）。
    不变量: 单例；弹窗依赖 QApplication 已存在。
    排错: 无弹窗 → show_dialog 参数；重复弹窗 → 级别过滤。
    """
    
    _instance: Optional['ErrorHandler'] = None
    
    # 信号
    error_occurred = pyqtSignal(str, str, str)  # (level, message, details)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """ErrorHandler.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        # 日志配置
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 错误回调注册表: error_type -> callback
        self.error_callbacks: Dict[str, Callable] = {}
        
        # 是否显示错误对话框
        self.show_error_dialogs = True
        
        # 父窗口（用于错误对话框）
        self.parent_widget: Optional[QWidget] = None
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志文件名（按日期）
        log_file = self.log_dir / f"vitaloom_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置根日志记录器
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('VitaLoom')
    
    def set_parent_widget(self, parent: QWidget):
        """设置父窗口。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.parent_widget = parent
    
    def register_error_callback(self, error_type: str, callback: Callable):
        """注册错误回调。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.error_callbacks[error_type] = callback
    
    def unregister_error_callback(self, error_type: str):
        """注销错误回调。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        if error_type in self.error_callbacks:
            del self.error_callbacks[error_type]
    
    def handle_exception(
        self,
        exc_type,
        exc_value,
        exc_traceback,
        show_dialog: bool = True
    ):
        """处理未捕获的异常。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        # 忽略键盘中断
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 格式化错误信息
        error_msg = str(exc_value)
        error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 记录错误
        self.logger.critical("Uncaught exception: %s\n%s", error_msg, error_details)
        
        # 发射信号
        self.error_occurred.emit(ErrorLevel.CRITICAL.value, error_msg, error_details)
        
        # 显示错误对话框
        if show_dialog and self.show_error_dialogs:
            self._show_error_dialog(
                ErrorLevel.CRITICAL,
                "未处理的异常",
                error_msg,
                error_details
            )
    
    def log_debug(self, message: str, details: str = ""):
        """记录调试信息。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.logger.debug(message)
        if details:
            self.logger.debug("Details: %s", details)
    
    def log_info(self, message: str, details: str = ""):
        """记录信息。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.logger.info(message)
        if details:
            self.logger.info("Details: %s", details)
        self.error_occurred.emit(ErrorLevel.INFO.value, message, details)
    
    def log_warning(self, message: str, details: str = "", show_dialog: bool = False):
        """记录警告。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.logger.warning(message)
        if details:
            self.logger.warning("Details: %s", details)
        
        self.error_occurred.emit(ErrorLevel.WARNING.value, message, details)
        
        if show_dialog and self.show_error_dialogs:
            self._show_error_dialog(ErrorLevel.WARNING, "警告", message, details)
    
    def log_error(self, message: str, details: str = "", show_dialog: bool = True):
        """记录错误。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.logger.error(message)
        if details:
            self.logger.error("Details: %s", details)
        
        self.error_occurred.emit(ErrorLevel.ERROR.value, message, details)
        
        if show_dialog and self.show_error_dialogs:
            self._show_error_dialog(ErrorLevel.ERROR, "错误", message, details)
    
    def log_critical(self, message: str, details: str = "", show_dialog: bool = True):
        """记录严重错误。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        self.logger.critical(message)
        if details:
            self.logger.critical("Details: %s", details)
        
        self.error_occurred.emit(ErrorLevel.CRITICAL.value, message, details)
        
        if show_dialog and self.show_error_dialogs:
            self._show_error_dialog(ErrorLevel.CRITICAL, "严重错误", message, details)
    
    def _show_error_dialog(
        self,
        level: ErrorLevel,
        title: str,
        message: str,
        details: str = ""
    ):
        """显示错误对话框"""
        # 确定图标类型
        icon_map = {
            ErrorLevel.DEBUG: QMessageBox.Icon.Information,
            ErrorLevel.INFO: QMessageBox.Icon.Information,
            ErrorLevel.WARNING: QMessageBox.Icon.Warning,
            ErrorLevel.ERROR: QMessageBox.Icon.Critical,
            ErrorLevel.CRITICAL: QMessageBox.Icon.Critical,
        }
        
        icon = icon_map.get(level, QMessageBox.Icon.Warning)
        
        # 创建消息框
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setDetailedText(details)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def install_exception_hook(self):
        """安装全局异常钩子。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        sys.excepthook = self.handle_exception
    
    def uninstall_exception_hook(self):
        """卸载全局异常钩子。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        sys.excepthook = sys.__excepthook__


def get_error_handler() -> ErrorHandler:
    """获取错误处理器单例"""
    return ErrorHandler()


# 便捷函数
def log_debug(message: str, details: str = ""):
    """记录调试信息"""
    get_error_handler().log_debug(message, details)


def log_info(message: str, details: str = ""):
    """记录信息"""
    get_error_handler().log_info(message, details)


def log_warning(message: str, details: str = "", show_dialog: bool = False):
    """记录警告"""
    get_error_handler().log_warning(message, details, show_dialog)


def log_error(message: str, details: str = "", show_dialog: bool = True):
    """记录错误"""
    get_error_handler().log_error(message, details, show_dialog)


def log_critical(message: str, details: str = "", show_dialog: bool = True):
    """记录严重错误"""
    get_error_handler().log_critical(message, details, show_dialog)
