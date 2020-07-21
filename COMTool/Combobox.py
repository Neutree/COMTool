from PyQt5.QtWidgets import QComboBox,QListView
from PyQt5.QtCore import pyqtSignal


class ComboBox(QComboBox):
    clicked = pyqtSignal()
    # popupAboutToBeShown = pyqtSignal()

    def __init__(self):
        QComboBox.__init__(self)
        listView = QListView()
        self.setView(listView)
        return

    def mouseReleaseEvent(self, QMouseEvent):
        self.showItems()

    def showPopup(self):
        # self.popupAboutToBeShown.emit()
        # prevent show popup, manually call it in mouse release event
        pass
    
    def showItems(self):
        super(ComboBox, self).showPopup()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


