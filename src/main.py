import sys
from src import parameters
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QComboBox)
from PyQt5.QtGui import QIcon,QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.InitWindow()
        return

    def __del__(self):
        return

    def InitWindow(self):
        QToolTip.setFont(QFont('SansSerif', 10))
        # main layout
        mainWidget = QWidget()
        settingLayout = QVBoxLayout()
        sendReceiveLayout = QVBoxLayout()
        sendFunctionalLayout = QVBoxLayout()
        mainLayout = QHBoxLayout()
        mainLayout.addLayout(settingLayout)
        mainLayout.addLayout(sendReceiveLayout)
        mainLayout.addLayout(sendFunctionalLayout)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)
        # widgets
        receiveArea = QTextEdit()
        sendArea = QTextEdit()
        sendButtion = QPushButton(parameters.strSend)
        sendHistory = QComboBox()
        sendAreaWidgetsLayout = QHBoxLayout()
        sendAreaWidgetsLayout.addWidget(sendArea)
        sendAreaWidgetsLayout.addWidget(sendButtion)

        sendReceiveLayout.addWidget(receiveArea)
        sendReceiveLayout.addLayout(sendAreaWidgetsLayout)
        sendReceiveLayout.addWidget(sendHistory)
        sendReceiveLayout.setStretch(0, 7)
        sendReceiveLayout.setStretch(1, 2)
        sendReceiveLayout.setStretch(2, 1)

        self.statusBar().showMessage('Ready')
        self.resize(800, 500)
        self.MoveToCenter()
        self.setWindowTitle(parameters.appName)
        self.setWindowIcon(QIcon(parameters.appIcon))
        self.show()
        return

    def MoveToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        return

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Sure To Quit?',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())



