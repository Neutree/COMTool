
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor, QFontMetricsF

try:
    import parameters
    from Combobox import ComboBox
    from i18n import _
    from widgets import TextEdit, PlainTextEdit
except ImportError:
    from COMTool import parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox
    from COMTool.widgets import TextEdit, PlainTextEdit

try:
    from base import Plugin_Base
except Exception:
    from .base import Plugin_Base

defaultCodes = {
    "default":
'''
def decode(data):
    return data

def encode(data):
    return data
''',

    "maix-mm": 
'''
def decode(data):
    data += b'123'
    return data

def encode(data):
    data += b'123'
    return data
'''
}


class Plugin(Plugin_Base):
    '''
        call sequence:
            set vars like hintSignal, hintSignal
            onInit
            onWidget
            onUiInitDone
                send
                onReceived
            getConfig
    '''
    # vars set by caller
    isConnected = lambda : False
    send = lambda x,y:None          # send(data_bytes=None, file_path=None, callback=lambda ok,msg:None)
    hintSignal = None               # hintSignal.emit(type(error, warning, info), title, msg)
    clearCountSignal = None         # clearCountSignal.emit()
    configGlobal = {}
    # other vars
    connParent = "dbg"       # parent id
    connChilds = []          # children ids
    id = "protocol"
    name = _("protocol")

    enabled = False          # user enabled this plugin
    active  = False          # using this plugin

    showReceiveDataSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        if not self.id:
            raise ValueError(f"var id of Plugin {self} should be set")

    def onInit(self, config, plugins):
        '''
            init params, DO NOT take too long time in this func
        '''
        self.plugins = plugins
        self.plugins_info = {}
        for p in self.plugins:
            if p.id in self.connChilds:
                self.plugins_info[p.id] = p
        default = {
            "sendAscii" : True,
            "useCRLF" : True,
            "sendEscape" : False,
            "code": defaultCodes.copy(),
            "currCode": "default",
            "customSendItems": []
        }
        self.config = config
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.editingDefaults = False
        self.codeGlobals = {}
        self.encodeMethod = lambda x:x
        self.decodeMethod = lambda x:x

    def onWidgetMain(self, parent, rootWindow):
        self.mainWidget = QSplitter(Qt.Vertical)
        self.receiveWidget = TextEdit()
        font = QFont('Menlo,Consolas,Bitstream Vera Sans Mono,Courier New,monospace, Microsoft YaHei', 10)
        self.receiveWidget.setFont(font)
        self.receiveWidget.setLineWrapMode(TextEdit.NoWrap)
        self.clearBtn = QPushButton(_("Clear"))
        self.addButton = QPushButton(_("+"))
        self.customSendScroll = QScrollArea()
        self.customSendScroll.setMinimumHeight(parameters.customSendItemHeight + 20)
        self.customSendScroll.setWidgetResizable(True)
        self.customSendScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.customSendScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cutomSendItemsWraper = QWidget()
        self.customSendScroll.setWidget(cutomSendItemsWraper)
        #   wrapper widget
        cutomSendItemsWraper0 = QWidget()
        layout0 = QVBoxLayout()
        layout0.setContentsMargins(0,8,0,0)
        cutomSendItemsWraper0.setLayout(layout0)
        layout0.addWidget(self.customSendScroll)
        customSendItemsLayoutWrapper = QVBoxLayout()
        customSendItemsLayoutWrapper.setContentsMargins(0,0,0,0)
        cutomSendItemsWraper.setLayout(customSendItemsLayoutWrapper)
        # items container
        customItems = QWidget()
        self.customSendItemsLayout = QVBoxLayout()
        self.customSendItemsLayout.setContentsMargins(0,0,0,0)
        customItems.setLayout(self.customSendItemsLayout)

        customSendItemsLayoutWrapper.addWidget(customItems)
        customSendItemsLayoutWrapper.addWidget(self.addButton)
        customSendItemsLayoutWrapper.addStretch(0)

        self.mainWidget.addWidget(self.receiveWidget)
        self.mainWidget.addWidget(self.clearBtn)
        self.mainWidget.addWidget(cutomSendItemsWraper0)
        self.mainWidget.setStretchFactor(0, 2)
        self.mainWidget.setStretchFactor(1, 1)
        self.mainWidget.setStretchFactor(2, 11)
        # event
        self.addButton.clicked.connect(lambda : self.insertSendItem())
        def clearReceived():
            self.receiveWidget.clear();self.clearCountSignal.emit()
        self.clearBtn.clicked.connect(clearReceived)
        return self.mainWidget

    def onWidgetSettings(self, parent):
        root = QWidget()
        rootLayout = QVBoxLayout()
        rootLayout.setContentsMargins(0,0,0,0)
        root.setLayout(rootLayout)
        setingGroup = QGroupBox(_("En-decoding settings"))
        layout = QGridLayout()
        setingGroup.setLayout(layout)
        self.codeItems = ComboBox()
        self.codeItemCustomStr = _("Custom, input name")
        self.codeItemLoadDefaultsStr = _("Load defaults")
        self.codeItems.setEditable(True)
        self.codeWidget = PlainTextEdit()
        self.saveCodeBtn = QPushButton(_("Save"))
        self.deleteCodeBtn = QPushButton(_("Delete"))
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.saveCodeBtn)
        btnLayout.addWidget(self.deleteCodeBtn)
        layout.addWidget(QLabel(_("Defaults")),0,0,1,1)
        layout.addWidget(self.codeItems,0,1,1,1)
        layout.addWidget(QLabel(_("Code")),1,0,1,1)
        layout.addWidget(self.codeWidget,1,1,1,1)
        layout.addLayout(btnLayout,2,1,1,1)
        serialSendSettingsLayout = QGridLayout()
        sendGroup = QGroupBox(_("Send settings"))
        sendGroup.setLayout(serialSendSettingsLayout)
        self.sendSettingsAscii = QRadioButton(_("ASCII"))
        self.sendSettingsHex = QRadioButton(_("HEX"))
        self.sendSettingsAscii.setToolTip(_("Get send data as visible format, select encoding method at top right corner"))
        self.sendSettingsHex.setToolTip(_("Get send data as hex format, e.g. hex '31 32 33' equal to ascii '123'"))
        self.sendSettingsAscii.setChecked(True)
        self.sendSettingsCRLF = QCheckBox(_("<CRLF>"))
        self.sendSettingsCRLF.setToolTip(_("Select to send \\r\\n instead of \\n"))
        self.sendSettingsCRLF.setChecked(False)
        self.sendSettingsEscape= QCheckBox(_("Escape"))
        self.sendSettingsEscape.setToolTip(_("Enable escape characters support like \\t \\r \\n \\x01 \\001"))
        serialSendSettingsLayout.addWidget(self.sendSettingsAscii,0,0,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsHex,0,1,1,1)
        serialSendSettingsLayout.addWidget(self.sendSettingsCRLF, 1, 0, 1, 1)
        serialSendSettingsLayout.addWidget(self.sendSettingsEscape, 1, 1, 1, 1)

        rootLayout.addWidget(sendGroup)
        rootLayout.addWidget(setingGroup)
        # event
        self.sendSettingsAscii.clicked.connect(lambda : self.bindVar(self.sendSettingsAscii, self.config, "sendAscii", bool))
        self.sendSettingsHex.clicked.connect(lambda : self.bindVar(self.sendSettingsHex, self.config, "sendAscii", bool, invert=True))
        self.sendSettingsCRLF.clicked.connect(lambda : self.bindVar(self.sendSettingsCRLF, self.config, "useCRLF", bool))
        self.sendSettingsEscape.clicked.connect(lambda : self.bindVar(self.sendSettingsEscape, self.config, "sendEscape", bool))
        self.saveCodeBtn.clicked.connect(self.saveCode)
        self.deleteCodeBtn.clicked.connect(self.deleteCode)
        return root

    def onWidgetFunctional(self, parent):
        self.funcParent = parent
        self.funcWidget = QWidget()
        layout = QVBoxLayout()
        self.funcWidget.setLayout(layout)
        return self.funcWidget

    def onUiInitDone(self):
        '''
            UI init done, you can update your widget here
            this method runs in UI thread, do not block too long
        '''
        for text in self.config["customSendItems"]:
            self.insertSendItem(text, load=True)
        self.sendSettingsAscii.setChecked(self.config["sendAscii"])
        self.sendSettingsHex.setChecked(not self.config["sendAscii"])
        self.sendSettingsCRLF.setChecked(self.config["useCRLF"])
        self.sendSettingsEscape.setChecked(self.config["sendEscape"])
        self.showReceiveDataSignal.connect(self.showReceivedData)
        # init decoder and encoder
        for k in self.config["code"]:
            self.codeItems.addItem(k)
        self.codeItems.addItem(self.codeItemCustomStr)
        self.codeItems.addItem(self.codeItemLoadDefaultsStr)
        name = self.config["currCode"]
        idx = self.codeItems.findText(self.config["currCode"])
        if idx < 0:
            idx = 0
            name = "default"
        self.codeItems.setCurrentIndex(idx)
        self.selectCode(name)
        self.codeItems.currentIndexChanged.connect(self.onCodeItemChanged) # add here to avoid self.selectCode trigger

    def onKeyPressEvent(self, event):
        pass

    def onKeyReleaseEvent(self, event):
        pass

    def insertSendItem(self, text="", load = False):
        # itemsNum = self.customSendItemsLayout.count() + 1
        # height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        # topHeight = self.receiveWidget.height() + 100
        # if height + topHeight > self.funcParent.height():
        #     height = self.funcParent.height() - topHeight
        # if height < 0:
        #     height = self.funcParent.height() // 3
        # self.customSendScroll.setMinimumHeight(height)
        item = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        item.setLayout(layout)
        cmd = QLineEdit(text)
        send = QPushButton(_("Send"))
        cmd.setToolTip(text)
        send.setToolTip(text)
        cmd.textChanged.connect(lambda: self.onCustomItemChange(self.customSendItemsLayout.indexOf(item), cmd, send))
        send.setProperty("class", "smallBtn")
        send.clicked.connect(lambda: self.sendCustomItem(self.config["customSendItems"][self.customSendItemsLayout.indexOf(item)]))
        delete = QPushButton("x")
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
        # itemsNum = self.customSendItemsLayout.count()
        # height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        # topHeight = self.receiveWidget.height() + 100
        # if height + topHeight > self.funcParent.height():
        #     height = self.funcParent.height() - topHeight
        # self.customSendScroll.setMinimumHeight(height)

    def showReceivedData(self, text: str):
            curScrollValue = self.receiveWidget.verticalScrollBar().value()
            self.receiveWidget.moveCursor(QTextCursor.End)
            endScrollValue = self.receiveWidget.verticalScrollBar().value()
            self.receiveWidget.insertPlainText(text)
            if curScrollValue < endScrollValue:
                self.receiveWidget.verticalScrollBar().setValue(curScrollValue)
            else:
                self.receiveWidget.moveCursor(QTextCursor.End)

    def onReceived(self, data : bytes):
        data = self.encodeMethod(data)
        for id in self.connChilds:
            self.plugins_info[id].onReceived(data)
        text = self.decodeReceivedData(data, self.configGlobal["encoding"], not self.config["sendAscii"], False)
        self.showReceiveDataSignal.emit(text)

    def sendData(self, data_bytes=None):
        data_bytes = self.encodeMethod(data_bytes)
        self.send(data_bytes)

    def sendCustomItem(self, text):
        dateBytes = self.parseSendData(text, self.configGlobal["encoding"], self.config["useCRLF"], not self.config["sendAscii"], self.config["sendEscape"])
        self.sendData(data_bytes = dateBytes)

    def onCustomItemChange(self, idx, edit, send):
        text = edit.text()
        edit.setToolTip(text)
        send.setToolTip(text)
        self.config["customSendItems"][idx] = text

    def onCodeItemChanged(self):
        if self.editingDefaults:
            return
        self.editingDefaults = True
        if self.codeItems.currentText() == self.codeItemCustomStr:
            self.codeItems.clearEditText()
            self.editingDefaults = False
            return
        if self.codeItems.currentText() == self.codeItemLoadDefaultsStr:
            for name in defaultCodes:
                idx = self.codeItems.findText(name)
                if idx >= 0:
                    self.codeItems.removeItem(idx)
                print(self.codeItems.count(), self.codeItems.count() - 2)
                self.codeItems.insertItem(self.codeItems.count() - 2, name)
                self.config["code"][name] = defaultCodes[name]
            self.codeItems.setCurrentIndex(0)
            self.selectCode(self.codeItems.currentText())
            self.editingDefaults = False
            return
        # update code from defaults
        self.selectCode(self.codeItems.currentText())
        self.editingDefaults = False

    def selectCode(self, name):
        if name in [self.codeItemCustomStr, self.codeItemLoadDefaultsStr] or not name or not name in self.config["code"]:
            print(f"name {name} invalid")
            return
        self.config["currCode"] = name
        self.codeWidget.clear()
        self.codeWidget.insertPlainText(self.config["code"][name])
        ok, e, d = self.getEnDecodeMethod(self.codeWidget.toPlainText())
        if ok:
            self.encodeMethod = e
            self.decodeMethod = d

    def getEnDecodeMethod(self, code):
        func = lambda x:x
        try:
            exec(code, self.codeGlobals)
            if (not "decode" in self.codeGlobals) or not "encode" in self.codeGlobals:
                raise ValueError(_("decode and encode method should be in code"))
            return True, self.codeGlobals["encode"], self.codeGlobals["decode"]
        except Exception as e:
            msg = _("Method error") + "\n" + str(e)
            self.hintSignal.emit("error", _("Error"), msg)
        return False, func, func

    def saveCode(self):
        self.editingDefaults = True
        name = self.codeItems.currentText()
        if name in [self.codeItemCustomStr, self.codeItemLoadDefaultsStr] or not name:
            self.hintSignal.emit("warning", _("Warning"), _("Please input code profile name first"))
            self.editingDefaults = False
            return
        idx = self.codeItems.findText(name)
        if idx < 0:
            self.codeItems.insertItem(self.codeItems.count() - 2, name)
        self.editingDefaults = False
        code = self.codeWidget.toPlainText()
        ok, e, d= self.getEnDecodeMethod(code)
        if ok:
            self.encodeMethod = e
            self.decodeMethod = d
            self.config["code"][name] = code
        
    def deleteCode(self):
        self.editingDefaults = True
        name = self.codeItems.currentText()
        itemsConfig = [self.codeItemCustomStr, self.codeItemLoadDefaultsStr]
        # QMessageBox.infomation()
        if name in itemsConfig or not name:
            self.hintSignal.emit("warning", _("Warning"), _("Please select a code profile name first to delte"))
            self.editingDefaults = False
            return
        idx = self.codeItems.findText(name)
        if idx < 0:
            self.editingDefaults = False
            return
        self.codeItems.removeItem(idx)
        self.config["code"].pop(name)
        name = list(self.config["code"].keys())
        if len(name) > 0:
            name = name[0]
            self.codeItems.setCurrentText(name)
            self.selectCode(name)
        self.editingDefaults = False

