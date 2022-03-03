
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QInputDialog, QDialog)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor, QFontMetricsF, QKeySequence, QFocusEvent
import qtawesome as qta # https://github.com/spyder-ide/qtawesome

try:
    import parameters
    from Combobox import ComboBox
    from i18n import _
    from widgets import TextEdit, PlainTextEdit
    import utils_ui
    from qta_icon_browser import selectIcon
except ImportError:
    from COMTool import parameters, utils_ui
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox
    from COMTool.widgets import TextEdit, PlainTextEdit
    from COMTool.qta_icon_browser import selectIcon

try:
    from base import Plugin_Base
    import crc
    from protocols import defaultProtocols
except Exception:
    from .base import Plugin_Base
    from . import crc
    from .protocols import defaultProtocols

import os, json, time
from struct import unpack, pack

class EditRemarDialog(QDialog):
    def __init__(self, remark = "", icon=None, shortcut = []) -> None:
        super().__init__()
        self.remark = remark
        self.icon = icon
        self.ok = False
        self.settingShortcut = False
        self.shortcut = shortcut

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(_("Input remark")), 0, 0, 1, 1)
        self.remarkInput = QLineEdit(self.remark)
        self.iconBtn = QPushButton(self.remark)
        if self.icon:
            self.iconBtn.setIcon(qta.icon(self.icon, color="white"))
        if self.shortcut:
            name = "+".join([str(name) for v,name in self.shortcut])
        else:
            name = _("Record")
        self.shortcutBtn = QPushButton(name)
        self.shortcutBtn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.remarkInput, 0, 1, 1, 1)
        layout.addWidget(QLabel(_("Select icon")), 1, 0, 1, 1)
        layout.addWidget(self.iconBtn, 1, 1, 1, 1)
        layout.addWidget(QLabel(_("Shortcut")), 2, 0, 1, 1)
        layout.addWidget(self.shortcutBtn, 2, 1, 1, 1)
        self.shortcutHint = QLabel(_("Press key to record, or click Cancel"))
        self.shortcutHint.hide()
        layout.addWidget(self.shortcutHint, 3, 0, 1, 2)
        self.okBtn = QPushButton(_("OK"))
        self.cancelBtn = QPushButton(_("Cancel"))
        layout.addWidget(self.okBtn, 4, 0, 1, 1)
        layout.addWidget(self.cancelBtn, 4, 1, 1, 1)

        def ok():
            self.ok = True
            self.close()
        self.okBtn.clicked.connect(lambda : ok())
        self.cancelBtn.clicked.connect(lambda : self.close())
        def updateRemark(text):
            self.remark = text
            self.iconBtn.setText(self.remark)
        self.remarkInput.textChanged.connect(updateRemark)
        self.iconBtn.clicked.connect(lambda: self.selectIcon())
        self.shortcutBtn.clicked.connect(self.setShortcut)

    def selectIcon(self):
        self.icon = selectIcon(parent = self, title = _("Select icon"), btnName = _("OK"), color = utils_ui.getStyleVar("iconSelectorColor"))
        if self.icon:
            self.iconBtn.setIcon(qta.icon(self.icon, color="white"))
        else:
            self.iconBtn.setIcon(QIcon())

    def exec(self):
        super().exec()
        return self.ok, self.remark, self.icon, self.shortcut

    def setShortcut(self):
        if not self.settingShortcut:
            self.onRecordShortcut()
        else:
            self.onRecordShortcutEnd()

    def onRecordShortcut(self):
        self.shortcut = []
        self.remarkInput.setEnabled(False)
        self.iconBtn.setEnabled(False)
        self.okBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)
        self.shortcutBtn.setText(_("Cancel"))
        self.shortcutHint.show()
        self.settingShortcut = True
        self.shortcutBtn.setProperty("class", "deleteBtn")
        self.updateStyle(self.shortcutBtn)

    def onRecordShortcutEnd(self, setOk=False):
        self.remarkInput.setEnabled(True)
        self.iconBtn.setEnabled(True)
        self.okBtn.setEnabled(True)
        self.cancelBtn.setEnabled(True)
        if not setOk:
            self.shortcutBtn.setText(_("Record"))
            self.shortcut = []
        self.shortcutHint.hide()
        self.settingShortcut = False
        self.shortcutBtn.setProperty("class", "")
        self.updateStyle(self.shortcutBtn)

    def keyPressEvent(self, event):
        if not self.settingShortcut:
            return
        key = event.key()
        name = QKeySequence(key).toString()
        if key == Qt.Key_Control:
            name = "Ctrl"
        elif key == Qt.Key_Shift:
            name = "Shift"
        elif key == Qt.Key_Alt:
            name = "Alt"
        elif key == Qt.Key_Super_L:
            name = "Super_L"
        elif key == Qt.Key_Super_R:
            name = "Super_R"
        self.shortcut.append((key, name))
        keys = "+".join([str(name) for v,name in self.shortcut])
        self.shortcutBtn.setText(keys)

    def keyReleaseEvent(self,event):
        if not self.settingShortcut:
            return
        self.onRecordShortcutEnd(setOk = True)

    def updateStyle(self, widget):
        self.style().unpolish(widget)
        self.style().polish(widget)
        self.update()


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
            "useCRLF" : False,
            "sendEscape" : True,
            "code": defaultProtocols.copy(),
            "currCode": "default",
            "customSendItems": [
                {
                    "text": "hello",
                    "remark": "hello",
                    "icon": "fa5.hand-paper"
                },{
                    "text": "\\x01\\x03\\x03\\x03\\x03\\x01",
                    "remark": "pre",
                    "icon": "ei.arrow-left",
                    "shortcut": [[16777234, "Left"]]
                },{
                    "text": "\\x01\\x04\\x04\\x04\\x04\\x01",
                    "remark": "next",
                    "icon": "ei.arrow-right",
                    "shortcut": [[16777236, "Right"]]
                },{
                    "text": "\\x01\\x01\\x01\\x01\\x01\\x01",
                    "remark": "ok",
                    "icon": "fa.circle-o",
                    "shortcut": [[16777220, "Return"]]
                },{
                    "text": "\\x01\\x02\\x02\\x02\\x02\\x01",
                    "remark": "ret",
                    "icon": "ei.return-key",
                    "shortcut": [[16777216, "Esc"]]
                }
            ]
        }
        self.config = config
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.editingDefaults = False
        self.codeGlobals = {"unpack": unpack, "pack": pack, "crc": crc, "encoding": self.configGlobal["encoding"], "print": self.print}
        self.encodeMethod = lambda x:x
        self.decodeMethod = lambda x:x
        self.pressedKeys = []
        self.keyModeClickTime = 0

    def print(self, *args, **kw_args):
        end = "\n"
        start = "[MSG]: "
        if "end" in kw_args:
            end = kw_args["end"]
        if "start" in kw_args:
            start = kw_args["start"]
        string = start  + " ".join(map(str, args)) + end
        self.showReceiveDataSignal.emit(string)


    class ModeButton(QPushButton):
        onFocusIn = pyqtSignal(QFocusEvent)
        onFocusOut = pyqtSignal(QFocusEvent)

        def __init__(self, text, eventFilter, parent = None) -> None:
            super().__init__(text, parent)
            self.installEventFilter(eventFilter)

        def focusInEvent(self, event):
            self.onFocusIn.emit(event)

        def focusOutEvent(self, event):
            self.onFocusOut.emit(event)

    def onWidgetMain(self, parent, rootWindow):
        self.mainWidget = QSplitter(Qt.Vertical)
        self.receiveWidget = TextEdit()
        font = QFont('Menlo,Consolas,Bitstream Vera Sans Mono,Courier New,monospace, Microsoft YaHei', 10)
        self.receiveWidget.setFont(font)
        self.receiveWidget.setLineWrapMode(TextEdit.NoWrap)
        self.clearBtn = QPushButton("")
        self.keyBtneventFilter = self.ModeButtonEventFilter(self.onModeBtnKeyPressEvent, self.onModeBtnKeyReleaseEvent)
        self.keyModeBtn = self.ModeButton(_("Key mode"), self.keyBtneventFilter)
        layoutClearMode = QHBoxLayout()
        layoutClearMode.addWidget(self.clearBtn)
        layoutClearMode.addWidget(self.keyModeBtn)
        clearModeWidget = QWidget()
        clearModeWidget.setLayout(layoutClearMode)
        utils_ui.setButtonIcon(self.clearBtn, "mdi6.broom")
        self.addButton = QPushButton("")
        utils_ui.setButtonIcon(self.addButton, "fa.plus")
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
        self.customItems = QWidget()
        self.customSendItemsLayout = QVBoxLayout()
        self.customSendItemsLayout.setContentsMargins(0,0,0,0)
        self.customItems.setLayout(self.customSendItemsLayout)

        customSendItemsLayoutWrapper.addWidget(self.customItems)
        customSendItemsLayoutWrapper.addWidget(self.addButton)
        customSendItemsLayoutWrapper.addStretch(0)

        self.mainWidget.addWidget(self.receiveWidget)
        self.mainWidget.addWidget(clearModeWidget)
        self.mainWidget.addWidget(cutomSendItemsWraper0)
        self.mainWidget.setStretchFactor(0, 2)
        self.mainWidget.setStretchFactor(1, 1)
        self.mainWidget.setStretchFactor(2, 11)
        # event
        self.addButton.clicked.connect(lambda : self.insertSendItem())
        def clearReceived():
            self.receiveWidget.clear();self.clearCountSignal.emit()
        self.clearBtn.clicked.connect(clearReceived)
        def keyModeOn(event):
            self.keyModeBtn.setProperty("class", "deleteBtn")
            utils_ui.updateStyle(self.mainWidget, self.keyModeBtn)
            self.keyModeClickTime = time.time()
            # show all shortcut
            widgets = self.customItems.findChildren(QPushButton, "editRemark")
            for i, w in enumerate(widgets):
                shortcut = "+".join((name for v, name in self.config["customSendItems"][i]["shortcut"]))
                w.setText(shortcut)
                utils_ui.updateStyle(self.mainWidget, w)

        def keyModeOff(event):
            self.keyModeBtn.setProperty("class", "")
            utils_ui.updateStyle(self.mainWidget, self.keyModeBtn)
            self.keyModeClickTime = 0
            # hide all shortcut
            widgets = self.customItems.findChildren(QPushButton, "editRemark")
            for w in widgets:
                w.setText("")

        def keyModeTuggle():
            if self.keyModeBtn.property("class") == "deleteBtn":
                if time.time() - self.keyModeClickTime < 0.2:
                    return
                else:
                    self.keyModeBtn.clearFocus()

        self.keyModeBtn.onFocusIn.connect(keyModeOn)
        self.keyModeBtn.onFocusOut.connect(keyModeOff)
        self.keyModeBtn.clicked.connect(keyModeTuggle)
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
        self.saveCodeBtn.setEnabled(False)
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
        self.codeWidget.onSave = self.saveCode
        return root

    def onWidgetFunctional(self, parent):
        self.funcParent = parent
        self.funcWidget = QWidget()
        layout0 = QVBoxLayout()
        loadConfigBtn = QPushButton(_("Load config"))
        shareConfigBtn = QPushButton(_("Share config"))
        layout0.addWidget(loadConfigBtn)
        layout0.addWidget(shareConfigBtn)
        layout0.addStretch()
        self.funcWidget.setLayout(layout0)
        # event
        def selectSharefile():
            oldPath = os.getcwd()
            fileName_choose, filetype = QFileDialog.getSaveFileName(self.funcWidget,
                                _("Select file"),
                                os.path.join(oldPath, "comtool.protocol.json"),
                                _("json file (*.json);;config file (*.conf);;All Files (*)"))
            if fileName_choose != "":
                with open(fileName_choose, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)

        def selectLoadfile():
            oldPath = os.getcwd()
            fileName_choose, filetype = QFileDialog.getOpenFileName(self.funcWidget,
                                    _("Select file"),
                                    oldPath,
                                    _("json file (*.json);;config file (*.conf);;All Files (*)"))
            if fileName_choose != "":
                with open(fileName_choose, "r", encoding="utf-8") as f:
                    config = json.load( f)
                    self.oldConfig = self.config.copy()
                    self.config.clear()
                    if "plugins" in config and self.id in config["plugins"]: # global config file
                        config = config["plugins"][self.id]
                    if (not "plugin_id" in config) or not config["plugin_id"] == self.id:
                        self.hintSignal.emit("error", _("Error"), _("config file format error"))
                        return
                    for k in config:
                        self.config[k] = config[k]
                    def onClose(ok):
                        if not ok:
                            self.config.clear()
                            self.config.update(self.oldConfig)
                    self.reloadWindowSignal.emit("", _("Restart to load config?"), onClose)


        loadConfigBtn.clicked.connect(lambda : selectLoadfile())
        shareConfigBtn.clicked.connect(lambda : selectSharefile())
        return self.funcWidget

    def onUiInitDone(self):
        '''
            UI init done, you can update your widget here
            this method runs in UI thread, do not block too long
        '''
        newItems = []
        for item in self.config["customSendItems"]:
            item = self.insertSendItem(item, load=True)
            newItems.append(item)
        self.config["customSendItems"] = newItems
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
        self.codeWidget.textChanged.connect(self.onCodeChanged)

    class ModeButtonEventFilter(QObject):
        def __init__(self, keyPressCb, keyReleaseCb) -> None:
            super().__init__()
            self.keyPressCb = keyPressCb
            self.keyReleaseCb = keyReleaseCb

        def eventFilter(self, obj, evt):
            if evt.type() == QEvent.KeyPress:
                # prevent default key events
                self.keyPressCb(evt)
                return True
            elif evt.type() == QEvent.KeyRelease:
                self.keyReleaseCb(evt)
                return True
            return False

    def onModeBtnKeyPressEvent(self, event):
        # send by shortcut
        key = event.key()
        self.pressedKeys.append(key)
        for item in self.config["customSendItems"]:
            if not "shortcut" in item:
                continue
            shortcut = item["shortcut"]
            if len(shortcut) == len(self.pressedKeys):
                same = True
                for i in range(len(shortcut)):
                    if shortcut[i][0] != self.pressedKeys[i]:
                        same = False
                        break
                if same:
                    self.sendCustomItem(item)

    def onModeBtnKeyReleaseEvent(self, event):
        key = event.key()
        if key in self.pressedKeys:
            self.pressedKeys.remove(key)

    def onKeyPressEvent(self, event):
        pass

    def onKeyReleaseEvent(self, event):
        pass

    def insertSendItem(self, item = None, load = False):
        # itemsNum = self.customSendItemsLayout.count() + 1
        # height = parameters.customSendItemHeight * (itemsNum + 1) + 20
        # topHeight = self.receiveWidget.height() + 100
        # if height + topHeight > self.funcParent.height():
        #     height = self.funcParent.height() - topHeight
        # if height < 0:
        #     height = self.funcParent.height() // 3
        # self.customSendScroll.setMinimumHeight(height)
        if not item:
            item = {"text": "", "remark": None, "icon": None}
        if type(item) == str:
            item = {
                "text": item,
                "remark": None
            }
        text = item["text"]
        remark = item["remark"]
        itemWidget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        itemWidget.setLayout(layout)
        cmd = QLineEdit(text)
        if remark:
            send = QPushButton(remark)
        else:
            send = QPushButton("")
        if (not "icon" in item) or not item["icon"]:
            item["icon"] = "fa.send"
        if not "shortcut" in item:
            item["shortcut"] = []
        utils_ui.setButtonIcon(send, item["icon"])
        editRemark = QPushButton("")
        editRemark.setObjectName("editRemark")
        utils_ui.setButtonIcon(editRemark, "ei.pencil")
        editRemark.setProperty("class", "remark")
        cmd.setToolTip(text)
        send.setToolTip(text)
        cmd.textChanged.connect(lambda: self.onCustomItemChange(self.customSendItemsLayout.indexOf(itemWidget), cmd, send))
        send.setProperty("class", "smallBtn")
        def sendCustomData(idx):
            self.sendCustomItem(self.config["customSendItems"][idx])
        send.clicked.connect(lambda: sendCustomData(self.customSendItemsLayout.indexOf(itemWidget)))
        delete = QPushButton("")
        utils_ui.setButtonIcon(delete, "fa.close")
        delete.setProperty("class", "deleteBtn")
        layout.addWidget(cmd)
        layout.addWidget(send)
        layout.addWidget(editRemark)
        layout.addWidget(delete)
        delete.clicked.connect(lambda: self.deleteSendItem(self.customSendItemsLayout.indexOf(itemWidget), itemWidget, [send, editRemark, delete]))
        def changeRemark(idx, obj):
            if not "icon" in self.config["customSendItems"][idx]:
                self.config["customSendItems"][idx]["icon"] = None
            shortcut = []
            if "shortcut" in self.config["customSendItems"][idx]:
                shortcut = self.config["customSendItems"][idx]["shortcut"]
            ok, remark, icon, shortcut = EditRemarDialog(obj.text(), self.config["customSendItems"][idx]["icon"], shortcut).exec()
            if ok:
                obj.setText(remark)
                if icon:
                    utils_ui.setButtonIcon(obj, icon)
                else:
                    obj.setIcon(QIcon())
                self.config["customSendItems"][idx]["remark"] = remark
                self.config["customSendItems"][idx]["icon"] = icon
                self.config["customSendItems"][idx]["shortcut"] = shortcut
        editRemark.clicked.connect(lambda: changeRemark(self.customSendItemsLayout.indexOf(itemWidget), send))
        self.customSendItemsLayout.addWidget(itemWidget)
        if not load:
            self.config["customSendItems"].append(item)
        return item

    def deleteSendItem(self, idx, item, iconItems = []):
        for obj in iconItems:
            utils_ui.clearButtonIcon(obj)
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
        try:
            data = self.decodeMethod(data)
        except Exception as e:
            self.hintSignal.emit("error", _("Error"), _("Run decode error") + " " + str(e))
            return
        if not data:
            return
        for id in self.connChilds:
            self.plugins_info[id].onReceived(data)
        if type(data) != str:
            data = self.decodeReceivedData(data, self.configGlobal["encoding"], not self.config["sendAscii"], self.config["sendEscape"])
        self.showReceiveDataSignal.emit(data + "\n")

    def sendData(self, data_bytes=None):
        try:
            data_bytes = self.encodeMethod(data_bytes)
        except Exception as e:
            self.hintSignal.emit("error", _("Error"), _("Run encode error") + " " + str(e))
            return
        if data_bytes:
            self.send(data_bytes)

    def sendCustomItem(self, item):
        text = item["text"]
        dateBytes = self.parseSendData(text, self.configGlobal["encoding"], self.config["useCRLF"], not self.config["sendAscii"], self.config["sendEscape"])
        if dateBytes:
            self.sendData(data_bytes = dateBytes)

    def onCustomItemChange(self, idx, edit, send):
        text = edit.text()
        edit.setToolTip(text)
        send.setToolTip(text)
        self.config["customSendItems"][idx].update({
            "text": text,
            "remark": send.text()
        })

    def onCodeItemChanged(self):
        if self.editingDefaults:
            return
        self.editingDefaults = True
        if self.codeItems.currentText() == self.codeItemCustomStr:
            self.codeItems.clearEditText()
            self.editingDefaults = False
            return
        if self.codeItems.currentText() == self.codeItemLoadDefaultsStr:
            for name in defaultProtocols:
                idx = self.codeItems.findText(name)
                if idx >= 0:
                    self.codeItems.removeItem(idx)
                self.codeItems.insertItem(self.codeItems.count() - 2, name)
                self.config["code"][name] = defaultProtocols[name]
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
        self.saveCodeBtn.setText(_("Save"))
        self.saveCodeBtn.setEnabled(False)

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

    def onCodeChanged(self):
        changed = True
        name = self.codeItems.currentText()
        if name in self.config["code"]:
            codeSaved = self.config["code"][name]
            code = self.codeWidget.toPlainText()
            if code == codeSaved:
                changed = False
        if changed:
            self.saveCodeBtn.setText(_("Save") + " *")
            self.saveCodeBtn.setEnabled(True)
        else:
            self.saveCodeBtn.setText(_("Save"))
            self.saveCodeBtn.setEnabled(False)

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
            self.saveCodeBtn.setText(_("Save"))
            self.saveCodeBtn.setEnabled(False)

    def deleteCode(self):
        self.editingDefaults = True
        name = self.codeItems.currentText()
        itemsConfig = [self.codeItemCustomStr, self.codeItemLoadDefaultsStr]
        # QMessageBox.infomation()
        if name in itemsConfig or not name:
            self.hintSignal.emit("warning", _("Warning"), _("Please select a code profile name first to delete"))
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

