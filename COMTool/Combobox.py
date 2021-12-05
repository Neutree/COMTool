from PyQt5.QtWidgets import QComboBox,QListView
from PyQt5.QtCore import pyqtSignal


class ComboBox(QComboBox):
    clicked = pyqtSignal()
    # popupAboutToBeShown = pyqtSignal()

    def __init__(self):
        QComboBox.__init__(self)
        listView = QListView()
        listView.executeDelayedItemsLayout()
        self.setView(listView)

    def mouseReleaseEvent(self, QMouseEvent):
        self.showItems()

    def showPopup(self):
        # self.popupAboutToBeShown.emit()
        # prevent show popup, manually call it in mouse release event
        pass

    def _showPopup(self):
        max_w = 0
        for i in range(self.count()):
            w = self.view().sizeHintForColumn(i)
            if w > max_w:
                max_w = w
        self.view().setMinimumWidth(max_w + 50)
        super(ComboBox, self).showPopup()
    
    def showItems(self):
        self._showPopup()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


