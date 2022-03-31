import sys,os

if sys.version_info < (3, 7):
    print("only support python >= 3.7, but now is {}".format(sys.version_info))
    sys.exit(1)

# Init lanuage first to ensure use function _  works correctly
try:
    import parameters
    import i18n
except ImportError:
    from COMTool import parameters
    from COMTool import i18n

def loadConfig():
    paramObj = parameters.Parameters()
    paramObj.load(parameters.configFilePath)
    return paramObj

log = parameters.log
log.i("loading config from", parameters.configFilePath)
programConfig = loadConfig()
log.i("loading config complete")
i18n.set_locale(programConfig["locale"])

try:
    import helpAbout,autoUpdate
    from Combobox import ComboBox
    from i18n import _
    import version
    import utils_ui
    from conn import ConnectionStatus, conns
    from plugins import builtinPlugins
    from pluginItems import PluginItem
    from widgets import TitleBar, CustomTitleBarWindowMixin, EventFilter, ButtonCombbox
except ImportError:
    from COMTool import helpAbout,autoUpdate, utils_ui
    from COMTool.Combobox import ComboBox
    from COMTool.i18n import _
    from COMTool import version
    from COMTool.conn import ConnectionStatus, conns
    from COMTool.plugins import builtinPlugins
    from COMTool.pluginItems import PluginItem
    from .widgets import TitleBar, CustomTitleBarWindowMixin, EventFilter, ButtonCombbox

from PyQt5.QtCore import pyqtSignal, Qt, QRect, QMargins
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QTabWidget, QMenu, QSplashScreen)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor, QCloseEvent
import qtawesome as qta # https://github.com/spyder-ide/qtawesome
import threading
import time
from datetime import datetime
import binascii,re
if sys.platform == "win32":
    import ctypes

g_all_windows = []

