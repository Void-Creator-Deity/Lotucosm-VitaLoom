# -*- coding: utf-8 -*-
"""logging.Handler → ConsolePanel 桥接（主线程 emit）。

排错: 子线程日志丢失 → 须 queue 到 GUI 线程。
"""
from __future__ import annotations

import logging
from typing import Optional

_HANDLER: Optional["ConsolePanelLogHandler"] = None


class ConsolePanelLogHandler(logging.Handler):
    """职责: 将 LogRecord 格式化为控制台行并安全 emit。"""
    def __init__(self, panel: object) -> None:
        """ConsolePanelLogHandler.__init__。

        
            职责:
                执行本函数声明的对外行为（见实现）。
        
            时机:
                由调用方在对应生命周期内调用。
        
            不变量:
                不破坏模块顶 docstring 与同级契约。
        
            排错:
                异常时见本文件模块说明与子树 README 排错表。
        """
        super().__init__()
        self._panel = panel
        self.setFormatter(logging.Formatter("[%(levelname)s][%(name)s] %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """ConsolePanelLogHandler.emit。

        
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
            msg = self.format(record)
            level = "info"
            if record.levelno >= logging.ERROR:
                level = "error"
            elif record.levelno >= logging.WARNING:
                level = "warning"
            elif record.levelno <= logging.DEBUG:
                level = "debug"
            log_fn = getattr(self._panel, "log", None)
            if callable(log_fn):
                log_fn(msg, level)
        except Exception:
            self.handleError(record)


def attach_console_logging(panel: object) -> ConsolePanelLogHandler:
    """Replace the active console handler and return the exact owned handler."""

    global _HANDLER
    root = logging.getLogger()
    previous = _HANDLER
    handler = ConsolePanelLogHandler(panel)
    handler.setLevel(logging.INFO)

    if previous is not None:
        root.removeHandler(previous)
    try:
        root.addHandler(handler)
    except Exception:
        if previous is not None:
            root.addHandler(previous)
        raise

    _HANDLER = handler
    return handler


def detach_console_logging(handler: Optional[ConsolePanelLogHandler] = None) -> bool:
    """Detach only the current handler, optionally requiring exact identity."""

    global _HANDLER
    if _HANDLER is None:
        return False
    if handler is not None and _HANDLER is not handler:
        return False
    logging.getLogger().removeHandler(_HANDLER)
    _HANDLER = None
    return True
