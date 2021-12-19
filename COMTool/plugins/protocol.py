
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
try:
    from Combobox import ComboBox
    from i18n import _
except ImportError:
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
    connParent = "main"      # parent id
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

    def onWidgetMain(self, parent, rootWindow):
        self.mainWidget = QWidget()
        layout = QVBoxLayout()
        self.mainWidget.setLayout(layout)
        return self.mainWidget

    def onWidgetSettings(self, parent):
        self.settingsWidget = QWidget()
        layout = QVBoxLayout()
        self.settingsWidget.setLayout(layout)
        return self.settingsWidget

    def onWidgetFunctional(self, parent):
        self.funcWidget = QWidget()
        layout = QVBoxLayout()
        self.funcWidget.setLayout(layout)
        return self.funcWidget

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
        pass

    def sendData(self, data_bytes=None, file_path=None):
        self.send(data_bytes, file_path)

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


