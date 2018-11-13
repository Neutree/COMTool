from PyQt5.QtWidgets import QComboBox,QListView
from PyQt5.QtCore import pyqtSignal


class ComboBox(QComboBox):
    clicked = pyqtSignal()
    def __init__(self):
        QComboBox.__init__(self)
        listView = QListView()
        self.setView(listView)
        return

    def __del__(self):
        return

    def mouseReleaseEvent(self, QMouseEvent):
        self.showPopup()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


