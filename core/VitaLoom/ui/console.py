"""编辑器控制台 Dock：日志行显示与过滤。

排错: 无输出 → logging_bridge.ConsolePanelLogHandler 是否挂载。
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QFrame,
    QHBoxLayout,
    QPushButton,
)

from core.VitaLoom.core.editor_context import get_editor_context


class ConsolePanel(QWidget):
    """展示 logging 与命令可视化日志流。"""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("consolePanel")
        self.editor_context = get_editor_context()
        self.editor_context.event_bus.subscribe("language_changed", self._on_language_changed)
        self.setMaximumHeight(220)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(4)
        header_layout = QHBoxLayout()
        self.title_label = QLabel(self._t("console.title", "控制台"))
        self.title_label.setObjectName("consoleTitle")
        header_layout.addWidget(self.title_label)

        self.clear_button = QPushButton(self._t("console.action.clear", "清空"))
        self.clear_button.setObjectName("consoleClearBtn")
        self.clear_button.clicked.connect(self.clear_console)  # type: ignore
        header_layout.addWidget(self.clear_button)
        header_layout.addStretch()
        self._layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._layout.addWidget(line)

        self.console_text = QTextEdit()
        self.console_text.setObjectName("consoleText")
        self.console_text.setReadOnly(True)
        self._layout.addWidget(self.console_text)
        self.init_console()

    def _t(self, key: str, default: str = "") -> str:
        tr_fn = getattr(self.editor_context, "i18n_tr", None)
        if callable(tr_fn):
            return tr_fn(key, default)
        return default or key

    def _on_language_changed(self, _data) -> None:
        self.title_label.setText(self._t("console.title", "控制台"))
        self.clear_button.setText(self._t("console.action.clear", "清空"))

    def init_console(self) -> None:
        self.log(self._t("console.log.initialized", "控制台已初始化"), "info")
        self.log(self._t("console.log.ready", "AI生命体编辑器就绪"), "success")

    def log(self, message: str, level: str = "info") -> None:
        colors = {
            "info": "#d4d4d4",
            "success": "#4ec9b0",
            "warning": "#ce9178",
            "error": "#f48771",
            "debug": "#9cdcfe",
        }
        color = colors.get(level, "#d4d4d4")
        formatted = f"<span style='color: {color};'>[{level.upper()}] {message}</span><br>"
        self.console_text.insertHtml(formatted)
        scrollbar = self.console_text.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def clear_console(self) -> None:
        self.console_text.clear()
        self.init_console()

    def append_text(self, text: str) -> None:
        self.log(text, "info")
