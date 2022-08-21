try:
    import parameters,helpAbout,autoUpdate
    from Combobox import ComboBox
    import i18n
    from i18n import _, tr
    import version
    import utils, utils_ui
    from conn.base import ConnectionStatus
    from widgets import statusBar
except ImportError:
    from COMTool import parameters,helpAbout,autoUpdate, utils, utils_ui
    from COMTool.Combobox import ComboBox
    from COMTool import i18n
    from COMTool.i18n import _, tr
    from COMTool import version
    from COMTool.conn.base import ConnectionStatus
    from COMTool.widgets import statusBar

try:
    from base import Plugin_Base
except Exception:
    from .base import Plugin_Base

from PyQt5.QtCore import pyqtSignal,Qt, QRect, QMargins
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor
import qtawesome as qta # https://github.com/spyder-ide/qtawesome
import os, threading, time, re
from datetime import datetime

class Plugin(Plugin_Base):
    '''
        call sequence:
            set vars like hintSignal, hintSignal
            onInit
            onWidget
            onUiInitDone
                send
                onReceived
    '''
    # vars set by caller
    send = None              # send(data_bytes=None, file_path=None)
    hintSignal = None       # hintSignal.emit(title, msg)
    configGlobal = {}
    # other vars
    connParent = "main"
    connChilds = []
    id = "dbg"
    name = _("Send Receive")
    #
    receiveUpdateSignal = pyqtSignal(str, list, str) # head, content, encoding
    receiveProgressStop = False
    receivedData = []
    lock = threading.Lock()
    sendRecord = []
    lastColor = None
    lastBg = None
    defaultColor = None
    defaultBg = None
    help = '''{}<br>
<b style="color:#ef5350;"><kbd>F11</kbd></b>: {}<br>
<b style="color:#ef5350;"><kbd>Ctrl+Enter</kbd></b>: {}<br>
<b style="color:#ef5350;"><kbd>Ctrl+L</kbd></b>: {}<br>
<b style="color:#ef5350;"><kbd>Ctrl+K</kbd></b>: {}<br>
'''.format(
        _('Shortcut:'),
        _('Full screen'),
        _('Send data'),
        _('Clear Send Area'),
        _('Clear Receive Area')
    )

    def onInit(self, config):
        super().onInit(config)
        self.keyControlPressed = False
        self.isScheduledSending = False
        self.config = config
        default = {
            "version": 1,
            "receiveAscii" : True,
            "receiveAutoLinefeed" : False,
            "receiveAutoLindefeedTime" : 200,
            "sendAscii" : True,
            "sendScheduled" : False,
            "sendScheduledTime" : 300,
            "sendAutoNewline": False,
            "useCRLF" : True,
            "showTimestamp" : False,
            "recordSend" : False,
            "saveLogPath" : "",
            "saveLog" : False,
            "color" : False,
            "sendEscape" : False,
            "customSendItems" : [],
            "sendHistoryList" : [],
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]

    def onWidgetMain(self, parent):
        self.mainWidget = QSplitter(Qt.Vertical)
        # widgets receive and send area
        self.receiveArea = QTextEdit()
        font = QFont('Menlo,Consolas,Bitstream Vera Sans Mono,Courier New,monospace, Microsoft YaHei', 10)
        self.receiveArea.setFont(font)
        self.receiveArea.setLineWrapMode(QTextEdit.NoWrap)
        self.sendArea = QTextEdit()
        self.sendArea.setLineWrapMode(QTextEdit.NoWrap)
        self.sendArea.setAcceptRichText(False)
        self.clearReceiveButtion = QPushButton("")
        utils_ui.setButtonIcon(self.clearReceiveButtion, "mdi6.broom")
        self.sendButton = QPushButton("")
        utils_ui.setButtonIcon(self.sendButton, "fa.send")
        self.sendHistory = ComboBox()
        sendWidget = QWidget()
        sendAreaWidgetsLayout = QHBoxLayout()
        sendAreaWidgetsLayout.setContentsMargins(0,4,0,0)
        sendWidget.setLayout(sendAreaWidgetsLayout)
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.clearReceiveButtion)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.sendButton)
        sendAreaWidgetsLayout.addWidget(self.sendArea)
        sendAreaWidgetsLayout.addLayout(buttonLayout)
        self.mainWidget.addWidget(self.receiveArea)
        self.mainWidget.addWidget(sendWidget)
        self.mainWidget.addWidget(self.sendHistory)
        self.mainWidget.setStretchFactor(0, 7)
        self.mainWidget.setStretchFactor(1, 2)
        self.mainWidget.setStretchFactor(2, 1)
        # event
        self.sendButton.clicked.connect(self.onSendData)
        self.clearReceiveButtion.clicked.connect(self.clearReceiveBuffer)
        self.receiveUpdateSignal.connect(self.updateReceivedDataDisplay)
        self.sendHistory.activated.connect(self.onSendHistoryIndexChanged)

        return self.mainWidget

    def onWidgetSettings(self, parent):
        # serial receive settings
        layout = QVBoxLayout()
        serialReceiveSettingsLayout = QGridLayout()
        serialReceiveSettingsGroupBox = QGroupBox(_("Receive Settings"))
        self.receiveSettingsAscii = QRadioButton(_("ASCII"))
        self.receiveSettingsAscii.setToolTip(_("Show recived data as visible format, select decode method at top right corner"))
        self.receiveSettingsHex = QRadioButton(_("HEX"))
        self.receiveSettingsHex.setToolTip(_("Show recived data as hex format"))
        self.receiveSettingsAscii.setChecked(True)
        self.receiveSettingsAutoLinefeed = QCheckBox(_("Auto\nLinefeed\nms"))
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
        serialReceiveSettingsGroupBox.setAlignment(Qt.AlignHCenter)
        layout.addWidget(serialReceiveSettingsGroupBox)

        # serial send settings
        serialSendSettingsLayout = QGridLayout()
        serialSendSettingsGroupBox = QGroupBox(_("Send Settings"))
        self.sendSettingsAscii = QRadioButton(_("ASCII"))
        self.sendSettingsHex = QRadioButton(_("HEX"))
        self.sendSettingsAscii.setToolTip(_("Get send data as visible format, select encoding method at top right corner"))
        self.sendSettingsHex.setToolTip(_("Get send data as hex format, e.g. hex '31 32 33' equal to ascii '123'"))
        self.sendSettingsAscii.setChecked(True)
        self.sendSettingsScheduledCheckBox = QCheckBox(_("Timed Send\nms"))
        self.sendSettingsScheduledCheckBox.setToolTip(_("Timed send, unit: ms"))
        self.sendSettingsScheduled = QLineEdit("300")
        self.sendSettingsScheduled.setProperty("class", "smallInput")
        self.sendSettingsScheduled.setToolTip(_("Timed send, unit: ms"))
        self.sendSettingsScheduledCheckBox.setMaximumWidth(75)
        self.sendSettingsScheduled.setMaximumWidth(75)
        self.sendSettingsCRLF = QCheckBox(_("<CRLF>"))
        self.sendSettingsCRLF.setToolTip(_("Select to send \\r\\n instead of \\n"))
        self.sendSettingsCRLF.setChecked(False)
        self.sendSettingsRecord = QCheckBox(_("Record"))
        self.sendSettingsRecord.setToolTip(_("Record send data"))
        self.sendSettingsEscape= QCheckBox(_("Escape"))
        self.sendSettingsEscape.setToolTip(_("Enable escape characters support like \\t \\r \\n \\x01 \\001"))
        self.sendSettingsAppendNewLine= QCheckBox(_("Newline"))
        self.sendSettingsAppendNewLine.setToolTip(_("Auto add new line when send"))
        serialSendSettingsLayout.addWidget(self.sendSettingsAscii,1,0,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsHex,1,1,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduledCheckBox, 2, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsScheduled, 2, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsCRLF, 3, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsAppendNewLine, 3, 1, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsEscape, 4, 0, 1, 2)
        serialSendSettingsLayout.addWidget(self.sendSettingsEscape, 4, 0, 1, 2)
        serialSendSettingsLayout.addWidget(self.sendSettingsRecord, 4, 1, 1, 1)
        serialSendSettingsGroupBox.setLayout(serialSendSettingsLayout)
        layout.addWidget(serialSendSettingsGroupBox)

        widget = QWidget()
        widget.setLayout(layout)
        layout.setContentsMargins(0,0,0,0)
        # event
        self.receiveSettingsTimestamp.clicked.connect(self.onTimeStampClicked)
        self.receiveSettingsAutoLinefeed.clicked.connect(self.onAutoLinefeedClicked)
        self.receiveSettingsAscii.clicked.connect(lambda : self.bindVar(self.receiveSettingsAscii, self.config, "receiveAscii"))
        self.receiveSettingsHex.clicked.connect(lambda : self.bindVar(self.receiveSettingsHex, self.config, "receiveAscii", invert = True))
        self.sendSettingsHex.clicked.connect(self.onSendSettingsHexClicked)
        self.sendSettingsAscii.clicked.connect(self.onSendSettingsAsciiClicked)
        self.sendSettingsRecord.clicked.connect(self.onRecordSendClicked)
        self.sendSettingsAppendNewLine.clicked.connect(lambda: self.bindVar(self.sendSettingsAppendNewLine, self.config, "sendAutoNewline"))
        self.sendSettingsEscape.clicked.connect(lambda: self.bindVar(self.sendSettingsEscape, self.config, "sendEscape"))
        self.sendSettingsCRLF.clicked.connect(lambda: self.bindVar(self.sendSettingsCRLF, self.config, "useCRLF"))
        self.receiveSettingsColor.clicked.connect(self.onSetColorChanged)
        self.receiveSettingsAutoLinefeedTime.textChanged.connect(lambda: self.bindVar(self.receiveSettingsAutoLinefeedTime, self.config, "receiveAutoLindefeedTime", vtype=int, vErrorMsg=_("Auto line feed value error, must be integer"), emptyDefault = "200"))
        self.sendSettingsScheduled.textChanged.connect(lambda: self.bindVar(self.sendSettingsScheduled, self.config, "sendScheduledTime", vtype=int, vErrorMsg=_("Timed send value error, must be integer"), emptyDefault = "300"))
        self.sendSettingsScheduledCheckBox.clicked.connect(lambda: self.bindVar(self.sendSettingsScheduledCheckBox, self.config, "sendScheduled"))
        return widget


    def onWidgetFunctional(self, parent):
        sendFunctionalLayout = QVBoxLayout()
        sendFunctionalLayout.setContentsMargins(0,0,0,0)
        # right functional layout
        self.filePathWidget = QLineEdit()
        self.openFileButton = QPushButton(_("Open File"))
        self.sendFileButton = QPushButton(_("Send File"))
        self.clearHistoryButton = QPushButton(_("Clear History"))
        self.addButton = QPushButton("")
        utils_ui.setButtonIcon(self.addButton, "fa.plus")
        self.fileSendGroupBox = QGroupBox(_("Sendding File"))
        fileSendGridLayout = QGridLayout()
        fileSendGridLayout.addWidget(self.filePathWidget, 0, 0, 1, 1)
        fileSendGridLayout.addWidget(self.openFileButton, 0, 1, 1, 1)
        fileSendGridLayout.addWidget(self.sendFileButton, 1, 0, 1, 2)
        self.fileSendGroupBox.setLayout(fileSendGridLayout)
        self.logFileGroupBox = QGroupBox(_("Save log"))
        # cumtom send zone
        #   groupbox
        customSendGroupBox = QGroupBox(_("Cutom send"))
        customSendItemsLayout0 = QVBoxLayout()
        customSendItemsLayout0.setContentsMargins(0,8,0,0)
        customSendGroupBox.setLayout(customSendItemsLayout0)
        #   scroll

        self.customSendScroll = QScrollArea()
        self.customSendScroll.setMinimumHeight(parameters.customSendItemHeight + 20)
        self.customSendScroll.setWidgetResizable(True)
        self.customSendScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #   add scroll to groupbox
        customSendItemsLayout0.addWidget(self.customSendScroll)
        #   wrapper widget
        cutomSendItemsWraper = QWidget()
        customSendItemsLayoutWrapper = QVBoxLayout()
        customSendItemsLayoutWrapper.setContentsMargins(0,0,0,0)
        cutomSendItemsWraper.setLayout(customSendItemsLayoutWrapper)
        #    custom items
        customItems = QWidget()
        self.customSendItemsLayout = QVBoxLayout()
        self.customSendItemsLayout.setContentsMargins(0,0,0,0)
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
        self.logFileGroupBox.setLayout(logFileLayout)
        sendFunctionalLayout.addWidget(self.logFileGroupBox)
        sendFunctionalLayout.addWidget(self.fileSendGroupBox)
        sendFunctionalLayout.addWidget(self.clearHistoryButton)
        sendFunctionalLayout.addWidget(customSendGroupBox)
        sendFunctionalLayout.addStretch(1)
        self.funcWidget = QWidget()
        self.funcWidget.setLayout(sendFunctionalLayout)
        # event
        self.sendFileButton.clicked.connect(self.sendFile)
        self.saveLogCheckbox.clicked.connect(self.setSaveLog)
        self.logFileBtn.clicked.connect(self.selectLogFile)
        self.openFileButton.clicked.connect(self.selectFile)
        self.addButton.clicked.connect(self.customSendAdd)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        self.funcParent = parent
        return self.funcWidget

    def onWidgetStatusBar(self, parent):
        self.statusBar = statusBar(rxTxCount=True)
        return self.statusBar

    def onUiInitDone(self):
        paramObj = self.config
        self.receiveSettingsHex.setChecked(not paramObj["receiveAscii"])
        self.receiveSettingsAutoLinefeed.setChecked(paramObj["receiveAutoLinefeed"])
        try:
            interval = int(paramObj["receiveAutoLindefeedTime"])
            paramObj["receiveAutoLindefeedTime"] = interval
        except Exception:
            interval = parameters.Parameters.receiveAutoLindefeedTime
        self.receiveSettingsAutoLinefeedTime.setText(str(interval) if interval > 0 else str(parameters.Parameters.receiveAutoLindefeedTime))
        self.receiveSettingsTimestamp.setChecked(paramObj["showTimestamp"])
        self.sendSettingsHex.setChecked(not paramObj["sendAscii"])
        self.sendSettingsScheduledCheckBox.setChecked(paramObj["sendScheduled"])
        try:
            interval = int(paramObj["sendScheduledTime"])
            paramObj["sendScheduledTime"] = interval
        except Exception:
            interval = parameters.Parameters.sendScheduledTime
        self.sendSettingsScheduled.setText(str(interval) if interval > 0 else str(parameters.Parameters.sendScheduledTime))
        self.sendSettingsCRLF.setChecked(paramObj["useCRLF"])
        self.sendSettingsAppendNewLine.setChecked(paramObj["sendAutoNewline"])
        self.sendSettingsRecord.setChecked(paramObj["recordSend"])
        self.sendSettingsEscape.setChecked(paramObj["sendEscape"])
        for i in range(0, len(paramObj["sendHistoryList"])):
            text = paramObj["sendHistoryList"][i]
            self.sendHistory.addItem(text)
        self.logFilePath.setText(paramObj["saveLogPath"])
        self.logFilePath.setToolTip(paramObj["saveLogPath"])
        self.saveLogCheckbox.setChecked(paramObj["saveLog"])
        self.receiveSettingsColor.setChecked(paramObj["color"])
        # send items
        for text in paramObj["customSendItems"]:
            self.insertSendItem(text, load=True)

        self.receiveProcess = threading.Thread(target=self.receiveDataProcess)
        self.receiveProcess.setDaemon(True)
        self.receiveProcess.start()

    def onSendSettingsHexClicked(self):
        self.config["sendAscii"] = False
        data = self.sendArea.toPlainText().replace("\n","\r\n")
        data = utils.bytes_to_hex_str(data.encode())
        self.sendArea.clear()
        self.sendArea.insertPlainText(data)

    def onSendSettingsAsciiClicked(self):
        self.config["sendAscii"] = True
        try:
            data = self.sendArea.toPlainText().replace("\n"," ").strip()
            self.sendArea.clear()
            if data != "":
                data = utils.hex_str_to_bytes(data).decode(self.configGlobal["encoding"],'ignore')
                self.sendArea.insertPlainText(data)
        except Exception as e:
            # QMessageBox.information(self,self.strings.strWriteFormatError,self.strings.strWriteFormatError)
            print("format error")

    def onAutoLinefeedClicked(self):
        if (self.config["showTimestamp"] or self.config["recordSend"]) and not self.receiveSettingsAutoLinefeed.isChecked():
            self.receiveSettingsAutoLinefeed.setChecked(True)
            self.hintSignal.emit("warning", _("Warning"), _("linefeed always on if timestamp or record send is on"))
        self.config["receiveAutoLinefeed"] = self.receiveSettingsAutoLinefeed.isChecked()

    def onTimeStampClicked(self):
        self.config["showTimestamp"] = self.receiveSettingsTimestamp.isChecked()
        if self.config["showTimestamp"]:
            self.config["receiveAutoLinefeed"] = True
            self.receiveSettingsAutoLinefeed.setChecked(True)

    def onRecordSendClicked(self):
        self.config["recordSend"] = self.sendSettingsRecord.isChecked()
        if self.config["recordSend"]:
            self.config["receiveAutoLinefeed"] = True
            self.receiveSettingsAutoLinefeed.setChecked(True)

    def onEscapeSendClicked(self):
        self.config["sendEscape"] = self.sendSettingsEscape.isChecked()

    def onSetColorChanged(self):
        self.config["color"] = self.receiveSettingsColor.isChecked()

    def onSendHistoryIndexChanged(self, idx):
        self.sendArea.clear()
        self.sendArea.insertPlainText(self.sendHistory.currentText())

    def clearHistory(self):
        self.config["sendHistoryList"].clear()
        self.sendHistory.clear()
        self.hintSignal.emit("info", _("OK"), _("History cleared!"))


    def onSent(self, ok, msg, length, path):
        if ok:
            self.statusBar.addTx(length)
        else:
            self.hintSignal.emit("error", _("Error"), _("Send data failed!") + " " + msg)

    def onSentFile(self, ok, msg, length, path):
        print("file sent {}, path: {}".format('ok' if ok else 'fail', path))
        if ok:
            self.sendFileButton.setText(_("Send file"))
            self.sendFileButton.setDisabled(False)
            self.statusBar.addTx(length)
        else:
            self.hintSignal.emit("error", _("Error"), _("Send file failed!") + " " + msg)

    def setSaveLog(self):
        if self.saveLogCheckbox.isChecked():
            self.config["saveLog"] = True
        else:
            self.config["saveLog"] = False

    def selectFile(self):
        oldPath = self.filePathWidget.text()
        if oldPath=="":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self.mainWidget,
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
        fileName_choose, filetype = QFileDialog.getSaveFileName(self.mainWidget,
                                    _("Select file"),
                                    os.path.join(oldPath, "comtool.log"),
                                    _("Log file (*.log);;txt file (*.txt);;All Files (*)"))

        if fileName_choose == "":
            return
        self.logFilePath.setText(fileName_choose)
        self.logFilePath.setToolTip(fileName_choose)
        self.config["saveLogPath"] = fileName_choose

    def onLog(self, text):
        if self.config["saveLogPath"]:
            with open(self.config["saveLogPath"], "a+", encoding=self.configGlobal["encoding"], newline="\n") as f:
                f.write(text)

    def onKeyPressEvent(self, event):
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

    def onKeyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = False

    def insertSendItem(self, text="", load = False):
        itemsNum = self.customSendItemsLayout.count() + 1
        height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        topHeight = self.fileSendGroupBox.height() + self.logFileGroupBox.height() + 100
        if height + topHeight > self.funcParent.height():
            height = self.funcParent.height() - topHeight
        if height < 0:
            height = self.funcParent.height() // 3
        self.customSendScroll.setMinimumHeight(height)
        item = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        item.setLayout(layout)
        cmd = QLineEdit(text)
        send = QPushButton("")
        utils_ui.setButtonIcon(send, "fa.send")
        cmd.setToolTip(text)
        send.setToolTip(text)
        cmd.textChanged.connect(lambda: self.onCustomItemChange(self.customSendItemsLayout.indexOf(item), cmd, send))
        send.setProperty("class", "smallBtn")
        send.clicked.connect(lambda: self.sendCustomItem(self.config["customSendItems"][self.customSendItemsLayout.indexOf(item)]))
        delete = QPushButton("")
        utils_ui.setButtonIcon(delete, "fa.close")
        delete.setProperty("class", "deleteBtn")
        layout.addWidget(cmd)
        layout.addWidget(send)
        layout.addWidget(delete)
        delete.clicked.connect(lambda: self.deleteSendItem(self.customSendItemsLayout.indexOf(item), item))
        self.customSendItemsLayout.addWidget(item)
        if not load:
            self.config["customSendItems"].append("")

    def deleteSendItem(self, idx, item):
        item.setParent(None)
        self.config["customSendItems"].pop(idx)
        itemsNum = self.customSendItemsLayout.count()
        height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        topHeight = self.fileSendGroupBox.height() + self.logFileGroupBox.height() + 100
        if height + topHeight > self.funcParent.height():
            height = self.funcParent.height() - topHeight
        self.customSendScroll.setMinimumHeight(height)

    def onCustomItemChange(self, idx, edit, send):
        text = edit.text()
        edit.setToolTip(text)
        send.setToolTip(text)
        self.config["customSendItems"][idx] = text

    def sendCustomItem(self, text):
        self.onSendData(data = text)

    def customSendAdd(self):
        self.insertSendItem()

    def getSendData(self, data=None) -> bytes:
        if data is None:
            data = self.sendArea.toPlainText()
        return self.parseSendData(data, self.configGlobal["encoding"], self.config["useCRLF"], not self.config["sendAscii"], self.config["sendEscape"])

    def sendFile(self):
        filename = self.filePathWidget.text()
        if not os.path.exists(filename):
            self.hintSignal.emit("error", _("Error"), _("File path error\npath") + ":%s" %(filename))
            return
        if not self.isConnected():
            self.hintSignal.emit("warning", _("Warning"), _("Connect first please"))
        else:
            self.sendFileButton.setDisabled(True)
            self.sendFileButton.setText(_("Sending file"))
            self.send(file_path=filename, callback = lambda ok, msg, length, path: self.onSentFile(ok, msg, length, path))


    def scheduledSend(self):
        self.isScheduledSending = True
        while self.config["sendScheduled"]:
            self.onSendData()
            try:
                time.sleep(self.config["sendScheduledTime"]/1000)
            except Exception:
                self.hintSignal.emit("error", _("Error"), _("Time format error"))
        self.isScheduledSending = False

    def sendData(self, data_bytes = None):
        try:
            if self.isConnected():
                if not data_bytes or type(data_bytes) == str:
                    data = self.getSendData(data_bytes)
                else:
                    data = data_bytes
                if not data:
                    return
                if self.config["sendAutoNewline"]:
                    data += b"\r\n" if self.config["useCRLF"] else b"\n"
                # record send data
                if self.config["recordSend"]:
                    head = '=> '
                    if self.config["showTimestamp"]:
                        head += '[{}] '.format(utils.datetime_format_ms(datetime.now()))
                    isHexStr, sendStr, sendStrsColored = self.bytes2String(data, not self.config["receiveAscii"], encoding=self.configGlobal["encoding"])
                    if isHexStr:
                        sendStr = sendStr.upper()
                        sendStrsColored= sendStr
                        head += "[HEX] "
                    if self.config["useCRLF"]:
                        head = "\r\n" + head
                    else:
                        head = "\n" + head
                    if head.strip() != '=>':
                        head = '{}: '.format(head.rstrip())
                    self.receiveUpdateSignal.emit(head, [sendStrsColored], self.configGlobal["encoding"])
                    self.sendRecord.insert(0, head + sendStr)
                self.send(data_bytes=data, callback = self.onSent)
                if data_bytes:
                    data = str(data_bytes)
                else:
                    data = self.sendArea.toPlainText()
                self.sendHistoryFindDelete(data)
                self.sendHistory.insertItem(0,data)
                self.sendHistory.setCurrentIndex(0)
                try:
                    idx = self.config["sendHistoryList"].index(data)
                    self.config["sendHistoryList"].pop(idx)
                except Exception:
                     pass
                self.config["sendHistoryList"].insert(0, data)

                # scheduled send
                if self.config["sendScheduled"]:
                    if not self.isScheduledSending:
                        t = threading.Thread(target=self.scheduledSend)
                        t.setDaemon(True)
                        t.start()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("[Error] sendData: ", e)
            self.hintSignal.emit("error", _("Error"), _("Send Error") + str(e))
            # print(e)

    def onSendData(self, call=True, data=None):
        try:
            self.sendData(data)
        except Exception as e:
            print("[Error] onSendData: ", e)
            self.hintSignal.emit("error", _("Error"), _("get data error") + ": " + str(e))

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

    def sendHistoryFindDelete(self,str):
        self.sendHistory.removeItem(self.sendHistory.findText(str))

    def _getColorByfmt(self, fmt:bytes):
        colors = {
            b"0": None,
            b"30": "#000000",
            b"31": "#f44336",
            b"32": "#4caf50",
            b"33": "#ffa000",
            b"34": "#2196f3",
            b"35": "#e85aad",
            b"36": "#26c6da",
            b"37": "#a1887f",
        }
        bgs = {
            b"0": None,
            b"40": "#000000",
            b"41": "#f44336",
            b"42": "#4caf50",
            b"43": "#ffa000",
            b"44": "#2196f3",
            b"45": "#e85aad",
            b"46": "#26c6da",
            b"47": "#a1887f",
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
        remain = b''
        ignoreCodes = [rb'\x1b\[\?.*?h', rb'\x1b\[\?.*?l']
        text = text.replace(b"\x1b[K", b"")
        for code in ignoreCodes:
            colorFmt = re.findall(code, text)
            for fmt in colorFmt:
                text = text.replace(fmt, b"")
        colorFmt = re.findall(rb'\x1b\[.*?m', text)
        if text.endswith(b"\x1b"): # ***\x1b
            text = text[:-1]
            remain = b'\x1b'
        elif text.endswith(b"\x1b["): # ***\x1b[
            text = text[:-2]
            remain = b'\x1b['
        else: # ****\x1b[****, ****\x1b[****;****m
            idx = -2
            idx_remain = -1
            while 1:
                idx = text.find(b"\x1b[", len(text) - 10 + idx + 2) # \x1b[00;00m]
                if idx < 0:
                    break
                remain = text[idx:]
                idx_remain = idx
            if len(remain) > 0:
                match = re.findall(rb'\x1b\[.*?m', remain)  # ****\x1b[****;****m***
                if len(match) > 0: # have full color format
                    remain = b''
                else:
                    text = text[:idx_remain]
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
        return plaintext, colorStrs, remain

    def getColoredText(self, data_bytes, decoding=None):
        plainText, coloredText, remain = self._texSplitByColor(data_bytes)
        if decoding:
            plainText = plainText.decode(encoding=decoding, errors="ignore")
            decodedColoredText = []
            for color, bg, text in coloredText:
                decodedColoredText.append([color, bg, text.decode(encoding=decoding, errors="ignore")])
            coloredText = decodedColoredText
        return plainText, coloredText, remain

    def bytes2String(self, data : bytes, showAsHex : bool, encoding="utf-8"):
        isHexString = False
        dataColored = None
        if showAsHex:
            return True, utils.hexlify(data, ' ').decode(encoding=encoding), dataColored
        try:
            dataPlain, dataColore, remain = self.getColoredText(data, self.configGlobal["encoding"])
            if remain:
                dataPlain += remain.decode(encoding=self.configGlobal["encoding"], errors="ignore")
        except Exception:
            dataPlain = utils.hexlify(data, ' ').decode(encoding=encoding)
            isHexString = True
        return isHexString, dataPlain, dataColored

    def clearReceiveBuffer(self):
        self.receiveArea.clear()
        self.statusBar.clear()

    def onReceived(self, data : bytes):
        self.receivedData.append(data)
        self.statusBar.addRx(len(data))
        self.lock.release()

    def receiveDataProcess(self):
        self.receiveProgressStop = False
        timeLastReceive = 0
        new_line = True
        logData = None
        buffer = b''
        remain = b''
        while(not self.receiveProgressStop):
            logData = None
            head = ""
            self.lock.acquire()
            new = b"".join(self.receivedData)
            buffer += new
            self.receivedData = []
            # timeout, add new line
            if time.time() - timeLastReceive> self.config["receiveAutoLindefeedTime"]:
                if self.config["showTimestamp"] or self.config["receiveAutoLinefeed"]:
                    if self.config["useCRLF"]:
                        head += "\r\n"
                    else:
                        head += "\n"
                    new_line = True
            data = ""
            # have data in buffer
            if len(buffer) > 0:
                hexstr = False
                # show as hex, just show
                if not self.config["receiveAscii"]:
                    data = utils.bytes_to_hex_str(buffer)
                    colorData = data
                    buffer = b''
                    hexstr = True
                # show as string, and don't need to render color
                elif not self.config["color"]:
                    data = buffer.decode(encoding=self.configGlobal["encoding"], errors="ignore")
                    colorData = data
                    buffer = b''
                # show as string, and need to render color, wait for \n or until timeout to ensure color flag in buffer
                else:
                    if time.time() - timeLastReceive >  self.config["receiveAutoLindefeedTime"] or b'\n' in buffer:
                        data, colorData, remain = self.getColoredText(buffer, self.configGlobal["encoding"])
                        buffer = remain
                # add time receive head
                # get data from buffer, now render
                if data:
                    # add time header, head format(send receive '123' for example):
                    # '123'  '[2021-12-20 11:02:08.02.754]: 123' '=> 12' '<= 123'
                    # '=> [2021-12-20 11:02:34.02.291]: 123' '<= [2021-12-20 11:02:40.02.783]: 123'
                    # '<= [2021-12-20 11:03:25.03.320] [HEX]: 31 32 33 ' '=> [2021-12-20 11:03:27.03.319] [HEX]: 31 32 33'
                    if new_line:
                        timeNow = '[{}] '.format(utils.datetime_format_ms(datetime.now()))
                        if self.config["recordSend"]:
                            head += "<= "
                        if self.config["showTimestamp"]:
                            head += timeNow
                            head = '{} '.format(head.rstrip())
                        if hexstr:
                            head += "[HEX] "
                        if (self.config["recordSend"] or self.config["showTimestamp"]) and not head.endswith("<= "):
                            head = head[:-1] + ": "
                        new_line = False
                    self.receiveUpdateSignal.emit(head, [colorData], self.configGlobal["encoding"])
                    logData = head + data
            if len(new) > 0:
                timeLastReceive = time.time()

            while len(self.sendRecord) > 0:
                self.onLog(self.sendRecord.pop())
            if logData:
                self.onLog(logData)

