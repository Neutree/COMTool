from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal


class Combobox(QComboBox):
    clicked = pyqtSignal()
    def __init__(self):
        QComboBox.__init__(self)
        return

    def __del__(self):
        return

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit()
        return


