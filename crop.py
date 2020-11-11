from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SelectAreaWidget(QWidget):
    def __init__(self, geometry=None, colour=QColor(250, 10, 10, 80)):
        self.points = []
        self.display_point_list = []
        self.colour=colour
        super().__init__()
        self.setGeometry(geometry)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.transparent)
        self.setPalette(p)
        self.begin = QPoint()
        self.end = QPoint()

    def paintEvent(self, event):
        qp = QPainter(self)
        br = QBrush(self.colour)
        qp.setBrush(br)

        qp.drawRect(QRect(self.begin, self.end))


    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        self.update()
