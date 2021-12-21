import sys,os

if sys.version_info < (3, 8):
    print("only support python >= 3.8, but now is {}".format(sys.version_info))
    sys.exit(1)


try:
    import parameters,helpAbout,autoUpdate
    from Combobox import ComboBox
    import i18n
    from i18n import _
    import version
    import utils
    from conn.conn_serial import Serial
    from plugins import plugins
    from widgets import TitleBar, WindowResizableMixin
except ImportError:
    from COMTool import parameters,helpAbout,autoUpdate, utils
    from COMTool.Combobox import ComboBox
    from COMTool import i18n
    from COMTool.i18n import _
    from COMTool import version
    from COMTool.conn.conn_serial import Serial
    from COMTool.plugins import plugins
    from .widgets import TitleBar, WindowResizableMixin

from PyQt5.QtCore import pyqtSignal, Qt, QRect, QMargins
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QTabWidget)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor
import qtawesome as qta # https://github.com/spyder-ide/qtawesome
import threading
import time
from datetime import datetime
import binascii,re
if sys.platform == "win32":
    import ctypes



class MainWindow(QMainWindow, WindowResizableMixin):
    hintSignal = pyqtSignal(str, str, str) # type(error, warning, info), title, msg
    statusBarSignal = pyqtSignal(str, str)
    updateSignal = pyqtSignal(object)
    countUpdateSignal = pyqtSignal(int, int)
    clearCountSignal = pyqtSignal()
    reloadWindowSignal = pyqtSignal(str, str, object)
    receiveCount = 0
    sendCount = 0
    DataPath = "./"
    app = None
    needRestart = False

    def __init__(self,app):
        QMainWindow.__init__(self)
        self.app = app
        self.DataPath = parameters.dataPath
        self.config = self.loadConfig()
        i18n.set_locale(self.config.basic["locale"])
        self.initVar()
        self.initConn(self.config.basic["connId"], self.config.conns)
        self.initPlugins(self.config.basic["plugins"], self.config.basic["activePlugin"], self.config.plugins)
        self.initWindow()
        self.uiLoadConfigs(self.config)
        self.initEvent()
        self.uiInitDone()

    def __del__(self):
        pass

    def initConn(self, connId, configs):
        # get all conn info
        self.connections = [Serial()]
        # init connections
        for conn in self.connections:
            conn.onReceived = self.onReceived
            conn.configGlobal = self.config.basic
            conn.hintSignal = self.hintSignal
            config = {}
            if conn.id in configs:
                config = configs[conn.id]
            else: # add new dict obj for conn to use
                configs[conn.id] = config
            conn.onInit(config)
        # init last used one
        self.connection = None
        for conn in self.connections:
            if conn.id == connId:
                self.connection = conn
        if not self.connection:
            self.connection = self.connections[0]


    def initPlugins(self, enabled, activeId, configs):
        if not enabled:
            enabled = ["dbg", "protocol"]
        self.connChilds = []
        self.plugins = [Plugin() for Plugin in plugins]
        for plugin in self.plugins:
            plugin.hintSignal = self.hintSignal
            plugin.send = self.sendData
            plugin.clearCountSignal = self.clearCountSignal
            plugin.reloadWindowSignal = self.reloadWindowSignal
            plugin.configGlobal = self.config.basic
            config = {}
            if plugin.id in configs:
                config = configs[plugin.id]
            else: # add new dict obj for plugin to use
                configs[plugin.id] = config
            plugin.onInit(config, self.plugins)
            if plugin.id in enabled:
                self.enablePlugin(plugin)
            if plugin.id == activeId:
                self.activePlugin(plugin)

    def enablePlugin(self, plugin):
        plugin.enabled = True
        if plugin.connParent == "main":
            self.connChilds.append(plugin)


    def activePlugin(self, plugin):
        for p in self.plugins:
            p.active = False
        plugin.active = True
        parent = None
        if (not "main" in plugin.connParent) and plugin.connParent:
            plugin.isConnected = self.connection.isConnected
            for pluginParent in self.plugins:
                if pluginParent.id == plugin.connParent:
                    pluginParent.active = True
                    pluginParent.isConnected = self.connection.isConnected
                    pluginParent.send = self.sendData
                    pluginParent.connChilds.append(plugin)
                    parent = pluginParent
                    break
            plugin.send = parent.sendData
        if not parent:
            plugin.isConnected = self.connection.isConnected
            plugin.send = self.sendData
        self.config.basic["activePlugin"] = plugin.id
    
    def initVar(self):
        self.strings = parameters.Strings(self.config.basic["locale"])
        self.dataToSend = []
        self.fileToSend = []

    def uiInitDone(self):
        self.connection.onUiInitDone()
        for plugin in self.plugins:
            plugin.onUiInitDone()
        # always hide functional, and show before init complete so we can get its width height
        self.hideFunctional()

        self.sendProcess = threading.Thread(target=self.sendDataProcess)
        self.sendProcess.setDaemon(True)
        self.sendProcess.start()

    def initWindow(self):
        # menu layout
        self.settingsButton = QPushButton()
        self.skinButton = QPushButton("")
        self.languageCombobox = ComboBox()
        self.languages = i18n.get_languages()
        for locale in self.languages:
            self.languageCombobox.addItem(self.languages[locale])
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
        self.settingsButton.setObjectName("menuItem")
        self.skinButton.setObjectName("menuItem")
        self.aboutButton.setObjectName("menuItem")
        self.functionalButton.setObjectName("menuItem")

        # title bar
        title = parameters.appName+" v"+version.__version__
        iconPath = self.DataPath+"/"+parameters.appIcon
        print("-- icon path: " + iconPath)
        titleBar = TitleBar(self, icon=iconPath, title=title, brothers=[], widgets=[[self.skinButton, self.aboutButton], []])
        WindowResizableMixin.__init__(self, titleBar=titleBar)

        # root layout
        self.frameWidget = QWidget()
        self.frameWidget.setMouseTracking(True)
        self.frameWidget.setLayout(self.rootLayout)
        self.setCentralWidget(self.frameWidget)
        # tab widgets
        def addTabPanel(tabWidget, name, plugin, connectionWidget = None):
            '''
                @return panenl widget, connectionWidget parent
            '''
            contentWidget = QSplitter(Qt.Horizontal)
            contentWidget.setProperty("class", "contentWrapper")
            # contentWidget.setContentsMargins(5,5,5,5)
            tabWidget.addTab(contentWidget, name)
            mainWidget = plugin.onWidgetMain(contentWidget, self)

            # widgets settings
            settingWidget = QWidget()
            settingWidget.setProperty("class","settingWidget")
            settingLayout = QVBoxLayout()
            settingWidget.setLayout(settingLayout)
            #    connection settings
            connSettingsGroupBox = QGroupBox(_("Connection"))
            layout = QVBoxLayout()
            connSettingsGroupBox.setLayout(layout)
            layout.addWidget(connectionWidget)
            settingLayout.addWidget(connSettingsGroupBox)
            #  other settings
            widget = plugin.onWidgetSettings(settingLayout)
            settingLayout.addWidget(widget)
            settingLayout.setContentsMargins(0,0,0,0)

            # right functional layout
            functionalWiget = plugin.onWidgetFunctional(contentWidget)
            contentWidget.addWidget(settingWidget)
            contentWidget.addWidget(mainWidget)
            contentWidget.addWidget(functionalWiget)
            contentWidget.setStretchFactor(0, 1)
            contentWidget.setStretchFactor(1, 2)
            contentWidget.setStretchFactor(2, 1)
            return contentWidget, connSettingsGroupBox
        self.tabWidget = QTabWidget()
        # self.contentLayout.setSpacing(0)
        # self.contentLayout.setContentsMargins(0,0,0,0)
        # tab left menu
        tabConerWidget = QWidget()
        tabConerLayout = QHBoxLayout()
        tabConerLayout.setSpacing(0)
        tabConerLayout.setContentsMargins(0, 0, 0, 0)
        tabConerWidget.setLayout(tabConerLayout)
        tabConerLayout.addWidget(self.settingsButton)
        # tab right menu
        tabConerWidgetRight = QWidget()
        tabConerLayoutRight = QHBoxLayout()
        tabConerLayoutRight.setSpacing(0)
        tabConerLayoutRight.setContentsMargins(0, 0, 0, 0)
        tabConerWidgetRight.setLayout(tabConerLayoutRight)
        tabConerLayoutRight.addWidget(self.languageCombobox)
        tabConerLayoutRight.addWidget(self.encodingCombobox)
        tabConerLayoutRight.addWidget(self.functionalButton)
        self.tabWidget.setCornerWidget(tabConerWidget, Qt.TopLeftCorner)
        self.tabWidget.setCornerWidget(tabConerWidgetRight, Qt.TopRightCorner)
        self.contentLayout.addWidget(self.tabWidget)
        # get widgets from plugins
            # widget main
        self.connectionWidget = self.connection.onWidget()
        self.tabWidgets = []
        self.connParentWidgets = []
        for i, plugin in enumerate(self.plugins):
            active = False
            if plugin.id == self.config.basic["activePlugin"]:
                active = True
                conn = self.connectionWidget
            else:
                conn = None
            w, connParent = addTabPanel(self.tabWidget, plugin.name, plugin, conn)
            self.tabWidgets.append(w)
            self.connParentWidgets.append(connParent)
            if active:
                self.tabWidget.setCurrentWidget(w)

        # main window
        self.statusBarStauts = QLabel()
        self.statusBarStauts.setMinimumWidth(80)
        self.onstatusBarText("info", self.strings.strReady)
        self.statusBarSendCount = QLabel('{}({}):0'.format(_("Sent"), _("bytes")))
        self.statusBarReceiveCount = QLabel('{}({}):0'.format(_("Received"), _("bytes")))
        self.statusBar = QWidget()
        self.statusBar.setProperty("class", "statusBar")
        self.statusBarLayout = QHBoxLayout()
        self.statusBarLayout.setSpacing(0)
        self.statusBarLayout.setContentsMargins(0, 5, 0, 0)
        self.statusBarLayout.addWidget(self.statusBarStauts)
        self.statusBarLayout.addWidget(self.statusBarSendCount)
        self.statusBarLayout.addWidget(self.statusBarReceiveCount)
        self.statusBar.setLayout(self.statusBarLayout)

        self.contentLayout.addWidget(self.statusBar)

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("comtool")
        self.resize(800, 500)
        self.MoveToCenter()
        self.show()
        print("config file path:",parameters.configFilePath)

    def initEvent(self):
        # menu
        self.settingsButton.clicked.connect(self.toggleSettings)
        self.languageCombobox.currentIndexChanged.connect(self.onLanguageChanged)
        self.encodingCombobox.currentIndexChanged.connect(lambda: self.bindVar(self.encodingCombobox, self.config.basic, "encoding"))
        self.functionalButton.clicked.connect(self.toggleFunctional)
        self.skinButton.clicked.connect(self.skinChange)
        self.aboutButton.clicked.connect(self.showAbout)
        # main
        self.tabWidget.currentChanged.connect(lambda idx: self.changeConnToTab(idx))
        # others
        self.updateSignal.connect(self.showUpdate)
        self.hintSignal.connect(self.showHint)
        self.statusBarSignal.connect(self.onstatusBarText)
        self.clearCountSignal.connect(self.onClearCount)
        self.reloadWindowSignal.connect(self.onReloadWindow)
        self.countUpdateSignal.connect(self.onUpdateCountUi)

    def bindVar(self, uiObj, varObj, varName: str, vtype=None, vErrorMsg="", checkVar=lambda v:v, invert = False):
        objType = type(uiObj)
        if objType == QCheckBox:
            v = uiObj.isChecked()
            if hasattr(varObj, varName):
                varObj.__setattr__(varName, v if not invert else not v)
            else:
                varObj[varName] = v if not invert else not v
            return
        elif objType == QLineEdit:
            v = uiObj.text()
        elif objType == ComboBox:
            if hasattr(varObj, varName):
                varObj.__setattr__(varName, uiObj.currentText())
            else:
                varObj[varName] = uiObj.currentText()
            return
        elif objType == QRadioButton:
            v = uiObj.isChecked()
            if hasattr(varObj, varName):
                varObj.__setattr__(varName, v if not invert else not v)
            else:
                varObj[varName] = v if not invert else not v
            return
        else:
            raise Exception("not support this object")
        if vtype:
            try:
                v = vtype(v)
            except Exception:
                uiObj.setText(str(varObj.__getattribute__(varName)))
                self.hintSignal.emit("error", _("Error"), vErrorMsg)
                return
        try:
            v = checkVar(v)
        except Exception as e:
            self.hintSignal.emit("error", _("Error"), str(e))
            return
        varObj.__setattr__(varName, v)

    def changeConnToTab(self, idx):
        print("-- switch to tab", idx)
        parent = self.connectionWidget.parentWidget()
        if parent.layout().indexOf(self.connectionWidget) >= 0:
            parent.layout().removeWidget(self.connectionWidget)
        newParent = self.connParentWidgets[idx]
        newParent.layout().addWidget(self.connectionWidget)
        self.updateStyle(parent)
        self.updateStyle(newParent)
        self.activePlugin(self.plugins[idx])

    def sendData(self, data_bytes=None, file_path=None, callback=lambda ok,msg:None):
        if data_bytes:
            self.dataToSend.insert(0, (data_bytes, callback))
        if file_path:
            self.fileToSend.insert(0, (file_path, callback))

    def onSent(self, data):
        self.sendCount += len(data)
        self.countUpdateSignal.emit(self.sendCount, self.receiveCount)

    def onReceived(self, data):
        self.receiveCount += len(data)
        self.countUpdateSignal.emit(self.sendCount, self.receiveCount)
        # invoke plugin onReceived
        for plugin in self.connChilds:
            if plugin.active:
                plugin.onReceived(data)


    def sendDataProcess(self):
        self.receiveProgressStop = False
        while(not self.receiveProgressStop):
            try:
                if not self.connection.isConnected():
                    time.sleep(0.001)
                    continue
                while len(self.dataToSend) > 0:
                    data, callback = self.dataToSend.pop()
                    self.connection.send(data)
                    self.onSent(data)
                    callback(True, "")
                while len(self.fileToSend) > 0:
                    file_path, callback = self.fileToSend.pop()
                    ok = False
                    if file_path and os.path.exists(file_path):
                        data = None
                        try:
                            with open(file_path, "rb") as f:
                                data = f.read()
                        except Exception as e:
                            self.hintSignal.emit("error", _("Error"), _("Open file failed!") + "\n%s\n%s" %(file_path, str(e)))
                        if data:
                            self.connection.send(data)
                            self.onSent(data)
                            ok = True
                    callback(ok, "")
                time.sleep(0.001)
            except Exception as e:
                import traceback
                traceback.print_exc()
                if 'multiple access' in str(e):
                    self.hintSignal.emit("error", _("Error"), "device disconnected or multiple access on port?")
                continue

    def onUpdateCountUi(self, send, receive):
        self.statusBarSendCount.setText('{}({}): {}'.format(_("Sent"), _("bytes"), send))
        self.statusBarReceiveCount.setText('{}({}): {}'.format(_("Received"), _("bytes"), receive))

    def onstatusBarText(self, msg_type, msg):
        if msg_type == "info":
            color = "#008200"
        elif msg_type == "warning":
            color = "#fb8c00"
        elif msg_type == "error":
            color = "#f44336"
        else:
            color = "#008200"
        text = '<font color={}>{}</font>'.format(color, msg)
        self.statusBarStauts.setText(text)        

    def updateStyle(self, widget):
        self.frameWidget.style().unpolish(widget)
        self.frameWidget.style().polish(widget)
        self.frameWidget.update()

    def onLanguageChanged(self):
        idx = self.languageCombobox.currentIndex()
        locale = list(self.languages.keys())[idx]
        self.config.basic["locale"] = locale
        i18n.set_locale(locale)
        reply = QMessageBox.question(self, _('Restart now?'),
                                     _("language changed to: ") + self.languages[self.config.basic["locale"]] + "\n" + _("Restart software to take effect now?"), QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.needRestart = True
            self.close()

    def onReloadWindow(self, title, msg, callback):
        if not title:
            title = _('Restart now?')
        reply = QMessageBox.question(self, title, msg,
                            QMessageBox.Yes |
                            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            callback(True)
            self.needRestart = True
            self.close()
        else:
            callback(False)

    def onClearCount(self):
        self.receiveCount = 0
        self.sendCount = 0
        self.countUpdateSignal.emit(self.sendCount, self.receiveCount)

    def MoveToCenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def showHint(self, info_type: str, title: str, msg: str):
        if info_type == "info":
            QMessageBox.information(self, title, msg)
        elif info_type == "warning":
            QMessageBox.warning(self, title, msg)
        elif info_type == "error":
            QMessageBox.critical(self, title, msg)

    def closeEvent(self, event):
        print("----- close event")
        # reply = QMessageBox.question(self, 'Sure To Quit?',
        #                              "Are you sure to quit?", QMessageBox.Yes |
        #                              QMessageBox.No, QMessageBox.No)
        if 1: # reply == QMessageBox.Yes:
            self.receiveProgressStop = True
            self.saveConfig()
            event.accept()
        else:
            event.ignore()

    def saveConfig(self):
        self.config.save(parameters.configFilePath)

    def loadConfig(self):
        paramObj = parameters.Parameters()
        paramObj.load(parameters.configFilePath)
        self.config = paramObj
        return self.config

    def uiLoadConfigs(self, config):
        config = config.basic
        # language
        try:
            idx = list(self.languages.keys()).index(config["locale"])
        except Exception:
            idx = 0
        self.languageCombobox.setCurrentIndex(idx)
        # encoding
        self.encodingCombobox.setCurrentIndex(self.supportedEncoding.index(config["encoding"]))

    def keyPressEvent(self, event):
        for plugin in self.plugins:
            if plugin.active:
                plugin.onKeyReleaseEvent(event)

    def keyReleaseEvent(self,event):
        for plugin in self.plugins:
            if plugin.active:
                plugin.onKeyReleaseEvent(event)

    def toggleSettings(self):
        widget = self.tabWidget.currentWidget().widget(0)
        if widget.isVisible():
            self.hideSettings()
        else:
            self.showSettings()

    def showSettings(self):
        widget = self.tabWidget.currentWidget().widget(0)
        widget.show()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath",self.DataPath))

    def hideSettings(self):
        widget = self.tabWidget.currentWidget().widget(0)
        widget.hide()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath", self.DataPath))

    def toggleFunctional(self):
        widget = self.tabWidget.currentWidget().widget(2)
        if widget.isVisible():
            self.hideFunctional()
        else:
            self.showFunctional()

    def showFunctional(self):
        widget = self.tabWidget.currentWidget().widget(2)
        widget.show()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath",self.DataPath))

    def hideFunctional(self):
        widget = self.tabWidget.currentWidget().widget(2)
        widget.hide()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath", self.DataPath))

    def skinChange(self):
        if self.config.basic["skin"] == "light": # light
            file = open(self.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
            self.config.basic["skin"] = "dark"
        else: # elif self.config.basic["skin"] == 2: # dark
            file = open(self.DataPath + '/assets/qss/style.qss', "r", encoding="utf-8")
            self.config.basic["skin"] = "light"
        self.app.setStyleSheet(file.read().replace("$DataPath", self.DataPath))

    def showAbout(self):
        QMessageBox.information(self, _("About"), helpAbout.strAbout())

    def showUpdate(self, versionInfo):
        versionInt = versionInfo.int()
        if self.config.basic["skipVersion"] and self.config.basic["skipVersion"] >= versionInt:
            return
        msgBox = QMessageBox()
        desc = versionInfo.desc if len(versionInfo.desc) < 300 else versionInfo.desc[:300] + " ... "
        link = '<a href="https://github.com/Neutree/COMTool/releases">github.com/Neutree/COMTool/releases</a>'
        info = '{}<br>{}<br><br>v{}: {}<br><br>{}'.format(_("New versioin detected, please click learn more to download"), link, '{}.{}.{}'.format(versionInfo.major, versionInfo.minor, versionInfo.dev), versionInfo.name, desc)
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
            self.config.basic["skipVersion"] = versionInt

            

    def autoUpdateDetect(self):
        auto = autoUpdate.AutoUpdate()
        needUpdate, versionInfo = auto.detectNewVersion()
        if needUpdate:
            self.updateSignal.emit(versionInfo)

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
            if(mainWindow.config.basic["skin"] == "light") :# light skin
                file = open(mainWindow.DataPath+'/assets/qss/style.qss',"r", encoding="utf-8")
            else: #elif mainWindow.config == "dark": # dark skin
                file = open(mainWindow.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
            qss = file.read().replace("$DataPath",mainWindow.DataPath)
            app.setStyleSheet(qss)
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