class MainWindow(CustomTitleBarWindowMixin, QMainWindow):
    hintSignal = pyqtSignal(str, str, str) # type(error, warning, info), title, msg
    # statusBarSignal = pyqtSignal(str, str)
    updateSignal = pyqtSignal(object)
    # countUpdateSignal = pyqtSignal(int, int)
    reloadWindowSignal = pyqtSignal(str, str, object)
    receiveCount = 0
    sendCount = 0
    DataPath = "./"
    app = None
    needRestart = False

    def __init__(self,app, eventFilter, config):
        QMainWindow.__init__(self)
        self.app = app
        self.eventFilter = eventFilter
        self.DataPath = parameters.dataPath
        self.config = config
        log.i("init main window")
        self.initVar()
        self.initWindow()
        self.uiLoadConfigs()
        log.i("init main window complete")
        self.loadPluginsInfoList()
        self.loadPluginItems()
        log.i("load plugin items complete")
        self.initEvent()
        # self.initPlugins(self.config.basic["pluginsInfo"], self.config.basic["activePlugin"], self.config.plugins)
        # self.initConn(self.config.basic["connId"], self.config.conns)
        # self.uiInitDone()

    def initVar(self):
        self.loadPluginStr = _("Load plugin from file")
        # self.strings = parameters.Strings(self.config.basic["locale"])
        # self.dataToSend = []
        # self.fileToSend = []
        # self.connSelectComboboxes = []
        # self.changingConn = False
        # self.connectionWidget = None
        # self.connection = None
        self.closeTimerId = None
        self.items = []
        self.pluginClasses = []

    def loadPluginsInfoList(self):
        for id, pluginClass in builtinPlugins.items(): 
            self.addPluginInfo(pluginClass)
            self.pluginClasses.append(pluginClass)
        rm = []
        for uid, info in self.config["pluginsInfo"]["external"].items():
            pluginClass = self._importPlugin(info["path"], test=True)
            if pluginClass:
                self.addPluginInfo(pluginClass)
                self.pluginClasses.append(pluginClass)
            else:
                rm.append(uid)
        for uid in rm:
            self.config["pluginsInfo"]["external"].pop(uid)

    def getPluginClassById(self, id):
        '''
            must call after loadPluginsInfoList
        '''
        for pluginClass in self.pluginClasses:
            if id == pluginClass.id:
                return pluginClass
        return None

    def loadPluginItems(self):
        items = self.config["items"]
        if items:
            for item in items:
                log.i("load plugin item", item["name"])
                pluginClass = self.getPluginClassById(item["pluginId"])
                if pluginClass:
                    setCurr = False
                    if self.config["currItem"] == item["name"]:
                        setCurr = True
                    # check language change, update item name to current lanuage
                    old_name_tail = item["name"].split(" ")[-1]
                    try:
                        int(old_name_tail)
                        item["name"] = pluginClass.name + " " + old_name_tail
                    except Exception: # for no number tailed name
                        item["name"] = pluginClass.name
                    self.addItem(pluginClass, nameSaved=item["name"], setCurrent=setCurr, connsConfigs = item["config"]["conns"], pluginConfig=item["config"]["plugin"])
        else:  # load builtin plugins
            for id, pluginClass in builtinPlugins.items(): 
                self.addItem(pluginClass)

    def addItem(self, pluginClass, nameSaved = None, setCurrent = False, connsConfigs=None, pluginConfig=None):
        '''
            @name add saved item, not add new item
        '''
        # set here, not set in arg, cause arg can lead to multi item use one object
        if not connsConfigs:
            connsConfigs = {}
        if not pluginConfig:
            pluginConfig = {}
        if nameSaved:
            name = nameSaved
        else:
            numbers = []
            for item in self.items:
                if item.plugin.id == pluginClass.id:
                    name = item.name.replace(item.plugin.name, "").split(" ")
                    if len(name) > 1:
                        number = int(name[-1])
                        numbers.append(number)
                    else:
                        numbers.append(0)
            if numbers:
                numbers = sorted(numbers)
            if (not numbers) or numbers[0] != 0:
                name = pluginClass.name
            else:
                last = numbers[0]
                number = -1
                for n in numbers[1:]:
                    if n != last + 1:
                        number = last + 1
                        break
                    last = n
                if number < 0:
                    number = numbers[-1] + 1
                name = f'{pluginClass.name} {number}'
        item = PluginItem(name, pluginClass,
                        conns, connsConfigs,
                        self.config, pluginConfig,
                        self.hintSignal, self.reloadWindowSignal)
        self.tabAddItem(item)
        self.items.append(item)
        if setCurrent:
            self.tabWidget.setCurrentWidget(item.widget)
        if not nameSaved:
            self.config["items"].append({
                    "name": name,
                    "pluginId": pluginClass.id,
                    "config": {
                        "conns": connsConfigs,
                        "plugin": pluginConfig
                        }
                })
        return item

    def tabAddItem(self, item):
        self.tabWidget.addTab(item.widget, item.name)

    def addPluginInfo(self, pluginClass):
        self.pluginsSelector.insertItem(self.pluginsSelector.count() - 1,
                                        f'{pluginClass.name} - {pluginClass.id}')

    # def initConn(self, connId, configs):
    #     # get all conn info
    #     self.connections = []
    #     for conn in conns:
    #         self.connections.append(conn())
    #     # add conn select combobox
    #     self.changingConn = True
    #     for i, conn in enumerate(self.connections):
    #         for combobox in self.connSelectComboboxes:
    #             combobox.addItem(conn.name)
    #             if conn.id == connId:
    #                 combobox.setCurrentIndex(i)
    #     self.changingConn = False
    #     # init connections
    #     activeConn = self.connections[0]
    #     for i, conn in enumerate(self.connections):
    #         conn.onReceived = self.onReceived
    #         conn.configGlobal = self.config.basic
    #         conn.hintSignal.connect(self.showHint)
    #         conn.onConnectionStatus.connect(self.onShowConnStatus)
    #         config = {}
    #         if conn.id in configs:
    #             config = configs[conn.id]
    #         else: # add new dict obj for conn to use
    #             configs[conn.id] = config
    #         conn.onInit(config)
    #         conn.onWidget()
    #         if conn.id == connId:
    #             activeConn = conn
    #     # init last used one
    #     self.changeConn(activeConn)

    def _importPlugin(self, path, test = False):
        if not os.path.exists(path):
            return None
        dir = os.path.dirname(path)
        name = os.path.splitext(os.path.basename(path))[0]
        sys.path.insert(0, dir)
        pluginClass = __import__(name).Plugin
        if test:
            sys.path.remove(dir)
        return pluginClass

    # def initPlugins(self, pluginsInfo, activeId, configs):
    #     enabled = []
    #     # find enabled builtin plugin
    #     for id, plugin in builtinPlugins.items():
    #         if not id in pluginsInfo["builtin"]:
    #            pluginsInfo["builtin"][id] = {"enabled": True}
    #         if pluginsInfo["builtin"][id]["enabled"]:
    #             enabled.append(id)

    #     # load external enabled plugins
    #     invalidPlugin = []
    #     for uid, info in pluginsInfo["external"].items():
    #         if info["enabled"]:
    #             pluginClass = self._importPlugin(info["path"])
    #             if pluginClass:
    #                 enabled.append(pluginClass.id)
    #                 builtinPlugins[pluginClass.id] = pluginClass
    #             else:
    #                 invalidPlugin.append(uid)
    #     # remove invalid external plugins
    #     for uid in invalidPlugin:
    #         pluginsInfo["external"].pop(uid)
    #     # init plugins
    #     self.connChilds = []
    #     self.plugins = []
    #     for id, pluinClass in builtinPlugins.items():
    #         if id in enabled:
    #             plugin = self.loadPlugin(pluinClass)

    # def loadPlugin(self, pluginClass, init = True):
    #     print("-- load plugin:", pluginClass.id)
    #     plugin = pluginClass()
    #     self.plugins.append(plugin)
    #     plugin.hintSignal = self.hintSignal
    #     plugin.send = self.sendData
    #     plugin.ctrlConn = self.ctrlConn
    #     plugin.isConnected = self.isConnected
    #     plugin.reloadWindowSignal = self.reloadWindowSignal
    #     plugin.configGlobal = self.config.basic
    #     config = {
    #         "plugin_id": plugin.id
    #     }
    #     configs = self.config.plugins
    #     if plugin.id in configs:
    #         config = configs[plugin.id]
    #     else: # add new dict obj for plugin to use
    #         configs[plugin.id] = config
    #     plugin.onInit(config)
    #     self.enablePlugin(plugin)
    #     if plugin.id == self.config.basic["activePlugin"]:
    #         self.activePlugin(plugin)
    #     if not init:
    #         self.addPluginTab(plugin, active=True)
    #         plugin.onUiInitDone()
    #         # load connections
    #         combobox = self.connSelectComboboxes[-1]
    #         self.changingConn = True
    #         for i, conn in enumerate(self.connections):
    #             combobox.addItem(conn.name)
    #             if conn.id == self.config.basic["connId"]:
    #                 combobox.setCurrentIndex(i)
    #         self.changingConn = False
    #     return plugin

    def loadExternalPlugin(self, path):
        extPlugsInfo = self.config["pluginsInfo"]["external"]
        found = False
        for uid, info in extPlugsInfo.items():
            if info["path"] == path:
                for pluginClass in self.pluginClasses:
                    # same plugin
                    if uid == pluginClass.id:
                        self.addItem(pluginClass, setCurrent = True)
                        found = True
                        break
                if found:
                    return True, ""
        pluginClass = self._importPlugin(path)
        if not pluginClass:
            return False, _("Load plugin fail")
        extPlugsInfo[pluginClass.id] = {
            "path": path
        }
        self.addItem(pluginClass, setCurrent=True)
        self.pluginClasses.append(pluginClass)
        self.addPluginInfo(pluginClass)
        return True, ""

    # def enablePlugin(self, plugin):
    #     plugin.enabled = True
    #     if plugin.connParent == "main":
    #         self.connChilds.append(plugin)


    # def activePlugin(self, plugin):
    #     for p in self.plugins:
    #         p.active = False
    #     plugin.active = True
    #     parent = None
    #     if (not "main" in plugin.connParent) and plugin.connParent:
    #         for pluginParent in self.plugins:
    #             if pluginParent.id == plugin.connParent:
    #                 pluginParent.active = True
    #                 pluginParent.send = self.sendData
    #                 if not plugin in pluginParent.connChilds:
    #                     pluginParent.connChilds.append(plugin)
    #                 parent = pluginParent
    #                 break
    #         if parent:
    #             plugin.send = parent.sendData
    #         else:
    #             self.hintSignal.emit("error", _("Error"), f"Plugin {plugin.id}'s connParent error")
    #     if not parent:
    #         plugin.send = self.sendData
    #     self.config.basic["activePlugin"] = plugin.id

    def onPluginSelectorChanged(self, idx):
        text = self.pluginsSelector.currentText()
        if text == self.loadPluginStr:
            oldPath = os.getcwd()
            fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                    _("Select file"),
                                    oldPath,
                                    _("python script (*.py)"))
            if fileName_choose != "":
                ok, msg = self.loadExternalPlugin(fileName_choose)
                if not ok:
                    self.hintSignal.emit("error", _("Error"), f'{_("Load plugin error")}: {msg}')
        else:
            loadID = text.split("-")[-1].strip()
            found = False
            # find in builtin plugins
            for id, c in builtinPlugins.items():
                if id == loadID:
                    item = self.addItem(c, setCurrent = True)
                    found = True
                    break
            # find in external plugins
            if not found:
                infos = self.config["pluginsInfo"]
                for id, info in infos["external"].items():
                    if id == loadID:
                        ok, msg = self.loadExternalPlugin(info["path"])
                        if not ok:
                            self.hintSignal.emit("error", _("Error"), f'{_("Load plugin error")}: {msg}')
                        break

    # def uiInitDone(self):
    #     for conn in self.connections:
    #         conn.onUiInitDone()
    #     for plugin in self.plugins:
    #         plugin.onUiInitDone()
    #     # always hide functional, and show before init complete so we can get its width height
    #     self.hideFunctional()

        # self.sendProcess = threading.Thread(target=self.sendDataProcess)
        # self.sendProcess.setDaemon(True)
        # self.sendProcess.start()

    def initWindow(self):
        # set skin for utils_ui
        utils_ui.setSkin(self.config["skin"])
        # menu layout
        self.settingsButton = QPushButton()
        self.skinButton = QPushButton("")
        self.languageCombobox = ButtonCombbox(icon="fa.language", btnClass="smallBtn2")
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
        # plugins slector
        self.pluginsSelector = ButtonCombbox(icon="fa.plus", btnClass="smallBtn2")
        self.pluginsSelector.addItem(self.loadPluginStr)
        self.pluginsSelector.activated.connect(self.onPluginSelectorChanged)

        # title bar
        title = parameters.appName+" v"+version.__version__
        iconPath = self.DataPath+"/"+parameters.appIcon
        log.i("icon path: " + iconPath)
        self.titleBar = TitleBar(self, icon=iconPath, title=title, brothers=[], widgets=[[self.skinButton, self.aboutButton], []])
        CustomTitleBarWindowMixin.__init__(self, titleBar=self.titleBar, init = True)

        # root layout
        self.frameWidget = QWidget()
        self.frameWidget.setMouseTracking(True)
        self.frameWidget.setLayout(self.rootLayout)
        self.setCentralWidget(self.frameWidget)
        # tab widgets
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabsClosable(True)
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
        tabConerLayoutRight.addWidget(self.pluginsSelector)
        tabConerLayoutRight.addWidget(self.languageCombobox)
        tabConerLayoutRight.addWidget(self.encodingCombobox)
        tabConerLayoutRight.addWidget(self.functionalButton)
        self.tabWidget.setCornerWidget(tabConerWidget, Qt.TopLeftCorner)
        self.tabWidget.setCornerWidget(tabConerWidgetRight, Qt.TopRightCorner)
        self.contentLayout = QVBoxLayout()
        self.contentWidget.setLayout(self.contentLayout)
        self.contentLayout.setContentsMargins(10, 0, 10, 10)
        self.contentLayout.addWidget(self.tabWidget)

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("comtool")
        elif sys.platform == 'darwin':
            self.macOsAddDockMenu()

        self.resize(800, 500)
        self.MoveToCenter()
        self.show()

    # def addPluginTab(self, plugin, active = False):
    #     w, connParent = self.addTabPanel(self.tabWidget, plugin.name, plugin, None)
    #     self.tabWidgets.append((w, plugin.id))
    #     self.connParentWidgets.append(connParent)
    #     if active:
    #         self.tabWidget.setCurrentWidget(w)
    #         plugin.onActive()

    # def addTabPanel(self, tabWidget, name, plugin, connectionWidget = None):
    #     '''
    #         @return panenl widget, connectionWidget parent
    #     '''
    #     contentWidget = QSplitter(Qt.Horizontal)
    #     contentWidget.setProperty("class", "contentWrapper")
    #     # contentWidget.setContentsMargins(5,5,5,5)
    #     tabWidget.addTab(contentWidget, name)
    #     mainWidget = plugin.onWidgetMain()

    #     # widgets settings
    #     settingWidget = QWidget()
    #     settingWidget.setProperty("class","settingWidget")
    #     settingLayout = QVBoxLayout()
    #     settingWidget.setLayout(settingLayout)
    #     #    connection settings
    #     connSelectCommbox = ComboBox()
    #     self.connSelectComboboxes.append(connSelectCommbox)
    #     connSelectCommbox.currentIndexChanged.connect(self.onConnChanged)
    #     connSettingsGroupBox = QGroupBox(_("Connection"))
    #     layout = QVBoxLayout()
    #     connSettingsGroupBox.setLayout(layout)
    #     layout.addWidget(connSelectCommbox)
    #     layout.setContentsMargins(1, 6, 0, 0)
    #     connectionWidgetWrapper = QWidget()
    #     layout2 = QVBoxLayout()
    #     layout2.setContentsMargins(0, 0, 0, 0)
    #     connectionWidgetWrapper.setLayout(layout2)
    #     layout.addWidget(connectionWidgetWrapper)
    #     if connectionWidget:
    #         layout2.addWidget(connectionWidget)
    #     settingLayout.addWidget(connSettingsGroupBox)
    #     #  other settings
    #     widget = plugin.onWidgetSettings(settingLayout)
    #     if not widget is None:
    #         settingLayout.addWidget(widget)
    #     settingLayout.setContentsMargins(0,0,0,0)

    #     # right functional layout
    #     functionalWidget = plugin.onWidgetFunctional(contentWidget)
    #     contentWidget.addWidget(settingWidget)
    #     contentWidget.addWidget(mainWidget)
    #     if not functionalWidget is None:
    #         contentWidget.addWidget(functionalWidget)
    #     contentWidget.setStretchFactor(0, 1)
    #     contentWidget.setStretchFactor(1, 2)
    #     contentWidget.setStretchFactor(2, 1)
    #     return contentWidget, connectionWidgetWrapper

    def add_new_window(self):
        import copy
        mainWindow = MainWindow(self.app, self.eventFilter, copy.deepcopy(self.config))
        self.eventFilter.listenWindow(mainWindow)
        g_all_windows.append(mainWindow)

    def macOsAddDockMenu(self):
        self.dockMenu = QMenu(self)
        self.dockMenu.addAction(_('New Window'),
                                self.add_new_window)
        self.dockMenu.setAsDockMenu()
        self.app.setAttribute(Qt.AA_DontShowIconsInMenus, True)

    def initEvent(self):
        # menu
        self.settingsButton.clicked.connect(self.toggleSettings)
        self.languageCombobox.currentIndexChanged.connect(self.onLanguageChanged)
        self.encodingCombobox.currentIndexChanged.connect(lambda: self.bindVar(self.encodingCombobox, self.config, "encoding"))
        self.functionalButton.clicked.connect(self.toggleFunctional)
        self.skinButton.clicked.connect(self.skinChange)
        self.aboutButton.clicked.connect(self.showAbout)
        # main
        self.tabWidget.currentChanged.connect(self.onSwitchTab)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        # others
        self.updateSignal.connect(self.showUpdate)
        self.hintSignal.connect(self.showHint)
        # self.statusBarSignal.connect(self.onstatusBarText)
        self.reloadWindowSignal.connect(self.onReloadWindow)
        # self.countUpdateSignal.connect(self.onUpdateCountUi)

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

    def onSwitchTab(self, idx):
        self.config["currItem"] = self.items[idx].name
        # log.i("switch to {}".format(self.items[idx].name))
        # remove from old container
        # parent = self.connectionWidget.parentWidget()
        # if parent:
        #     parent.layout().removeWidget(self.connectionWidget)
        # # add to new container
        # newParent = self.connParentWidgets[idx]
        # newParent.layout().addWidget(self.connectionWidget)
        # self.plugins[idx].onActive()
        # self.updateStyle(parent)
        # self.updateStyle(newParent)
        # self.activePlugin(self.plugins[idx])

    def closeTab(self, idx):
        # only one, ignore
        if self.tabWidget.count() == 1:
            return
        self.tabWidget.removeTab(idx)
        item = self.items.pop(idx)
        for _item in self.config["items"]:
            if _item["name"] == item.name:
                self.config["items"].remove(_item)
                break
        # # if conn widget in this plugin, remove conn widget
        # parent = self.connectionWidget.parentWidget()
        # if parent == self.connParentWidgets[idx]:
        #     parent.layout().removeWidget(self.connectionWidget)
        # # set config, set plugin as disabled
        # infos = self.config.basic["pluginsInfo"]
        # uid = self.tabWidgets[idx][1]
        # for id, info in infos["builtin"].items():
        #     if id == uid:
        #         info["enabled"] = False
        # for id, info in infos["external"].items():
        #     if id == uid:
        #         info["enabled"] = False
        # # remove plugin
        # self.connParentWidgets.pop(idx)
        # self.tabWidgets.pop(idx)

    # def changeConn(self, connection:object):
    #     # remove conn widget from the container
    #     parent = None
    #     if self.connectionWidget:
    #         parent = self.connectionWidget.parentWidget()
    #         parent.layout().removeWidget(self.connectionWidget)
    #         self.connectionWidget.setParent(None)
    #         self.updateStyle(parent)
    #     # add new conn widget to container
    #     self.connection = connection
    #     self.connectionWidget = connection.widget
    #     if not parent:
    #         parent = self.connParentWidgets[self.tabWidget.currentIndex()]
    #     parent.layout().addWidget(self.connectionWidget)
    #     self.updateStyle(parent)

    # def onConnChanged(self, idx):
    #     '''
    #         combobox changed item
    #     '''
    #     if self.changingConn:
    #         return
    #     self.changingConn = True
    #     # update all tab's connSelectCombobox widget show
    #     for w in self.connSelectComboboxes:
    #         w.setCurrentIndex(idx)
    #     # change connection
    #     print("-- change conn to", self.connections[idx].id)
    #     self.changeConn(self.connections[idx])
    #     self.config.basic["connId"] = self.connections[idx].id
    #     self.changingConn = False

    # def sendData(self, data_bytes=None, file_path=None, callback=lambda ok, msg:None):
    #     if data_bytes:
    #         self.dataToSend.insert(0, (data_bytes, callback))
    #     if file_path:
    #         self.fileToSend.insert(0, (file_path, callback))

    # def ctrlConn(self, k, v):
    #     if self.connection:
    #         self.connection.ctrl(k, v)

    # def onSent(self, data):
    #     self.sendCount += len(data)
    #     self.countUpdateSignal.emit(self.sendCount, self.receiveCount)

    # def onReceived(self, data):
    #     self.receiveCount += len(data)
    #     self.countUpdateSignal.emit(self.sendCount, self.receiveCount)
    #     # invoke plugin onReceived
    #     for plugin in self.connChilds:
    #         if plugin.active:
    #             plugin.onReceived(data)

    # def isConnected(self):
    #     return self.connection.isConnected()

    # def sendDataProcess(self):
    #     self.receiveProgressStop = False
    #     while(not self.receiveProgressStop):
    #         try:
    #             if not self.connection.isConnected():
    #                 time.sleep(0.001)
    #                 continue
    #             while len(self.dataToSend) > 0:
    #                 data, callback = self.dataToSend.pop()
    #                 self.connection.send(data)
    #                 self.onSent(data)
    #                 callback(True, "")
    #             while len(self.fileToSend) > 0:
    #                 file_path, callback = self.fileToSend.pop()
    #                 ok = False
    #                 if file_path and os.path.exists(file_path):
    #                     data = None
    #                     try:
    #                         with open(file_path, "rb") as f:
    #                             data = f.read()
    #                     except Exception as e:
    #                         self.hintSignal.emit("error", _("Error"), _("Open file failed!") + "\n%s\n%s" %(file_path, str(e)))
    #                     if data:
    #                         self.connection.send(data)
    #                         self.onSent(data)
    #                         ok = True
    #                 callback(ok, "")
    #             time.sleep(0.001)
    #         except Exception as e:
    #             import traceback
    #             traceback.print_exc()
    #             if 'multiple access' in str(e):
    #                 self.hintSignal.emit("error", _("Error"), "device disconnected or multiple access on port?")
    #             continue

    # def onUpdateCountUi(self, send, receive):
    #     self.statusBarSendCount.setText('{}({}): {}'.format(_("Sent"), _("bytes"), send))
    #     self.statusBarReceiveCount.setText('{}({}): {}'.format(_("Received"), _("bytes"), receive))

    # def onShowConnStatus(self, status, msg):
    #     if status == ConnectionStatus.CONNECTED:
    #         self.onstatusBarText("info", '{} {}'.format(_("Connected"), msg))
    #     elif status == ConnectionStatus.CLOSED:
    #         self.onstatusBarText("info", '{} {}'.format(_("Closed"), msg))
    #     elif status == ConnectionStatus.CONNECTING:
    #         self.onstatusBarText("info", '{} {}'.format(_("Connecting"), msg))
    #     elif status == ConnectionStatus.LOSE:
    #         self.onstatusBarText("warning", '{} {}'.format(_("Connection lose"), msg))
    #     else:
    #         self.onstatusBarText("warning", msg)
    #     for plugin in self.plugins:
    #         if plugin.active:
    #             plugin.onConnChanged(status, msg)

    # def onstatusBarText(self, msg_type, msg):
    #     if msg_type == "info":
    #         color = "#008200"
    #     elif msg_type == "warning":
    #         color = "#fb8c00"
    #     elif msg_type == "error":
    #         color = "#f44336"
    #     else:
    #         color = "#008200"
    #     text = '<font color={}>{}</font>'.format(color, msg)
    #     self.statusBarStauts.setText(text)

    def updateStyle(self, widget):
        self.frameWidget.style().unpolish(widget)
        self.frameWidget.style().polish(widget)
        self.frameWidget.update()

    def onLanguageChanged(self):
        idx = self.languageCombobox.currentIndex()
        locale = list(self.languages.keys())[idx]
        self.config["locale"] = locale
        i18n.set_locale(locale)
        reply = QMessageBox.question(self, _('Restart now?'),
                                     _("language changed to: ") + self.languages[self.config["locale"]] + "\n" + _("Restart software to take effect now?"), QMessageBox.Yes |
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

    # def onClearCount(self):
    #     self.receiveCount = 0
    #     self.sendCount = 0
    #     self.countUpdateSignal.emit(self.sendCount, self.receiveCount)

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
        if self.closeTimerId:
            event.accept()
            return
        print("----- close event")
        # reply = QMessageBox.question(self, 'Sure To Quit?',
        #                              "Are you sure to quit?", QMessageBox.Yes |
        #                              QMessageBox.No, QMessageBox.No)
        if 1: # reply == QMessageBox.Yes:
            self.receiveProgressStop = True
            # inform plugins
            # TODO: deinit all items
            # for p in self.plugins:
            #     p.onDel()
            # for c in self.connections:
            #     c.onDel()
            self.saveConfig()
            # actual exit after 500ms
            self.closeTimerId = self.startTimer(500)
            self.setWindowTitle(_("Closing ..."))
            self.titleBar.setTitle(_("Closing ..."))
            self.setEnabled(False)
            event.ignore()
        else:
            event.ignore()

    def timerEvent(self, e):
        log.i("Close window")
        self.killTimer(self.closeTimerId)
        self.close()

    def saveConfig(self):
        # print("save config:", self.config)
        self.config.save(parameters.configFilePath)
        print("save config compelte")

    def uiLoadConfigs(self):
        # language
        try:
            idx = list(self.languages.keys()).index(self.config["locale"])
        except Exception:
            idx = 0
        self.languageCombobox.setCurrentIndex(idx)
        # encoding
        self.encodingCombobox.setCurrentIndex(self.supportedEncoding.index(self.config["encoding"]))

    # def loadPluginList(self):
    #     # load disabled plugins name to plugin list
    #     infos = self.config.basic["pluginsInfo"]
    #     for id, info in infos["builtin"].items():
    #         if self.pluginsSelector.findText(f'{id} - ') < 0:
    #             self.pluginsSelector.insertItem(self.pluginsSelector.count() - 1, f'{id} - {builtinPlugins[id].name}')
    #     for id, info in infos["external"].items():
    #         if self.pluginsSelector.findText(f'{id} - ') < 0:
    #             c = self._importPlugin(info["path"], test = True)
    #             self.pluginsSelector.insertItem(self.pluginsSelector.count() - 1, f'{id} - {c.name}')

    def keyPressEvent(self, event):
        CustomTitleBarWindowMixin.keyPressEvent(self, event)
        item = self.getCurrentItem()
        item.onKeyPressEvent(event)

    def keyReleaseEvent(self,event):
        CustomTitleBarWindowMixin.keyReleaseEvent(self, event)
        item = self.getCurrentItem()
        item.onKeyReleaseEvent(event)

    def getCurrentItem(self):
        widget = self.tabWidget.currentWidget()
        for item in self.items:
            if item.widget == widget:
                return item

    def toggleSettings(self):
        widget = self.getCurrentItem().settingWidget
        if widget.isVisible():
            self.hideSettings()
        else:
            self.showSettings()

    def showSettings(self):
        widget = self.getCurrentItem().settingWidget
        widget.show()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath",self.DataPath))

    def hideSettings(self):
        widget = self.getCurrentItem().settingWidget
        widget.hide()
        self.settingsButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath", self.DataPath))

    def toggleFunctional(self):
        widget = self.getCurrentItem().functionalWidget
        if widget is None:
            return
        if widget.isVisible():
            self.hideFunctional()
        else:
            self.showFunctional()

    def showFunctional(self):
        widget = self.getCurrentItem().functionalWidget
        if not widget is None:
            widget.show()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonRight.replace("$DataPath",self.DataPath))

    def hideFunctional(self):
        widget = self.getCurrentItem().functionalWidget
        if not widget is None:
            widget.hide()
        self.functionalButton.setStyleSheet(
            parameters.strStyleShowHideButtonLeft.replace("$DataPath", self.DataPath))

    def skinChange(self):
        if self.config["skin"] == "light": # light
            file = open(self.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
            self.config["skin"] = "dark"
        else: # elif self.config["skin"] == 2: # dark
            file = open(self.DataPath + '/assets/qss/style.qss', "r", encoding="utf-8")
            self.config["skin"] = "light"
        self.app.setStyleSheet(file.read().replace("$DataPath", self.DataPath))
        utils_ui.setSkin(self.config["skin"])

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

class Splash(QSplashScreen):
    '''
        show splash when window is loading
    '''
    def __init__(self, app) -> None:
        super().__init__(QPixmap(os.path.join(parameters.assetsDir, "logo.png")))
        self.app = app
        self.exit = False
        self.show()
        t = threading.Thread(target=self._processEventsProcess)
        t.setDaemon(True)
        t.start()

    def event(self, e):
        if type(e) == QCloseEvent:
            self.exit = True
        return super().event(e)

    def finish(self, w):
        self.exit = True
        return super().finish(w)

    def _processEventsProcess(self):
        while not self.exit:
            self.app.processEvents()
            time.sleep(0.001)


def main():
    '''
        @retval None: need restart
                0: exit ok
                others: exit error
    '''
    ret = 1
    try:
        # check translate
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        log.i("curr_dir   ", curr_dir)
        mo_path = os.path.join(curr_dir, "locales", "en", "LC_MESSAGES", "messages.mo")
        if not os.path.exists(mo_path):
            gen_tranlate_files(curr_dir)
        app = QApplication(sys.argv)
        splash = Splash(app)
        eventFilter = EventFilter()
        mainWindow = MainWindow(app, eventFilter, programConfig)
        eventFilter.listenWindow(mainWindow)
        app.installEventFilter(eventFilter)
        g_all_windows.append(mainWindow)
        # path = os.path.join(mainWindow.DataPath, "assets", "fonts", "JosefinSans-Regular.ttf")
        # load_fonts([path])
        log.i("data path:"+mainWindow.DataPath)
        if(mainWindow.config["skin"] == "light") :# light skin
            file = open(mainWindow.DataPath+'/assets/qss/style.qss',"r", encoding="utf-8")
        else: #elif mainWindow.config == "dark": # dark skin
            file = open(mainWindow.DataPath + '/assets/qss/style-dark.qss', "r", encoding="utf-8")
        qss = file.read().replace("$DataPath",mainWindow.DataPath)
        app.setStyleSheet(qss)
        t = threading.Thread(target=mainWindow.autoUpdateDetect)
        t.setDaemon(True)
        t.start()
        splash.finish(mainWindow)
        ret = app.exec_()
        if mainWindow.needRestart:
            ret = None
        else:
            app.removeEventFilter(eventFilter)
            print("-- no need to restart, now exit")
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



