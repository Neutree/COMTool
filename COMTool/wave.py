
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter)


class Wave(QWidget):

    closed = pyqtSignal()
    updatedisTextRawSignal = pyqtSignal(str)
    buffer = ""

    def __init__(self,parent = None):
        super(Wave,self).__init__(parent)
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
        self.updatedisTextRawSignal.connect(self.updateTextRaw)

    def displayData(self,bytes):
        try:
            self.buffer += bytes.decode("utf-8")
            end = self.buffer.index("\r\n")
            frame = self.buffer[0:end]
            self.buffer = self.buffer[end+2:]
            self.updatedisTextRawSignal.emit(frame)
            # print("==========\n",frame,",",self.buffer,"\n==========")

        except Exception:
            pass

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()

    def updateTextRaw(self,frame):
        self.disTextRaw.setText(frame)

