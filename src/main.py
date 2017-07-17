import sys
from src import parameters
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QComboBox,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox)
from PyQt5.QtGui import QIcon,QFont,QTextCursor
import serial
import serial.tools.list_ports
import serial.threaded
import threading
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initTool()
        self.initEvent()
        return

    def __del__(self):
        return
    def initTool(self):
        self.com = serial.Serial()
        return

    def initWindow(self):
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
        self.receiveArea = QTextEdit()
        self.sendArea = QTextEdit()
        self.clearReceiveButtion = QPushButton(parameters.strClearReceive)
        self.sendButtion = QPushButton(parameters.strSend)
        sendHistory = QComboBox()
        sendAreaWidgetsLayout = QHBoxLayout()
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.sendButtion)
        sendAreaWidgetsLayout.addWidget(self.sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)
        sendReceiveLayout.addWidget(self.receiveArea)
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

    def initEvent(self):
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.sendButtion.clicked.connect(self.sendData)
        return

    def openCloseSerial(self):
        try:
            if self.com.is_open:
                self.com.close()
                self.serialOpenCloseButton.setText(parameters.strOpen)
                self.statusBar().showMessage(parameters.strClosed)
                self.receiveProgressStop = True
            else:
                try:
                    self.com.baudrate = int(self.serailBaudrateEditText.text())
                    self.com.port = self.serialPortCombobox.currentText().split(" ")[0]
                    self.com.bytesize = int(self.serailBytesCombobox.currentText())
                    self.com.parity = self.serailParityCombobox.currentText()[0]
                    self.com.stopbits = float(self.serailStopbitsCombobox.currentText())
                    self.com.timeout = None
                    self.com.open()
                    self.serialOpenCloseButton.setText(parameters.strClose)
                    self.statusBar().showMessage(parameters.strOpenReady)
                    receiveProcess = threading.Thread(target=self.receiveData)
                    receiveProcess.setDaemon(True)
                    receiveProcess.start()
                except Exception:
                    self.com.close()
                    self.receiveProgressStop = True
                    QMessageBox.information(self, parameters.strOpenFailed, parameters.strOpenFailed)
        except Exception:
            pass
        return

    def sendData(self):
        try:
            if self.com.is_open:
                data = self.sendArea.toPlainText().replace("\n","\r\n").encode()
                print(data)
                self.com.write(data)
        except Exception as e:
            QMessageBox.information(self, parameters.strWriteError, parameters.strWriteError)
            print(e)
        return

    def receiveData(self):
        self.receiveProgressStop = False
        while(not self.receiveProgressStop):
            try:
                byte = self.com.read(1)
                self.receiveArea.moveCursor(QTextCursor.End)
                self.receiveArea.insertPlainText(byte.decode())
                time.sleep(0.1)
            except Exception as e:
                print("receiveData")
                print(e)
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
            self.com.close()
            self.receiveProgressStop = True
            event.accept()
        else:
            event.ignore()

    def findSerialPort(self):
        self.port_list = list(serial.tools.list_ports.comports())
        return self.port_list

    def portChanged(self):
        self.serialPortCombobox.setCurrentIndex(0)
        self.serialPortCombobox.setToolTip(str(self.portList[0]))

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
            time.sleep(1)
        return

    def test(self):
        print("test")
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



