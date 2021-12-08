import sys,os

if sys.version_info < (3, 8):
    print("only support python >= 3.8")
    sys.exit(1)


try:
    import parameters,helpAbout,autoUpdate
    from Combobox import ComboBox
    import i18n
    from i18n import _
    import version
    import utils
except ImportError:
    from COMTool import parameters,helpAbout,autoUpdate, utils
    from COMTool.Combobox import ComboBox
    from COMTool import i18n
    from COMTool.i18n import _
    from COMTool import version

# from COMTool.wave import Wave
from PyQt5.QtCore import pyqtSignal,Qt, QRect
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import binascii,re
from enum import Enum
if sys.platform == "win32":
    import ctypes

class MyClass(object):
    def __init__(self, arg):
        super(MyClass, self).__init__()
        self.arg = arg

class ConnectionStatus(Enum):
    CLOSED = 0
    CONNECTED = 1
    LOSE = 2 

class MainWindow(QMainWindow):
    receiveUpdateSignal = pyqtSignal(str, list, str) # head, content, encoding
    errorSignal = pyqtSignal(str)
    statusBarSignal = pyqtSignal(str, str)
    connectionSignal = pyqtSignal(ConnectionStatus)
    sendFileOkSignal = pyqtSignal(bool, str)
    updateSignal = pyqtSignal(object)
    showSerialComboboxSignal = pyqtSignal()
    setDisableSettingsSignal = pyqtSignal(bool)
    isDetectSerialPort = False
    receiveCount = 0
    sendCount = 0
    isScheduledSending = False
    DataPath = "./"
    isHideSettings = False
    isHideFunctinal = True
    app = None
    isWaveOpen = False
    needRestart = False

    def __init__(self,app):
        super().__init__()
        self.app = app
        self.DataPath = parameters.dataPath
        self.config = self.loadParameters()
        self.initVar()
        i18n.set_locale(self.config.locale)
        self.initWindow()
        self.initTool()
        self.programStartGetSavedParameters(self.config)
        self.initEvent()

    def __del__(self):
        pass

    def initTool(self):
        self.com = serial.Serial()
    
    def initVar(self):
        self.keyControlPressed = False
        self.baudrateCustomStr = "custom, input baudrate"
        self.strings = parameters.Strings(self.config.locale)
        self.dataToSend = []
        self.fileToSend = []
        self.sendRecord = []
        self.lastColor = None
        self.lastBg = None
        self.defaultColor = None
        self.defaultBg = None

    def initWindow(self):
        # main layout
        self.frameWidget = QWidget()
        mainWidget = QSplitter(Qt.Horizontal)
        frameLayout = QVBoxLayout()
        self.settingWidget = QWidget()
        self.settingWidget.setProperty("class","settingWidget")
        self.receiveSendWidget = QSplitter(Qt.Vertical)
        self.functionalWiget = QWidget()
        settingLayout = QVBoxLayout()
        sendFunctionalLayout = QVBoxLayout()
        self.settingWidget.setLayout(settingLayout)
        self.functionalWiget.setLayout(sendFunctionalLayout)
        mainWidget.addWidget(self.settingWidget)
        mainWidget.addWidget(self.receiveSendWidget)
        mainWidget.addWidget(self.functionalWiget)
        mainWidget.setStretchFactor(0, 4)
        mainWidget.setStretchFactor(1, 7)
        mainWidget.setStretchFactor(2, 2)
        menuLayout = QHBoxLayout()
        frameLayout.addLayout(menuLayout)
        frameLayout.addWidget(mainWidget)
        self.frameWidget.setLayout(frameLayout)
        self.setCentralWidget(self.frameWidget)

        # option layout
        self.settingsButton = QPushButton()
        self.skinButton = QPushButton("")
        self.languageCombobox = ComboBox()
        self.languages = i18n.get_languages()
        for locale in self.languages:
            self.languageCombobox.addItem(self.languages[locale])
        # self.waveButton = QPushButton("")
        self.aboutButton = QPushButton()
        self.functionalButton = QPushButton()
        self.encodingCombobox = ComboBox()
        self.supportedEncoding = parameters.encodings
        for encoding in self.supportedEncoding:
            self.encodingCombobox.addItem(encoding)
        self.settingsButton.setProperty("class", "menuItem1")
        self.skinButton.setProperty("class", "menuItem2")
        self.aboutButton.setProperty("class", "menuItem3")
        self.functionalButton.setProperty("class", "menuItem4")
        # self.waveButton.setProperty("class", "menuItem5")
        self.settingsButton.setObjectName("menuItem")
        self.skinButton.setObjectName("menuItem")
        self.aboutButton.setObjectName("menuItem")
        self.functionalButton.setObjectName("menuItem")
        # self.waveButton.setObjectName("menuItem")
        menuLayout.addWidget(self.settingsButton)
        menuLayout.addWidget(self.skinButton)
        # menuLayout.addWidget(self.waveButton)
        menuLayout.addWidget(self.aboutButton)
        menuLayout.addWidget(self.languageCombobox)
        menuLayout.addStretch(0)
        menuLayout.addWidget(self.encodingCombobox)
        menuLayout.addWidget(self.functionalButton)


        # widgets receive and send area
        self.receiveArea = QTextEdit()
        font = QFont('Menlo,Consolas,Bitstream Vera Sans Mono,Courier New,monospace, Microsoft YaHei', 10)
        self.receiveArea.setFont(font)
        self.receiveArea.setLineWrapMode(QTextEdit.NoWrap)
        self.sendArea = QTextEdit()
        self.clearReceiveButtion = QPushButton(self.strings.strClearReceive)
        self.sendButtion = QPushButton(self.strings.strSend)
        self.sendHistory = ComboBox()
        sendWidget = QWidget()
        sendAreaWidgetsLayout = QHBoxLayout()
        sendWidget.setLayout(sendAreaWidgetsLayout)
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.sendButtion)
        sendAreaWidgetsLayout.addWidget(self.sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)
        self.receiveSendWidget.addWidget(self.receiveArea)
        self.receiveSendWidget.addWidget(sendWidget)
        self.receiveSendWidget.addWidget(self.sendHistory)
        self.receiveSendWidget.setStretchFactor(0, 7)
        self.receiveSendWidget.setStretchFactor(1, 2)
        self.receiveSendWidget.setStretchFactor(2, 1)

        # widgets serial settings
        serialSettingsGroupBox = QGroupBox(self.strings.strSerialSettings)
        serialSettingsLayout = QGridLayout()
        serialReceiveSettingsLayout = QGridLayout()
        serialSendSettingsLayout = QGridLayout()
        serialPortLabek = QLabel(self.strings.strSerialPort)
        serailBaudrateLabel = QLabel(self.strings.strSerialBaudrate)
        serailBytesLabel = QLabel(self.strings.strSerialBytes)
        serailParityLabel = QLabel(self.strings.strSerialParity)
        serailStopbitsLabel = QLabel(self.strings.strSerialStopbits)
        serialFlowControlLabel = QLabel(_("Flow control"))
        self.serialPortCombobox = ComboBox()
        self.serailBaudrateCombobox = ComboBox()
        for baud in parameters.defaultBaudrates:
            self.serailBaudrateCombobox.addItem(str(baud))
        self.serailBaudrateCombobox.addItem(self.baudrateCustomStr)
        self.serailBaudrateCombobox.setCurrentIndex(4)
        self.serailBaudrateCombobox.setEditable(True)
        self.serailBytesCombobox = ComboBox()
        self.serailBytesCombobox.addItem("5")
        self.serailBytesCombobox.addItem("6")
        self.serailBytesCombobox.addItem("7")
        self.serailBytesCombobox.addItem("8")
        self.serailBytesCombobox.setCurrentIndex(3)
        self.serailParityCombobox = ComboBox()
        self.serailParityCombobox.addItem("None")
        self.serailParityCombobox.addItem("Odd")
        self.serailParityCombobox.addItem("Even")
        self.serailParityCombobox.addItem("Mark")
        self.serailParityCombobox.addItem("Space")
        self.serailParityCombobox.setCurrentIndex(0)
        self.serailStopbitsCombobox = ComboBox()
        self.serailStopbitsCombobox.addItem("1")
        self.serailStopbitsCombobox.addItem("1.5")
        self.serailStopbitsCombobox.addItem("2")
        self.serailStopbitsCombobox.setCurrentIndex(0)
        self.serialFlowControlCombobox = ComboBox()
        self.serialFlowControlCombobox.addItem("None")
        self.serialFlowControlCombobox.addItem("XON/XOFF")
        self.serialFlowControlCombobox.addItem("RTS/CTS")
        self.serialFlowControlCombobox.addItem("DSR/DTR")
        self.serialFlowControlCombobox.setCurrentIndex(0)
        self.checkBoxRTS = QCheckBox("rts")
        self.checkBoxDTR = QCheckBox("dtr")
        self.checkBoxRTS.setToolTip(_("Check to enable(usually output low level)"))
        self.checkBoxDTR.setToolTip(_("Check to enable(usually output low level)"))
        self.serialOpenCloseButton = QPushButton(self.strings.strOpen)
        serialSettingsLayout.addWidget(serialPortLabek,0,0)
        serialSettingsLayout.addWidget(serailBaudrateLabel, 1, 0)
        serialSettingsLayout.addWidget(serailBytesLabel, 2, 0)
        serialSettingsLayout.addWidget(serailParityLabel, 3, 0)
        serialSettingsLayout.addWidget(serailStopbitsLabel, 4, 0)
        serialSettingsLayout.addWidget(serialFlowControlLabel, 5, 0)
        serialSettingsLayout.addWidget(self.serialPortCombobox, 0, 1)
        serialSettingsLayout.addWidget(self.serailBaudrateCombobox, 1, 1)
        serialSettingsLayout.addWidget(self.serailBytesCombobox, 2, 1)
        serialSettingsLayout.addWidget(self.serailParityCombobox, 3, 1)
        serialSettingsLayout.addWidget(self.serailStopbitsCombobox, 4, 1)
        serialSettingsLayout.addWidget(self.serialFlowControlCombobox, 5, 1)
        serialSettingsLayout.addWidget(self.checkBoxRTS, 6, 0,1,1)
        serialSettingsLayout.addWidget(self.checkBoxDTR, 6, 1,1,1)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 7, 0,1,2)
        serialSettingsGroupBox.setLayout(serialSettingsLayout)
        settingLayout.addWidget(serialSettingsGroupBox)

        # serial receive settings
        serialReceiveSettingsGroupBox = QGroupBox(self.strings.strSerialReceiveSettings)
        self.receiveSettingsAscii = QRadioButton(self.strings.strAscii)
        self.receiveSettingsAscii.setToolTip(_("Show recived data as visible format, select decode method at top right corner"))
        self.receiveSettingsHex = QRadioButton(self.strings.strHex)
        self.receiveSettingsHex.setToolTip(_("Show recived data as hex format"))
        self.receiveSettingsAscii.setChecked(True)
        self.receiveSettingsAutoLinefeed = QCheckBox(self.strings.strAutoLinefeed)
        self.receiveSettingsAutoLinefeed.setToolTip(_("Auto linefeed after interval, unit: ms"))
        self.receiveSettingsAutoLinefeedTime = QLineEdit("200")
        self.receiveSettingsAutoLinefeedTime.setProperty("class", "smallInput")
        self.receiveSettingsAutoLinefeedTime.setToolTip(_("Auto linefeed after interval, unit: ms"))
        self.receiveSettingsAutoLinefeed.setMaximumWidth(75)
        self.receiveSettingsAutoLinefeedTime.setMaximumWidth(75)
        self.receiveSettingsTimestamp = QCheckBox(_("Timestamp"))
        self.receiveSettingsTimestamp.setToolTip(_("Add timestamp before received data, will automatically enable auto line feed"))
        self.receiveSettingsColor = QCheckBox(_("Color"))
        self.receiveSettingsColor.setToolTip(_("Enable unix terminal color support, e.g. \\33[31;43mhello\\33[0m"))
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAscii,1,0,1,1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsHex,1,1,1,1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeed, 2, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsAutoLinefeedTime, 2, 1, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsTimestamp, 3, 0, 1, 1)
        serialReceiveSettingsLayout.addWidget(self.receiveSettingsColor, 3, 1, 1, 1)
        serialReceiveSettingsGroupBox.setLayout(serialReceiveSettingsLayout)
        settingLayout.addWidget(serialReceiveSettingsGroupBox)

        # serial send settings
        serialSendSettingsGroupBox = QGroupBox(self.strings.strSerialSendSettings)
        self.sendSettingsAscii = QRadioButton(self.strings.strAscii)
        self.sendSettingsHex = QRadioButton(self.strings.strHex)
        self.sendSettingsAscii.setToolTip(_("Get send data as visible format, select encoding method at top right corner"))
        self.sendSettingsHex.setToolTip(_("Get send data as hex format, e.g. hex '31 32 33' equal to ascii '123'"))
        self.sendSettingsAscii.setChecked(True)
        self.sendSettingsScheduledCheckBox = QCheckBox(self.strings.strScheduled)
        self.sendSettingsScheduledCheckBox.setToolTip(_("Timed send, unit: ms"))
        self.sendSettingsScheduled = QLineEdit("300")
        self.sendSettingsScheduled.setProperty("class", "smallInput")
        self.sendSettingsScheduled.setToolTip(_("Timed send, unit: ms"))
        self.sendSettingsScheduledCheckBox.setMaximumWidth(75)
        self.sendSettingsScheduled.setMaximumWidth(75)
        self.sendSettingsCRLF = QCheckBox(self.strings.strCRLF)
        self.sendSettingsCRLF.setToolTip(_("Select to send \\r\\n instead of \\n"))
        self.sendSettingsCRLF.setChecked(False)
        self.sendSettingsRecord = QCheckBox(_("Record"))
        self.sendSettingsRecord.setToolTip(_("Record send data"))
        self.sendSettingsEscape= QCheckBox(_("Escape"))
        self.sendSettingsEscape.setToolTip(_("Enable escape characters support like \\t \\r \\n \\x01 \\001"))
        serialSendSettingsLayout.addWidget(self.sendSettingsAscii,1,0,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsHex,1,1,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduledCheckBox, 2, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduled, 2, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsCRLF, 3, 0, 1, 2)
        serialSendSettingsLayout.addWidget(self.sendSettingsRecord, 3, 1, 1, 2)
        serialSendSettingsLayout.addWidget(self.sendSettingsEscape, 4, 0, 1, 2)
        serialSendSettingsGroupBox.setLayout(serialSendSettingsLayout)
        settingLayout.addWidget(serialSendSettingsGroupBox)

        settingLayout.setStretch(0, 6)
        settingLayout.setStretch(1, 3)
        settingLayout.setStretch(2, 3)

        # right functional layout
        self.filePathWidget = QLineEdit()
        self.openFileButton = QPushButton(_("Open File"))
        self.sendFileButton = QPushButton(_("Send File"))
        self.clearHistoryButton = QPushButton(_("Clear History"))
        self.addButton = QPushButton(self.strings.strAdd)
        fileSendGroupBox = QGroupBox(self.strings.strSendFile)
        fileSendGridLayout = QGridLayout()
        fileSendGridLayout.addWidget(self.filePathWidget, 0, 0, 1, 1)
        fileSendGridLayout.addWidget(self.openFileButton, 0, 1, 1, 1)
        fileSendGridLayout.addWidget(self.sendFileButton, 1, 0, 1, 2)
        fileSendGroupBox.setLayout(fileSendGridLayout)
        logFileGroupBox = QGroupBox(_("Save log"))
        # cumtom send zone
        #   groupbox
        customSendGroupBox = QGroupBox(_("Cutom send"))
        customSendItemsLayout0 = QVBoxLayout()
        customSendGroupBox.setLayout(customSendItemsLayout0)
        #   scroll

        self.customSendScroll = QScrollArea()
        self.customSendScroll.setMinimumHeight(parameters.customSendItemHeight)
        self.customSendScroll.setWidgetResizable(True)
        self.customSendScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #   add scroll to groupbox
        customSendItemsLayout0.addWidget(self.customSendScroll)
        #   wrapper widget
        cutomSendItemsWraper = QWidget()
        customSendItemsLayoutWrapper = QVBoxLayout()
        cutomSendItemsWraper.setLayout(customSendItemsLayoutWrapper)
        #    custom items
        customItems = QWidget()
        self.customSendItemsLayout = QVBoxLayout()
        customItems.setLayout(self.customSendItemsLayout)
        customSendItemsLayoutWrapper.addWidget(customItems)
        customSendItemsLayoutWrapper.addWidget(self.addButton)
        #   set wrapper widget
        self.customSendScroll.setWidget(cutomSendItemsWraper)
        self.customSendScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 
        logFileLayout = QHBoxLayout()
        self.saveLogCheckbox = QCheckBox()
        self.logFilePath = QLineEdit()
        self.logFileBtn = QPushButton(_("Log path"))
        logFileLayout.addWidget(self.saveLogCheckbox)
        logFileLayout.addWidget(self.logFilePath)
        logFileLayout.addWidget(self.logFileBtn)
        logFileGroupBox.setLayout(logFileLayout)
        sendFunctionalLayout.addWidget(logFileGroupBox)
        sendFunctionalLayout.addWidget(fileSendGroupBox)
        sendFunctionalLayout.addWidget(self.clearHistoryButton)
        sendFunctionalLayout.addWidget(customSendGroupBox)
        sendFunctionalLayout.addStretch(1)
        self.isHideFunctinal = True
        self.hideFunctional()

        # main window
        self.statusBarStauts = QLabel()
        self.statusBarStauts.setMinimumWidth(80)
        self.onstatusBarText("info", self.strings.strReady)
        self.statusBarSendCount = QLabel(self.strings.strSend+"("+self.strings.strBytes+"): "+"0")
        self.statusBarReceiveCount = QLabel(self.strings.strReceive+"("+self.strings.strBytes+"): "+"0")
        self.statusBar().addWidget(self.statusBarStauts)
        self.statusBar().addWidget(self.statusBarSendCount,2)
        self.statusBar().addWidget(self.statusBarReceiveCount,3)

        self.resize(800, 500)
        self.MoveToCenter()
        self.setWindowTitle(parameters.appName+" v"+version.__version__)
        icon = QIcon()
        print("icon path:"+self.DataPath+"/"+parameters.appIcon)
        icon.addPixmap(QPixmap(self.DataPath+"/"+parameters.appIcon), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("comtool")
        self.show()
        print("config file path:",parameters.configFilePath)

    def initEvent(self):
        self.updateSignal.connect(self.showUpdate)
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.sendButtion.clicked.connect(self.onSendData)
        self.receiveUpdateSignal.connect(self.updateReceivedDataDisplay)
        self.clearReceiveButtion.clicked.connect(self.clearReceiveBuffer)
        self.serialPortCombobox.clicked.connect(self.portComboboxClicked)
        self.serailBaudrateCombobox.currentIndexChanged.connect(self.baudrateIndexChanged)
        self.serailBaudrateCombobox.editTextChanged.connect(self.baudrateIndexChanged)
        self.languageCombobox.currentIndexChanged.connect(self.onLanguageChanged)
        self.receiveSettingsTimestamp.clicked.connect(self.onTimeStampClicked)
        self.receiveSettingsAutoLinefeed.clicked.connect(self.onAutoLinefeedClicked)
        self.receiveSettingsAscii.clicked.connect(lambda : self.bindVar(self.receiveSettingsAscii, self.config, "receiveAscii"))
        self.receiveSettingsHex.clicked.connect(lambda : self.bindVar(self.receiveSettingsHex, self.config, "receiveAscii", invert = True))
        self.sendSettingsHex.clicked.connect(self.onSendSettingsHexClicked)
        self.sendSettingsAscii.clicked.connect(self.onSendSettingsAsciiClicked)
        self.sendSettingsRecord.clicked.connect(self.onRecordSendClicked)
        self.sendSettingsEscape.clicked.connect(lambda: self.bindVar(self.sendSettingsEscape, self.config, "sendEscape"))
        self.sendSettingsCRLF.clicked.connect(lambda: self.bindVar(self.sendSettingsCRLF, self.config, "useCRLF"))
        self.errorSignal.connect(self.errorHint)
        self.sendFileOkSignal.connect(self.onSentFile)
        self.statusBarSignal.connect(self.onstatusBarText)
        self.connectionSignal.connect(self.onConnection)
        self.showSerialComboboxSignal.connect(self.showCombobox)
        # self.showBaudComboboxSignal.connect(self.showBaudCombobox)
        self.setDisableSettingsSignal.connect(self.setDisableSettings)
        self.sendHistory.activated.connect(self.sendHistoryIndexChanged)
        self.settingsButton.clicked.connect(self.showHideSettings)
        self.skinButton.clicked.connect(self.skinChange)
        self.aboutButton.clicked.connect(self.showAbout)
        self.openFileButton.clicked.connect(self.selectFile)
        self.logFileBtn.clicked.connect(self.selectLogFile)
        self.sendFileButton.clicked.connect(self.sendFile)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        self.addButton.clicked.connect(self.customSendAdd)
        self.functionalButton.clicked.connect(self.showHideFunctional)
        self.sendArea.currentCharFormatChanged.connect(self.sendAreaFontChanged)
        # self.waveButton.clicked.connect(self.openWaveDisplay)
        self.checkBoxRTS.clicked.connect(self.rtsChanged)
        self.checkBoxDTR.clicked.connect(self.dtrChanged)
        self.saveLogCheckbox.clicked.connect(self.setSaveLog)
        self.encodingCombobox.currentIndexChanged.connect(lambda: self.bindVar(self.encodingCombobox, self.config, "encoding"))
        self.receiveSettingsColor.clicked.connect(self.onSetColorChanged)
        self.receiveSettingsAutoLinefeedTime.textChanged.connect(lambda: self.bindVar(self.receiveSettingsAutoLinefeedTime, self.config, "receiveAutoLindefeedTime", vtype=int, vErrorMsg=_("Auto line feed value error, must be integer")))
        self.sendSettingsScheduled.textChanged.connect(lambda: self.bindVar(self.sendSettingsScheduled, self.config, "sendScheduledTime", vtype=int, vErrorMsg=_("Timed send value error, must be integer")))
        self.sendSettingsScheduledCheckBox.clicked.connect(lambda: self.bindVar(self.sendSettingsScheduledCheckBox, self.config, "sendScheduled"))

        self.myObject=MyClass(self)
        slotLambda = lambda: self.indexChanged_lambda(self.myObject)
        self.serialPortCombobox.currentIndexChanged.connect(slotLambda)

    def bindVar(self, uiObj, varObj, varName: str, vtype=None, vErrorMsg="", checkVar=lambda v:v, invert = False):
        objType = type(uiObj)
        if objType == QCheckBox:
            v = uiObj.isChecked()
            varObj.__setattr__(varName, v if not invert else not v)
            return
        elif objType == QLineEdit:
            v = uiObj.text()
        elif objType == ComboBox:
            varObj.__setattr__(varName, uiObj.currentText())
            return
        elif objType == QRadioButton:
            v = uiObj.isChecked()
            varObj.__setattr__(varName, v if not invert else not v)
            return
        else:
            raise Exception("not support this object")
        if vtype:
            try:
                v = vtype(v)
            except Exception:
                varObj.setText(str(varObj.__getattribute__(varName)))
                self.errorSignal.emit(vErrorMsg)
                return
        try:
            v = checkVar(v)
        except Exception as e:
            self.errorSignal.emit(str(e))
            return
        varObj.__setattr__(varName, v)

    # @QtCore.pyqtSlot(str)
    def indexChanged_lambda(self, obj):
        mainObj = obj.arg
        # print("item changed:",mainObj.serialPortCombobox.currentText())
        try:
            self.serialPortCombobox.setToolTip(mainObj.serialPortCombobox.currentText())
        except Exception as e:
            print("[error] indexChanged_lambda:", e)


    def openCloseSerialProcess(self):
        try:
            if self.serialOpenCloseButton.text() == self.strings.strClose:
                self.receiveProgressStop = True
                try:
                    self.com.close()
                except Exception:
                    pass
                self.setDisableSettingsSignal.emit(False)
                self.connectionSignal.emit(ConnectionStatus.CLOSED)
            else:
                try:
                    self.com.baudrate = int(self.serailBaudrateCombobox.currentText())
                    self.com.port = self.serialPortCombobox.currentText().split(" ")[0]
                    if not self.com.port:
                        raise Exception("please select port")
                    self.com.bytesize = int(self.serailBytesCombobox.currentText())
                    self.com.parity = self.serailParityCombobox.currentText()[0]
                    self.com.stopbits = float(self.serailStopbitsCombobox.currentText())
                    self.com.timeout = None
                    self.com.rts = self.config.rts  # request to send data to device(we have data to send)
                    self.com.dtr = self.config.dtr  # data terminal ready, read only, i.e. we can send now
                    self.com.xonxoff = False
                    self.com.rtscts = False
                    self.com.dsrdtr = False
                    disableDtrRtsControl = False
                    if self.serialFlowControlCombobox.currentText() == "XON/XOFF":
                        self.com.xonxoff = True
                    elif self.serialFlowControlCombobox.currentText() == "RTS/CTS":
                        self.com.rtscts = True
                        disableDtrRtsControl = True
                    elif self.serialFlowControlCombobox.currentText() == "DSR/DTR":
                        self.com.dsrdtr = True
                        disableDtrRtsControl = True
                    if disableDtrRtsControl:
                        self.checkBoxRTS.setDisabled(True)
                        self.checkBoxDTR.setDisabled(True)
                    else:
                        self.checkBoxRTS.setDisabled(False)
                        self.checkBoxDTR.setDisabled(False)
                    self.com.open()
                    # print("open success")
                    # print(self.com)
                    self.setDisableSettingsSignal.emit(True)
                    self.connectionSignal.emit(ConnectionStatus.CONNECTED)
                    self.receiveProcess = threading.Thread(target=self.receiveDataProcess)
                    self.receiveProcess.setDaemon(True)
                    self.sendProcess = threading.Thread(target=self.sendDataProcess)
                    self.sendProcess.setDaemon(True)
                    self.dataToSend = []
                    self.fileToSend = []
                    self.receiveProcess.start()
                    self.sendProcess.start()
                except Exception as e:
                    self.receiveProgressStop = True
                    self.com.close()
                    self.errorSignal.emit( self.strings.strOpenFailed +"\n"+ str(e))
                    self.setDisableSettingsSignal.emit(False)
                    self.connectionSignal.emit(ConnectionStatus.CLOSED)
        except Exception as e:
            print(e)
    
    def setDisableSettings(self, disable):
        if disable:
            self.serialOpenCloseButton.setText(self.strings.strClose)
            self.onstatusBarText("info", self.strings.strReady)
            self.serialPortCombobox.setDisabled(True)
            self.serailBaudrateCombobox.setDisabled(True)
            self.serailParityCombobox.setDisabled(True)
            self.serailStopbitsCombobox.setDisabled(True)
            self.serailBytesCombobox.setDisabled(True)
            self.serialFlowControlCombobox.setDisabled(True)
            self.serialOpenCloseButton.setDisabled(False)
        else:
            self.serialOpenCloseButton.setText(self.strings.strOpen)
            self.onstatusBarText("info", self.strings.strClosed)
            self.serialPortCombobox.setDisabled(False)
            self.serailBaudrateCombobox.setDisabled(False)
            self.serailParityCombobox.setDisabled(False)
            self.serailStopbitsCombobox.setDisabled(False)
            self.serailBytesCombobox.setDisabled(False)
            self.serialFlowControlCombobox.setDisabled(False)
            self.programExitSaveParameters()

    def openCloseSerial(self):
        t = threading.Thread(target=self.openCloseSerialProcess)
        t.setDaemon(True)
        t.start()

    def rtsChanged(self):
        self.config.rts = self.checkBoxRTS.isChecked()
        self.com.rts = self.config.rts
    
    def dtrChanged(self):
        self.config.dtr = self.checkBoxDTR.isChecked()
        self.com.dtr = self.config.dtr

    def setSaveLog(self):
        if self.saveLogCheckbox.isChecked():
            self.config.saveLog = True
        else:
            self.config.saveLog = False

    def portComboboxClicked(self):
        self.detectSerialPort()

    def getSendData(self, data=None) -> bytes:
        if data is None:
            data = self.sendArea.toPlainText()
        if not data:
            return b''
        if self.config.useCRLF:
            data = data.replace("\n", "\r\n")
        if not self.config.sendAscii:
            if self.config.useCRLF:
                data = data.replace("\r\n", " ")
            else:
                data = data.replace("\n", " ")
            data = utils.hex_str_to_bytes(data)
            if data == -1:
                self.errorSignal.emit(_("Format error, should be like 00 01 02 03"))
                return b''
        else:
            encoding = self.config.encoding
            if not self.config.sendEscape:
                data = data.encode(encoding,"ignore")
            else: # '11234abcd\n123你好\r\n\thello\x00\x01\x02'
                final = b""
                p = 0
                escapes = {
                    "a": (b'\a', 2),
                    "b": (b'\b', 2),
                    "f": (b'\f', 2),
                    "n": (b'\n', 2),
                    "r": (b'\r', 2),
                    "t": (b'\t', 2),
                    "v": (b'\v', 2),
                    "\\": (b'\\', 2),
                    "\'": (b"'", 2),
                    '\"': (b'"', 2),
                }
                octstr = ["0", "1", "2", "3", "4", "5", "6", "7"]
                while 1:
                    idx = data[p:].find("\\")
                    if idx < 0:
                        final += data[p:].encode(encoding, "ignore")
                        break
                    final += data[p : p + idx].encode(encoding, "ignore")
                    p += idx
                    e = data[p+1]
                    if e in escapes:
                        r = escapes[e][0]
                        p += escapes[e][1]
                    elif e == "x": # \x01
                        try:
                            r = bytes([int(data[p+2 : p+4], base=16)])
                            p += 4
                        except Exception:
                            self.errorSignal.emit(_("Escape is on, but escape error:") + data[p : p+4])
                            return b''
                    elif e in octstr and len(data) > (p+2) and data[p+2] in octstr: # \dd or \ddd e.g. \001
                        try:
                            twoOct = False
                            if len(data) > (p+3) and data[p+3] in octstr: # \ddd
                                try:
                                    r = bytes([int(data[p+1 : p+4], base=8)])
                                    p += 4
                                except Exception:
                                    twoOct = True
                            else:
                                twoOct = True
                            if twoOct:
                                r = bytes([int(data[p+1 : p+3], base=8)])
                                p += 3
                        except Exception as e:
                            print(e)
                            self.errorSignal.emit(_("Escape is on, but escape error:") + data[p : p+4])
                            return b''
                    else:
                        r = data[p: p+2].encode(encoding, "ignore")
                        p += 2
                    final += r

                data = final
        return data

    def onSendData(self, notClick=True, data=None):
        try:
            if self.com.is_open:
                data = self.getSendData(data)
                if not data:
                    return
                # record send data
                if self.config.recordSend:
                    head = '=> '
                    if self.config.showTimestamp:
                        head += f'[{utils.datetime_format_ms(datetime.now())}] '
                    isHexStr, sendStr, sendStrsColored = self.bytes2String(data, not self.config.receiveAscii, encoding=self.config.encoding)
                    if isHexStr:
                        head += "[HEX] "
                        sendStr = sendStr.upper()
                        sendStrsColored= sendStr
                    if self.config.useCRLF:
                        head = "\r\n" + head
                    else:
                        head = "\n" + head
                    if head.strip() != '=>':
                        head = f'{head.rstrip()}: '
                    self.receiveUpdateSignal.emit(head, [sendStrsColored], self.config.encoding)
                    self.sendRecord.insert(0, head + sendStr)
                self.sendData(data_bytes=data)
                data = self.sendArea.toPlainText()
                self.sendHistoryFindDelete(data)
                self.sendHistory.insertItem(0,data)
                self.sendHistory.setCurrentIndex(0)
                # scheduled send
                if self.config.sendScheduled:
                    if not self.isScheduledSending:
                        t = threading.Thread(target=self.scheduledSend)
                        t.setDaemon(True)
                        t.start()
        except Exception as e:
            print("[Error] onSendData", e)
            self.errorSignal.emit(self.strings.strWriteError)
            # print(e)

    def scheduledSend(self):
        self.isScheduledSending = True
        while self.config.sendScheduled:
            self.onSendData()
            try:
                time.sleep(self.config.sendScheduledTime/1000)
            except Exception:
                self.errorSignal.emit(self.strings.strTimeFormatError)
        self.isScheduledSending = False

    def receiveDataProcess(self):
        def portExits():
            ports = self.findSerialPort()
            devices = []
            for p in ports:
                devices.append(p.device)
            if self.com.port in devices:
                return True
            return False
        self.receiveProgressStop = False
        timeLastReceive = 0
        waitingReconnect = False
        new_line = True
        logData = None
        self.com.timeout = 0.010
        buffer = b''
        while(not self.receiveProgressStop):
            logData = None
            bytes = b''
            if waitingReconnect:
                if portExits():
                    try:
                        self.com.open()
                        print("reopen connection")
                        waitingReconnect = False
                        self.statusBarSignal.emit("info", _("Ready"))
                        self.connectionSignal.emit(ConnectionStatus.CONNECTED)
                        continue
                    except Exception as e:
                        pass
                time.sleep(0.01)
                continue
            try:
                # length = self.com.in_waiting
                length = max(1, self.com.in_waiting)
                bytes = self.com.read(length)
                if bytes:
                    buffer += bytes
                    self.receiveCount += len(bytes)
            except Exception as e:
                if (not self.receiveProgressStop) and not portExits():
                    self.com.close()
                    waitingReconnect = True
                    self.connectionSignal.emit(ConnectionStatus.LOSE)
                    self.statusBarSignal.emit("warning", _("Connection lose!"))
            # check buffer and timeout
            head = ""
            # timeout, add new line
            if time.time() - timeLastReceive> self.config.receiveAutoLindefeedTime:
                if self.config.showTimestamp or self.config.receiveAutoLinefeed:
                    if self.config.useCRLF:
                        head += "\r\n"
                    else:
                        head += "\n"
                    new_line = True
            if bytes:
                timeLastReceive = time.time()
            data = ""
            # have data in buffer
            if len(buffer) > 0:
                # show as hex, just show
                if not self.config.receiveAscii:
                    data = utils.bytes_to_hex_str(buffer)
                    colorData = data
                    buffer = b''
                # show as string, and don't need to render color
                elif not self.config.color:
                    data = buffer.decode(encoding=self.config.encoding, errors="ignore")
                    colorData = data
                    buffer = b''
                # show as string, and need to render color, wait for \n or until timeout to ensure color flag in buffer
                else:
                    if time.time() - timeLastReceive >  self.config.receiveAutoLindefeedTime or b'\n' in buffer:
                        data, colorData = self.getColoredText(buffer, self.config.encoding)
                        buffer = b''
                # add time receive head
                # get data from buffer, now render
                if data:
                    # add time header
                    if new_line:
                        timeNow = f'[{utils.datetime_format_ms(datetime.now())}] '
                        if self.config.recordSend:
                            head += "<= " 
                        if self.config.showTimestamp:
                            head += timeNow
                            head = f'{head.rstrip()}: '
                        new_line = False
                    self.receiveUpdateSignal.emit(head, [colorData], self.config.encoding)
                    logData = head + data

            while len(self.sendRecord) > 0:
                self.onLog(self.sendRecord.pop())
            if logData:
                self.onLog(logData)

    def sendData(self, data_bytes=None, file_path=None):
        if data_bytes:
            self.dataToSend.insert(0, data_bytes)
        if file_path:
            self.fileToSend.insert(0, file_path)

    def sendFile(self):
        filename = self.filePathWidget.text()
        if not os.path.exists(filename):
            self.errorSignal.emit(_("File path error\npath") + ":%s" %(filename))
            return
        if not self.com.is_open:
            self.errorSignal.emit(_("Connect first please"))
        else:
            self.sendFileButton.setDisabled(True)
            self.sendFileButton.setText(self.strings.strSendingFile)
            self.sendData(file_path=filename)

    def onSent(self, n_bytes):
        self.sendCount += n_bytes
        self.receiveUpdateSignal.emit("", [], "")

    def onSentFile(self, ok, path):
        print(f"file sent {'ok' if ok else 'fail'}, path: {path}")
        self.sendFileButton.setText(self.strings.strSendFile)
        self.sendFileButton.setDisabled(False)

    def sendDataProcess(self):
        self.receiveProgressStop = False
        while(not self.receiveProgressStop):
            try:
                while len(self.dataToSend) > 0:
                    data = self.dataToSend.pop()
                    self.com.write(data)
                    self.onSent(len(data))
                while len(self.fileToSend) > 0:
                    file_path = self.fileToSend.pop()
                    ok = False
                    if file_path and os.path.exists(file_path):
                        data = None
                        try:
                            with open(file_path, "rb") as f:
                                data = f.read()
                        except Exception as e:
                            self.errorSignal.emit(_("Open file failed!") + "\n%s\n%s" %(file_path, str(e)))
                        if data:
                            self.com.write(data)
                            self.onSent(len(data))
                            ok = True
                    self.sendFileOkSignal.emit(ok, file_path)
                time.sleep(0.001)
            except Exception as e:
                if 'multiple access' in str(e):
                    self.errorSignal.emit("device disconnected or multiple access on port?")
                break

    def _canDraw(self, ucs4cp):
        return 0x2500 <= ucs4cp and ucs4cp <= 0x259F

    def _getColorByfmt(self, fmt:bytes):
        colors = {
            b"0": None,
            b"30": "#000000",
            b"31": "#ff0000",
            b"32": "#008000",
            b"33": "#f9a825",
            b"34": "#0000ff",
            b"35": "#9c27b0",
            b"36": "#1b5e20",
            b"37": "#000000",
        }
        bgs = {
            b"0": None,
            b"40": "#000000",
            b"41": "#ff0000",
            b"42": "#008000",
            b"43": "#f9a825",
            b"44": "#0000ff",
            b"45": "#9c27b0",
            b"46": "#1b5e20",
            b"47": "#000000",
        }
        fmt = fmt[2:-1].split(b";")
        color = colors[b'0']
        bg = bgs[b'0']
        for cmd in fmt:
            if cmd in colors:
                color = colors[cmd]
            if cmd in bgs:
                bg = bgs[cmd]
        return color, bg

    def _texSplitByColor(self, text:bytes):
        colorFmt = re.findall(rb'\x1b\[.*?m', text)
        plaintext = text
        for fmt in colorFmt:
            plaintext = plaintext.replace(fmt, b"")
        colorStrs = []
        if colorFmt:
            p = 0
            for fmt in colorFmt:
                idx = text[p:].index(fmt)
                if idx != 0:
                    colorStrs.append([self.lastColor, self.lastBg, text[p:p+idx]])
                    p += idx
                self.lastColor, self.lastBg = self._getColorByfmt(fmt)
                p += len(fmt)
            colorStrs.append([self.lastColor, self.lastBg, text[p:]])
        else:
            colorStrs = [[self.lastColor, self.lastBg, text]]
        return plaintext, colorStrs

    def getColoredText(self, data_bytes, decoding=None):
        plainText, coloredText = self._texSplitByColor(data_bytes)
        if decoding:
            plainText = plainText.decode(encoding=decoding, errors="ignore")
            decodedColoredText = []
            for color, bg, text in coloredText:
                decodedColoredText.append([color, bg, text.decode(encoding=decoding, errors="ignore")])
            coloredText = decodedColoredText
        return plainText, coloredText



    def updateReceivedDataDisplay(self, head : str, datas : list, encoding):
        if datas:
            curScrollValue = self.receiveArea.verticalScrollBar().value()
            self.receiveArea.moveCursor(QTextCursor.End)
            endScrollValue = self.receiveArea.verticalScrollBar().value()
            cursor = self.receiveArea.textCursor()
            format = cursor.charFormat()
            font = QFont('Menlo,Consolas,Bitstream Vera Sans Mono,Courier New,monospace, Microsoft YaHei', 10)
            format.setFont(font)
            if not self.defaultColor:
                self.defaultColor = format.foreground()
            if not self.defaultBg:
                self.defaultBg = format.background()
            if head:
                format.setForeground(self.defaultColor)
                cursor.setCharFormat(format)
                format.setBackground(self.defaultBg)
                cursor.setCharFormat(format)
                cursor.insertText(head)
            for data in datas:
                if type(data) == str:
                    self.receiveArea.insertPlainText(data)
                elif type(data) == list:
                    for color, bg, text in data:
                        if color:
                            format.setForeground(QColor(color))
                            cursor.setCharFormat(format)
                        else:
                            format.setForeground(self.defaultColor)
                            cursor.setCharFormat(format)
                        if bg:
                            format.setBackground(QColor(bg))
                            cursor.setCharFormat(format)
                        else:
                            format.setBackground(self.defaultBg)
                            cursor.setCharFormat(format)
                        cursor.insertText(text)
                else: # bytes
                    self.receiveArea.insertPlainText(data.decode(encoding=encoding, errors="ignore"))
            if curScrollValue < endScrollValue:
                self.receiveArea.verticalScrollBar().setValue(curScrollValue)
            else:
                self.receiveArea.moveCursor(QTextCursor.End)
        self.statusBarSendCount.setText(f'{self.strings.strSend}({_("bytes")}): {self.sendCount}')
        self.statusBarReceiveCount.setText(f'{self.strings.strReceive}({_("bytes")}): {self.receiveCount}')

    def onstatusBarText(self, msg_type, msg):
        if msg_type == "info":
            color = "#008200"
        elif msg_type == "warning":
            color = "#fb8c00"
        elif msg_type == "error":
            color = "#f44336"
        else:
            color = "#008200"
        text = f'<font color={color}>{msg}</font>'
        self.statusBarStauts.setText(text)

    def onConnection(self, status : ConnectionStatus):
        if status == ConnectionStatus.LOSE:
            self.serialOpenCloseButton.setProperty("class", "warning")
        else:
            self.serialOpenCloseButton.setProperty("class", "")
        self.updateStyle(self.serialOpenCloseButton)

    def updateStyle(self, widget):
        self.frameWidget.style().unpolish(widget)
        self.frameWidget.style().polish(widget)
        self.frameWidget.update()


    def onSendSettingsHexClicked(self):
        self.config.sendAscii = False
        data = self.sendArea.toPlainText().replace("\n","\r\n")
        data = utils.bytes_to_hex_str(data.encode())
        self.sendArea.clear()
        self.sendArea.insertPlainText(data)

    def onSendSettingsAsciiClicked(self):
        self.config.sendAscii = True
        try:
            data = self.sendArea.toPlainText().replace("\n"," ").strip()
            self.sendArea.clear()
            if data != "":
                data = utils.hex_str_to_bytes(data).decode(self.config.encoding,'ignore')
                self.sendArea.insertPlainText(data)
        except Exception as e:
            # QMessageBox.information(self,self.strings.strWriteFormatError,self.strings.strWriteFormatError)
            print("format error")

    def onAutoLinefeedClicked(self):
        if (self.config.showTimestamp or self.config.recordSend) and not self.receiveSettingsAutoLinefeed.isChecked():
            self.receiveSettingsAutoLinefeed.setChecked(True)
            self.errorSignal.emit(_("linefeed always on if timestamp or record send is on"))
        self.config.receiveAutoLinefeed = self.receiveSettingsAutoLinefeed.isChecked()

    def onTimeStampClicked(self):
        self.config.showTimestamp = self.receiveSettingsTimestamp.isChecked()
        if self.config.showTimestamp:
            self.config.receiveAutoLinefeed = True
            self.receiveSettingsAutoLinefeed.setChecked(True)

    def onRecordSendClicked(self):
        self.config.recordSend = self.sendSettingsRecord.isChecked()
        if self.config.recordSend:
            self.config.receiveAutoLinefeed = True
            self.receiveSettingsAutoLinefeed.setChecked(True)

    def onEscapeSendClicked(self):
        self.config.sendEscape = self.sendSettingsEscape.isChecked()

    def onLanguageChanged(self):
        idx = self.languageCombobox.currentIndex()
        locale = list(self.languages.keys())[idx]
        self.config.locale = locale
        i18n.set_locale(locale)
        reply = QMessageBox.question(self, _('Restart now?'),
                                     _("language changed to: ") + self.languages[self.config.locale] + "\n" + _("Restart software to take effect now?"), QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.needRestart = True
            self.close()

    def baudrateIndexChanged(self):
        if self.serailBaudrateCombobox.currentText() == self.baudrateCustomStr:
            self.serailBaudrateCombobox.clearEditText()

    def sendHistoryIndexChanged(self):
        self.sendArea.clear()
        self.sendArea.insertPlainText(self.sendHistory.currentText())

    def clearReceiveBuffer(self):
        self.receiveArea.clear()
        self.receiveCount = 0
        self.sendCount = 0
        self.receiveUpdateSignal.emit("", [], "")

    def MoveToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def errorHint(self,str):
        QMessageBox.information(self, str, str)

    def closeEvent(self, event):
        print("----- close event")
        # reply = QMessageBox.question(self, 'Sure To Quit?',
        #                              "Are you sure to quit?", QMessageBox.Yes |
        #                              QMessageBox.No, QMessageBox.No)
        if 1: # reply == QMessageBox.Yes:
            self.receiveProgressStop = True
            self.com.close()
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

    def showCombobox(self):
        self.serialPortCombobox.showPopup()

    def detectSerialPortProcess(self):
        while(1):
            portList = self.findSerialPort()
            if len(portList)>0:
                currText = self.serialPortCombobox.currentText()
                self.serialPortCombobox.clear()
                for p in portList:
                    showStr = "{} {} - {}".format(p.device, p.name, p.description)
                    if p.manufacturer:
                        showStr += f' - {p.manufacturer}'
                    if p.pid:
                        showStr += ' - pid(0x{:04X})'.format(p.pid)
                    if p.vid:
                        showStr += ' - vid(0x{:04X})'.format(p.vid)
                    if p.serial_number:
                        showStr += f' - v{p.serial_number}'
                    if p.device.startswith("/dev/cu.Bluetooth-Incoming-Port"):
                        continue
                    self.serialPortCombobox.addItem(showStr)    
                index = self.serialPortCombobox.findText(currText)
                if index>=0:
                    self.serialPortCombobox.setCurrentIndex(index)
                else:
                    self.serialPortCombobox.setCurrentIndex(0)
                break
            time.sleep(1)
        self.showSerialComboboxSignal.emit()
        self.isDetectSerialPort = False

    def sendHistoryFindDelete(self,str):
        self.sendHistory.removeItem(self.sendHistory.findText(str))

    def bytes2String(self, data : bytes, showAsHex : bool, encoding="utf-8"):
        isHexString = False
        dataColored = None
        if showAsHex:
            return True, binascii.hexlify(data, ' ').decode(encoding=encoding), dataColored
        try:
            dataPlain, dataColored = self.getColoredText(data, self.config.encoding)
        except Exception:
            dataPlain = binascii.hexlify(data, ' ').decode(encoding=encoding)
            isHexString = True
        return isHexString, dataPlain, dataColored

    def programExitSaveParameters(self):
        paramObj = self.config
        paramObj.baudRate = self.serailBaudrateCombobox.currentIndex()
        paramObj.dataBytes = self.serailBytesCombobox.currentIndex()
        paramObj.parity = self.serailParityCombobox.currentIndex()
        paramObj.stopBits = self.serailStopbitsCombobox.currentIndex()
        paramObj.skin = self.config.skin
        paramObj.sendHistoryList.clear()
        for i in range(0,self.sendHistory.count()):
            paramObj.sendHistoryList.append(self.sendHistory.itemText(i))
        # send items
        valid = []
        for text in self.config.customSendItems:
            if text:
                valid.append(text)
        self.config.customSendItems = valid
        paramObj.save(parameters.configFilePath)

    def loadParameters(self):
        paramObj = parameters.Parameters()
        paramObj.load(parameters.configFilePath)
        return paramObj

    def programStartGetSavedParameters(self, paramObj):
        self.serailBaudrateCombobox.setCurrentIndex(paramObj.baudRate)
        self.serailBytesCombobox.setCurrentIndex(paramObj.dataBytes)
        self.serailParityCombobox.setCurrentIndex(paramObj.parity)
        self.serailStopbitsCombobox.setCurrentIndex(paramObj.stopBits)
        self.receiveSettingsHex.setChecked(not paramObj.receiveAscii)
        self.receiveSettingsAutoLinefeed.setChecked(paramObj.receiveAutoLinefeed)
        try:
            interval = int(paramObj.receiveAutoLindefeedTime)
        except Exception:
            interval = parameters.Parameters.receiveAutoLindefeedTime
        self.receiveSettingsAutoLinefeedTime.setText(str(interval) if interval > 0 else str(parameters.Parameters.receiveAutoLindefeedTime))
        self.receiveSettingsTimestamp.setChecked(paramObj.showTimestamp)
        self.sendSettingsHex.setChecked(not paramObj.sendAscii)
        self.sendSettingsScheduledCheckBox.setChecked(paramObj.sendScheduled)
        try:
            interval = int(paramObj.sendScheduledTime)
        except Exception:
            interval = parameters.Parameters.sendScheduledTime
        self.sendSettingsScheduled.setText(str(interval) if interval > 0 else str(parameters.Parameters.sendScheduledTime))
        self.sendSettingsCRLF.setChecked(paramObj.useCRLF)
        self.sendSettingsRecord.setChecked(paramObj.recordSend)
        self.sendSettingsEscape.setChecked(paramObj.sendEscape)
        for i in range(0, len(paramObj.sendHistoryList)):
            text = paramObj.sendHistoryList[i]
            self.sendHistory.addItem(text)
        self.checkBoxRTS.setChecked(paramObj.rts)
        self.checkBoxDTR.setChecked(paramObj.dtr)
        self.encodingCombobox.setCurrentIndex(self.supportedEncoding.index(paramObj.encoding))
        try:
            idx = list(self.languages.keys()).index(paramObj.locale)
        except Exception:
            idx = 0
        self.languageCombobox.setCurrentIndex(idx)
        self.logFilePath.setText(paramObj.saveLogPath)
        self.logFilePath.setToolTip(paramObj.saveLogPath)
        self.saveLogCheckbox.setChecked(paramObj.saveLog)
        self.receiveSettingsColor.setChecked(paramObj.color)
        # send items
        for text in self.config.customSendItems:
            self.insertSendItem(text, load=True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = True
        elif event.key() == Qt.Key_Return or event.key()==Qt.Key_Enter:
            if self.keyControlPressed:
                self.onSendData()
        elif event.key() == Qt.Key_L:
            if self.keyControlPressed:
                self.sendArea.clear()
        elif event.key() == Qt.Key_K:
            if self.keyControlPressed:
                self.receiveArea.clear()

    def keyReleaseEvent(self,event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = False

    def sendAreaFontChanged(self,font):
        pass

    def insertSendItem(self, text="", load = False):
        itemsNum = self.customSendItemsLayout.count() + 1
        if itemsNum > parameters.customSendItemFixHeightNum:
            itemsNum = parameters.customSendItemFixHeightNum
        self.customSendScroll.setMinimumHeight(parameters.customSendItemHeight * (itemsNum + 1))
        item = QWidget()
        layout = QHBoxLayout()
        item.setLayout(layout)
        cmd = QLineEdit(text)
        cmd.textChanged.connect(lambda: self.onCustomItemChange(self.customSendItemsLayout.indexOf(item), cmd))
        send = QPushButton(_("Send"))
        send.setProperty("class", "smallBtn")
        send.clicked.connect(lambda: self.sendCustomItem(self.config.customSendItems[self.customSendItemsLayout.indexOf(item)]))
        delete = QPushButton("x")
        delete.setProperty("class", "deleteBtn")
        layout.addWidget(cmd)
        layout.addWidget(send)
        layout.addWidget(delete)
        delete.clicked.connect(lambda: self.deleteSendItem(self.customSendItemsLayout.indexOf(item), item))
        self.customSendItemsLayout.addWidget(item)
        if not load:
            self.config.customSendItems.append("")

    def deleteSendItem(self, idx, item):
        item.setParent(None)
        self.config.customSendItems.pop(idx)
        itemsNum = self.customSendItemsLayout.count()
        if itemsNum > parameters.customSendItemFixHeightNum:
            itemsNum = parameters.customSendItemFixHeightNum
        self.customSendScroll.setMinimumHeight(parameters.customSendItemHeight * (itemsNum + 1))

    def onCustomItemChange(self, idx, edit):
        text = edit.text()
        self.config.customSendItems[idx] = text

    def sendCustomItem(self, text):
        self.onSendData(data = text)

    def customSendAdd(self):
        self.insertSendItem()

    def showHideSettings(self):
        if self.isHideSettings:
            self.showSettings()
            self.isHideSettings = False
        else:
            self.hideSettings()
            self.isHideSettings = True

    def showSettings(self):
        self.settingWidget.show()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath",self.DataPath))

    def hideSettings(self):
        self.settingWidget.hide()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath", self.DataPath))

    def showHideFunctional(self):
        if self.isHideFunctinal:
            self.showFunctional()
            self.isHideFunctinal = False
        else:
            self.hideFunctional()
            self.isHideFunctinal = True

    def showFunctional(self):
        self.functionalWiget.show()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath",self.DataPath))

    def hideFunctional(self):
        self.functionalWiget.hide()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath", self.DataPath))

    def skinChange(self):
        if self.config.skin == 1: # light
            file = open(self.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
            self.config.skin = 2
        else: # elif self.config.skin == 2: # dark
            file = open(self.DataPath + '/assets/qss/style.qss', "r", encoding="utf-8")
            self.config.skin = 1
        self.app.setStyleSheet(file.read().replace("$DataPath", self.DataPath))

    def onSetColorChanged(self):
        self.config.color = self.receiveSettingsColor.isChecked()

    def showAbout(self):
        QMessageBox.information(self, _("About"), helpAbout.strAbout())
    def selectFile(self):
        oldPath = self.filePathWidget.text()
        if oldPath=="":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,  
                                    _("Select file"),
                                    oldPath,
                                    _("All Files (*)"))

        if fileName_choose == "":
            return
        self.filePathWidget.setText(fileName_choose)
        self.filePathWidget.setToolTip(fileName_choose)

    def selectLogFile(self):
        oldPath = self.logFilePath.text()
        if oldPath=="":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,  
                                    _("Select file"),
                                    os.path.join(oldPath, "comtool.log"),
                                    _("Log file (*.log);;txt file (*.txt);;All Files (*)"))

        if fileName_choose == "":
            return
        self.logFilePath.setText(fileName_choose)
        self.logFilePath.setToolTip(fileName_choose)
        self.config.saveLogPath = fileName_choose

    def onLog(self, text):
        if self.config.saveLogPath:
            with open(self.config.saveLogPath, "a+", encoding=self.config.encoding, newline="\n") as f:
                f.write(text)

    def clearHistory(self):
        self.config.sendHistoryList.clear()
        self.sendHistory.clear()
        self.errorSignal.emit(_("History cleared!"))

    def showUpdate(self, versionInfo):
        versionInt = versionInfo.int()
        if self.config.skipVersion and self.config.skipVersion >= versionInt:
            return
        msgBox = QMessageBox()
        desc = versionInfo.desc if len(versionInfo.desc) < 300 else versionInfo.desc[:300] + " ... "
        link = '<a href="https://github.com/Neutree/COMTool/releases">github.com/Neutree/COMTool/releases</a>'
        info = '{}<br>{}<br><br>v{}: {}<br><br>{}'.format(_("New versioin detected, please click learn more to download"), link, f'{versionInfo.major}.{versionInfo.minor}.{versionInfo.dev}', versionInfo.name, desc)
        learn = msgBox.addButton(_("Learn More"), QMessageBox.YesRole)
        skip = msgBox.addButton(_("Skip this version"), QMessageBox.YesRole)
        nextTime = msgBox.addButton(_("Remind me next time"), QMessageBox.NoRole)
        msgBox.setWindowTitle(_("Need update"))
        msgBox.setText(info)
        result = msgBox.exec_()
        if result == 0:
            auto = autoUpdate.AutoUpdate()
            auto.OpenBrowser()
        elif result == 1:
            self.config.skipVersion = versionInt

            

    def autoUpdateDetect(self):
        auto = autoUpdate.AutoUpdate()
        needUpdate, versionInfo = auto.detectNewVersion()
        if needUpdate:
            self.updateSignal.emit(versionInfo)

    # def openWaveDisplay(self):
    #     self.wave = Wave()
    #     self.isWaveOpen = True
    #     self.wave.closed.connect(self.OnWaveClosed)
    #
    # def OnWaveClosed(self):
    #     print("wave window closed")
    #     self.isWaveOpen = False

def gen_tranlate_files(curr_dir):
    try:
        import i18n
    except Exception:
        from COMTool import i18n
    cwd = os.getcwd()
    os.chdir(curr_dir)
    i18n.main("finish")
    os.chdir(cwd)

def load_fonts(paths):
    from PyQt5 import QtGui
    for path in paths:
        id = QtGui.QFontDatabase.addApplicationFont(path)
        fonts = QtGui.QFontDatabase.applicationFontFamilies(id)
        print("load fonts:", fonts)

def main():
    ret = 1
    try:
        while 1:
            # check translate
            curr_dir = os.path.abspath(os.path.dirname(__file__))
            print("curr_dir   ", curr_dir)
            mo_path = os.path.join(curr_dir, "locales", "en", "LC_MESSAGES", "messages.mo")
            if not os.path.exists(mo_path):
                gen_tranlate_files(curr_dir)
            app = QApplication(sys.argv)
            mainWindow = MainWindow(app)
            # path = os.path.join(mainWindow.DataPath, "assets", "fonts", "JosefinSans-Regular.ttf")
            # load_fonts([path])
            print("data path:"+mainWindow.DataPath)
            if(mainWindow.config.skin == 1) :# light skin
                file = open(mainWindow.DataPath+'/assets/qss/style.qss',"r", encoding="utf-8")
            else: #elif mainWindow.config == 2: # dark skin
                file = open(mainWindow.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
            qss = file.read().replace("$DataPath",mainWindow.DataPath)
            app.setStyleSheet(qss)
            mainWindow.detectSerialPort()
            t = threading.Thread(target=mainWindow.autoUpdateDetect)
            t.setDaemon(True)
            t.start()
            ret = app.exec_()
            if not mainWindow.needRestart:
                print("not mainWindow.needRestart")
                break
    except Exception as e:
        import traceback
        exc = traceback.format_exc()
        show_error(_("Error"), exc)
    return ret

def show_error(title, msg):
    print("error:", msg)
    app = QApplication(sys.argv)
    window = QMainWindow()
    QMessageBox.information(window, title, msg)

if __name__ == '__main__':
    sys.exit(main())

