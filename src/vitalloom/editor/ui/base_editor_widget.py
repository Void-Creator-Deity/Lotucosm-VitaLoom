"""编辑器基类 - 包含公共样式和功能"""


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class BaseEditorWidget(QWidget):

    """编辑器基类，提供公共样式和功能"""

    def __init__(self):

        """初始化编辑器基类"""

        super().__init__()

        # 设置默认样式

        self._setup_styles()

    def _setup_styles(self):

        """设置编辑器的公共样式"""

        self.setStyleSheet("""

            QWidget {

                background-color: #2d2d2d;

                color: #d4d4d4;

            }

            QGroupBox {

                border: 1px solid #404040;

                border-radius: 4px;

                margin-top: 10px;

                color: #d4d4d4;

                font-weight: bold;

            }

            QGroupBox::title {

                subcontrol-origin: margin;

                left: 10px;

                padding: 0 5px 0 5px;

            }

            QListWidget {

                background-color: #1e1e1e;

                border: 1px solid #404040;

                border-radius: 4px;

                color: #d4d4d4;

            }

            QListWidget::item {

                padding: 8px;

                border-bottom: 1px solid #333333;

            }

            QListWidget::item:selected {

                background-color: #264f78;

                color: #ffffff;

            }

            QPushButton {

                background-color: #3c3c3c;

                border: 1px solid #555555;

                border-radius: 4px;

                color: #d4d4d4;

                padding: 6px 12px;

            }

            QPushButton:hover {

                background-color: #4c4c4c;

            }

            QPushButton:pressed {

                background-color: #2c2c2c;

            }

            QLineEdit, QTextEdit {

                background-color: #1e1e1e;

                border: 1px solid #404040;

                border-radius: 4px;

                color: #d4d4d4;

                padding: 6px;

            }

            QDoubleSpinBox, QSpinBox {

                background-color: #1e1e1e;

                border: 1px solid #404040;

                border-radius: 4px;

                color: #d4d4d4;

            }

            QComboBox {

                background-color: #1e1e1e;

                border: 1px solid #404040;

                border-radius: 4px;

                color: #d4d4d4;

                padding: 6px;

            }

            QTabWidget::pane {

                border: 1px solid #404040;

                background-color: #2d2d2d;

            }

            QTabWidget::tab-bar {

                alignment: center;

            }

            QTabBar::tab {

                background-color: #3c3c3c;

                color: #d4d4d4;

                padding: 8px 16px;

                border-top-left-radius: 4px;

                border-top-right-radius: 4px;

            }

            QTabBar::tab:selected {

                background-color: #2d2d2d;

                color: #ffffff;

            }

            QSplitter::handle {

                background-color: #404040;

                width: 4px;

            }

            QSplitter::handle:hover {

                background-color: #555555;

            }

        """)

    def _create_title_section(self, title: str, parent_layout: QVBoxLayout):

        """创建标题部分，包含标题和分隔线"""

        # 标题

        title_label = QLabel(title)

        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")

        parent_layout.addWidget(title_label)

        # 分隔线

        line = QFrame()

        line.setFrameShape(QFrame.Shape.HLine)

        line.setFrameShadow(QFrame.Shadow.Sunken)

        line.setStyleSheet("background-color: #404040;")

        parent_layout.addWidget(line)
