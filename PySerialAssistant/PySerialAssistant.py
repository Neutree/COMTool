import sys,os
from PySerialAssistant import parameters,Combobox,helpAbout,autoUpdate
from PyQt5.QtCore import pyqtSignal,Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QComboBox,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox)
from PyQt5.QtGui import QIcon,QFont,QTextCursor
import serial
import serial.tools.list_ports
import serial.threaded
import threading
import time
import binascii,re
try:
  import cPickle as pickle
except ImportError:
  import pickle

class MainWindow(QMainWindow):
    receiveUpdateSignal = pyqtSignal(str)
    errorSignal = pyqtSignal(str)
    isDetectSerialPort = False
    receiveCount = 0
    sendCount = 0
    isScheduledSending = False

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initTool()
        self.initEvent()
        self.programStartGetSavedParameters()
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
        self.sendHistory = QComboBox()
        sendAreaWidgetsLayout = QHBoxLayout()
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.sendButtion)
        sendAreaWidgetsLayout.addWidget(self.sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)
        sendReceiveLayout.addWidget(self.receiveArea)
        sendReceiveLayout.addLayout(sendAreaWidgetsLayout)
        sendReceiveLayout.addWidget(self.sendHistory)
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
        self.serialPortCombobox = Combobox.Combobox()
        self.serailBaudrateCombobox = QComboBox()
        self.serailBaudrateCombobox.addItem("9600")
        self.serailBaudrateCombobox.addItem("19200")
        self.serailBaudrateCombobox.addItem("38400")
        self.serailBaudrateCombobox.addItem("57600")
        self.serailBaudrateCombobox.addItem("115200")
        self.serailBaudrateCombobox.setCurrentIndex(4)
        self.serailBaudrateCombobox.setEditable(True)
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
        serialSettingsLayout.addWidget(self.serailBaudrateCombobox, 1, 1)
        serialSettingsLayout.addWidget(self.serailBytesCombobox, 2, 1)
        serialSettingsLayout.addWidget(self.serailParityCombobox, 3, 1)
        serialSettingsLayout.addWidget(self.serailStopbitsCombobox, 4, 1)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 5, 0,1,2)
        serialSettingsGroupBox.setLayout(serialSettingsLayout)
        settingLayout.addWidget(serialSettingsGroupBox)

        # serial receive settings
        serialReceiveSettingsGroupBox = QGroupBox(parameters.strSerialReceiveSettings)
        self.receiveSettingsAscii = QRadioButton(parameters.strAscii)
        self.receiveSettingsHex = QRadioButton(parameters.strHex)
        self.receiveSettingsAscii.setChecked(True)
        self.receiveSettingsAutoLinefeed = QCheckBox(parameters.strAutoLinefeed)
        self.receiveSettingsAutoLinefeedTime = QLineEdit(parameters.strAutoLinefeedTime)
        self.receiveSettingsAutoLinefeed.setMaximumWidth(75)
        self.receiveSettingsAutoLinefeedTime.setMaximumWidth(75)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAscii,1,0,1,1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsHex,1,1,1,1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeed, 2, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeedTime, 2, 1, 1, 1)
        serialReceiveSettingsGroupBox.setLayout(serialReceiveSettingsLayout)
        settingLayout.addWidget(serialReceiveSettingsGroupBox)

        # serial send settings
        serialSendSettingsGroupBox = QGroupBox(parameters.strSerialSendSettings)
        self.sendSettingsAscii = QRadioButton(parameters.strAscii)
        self.sendSettingsHex = QRadioButton(parameters.strHex)
        self.sendSettingsAscii.setChecked(True)
        self.sendSettingsScheduledCheckBox = QCheckBox(parameters.strScheduled)
        self.sendSettingsScheduled = QLineEdit(parameters.strScheduledTime)
        self.sendSettingsScheduledCheckBox.setMaximumWidth(75)
        self.sendSettingsScheduled.setMaximumWidth(75)
        self.sendSettingsCFLF = QCheckBox(parameters.strCRLF)
        self.sendSettingsCFLF.setChecked(False)
        serialSendSettingsLayout.addWidget(self.sendSettingsAscii,1,0,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsHex,1,1,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduledCheckBox, 2, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduled, 2, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsCFLF, 3, 0, 1, 2)
        serialSendSettingsGroupBox.setLayout(serialSendSettingsLayout)
        settingLayout.addWidget(serialSendSettingsGroupBox)

        settingLayout.setStretch(0, 5)
        settingLayout.setStretch(1, 2.5)
        settingLayout.setStretch(2, 2.5)

        # right functional layout
        self.addButton = QPushButton(parameters.strAdd)
        self.settingsButton = QPushButton(parameters.strSettings)
        self.aboutButton = QPushButton(parameters.strAbout)
        menuLayout = QHBoxLayout()
        menuLayout.addWidget(self.settingsButton)
        menuLayout.addWidget(self.aboutButton)
        functionalGroupBox = QGroupBox(parameters.strFunctionalSend)
        functionalGridLayout = QGridLayout()
        functionalGridLayout.addWidget(self.addButton,0,1)
        functionalGroupBox.setLayout(functionalGridLayout)
        sendFunctionalLayout.addLayout(menuLayout)
        sendFunctionalLayout.addWidget(functionalGroupBox)

        # main window
        self.statusBarStauts = QLabel()
        self.statusBarStauts.setMinimumWidth(80)
        self.statusBarStauts.setText("<font color=%s>%s</font>" %("#008200", parameters.strReady))
        self.statusBarSendCount = QLabel(parameters.strSend+"(bytes): "+"0")
        self.statusBarReceiveCount = QLabel(parameters.strReceive+"(bytes): "+"0")
        self.statusBar().addWidget(self.statusBarStauts)
        self.statusBar().addWidget(self.statusBarSendCount,2)
        self.statusBar().addWidget(self.statusBarReceiveCount,3)
        # self.statusBar()

        self.resize(800, 500)
        self.MoveToCenter()
        self.setWindowTitle(parameters.appName+" V"+str(helpAbout.versionMajor)+"."+str(helpAbout.versionMinor))
        self.setWindowIcon(QIcon(parameters.appIcon))
        self.show()
        return

    def initEvent(self):
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.sendButtion.clicked.connect(self.sendData)
        self.receiveUpdateSignal.connect(self.updateReceivedDataDisplay)
        self.clearReceiveButtion.clicked.connect(self.clearReceiveBuffer)
        self.serialPortCombobox.clicked.connect(self.portComboboxClicked)
        self.sendSettingsHex.clicked.connect(self.onSendSettingsHexClicked)
        self.sendSettingsAscii.clicked.connect(self.onSendSettingsAsciiClicked)
        self.errorSignal.connect(self.errorHint)
        self.sendHistory.currentIndexChanged.connect(self.sendHistoryIndexChanged)
        self.settingsButton.clicked.connect(self.showSettings)
        self.aboutButton.clicked.connect(self.showAbout)
        self.addButton.clicked.connect(self.functionAdd)
        return

    def openCloseSerial(self):
        try:
            if self.com.is_open:
                self.com.close()
                self.serialOpenCloseButton.setText(parameters.strOpen)
                self.statusBarStauts.setText("<font color=%s>%s</font>" % ("#f31414", parameters.strClosed))
                self.receiveProgressStop = True
                self.serialPortCombobox.setDisabled(False)
                self.serailBaudrateCombobox.setDisabled(False)
                self.serailParityCombobox.setDisabled(False)
                self.serailStopbitsCombobox.setDisabled(False)
                self.serailBytesCombobox.setDisabled(False)
                self.programExitSaveParameters()
            else:
                try:
                    self.com.baudrate = int(self.serailBaudrateCombobox.currentText())
                    self.com.port = self.serialPortCombobox.currentText().split(" ")[0]
                    self.com.bytesize = int(self.serailBytesCombobox.currentText())
                    self.com.parity = self.serailParityCombobox.currentText()[0]
                    self.com.stopbits = float(self.serailStopbitsCombobox.currentText())
                    self.com.timeout = None
                    self.com.open()
                    self.serialOpenCloseButton.setText(parameters.strClose)
                    self.statusBarStauts.setText("<font color=%s>%s</font>" % ("#008200", parameters.strReady))
                    self.serialPortCombobox.setDisabled(True)
                    self.serailBaudrateCombobox.setDisabled(True)
                    self.serailParityCombobox.setDisabled(True)
                    self.serailStopbitsCombobox.setDisabled(True)
                    self.serailBytesCombobox.setDisabled(True)
                    receiveProcess = threading.Thread(target=self.receiveData)
                    receiveProcess.setDaemon(True)
                    receiveProcess.start()
                except Exception as e:
                    self.com.close()
                    self.receiveProgressStop = True
                    self.errorHint( parameters.strOpenFailed + str(e))
        except Exception:
            pass
        return

    def portComboboxClicked(self):
        self.detectSerialPort()
        return

    def getSendData(self):
        data = self.sendArea.toPlainText()
        if self.sendSettingsCFLF.isChecked():
            data = data.replace("\n", "\r\n")
        if self.sendSettingsHex.isChecked():
            if self.sendSettingsCFLF.isChecked():
                data = data.replace("\r\n", " ")
            else:
                data = data.replace("\n", " ")
            data = self.hexStringB2Hex(data)
            if data == -1:
                self.errorHint( parameters.strWriteFormatError)
                return -1
        else:
            data = data.encode()
        return data

    def sendData(self):
        try:
            if self.com.is_open:
                data = self.getSendData()
                if data == -1:
                    return
                print("send:",data)
                self.sendCount += len(data)
                self.com.write(data)
                self.sendHistoryFindDelete(data.decode())
                self.sendHistory.insertItem(0,data.decode())
                self.sendHistory.setCurrentIndex(0)
                self.receiveUpdateSignal.emit(None)
                # scheduled send
                if self.sendSettingsScheduledCheckBox.isChecked():
                    if not self.isScheduledSending:
                        t = threading.Thread(target=self.scheduledSend)
                        t.setDaemon(True)
                        t.start()
        except Exception as e:
            self.errorHint(parameters.strWriteError)
            print(e)
        return

    def scheduledSend(self):
        self.isScheduledSending = True
        while self.sendSettingsScheduledCheckBox.isChecked():
            self.sendData()
            try:
                time.sleep(int(self.sendSettingsScheduled.text().strip())/1000)
            except Exception:
                self.errorHint(parameters.strTimeFormatError)
        self.isScheduledSending = False
        return

    def receiveData(self):
        self.receiveProgressStop = False
        self.timeLastReceive = 0
        while(not self.receiveProgressStop):
            try:
                length = self.com.in_waiting
                if length>0:
                    bytes = self.com.read(length)
                    self.receiveCount += len(bytes)
                    if self.receiveSettingsHex.isChecked():
                        strReceived = self.asciiB2HexString(bytes)
                        self.receiveUpdateSignal.emit(strReceived)
                    else:
                        self.receiveUpdateSignal.emit(bytes.decode("utf-8","ignore"))
                    if self.receiveSettingsAutoLinefeed.isChecked():
                        if time.time() - self.timeLastReceive> int(self.receiveSettingsAutoLinefeedTime.text())/1000:
                            if self.sendSettingsCFLF.isChecked():
                                self.receiveUpdateSignal.emit("\r\n")
                            else:
                                self.receiveUpdateSignal.emit("\n")
                            self.timeLastReceive = time.time()
            except Exception as e:
                print("receiveData error")
                if self.com.is_open and not self.serialPortCombobox.isEnabled():
                    self.openCloseSerial()
                    self.serialPortCombobox.clear()
                    self.detectSerialPort()
                print(e)
            time.sleep(0.009)
        return

    def updateReceivedDataDisplay(self,str):
        if str != None:
            curScrollValue = self.receiveArea.verticalScrollBar().value()
            self.receiveArea.moveCursor(QTextCursor.End)
            endScrollValue = self.receiveArea.verticalScrollBar().value()
            self.receiveArea.insertPlainText(str)
            if curScrollValue < endScrollValue:
                self.receiveArea.verticalScrollBar().setValue(curScrollValue)
            else:
                self.receiveArea.moveCursor(QTextCursor.End)
        self.statusBarSendCount.setText("%s(bytes):%d" %(parameters.strSend ,self.sendCount))
        self.statusBarReceiveCount.setText("%s(bytes):%d" %(parameters.strReceive ,self.receiveCount))
        return

    def onSendSettingsHexClicked(self):
        data = self.sendArea.toPlainText().replace("\n","\r\n")
        data = self.asciiB2HexString(data.encode())
        self.sendArea.clear()
        self.sendArea.insertPlainText(data)
        return

    def onSendSettingsAsciiClicked(self):
        try:
            data = self.sendArea.toPlainText().replace("\n"," ").strip()
            self.sendArea.clear()
            if data != "":
                data = self.hexStringB2Hex(data).decode('utf-8','ignore')
                self.sendArea.insertPlainText(data)
        except Exception as e:
            QMessageBox.information(self,parameters.strWriteFormatError,parameters.strWriteFormatError)
        return

    def sendHistoryIndexChanged(self):
        self.sendArea.clear()
        self.sendArea.insertPlainText(self.sendHistory.currentText())
        return

    def clearReceiveBuffer(self):
        self.receiveArea.clear()
        self.receiveCount = 0;
        self.sendCount = 0;
        self.receiveUpdateSignal.emit(None)
        return

    def MoveToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        return

    def errorHint(self,str):
        QMessageBox.information(self, str, str)
        return

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Sure To Quit?',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.com.close()
            self.receiveProgressStop = True
            self.programExitSaveParameters()
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
        if not self.isDetectSerialPort:
            self.isDetectSerialPort = True
            t = threading.Thread(target=self.detectSerialPortProcess)
            t.setDaemon(True)
            t.start()

    def detectSerialPortProcess(self):
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
        self.isDetectSerialPort = False
        return

    def sendHistoryFindDelete(self,str):
        self.sendHistory.removeItem(self.sendHistory.findText(str))
        return

    def test(self):
        print("test")
        return

    def asciiB2HexString(self,strB):
        strHex = binascii.b2a_hex(strB).upper()
        return re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", strHex.decode())+" "

    def hexStringB2Hex(self,hexString):
        dataList = hexString.split(" ")
        j = 0
        for i in dataList:
            if len(i) > 2:
                return -1
            elif len(i) == 1:
                dataList[j] = "0" + i
            j += 1
        data = "".join(dataList)
        try:
            data = bytes.fromhex(data)
        except Exception:
            return -1
        print(data)
        return data

    def programExitSaveParameters(self):
        paramObj = parameters.ParametersToSave()
        paramObj.baudRate = self.serailBaudrateCombobox.currentIndex()
        paramObj.dataBytes = self.serailBytesCombobox.currentIndex()
        paramObj.parity = self.serailParityCombobox.currentIndex()
        paramObj.stopBits = self.serailStopbitsCombobox.currentIndex()
        if self.receiveSettingsHex.isChecked():
            paramObj.receiveAscii = False
        if not self.receiveSettingsAutoLinefeed.isChecked():
            paramObj.receiveAutoLinefeed = False
        else:
            paramObj.receiveAutoLinefeed = True
        paramObj.receiveAutoLindefeedTime = self.receiveSettingsAutoLinefeedTime.text()
        if self.sendSettingsHex.isChecked():
            paramObj.sendAscii = False
        if not self.sendSettingsScheduledCheckBox.isChecked():
            paramObj.sendScheduled = False
        paramObj.sendScheduledTime = self.sendSettingsScheduled.text()
        if not self.sendSettingsCFLF.isChecked():
            paramObj.useCRLF = False
        paramObj.sendHistoryList.clear()
        for i in range(0,self.sendHistory.count()):
            paramObj.sendHistoryList.append(self.sendHistory.itemText(i))
        f = open("settings.config","wb")
        f.truncate()
        pickle.dump(paramObj, f)
        pickle.dump(paramObj.sendHistoryList,f)
        f.close()
        return

    def programStartGetSavedParameters(self):
        paramObj = parameters.ParametersToSave()
        try:
            f = open("settings.config", "rb")
            paramObj = pickle.load( f)
            paramObj.sendHistoryList = pickle.load(f)
            f.close()
        except Exception as e:
            f = open("settings.config", "wb")
            f.close()
        self.serailBaudrateCombobox.setCurrentIndex(paramObj.baudRate)
        self.serailBytesCombobox.setCurrentIndex(paramObj.dataBytes)
        self.serailParityCombobox.setCurrentIndex(paramObj.parity)
        self.serailStopbitsCombobox.setCurrentIndex(paramObj.stopBits)
        if paramObj.receiveAscii == False:
            self.receiveSettingsHex.setChecked(True)
        if paramObj.receiveAutoLinefeed == False:
            self.receiveSettingsAutoLinefeed.setChecked(False)
        else:
            self.receiveSettingsAutoLinefeed.setChecked(True)
        self.receiveSettingsAutoLinefeedTime.setText(paramObj.receiveAutoLindefeedTime)
        if paramObj.sendAscii == False:
            self.sendSettingsHex.setChecked(True)
        if paramObj.sendScheduled == False:
            self.sendSettingsScheduledCheckBox.setChecked(False)
        else:
            self.sendSettingsScheduledCheckBox.setChecked(True)
        self.sendSettingsScheduled.setText(paramObj.sendScheduledTime)
        if paramObj.useCRLF == False:
            self.sendSettingsCFLF.setChecked(False)
        else:
            self.sendSettingsCFLF.setChecked(True)
        for i in range(0, len(paramObj.sendHistoryList)):
            str = paramObj.sendHistoryList[i]
            self.sendHistory.addItem(str)
        return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = True
        elif event.key() == Qt.Key_Return or event.key()==Qt.Key_Enter:
            if self.keyControlPressed:
                self.sendData()
        return

    def keyReleaseEvent(self,event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = False
        return

    def functionAdd(self):
        QMessageBox.information(self, "On the way", "On the way")
        return

    def showSettings(self):
        QMessageBox.information(self,"Settings","On the way")
        return

    def showAbout(self):
        QMessageBox.information(self, "About","<h1 style='color:#f75a5a';margin=10px;>"+parameters.appName+'</h1><br><b style="color:#08c7a1;margin = 5px;">V'+str(helpAbout.versionMajor)+"."+str(helpAbout.versionMinor)+
                                "</b><br><br>"+helpAbout.date+"<br><br>"+helpAbout.strAbout)
        return

    def autoUpdateDetect(self):
        auto = autoUpdate.AutoUpdate()
        if auto.detectNewVersion():
            auto.OpenBrowser()

    def openDevManagement(self):
        os.system('echo aaaa')
        os.system('start devmgmt.msc')



def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.detectSerialPort()
    t = threading.Thread(target=mainWindow.autoUpdateDetect)
    t.setDaemon(True)
    t.start()
    sys.exit(app.exec_())
