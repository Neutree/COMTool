import sys
from src import parameters
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QComboBox,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox)
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
        mainLayout.setStretch(0,2)
        mainLayout.setStretch(1, 6)
        mainLayout.setStretch(2, 2)
        self.setCentralWidget(mainWidget)

        # widgets receive and send area
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

        # widgets serial settings
        serialSettingsGroupBox = QGroupBox(parameters.strSerialSettings)
        serialSettingsLayout = QGridLayout()
        serialReceiveSettingsLayout = QGridLayout()
        serialSendSettingsLayout = QGridLayout()
        serialPortLabek = QLabel(parameters.strSerialPort)
        serailBaudrateLabel = QLabel(parameters.strSerialBaudrate)
        serailBytesLabel = QLabel(parameters.strSerialBytes)
        serailParityLabel = QLabel(parameters.strSerialParity)
        serailStopbitsLabel = QLabel(parameters.strSerialStopbits)
        serialPortCombobox = QComboBox()
        serailBaudrateCombobox = QComboBox()
        serailBytesCombobox = QComboBox()
        serailParityCombobox = QComboBox()
        serailStopbitsCombobox = QComboBox()
        serialOpenCloseButton = QPushButton(parameters.strOpen)
        serialSettingsLayout.addWidget(serialPortLabek,0,0)
        serialSettingsLayout.addWidget(serailBaudrateLabel, 1, 0)
        serialSettingsLayout.addWidget(serailBytesLabel, 2, 0)
        serialSettingsLayout.addWidget(serailParityLabel, 3, 0)
        serialSettingsLayout.addWidget(serailStopbitsLabel, 4, 0)
        serialSettingsLayout.addWidget(serialPortCombobox, 0, 1)
        serialSettingsLayout.addWidget(serailBaudrateCombobox, 1, 1)
        serialSettingsLayout.addWidget(serailBytesCombobox, 2, 1)
        serialSettingsLayout.addWidget(serailParityCombobox, 3, 1)
        serialSettingsLayout.addWidget(serailStopbitsCombobox, 4, 1)
        serialSettingsLayout.addWidget(serialOpenCloseButton, 5, 0,1,2)
        serialSettingsGroupBox.setLayout(serialSettingsLayout)
        settingLayout.addWidget(serialSettingsGroupBox)

        # serial receive settings
        serialReceiveSettingsGroupBox = QGroupBox(parameters.strSerialReceiveSettings)
        receiveSettingsAscii = QRadioButton(parameters.strAscii)
        receiveSettingsHex = QRadioButton(parameters.strHex)
        receiveSettingsAutoLinefeed = QCheckBox(parameters.strAutoLinefeed)
        receiveSettingsAutoLinefeedTime = QLineEdit(parameters.strAutoLinefeedTime)
        receiveSettingsAutoLinefeed.setMaximumWidth(75)
        receiveSettingsAutoLinefeedTime.setMaximumWidth(75)
        serialReceiveSettingsLayout.addWidget(receiveSettingsAscii,1,0,1,1)
        serialReceiveSettingsLayout.addWidget(receiveSettingsHex,1,1,1,1)
        serialReceiveSettingsLayout.addWidget(receiveSettingsAutoLinefeed, 2, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(receiveSettingsAutoLinefeedTime, 2, 1, 1, 1)
        serialReceiveSettingsGroupBox.setLayout(serialReceiveSettingsLayout)
        settingLayout.addWidget(serialReceiveSettingsGroupBox)

        # serial send settings
        serialSendSettingsGroupBox = QGroupBox(parameters.strSerialSendSettings)
        sendSettingsAscii = QRadioButton(parameters.strAscii)
        sendSettingsHex = QRadioButton(parameters.strHex)
        sendSettingsScheduledLabel = QCheckBox(parameters.strScheduled)
        sendSettingsScheduled = QLineEdit(parameters.strScheduledTime)
        sendSettingsScheduledLabel.setMaximumWidth(75)
        sendSettingsScheduled.setMaximumWidth(75)
        serialSendSettingsLayout.addWidget(sendSettingsAscii,1,0,1,1)
        serialSendSettingsLayout.addWidget(sendSettingsHex,1,1,1,1)
        serialSendSettingsLayout.addWidget(sendSettingsScheduledLabel, 2, 0, 1, 1)
        serialSendSettingsLayout.addWidget(sendSettingsScheduled, 2, 1, 1, 1)
        serialSendSettingsGroupBox.setLayout(serialSendSettingsLayout)
        settingLayout.addWidget(serialSendSettingsGroupBox)

        settingLayout.setStretch(0, 5)
        settingLayout.setStretch(1, 2.5)
        settingLayout.setStretch(2, 2.5)


        # main window
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



