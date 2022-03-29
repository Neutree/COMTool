import imp
from PyQt5.QtCore import pyqtSignal, Qt, QRect, QMargins
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QTabWidget, QMenu, QSplashScreen)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor, QCloseEvent
import threading
import time
import os

try:
    from i18n import _
    from Combobox import ComboBox
    from parameters import log
except ImportError:
    from COMTool.Combobox import ComboBox
    from COMTool.i18n import _
    from COMTool.parameters import log

class PluginItem:
    # display name
    name = ''
    widget = None
    def __init__(self, name, pluginClass, connClasses,
                    globalConfig, itemConfig,
                    hintSignal, reloadWindowSignal):
        '''
            item show name, e.g. dbg-1
        '''
        self.reloadWindowSignal = reloadWindowSignal
        self.hintSignal = hintSignal
        self.name = name
        self.connClasses = connClasses
        self.currConnWidgets = None
        self.currConnIdx = 0
        self.sendProcess = None
        self.dataToSend = []
        self.fileToSend = []
        # widgets
        self.settingWidget = None
        self.mainWidget = None
        self.functionalWidget = None
        # init plugin
        self.plugin = pluginClass()
        self.plugin.configGlobal = globalConfig
        self.plugin.send = self.sendData
        self.plugin.ctrlConn = self.ctrlConn
        self.plugin.hintSignal = self.hintSignal
        self.plugin.reloadWindowSignal = self.reloadWindowSignal
        self.plugin.onInit(config=itemConfig)
        # conn
        self.conns, self.connWidgets = self.newConnWidgets()
        # frame
        self.widget = self.newFrame()
        self.uiLoadConfigs()
    
    def newConnWidgets(self):
        connsWidgets = []
        conns = []
        for Conn in self.connClasses:
            # conn.onInit()
            conn = Conn()
            conns.append(conn)
            conn.onInit({})
            widget = conn.onWidget()
            conn.onUiInitDone()
            connsWidgets.append(widget)
        return conns, connsWidgets

    def newFrame(self):
        wrapper = QWidget()
        wrapperLayout = QVBoxLayout()
        wrapperLayout.setContentsMargins(0, 0, 0, 0)
        widget = QSplitter(Qt.Horizontal)
        widget.setProperty("class", "contentWrapper")
        statusBar = self.plugin.onWidgetStatusBar(wrapper)
        wrapper.setLayout(wrapperLayout)
        wrapperLayout.addWidget(widget)
        if not statusBar is None:
            wrapperLayout.addWidget(statusBar)
        # widgets settings
        self.settingWidget = QWidget()
        self.settingWidget.setProperty("class","settingWidget")
        settingLayout = QVBoxLayout()
        self.settingWidget.setLayout(settingLayout)
        #    get connection settings widgets
        connSettingsGroupBox = QGroupBox(_("Connection"))
        layout = QVBoxLayout()
        connSettingsGroupBox.setLayout(layout)
        connSelectCommbox = ComboBox()
        for conn in self.conns:
            connSelectCommbox.addItem(conn.name)
        connSelectCommbox.currentIndexChanged.connect(self.onConnChanged)
        layout.addWidget(connSelectCommbox)
        layout.setContentsMargins(1, 6, 0, 0)
        self.connsParent = QWidget()
        layout2 = QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        self.connsParent.setLayout(layout2)
        layout.addWidget(self.connsParent)
        settingLayout.addWidget(connSettingsGroupBox)
        #    get settings widgets
        subSettingWidget = self.plugin.onWidgetSettings(widget)
        if not subSettingWidget is None:
            settingLayout.addWidget(subSettingWidget)
        # widgets main
        self.mainWidget = self.plugin.onWidgetMain(widget)
        # widgets functional
        self.functionalWidget = self.plugin.onWidgetFunctional(widget)
        # add to frame
        widget.addWidget(self.settingWidget)
        widget.addWidget(self.mainWidget)
        if not self.functionalWidget is None:
            widget.addWidget(self.functionalWidget)
        widget.setStretchFactor(0, 1)
        widget.setStretchFactor(1, 2)
        widget.setStretchFactor(2, 1)
        # UI init done
        self.plugin.onUiInitDone()
        return wrapper

    def _setConn(self, idx):
        if self.currConnWidgets:
            self.currConnWidgets.setParent(None)
            self.conns[idx].onReceived = lambda x:None
        self.currConnWidgets = self.connWidgets[idx]
        self.connsParent.layout().addWidget(self.currConnWidgets)
        self.conns[idx].onReceived = self.onReceived
        self.plugin.isConnected = self.conns[idx].isConnected
        self.currConnIdx = idx
        self.conns[idx].onConnectionStatus.connect(self.onConnStatus)


    def uiLoadConfigs(self):
        self._setConn(0)

    def onConnChanged(self, idx):
        self.conns[self.currConnIdx].disconnect()
        self._setConn(idx)

    def ctrlConn(self, k, v):
        self.conns[self.currConnIdx].ctrl(k, v)

    def onConnStatus(self, status, msg):
        self.plugin.onConnChanged(status, msg)
        if self.sendProcess is None:
            self.sendProcess = threading.Thread(target=self.sendDataProcess)
            self.sendProcess.setDaemon(True)
            self.sendProcess.start()

    def sendData(self, data_bytes=None, file_path=None, callback=lambda ok, msg, length, path:None):
        if data_bytes:
            self.dataToSend.insert(0, (data_bytes, callback))
        if file_path:
            self.fileToSend.insert(0, (file_path, callback))

    def onReceived(self, data):
        self.plugin.onReceived(data)

    def onKeyPressEvent(self, e):
        self.plugin.onKeyPressEvent(e)

    def onKeyReleaseEvent(self, e):
        self.plugin.onKeyReleaseEvent(e)

    def sendDataProcess(self):
        self.receiveProgressStop = False
        while not self.receiveProgressStop:
            try:
                if not self.conns[self.currConnIdx].isConnected():
                    time.sleep(0.001)
                    continue
                while len(self.dataToSend) > 0:
                    data, callback = self.dataToSend.pop()
                    self.conns[self.currConnIdx].send(data)
                    callback(True, "", len(data), "")
                while len(self.fileToSend) > 0:
                    file_path, callback = self.fileToSend.pop()
                    ok = False
                    length = 0
                    if file_path and os.path.exists(file_path):
                        data = None
                        try:
                            with open(file_path, "rb") as f:
                                data = f.read()
                        except Exception as e:
                            self.hintSignal.emit("error", _("Error"), _("Open file failed!") + "\n%s\n%s" %(file_path, str(e)))
                        if data:
                            self.conns[self.currConnIdx].send(data)
                            length = len(data)
                            ok = True
                    callback(ok, "", length, file_path)
                time.sleep(0.001)
            except Exception as e:
                import traceback
                exc = traceback.format_exc()
                log.e(exc)
                if 'multiple access' in str(e):
                    self.hintSignal.emit("error", _("Error"), "device disconnected or multiple access on port?")
                continue
