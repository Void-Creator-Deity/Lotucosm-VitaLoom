"""基于PyQt6的AI生命体编辑器 - 节点和连接线模块"""

from PyQt6.QtCore import Qt, QPoint, QPointF, QRect

from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient


class Node:

    """节点类"""

    def __init__(self, node_id: str, x: float, y: float, node_type: str = "sensor"):

        self.id = node_id

        self.x = x

        self.y = y

        self.type = node_type  # sensor, actuator, or organism

        self.radius = 25.0

        self.connections: list[ConnectionLine] = []

        # 根据类型设置颜色

        if node_type == "organism":

            self.color = QColor(100, 150, 200)  # 蓝色（细胞膜）

            self.radius = 30.0

        elif node_type == "sensor":

            self.color = QColor(0, 255, 0)  # 绿色

        elif node_type == "actuator":

            self.color = QColor(255, 0, 0)  # 红色

        elif node_type == "central_brain":

            self.color = QColor(255, 255, 0)  # 黄色（中枢管理器）

            self.radius = 25.0

        else:

            self.color = QColor(255, 255, 255)  # 白色

    def contains(self, point: QPoint) -> bool:

        """判断点是否在节点内"""

        return (point.x() - self.x) ** 2 + (point.y() - self.y) ** 2 <= self.radius ** 2

    def draw(self, painter: QPainter) -> None:

        """绘制节点"""

        # 绘制节点阴影效果 - 现代化的模糊阴影

        shadow_rect = QRect(int(self.x - self.radius - 5), int(self.y - self.radius - 5), 

                           int(self.radius * 2 + 10), int(self.radius * 2 + 10))

        shadow_gradient = QLinearGradient(shadow_rect.topLeft().x(), shadow_rect.topLeft().y(), 

                                         shadow_rect.bottomRight().x(), shadow_rect.bottomRight().y())

        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 30))

        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(shadow_gradient))

        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(shadow_rect)

        # 绘制节点主体 - 渐变效果

        body_rect = QRect(int(self.x - self.radius), int(self.y - self.radius), 

                           int(self.radius * 2), int(self.radius * 2))

        # 创建渐变填充

        gradient = QLinearGradient(body_rect.topLeft().x(), body_rect.topLeft().y(), 

                                  body_rect.bottomRight().x(), body_rect.bottomRight().y())

        gradient.setColorAt(0, self.color.lighter(120))

        gradient.setColorAt(1, self.color.darker(120))

        painter.setBrush(QBrush(gradient))

        # 绘制节点边框 - 更细的边框，更现代的效果

        painter.setPen(QPen(self.color.darker(150), 2))

        painter.drawEllipse(body_rect)

        # 绘制节点高光 - 增加光泽效果

        highlight_rect = QRect(int(self.x - self.radius * 0.6), int(self.y - self.radius * 0.6), 

                              int(self.radius * 1.2), int(self.radius * 1.2))

        highlight_gradient = QLinearGradient(highlight_rect.topLeft().x(), highlight_rect.topLeft().y(), 

                                            highlight_rect.bottomRight().x(), highlight_rect.bottomRight().y())

        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 80))

        highlight_gradient.setColorAt(0.3, QColor(255, 255, 255, 40))

        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(QBrush(highlight_gradient))

        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(highlight_rect)

        # 绘制节点标签 - 现代化的文字效果

        painter.setPen(QPen(QColor(0, 0, 0, 150)))

        painter.drawText(int(self.x - 15), int(self.y + 5), self.id[-3:])

    def update_position(self, x: float, y: float) -> None:

        """更新节点位置"""

        self.x = x

        self.y = y


