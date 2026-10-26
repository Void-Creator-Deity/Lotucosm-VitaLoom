"""编辑器控件基类：统一暗色样式与 i18n 辅助。

排错: 样式不一致 → 子类是否调用 _apply_base_style。
"""


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class BaseEditorWidget(QWidget):
    """职责: Dock 面板公共 QWidget 基类（主题、翻译键）。"""

    """编辑器基类，提供公共样式和功能"""

    def __init__(self):

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

        super().__init__()

        self.setObjectName("editorPanel")

    def _setup_styles(self):
        """面板样式由 ThemeManager 全局 QSS 提供，避免与全局主题冲突。"""
        self.setObjectName("editorPanel")

    def _create_title_section(self, title: str, parent_layout: QVBoxLayout):

        """创建标题部分，包含标题和分隔线"""

        # 标题

        title_label = QLabel(title)

        title_label.setObjectName("editorPanelTitle")

        parent_layout.addWidget(title_label)

        # 分隔线

        line = QFrame()

        line.setFrameShape(QFrame.Shape.HLine)

        line.setFrameShadow(QFrame.Shadow.Sunken)

        line.setObjectName("editorPanelDivider")

        parent_layout.addWidget(line)
