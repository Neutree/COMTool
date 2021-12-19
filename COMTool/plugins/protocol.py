
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QPlainTextEdit)
try:
    import parameters
    from Combobox import ComboBox
    from i18n import _
except ImportError:
    from COMTool import parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox

try:
    from base import Plugin_Base
except Exception:
    from .base import Plugin_Base

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
            "customSendItems": []
        }
        self.config = config
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]

    def onWidgetMain(self, parent, rootWindow):
        self.mainWidget = QSplitter(Qt.Vertical)
        self.receiveWidget = QTextEdit()
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
        self.mainWidget.addWidget(cutomSendItemsWraper0)
        self.mainWidget.setStretchFactor(0, 1)
        self.mainWidget.setStretchFactor(1, 8)
        # event
        self.addButton.clicked.connect(lambda : self.insertSendItem())
        return self.mainWidget

    def onWidgetSettings(self, parent):
        setingGroup = QGroupBox(_("En-decoding Settings"))
        layout = QVBoxLayout()
        setingGroup.setLayout(layout)
        default = ComboBox()
        decoding = QPlainTextEdit()
        encoding = QPlainTextEdit()
        save = QPushButton(_("Save"))
        layout.addWidget(default)
        layout.addWidget(decoding)
        layout.addWidget(encoding)
        layout.addWidget(save)
        return setingGroup

    def onWidgetFunctional(self, parent):
        self.funcParent = parent
        self.funcWidget = QWidget()
        layout = QVBoxLayout()
        self.funcWidget.setLayout(layout)
        return self.funcWidget

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
        itemsNum = self.customSendItemsLayout.count()
        height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        topHeight = self.receiveWidget.height() + 100
        if height + topHeight > self.funcParent.height():
            height = self.funcParent.height() - topHeight
        self.customSendScroll.setMinimumHeight(height)

    def onReceived(self, data : bytes):
        for id in self.connChilds:
            self.plugins_info[id].onReceived(data)

    def onKeyPressEvent(self, event):
        pass

    def onKeyReleaseEvent(self, event):
        pass

    def getConfig(self):
        '''
            get config, dict type
            this method runs in UI thread, do not block too long
        '''
        return {}

    def onUiInitDone(self):
        '''
            UI init done, you can update your widget here
            this method runs in UI thread, do not block too long
        '''
        for text in self.config["customSendItems"]:
            self.insertSendItem(text, load=True)

    def sendData(self, data_bytes=None):
        self.send(data_bytes)

    def sendCustomItem(self, text):
        # text = text.encode(encoding=self.configGlobal["encoding"])
        self.sendData(data_bytes = text)

    def onCustomItemChange(self, idx, edit, send):
        text = edit.text()
        edit.setToolTip(text)
        send.setToolTip(text)
        self.config["customSendItems"][idx] = text

    def bindVar(self, uiObj, varObj, varName: str, vtype=None, vErrorMsg="", checkVar=lambda v:v, invert = False):
        objType = type(uiObj)
        if objType == QCheckBox:
            v = uiObj.isChecked()
            varObj[varName] = v if not invert else not v
            return
        elif objType == QLineEdit:
            v = uiObj.text()
        elif objType == ComboBox:
            varObj[varName] = uiObj.currentText()
            return
        elif objType == QRadioButton:
            v = uiObj.isChecked()
            varObj[varName] = v if not invert else not v
            return
        else:
            raise Exception("not support this object")
        if vtype:
            try:
                v = vtype(v)
            except Exception:
                uiObj.setText(str(varObj[varName]))
                self.hintSignal.emit("error", _("Error"), vErrorMsg)
                return
        try:
            v = checkVar(v)
        except Exception as e:
            self.hintSignal.emit("error", _("Error"), str(e))
            return
        varObj[varName] = v