class ConnectionLine:

    """连接线类"""

    def __init__(self, start_node: Node, end_node: Node):

        self.start_node = start_node

        self.end_node = end_node

        self.weight = 1.0

        self.color = QColor(100, 100, 255)

        self.width = 2

    def draw(self, painter: QPainter) -> None:

        """绘制连接线 - 现代化的连接线样式"""

        # 计算线条（使用整数）

        start_x = int(self.start_node.x)

        start_y = int(self.start_node.y)

        end_x = int(self.end_node.x)

        end_y = int(self.end_node.y)

        # 计算向量

        import math

        dx = end_x - start_x

        dy = end_y - start_y

        length = math.hypot(dx, dy)

        if length < 5:  # 太短的连接线不绘制

            return

        # 计算单位向量

        unit_dx = dx / length

        unit_dy = dy / length

        # 现代化的连接线样式 - 渐变线条

        line_pen = QPen()

        line_gradient = QLinearGradient(start_x, start_y, end_x, end_y)

        line_gradient.setColorAt(0, self.color.lighter(150))

        line_gradient.setColorAt(0.5, self.color.darker(50))

        line_gradient.setColorAt(1, self.color.lighter(150))

        line_pen.setBrush(line_gradient)

        line_pen.setWidth(self.width)

        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)  # 圆形端点

        painter.setPen(line_pen)

        painter.drawLine(start_x, start_y, end_x, end_y)

        # 发光效果 - 更现代化的视觉效果

        glow_pen = QPen(QColor(255, 255, 255, 30), self.width + 4)

        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(glow_pen)

        painter.drawLine(start_x, start_y, end_x, end_y)

        # 现代化的箭头 - 渐变填充的三角形箭头

        arrow_size = 8

        arrow_width = 14

        # 计算箭头位置

        arrow_base = QPoint(

            end_x - int(unit_dx * arrow_size),

            end_y - int(unit_dy * arrow_size)

        )

        # 计算箭头三个点

        arrow_p1 = QPoint(

            end_x,

            end_y

        )

        arrow_p2 = QPoint(

            arrow_base.x() + int(unit_dy * arrow_width / 2),

            arrow_base.y() - int(unit_dx * arrow_width / 2)

        )

        arrow_p3 = QPoint(

            arrow_base.x() - int(unit_dy * arrow_width / 2),

            arrow_base.y() + int(unit_dx * arrow_width / 2)

        )

        # 绘制箭头 - 渐变填充

        arrow_gradient = QLinearGradient(arrow_p1.x(), arrow_p1.y(), arrow_base.x(), arrow_base.y())

        arrow_gradient.setColorAt(0, self.color.lighter(120))

        arrow_gradient.setColorAt(1, self.color.darker(120))

        painter.setBrush(QBrush(arrow_gradient))

        painter.setPen(QPen(self.color.darker(150), 1))

        # 直接使用QPainter.drawPolygon的可变参数版本

        painter.drawPolygon(arrow_p1, arrow_p2, arrow_p3)

        # 箭头高光效果

        arrow_highlight = QPointF(

            arrow_p1.x() - unit_dx * 2 - unit_dy * 2,

            arrow_p1.y() - unit_dy * 2 + unit_dx * 2

        )

        highlight_brush = QBrush(QColor(255, 255, 255, 80))

        painter.setBrush(highlight_brush)

        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(arrow_highlight, 2, 2)

    def contains(self, point: QPoint, tolerance: int = 5) -> bool:

        """判断点是否在线附近"""

        # 计算点到线段的距离

        def distance_point_line(p: QPoint, a: QPoint, b: QPoint) -> int:

            if a == b:

                return (p - a).manhattanLength()

            # 计算向量

            ap = p - a

            ab = b - a

            # 使用静态方法计算点积

            dot_ap_ab = QPoint.dotProduct(ap, ab)

            dot_ab_ab = QPoint.dotProduct(ab, ab)

            if dot_ab_ab == 0:

                return (p - a).manhattanLength()

            t = max(0, min(1, dot_ap_ab / dot_ab_ab))

            # 计算投影点

            projection_x = int(a.x() + t * ab.x())

            projection_y = int(a.y() + t * ab.y())

            projection = QPoint(projection_x, projection_y)

            return (p - projection).manhattanLength()

        a = QPoint(int(self.start_node.x), int(self.start_node.y))

        b = QPoint(int(self.end_node.x), int(self.end_node.y))

        return distance_point_line(point, a, b) <= tolerance
