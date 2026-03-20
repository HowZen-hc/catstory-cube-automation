from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from app.models.config import Region


class RegionSelector(QWidget):
    """全螢幕半透明覆蓋層，讓使用者拖曳滑鼠框選矩形區域。"""

    region_selected = pyqtSignal(Region)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._start: QPoint | None = None
        self._end: QPoint | None = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        # 半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            # 清除選取區域的遮罩
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            # 畫紅色邊框
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._end = event.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._start:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            # 邏輯座標 → 實體像素座標（處理 DPI 縮放）
            ratio = self.devicePixelRatio()
            region = Region(
                x=int(rect.x() * ratio),
                y=int(rect.y() * ratio),
                width=int(rect.width() * ratio),
                height=int(rect.height() * ratio),
            )
            self.region_selected.emit(region)
            self.close()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
