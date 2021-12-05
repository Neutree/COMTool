
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter)


class Settings(QWidget):

    closed = pyqtSignal()
    updatedisTextRawSignal = pyqtSignal(str)
    buffer = ""

    def __init__(self,parent = None):
        super().__init__(parent)
        self.init()
        self.initEvent()
        self.show()

    def __del__(self):
        pass

    def init(self):
        self.resize(500,400)
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.disTextRaw = QLabel("0000")
        self.mainLayout.addWidget(self.disTextRaw)

    def initEvent(self):
        pass

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()



