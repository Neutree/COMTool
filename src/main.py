import sys
from src import parameters
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QComboBox,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox)
from PyQt5.QtGui import QIcon,QFont
import serial
import serial.tools.list_ports
import threading
import time

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
        clearReceiveButtion = QPushButton(parameters.strClearReceive)
        sendButtion = QPushButton(parameters.strSend)
        sendHistory = QComboBox()
        sendAreaWidgetsLayout = QHBoxLayout()
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(sendButtion)
        sendAreaWidgetsLayout.addWidget(sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)
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
        self.serialPortCombobox = QComboBox()
        self.serailBaudrateEditText = QLineEdit()
        self.serailBaudrateEditText.setText(parameters.strBaudRateDefault)
        self.serailBytesCombobox = QComboBox()
        self.serailBytesCombobox.addItem("5")
        self.serailBytesCombobox.addItem("6")
        self.serailBytesCombobox.addItem("7")
        self.serailBytesCombobox.addItem("8")
        self.serailBytesCombobox.setCurrentIndex(3)
        self.serailParityCombobox = QComboBox()
        self.serailParityCombobox.addItem("None")
        self.serailParityCombobox.addItem("Odd")
        self.serailParityCombobox.addItem("Even")
        self.serailParityCombobox.addItem("Mark")
        self.serailParityCombobox.addItem("Space")
        self.serailParityCombobox.setCurrentIndex(0)
        self.serailStopbitsCombobox = QComboBox()
        self.serailStopbitsCombobox.addItem("1")
        self.serailStopbitsCombobox.addItem("1.5")
        self.serailStopbitsCombobox.addItem("2")
        self.serailStopbitsCombobox.setCurrentIndex(0)
        self.serialOpenCloseButton = QPushButton(parameters.strOpen)
        serialSettingsLayout.addWidget(serialPortLabek,0,0)
        serialSettingsLayout.addWidget(serailBaudrateLabel, 1, 0)
        serialSettingsLayout.addWidget(serailBytesLabel, 2, 0)
        serialSettingsLayout.addWidget(serailParityLabel, 3, 0)
        serialSettingsLayout.addWidget(serailStopbitsLabel, 4, 0)
        serialSettingsLayout.addWidget(self.serialPortCombobox, 0, 1)
        serialSettingsLayout.addWidget(self.serailBaudrateEditText, 1, 1)
        serialSettingsLayout.addWidget(self.serailBytesCombobox, 2, 1)
        serialSettingsLayout.addWidget(self.serailParityCombobox, 3, 1)
        serialSettingsLayout.addWidget(self.serailStopbitsCombobox, 4, 1)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 5, 0,1,2)
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

        # right functional layout
        addButton = QPushButton(parameters.strAdd)
        functionalGroupBox = QGroupBox(parameters.strFunctionalSend)
        functionalGridLayout = QGridLayout()
        functionalGridLayout.addWidget(addButton,0,1)
        functionalGroupBox.setLayout(functionalGridLayout)
        sendFunctionalLayout.addWidget(functionalGroupBox)

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

    def findSerialPort(self):
        port_list = list(serial.tools.list_ports.comports())
        return port_list

    def portChanged(self):
        self.serialPortCombobox.setCurrentIndex(0)
        self.serialPortCombobox.setToolTip(str(portList[0]))

    def detectSerialPort(self):
        self.serialPortCombobox.clear()
        while(1):
            portList = self.findSerialPort();
            for i in portList:
                self.serialPortCombobox.addItem(str(i[0])+" "+str(i[1]))
            if len(portList)>0:
                self.serialPortCombobox.setCurrentIndex(0)
                self.serialPortCombobox.setToolTip(str(portList[0]))
                break
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    threads = []
    t1 = threading.Thread(target=mainWindow.detectSerialPort)
    threads.append(t1)
    for t in threads:
        t.setDaemon(True)
        t.start()
    sys.exit(app.exec_())



