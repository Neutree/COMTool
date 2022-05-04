
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
try:
    from Combobox import ComboBox
    from i18n import _
    import utils, parameters
    from conn.base import ConnectionStatus
    from widgets import statusBar
except ImportError:
    from COMTool import utils, parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox
    from COMTool.conn.base import  ConnectionStatus
    from COMTool.widgets import statusBar

class Plugin_Base(QObject):
    '''
        call sequence:
            set vars like hintSignal, hintSignal
            onInit
            onWidget
            onUiInitDone
            onActive
                send
                onReceived
            onDel
    '''
    # vars set by caller
    isConnected = lambda o: False
    send = lambda o,x,y:None          # send(data_bytes=None, file_path=None, callback=lambda ok,msg:None), can call in UI thread directly
    ctrlConn = lambda o,k,v:None      # call ctrl func of connection
    hintSignal = None               # hintSignal.emit(type(error, warning, info), title, msg)
    reloadWindowSignal = None       # reloadWindowSignal.emit(title, msg, callback(close or not)), reload window to load new configs
    configGlobal = {}
    # other vars
    connParent = "main"      # parent id
    connChilds = []          # children ids
    id = ""
    name = ""

    enabled = False          # user enabled this plugin
    active  = False          # using this plugin

    help = None                # help info, can be str or QWidget

    def __init__(self):
        super().__init__()
        if not self.id:
            raise ValueError(f"var id of Plugin {self} should be set")

    def onInit(self, config):
        '''
            init params, DO NOT take too long time in this func
            @config dict type, just change this var's content,
                               when program exit, this config will be auto save to config file
        '''
        self.config = config
        default = {
            "version": 1,
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]

    def onDel(self):
        pass

    def onConnChanged(self, status:ConnectionStatus, msg:str):
        '''
            call in UI thread, be carefully!!
        '''
        if status == ConnectionStatus.CONNECTED:
            self.statusBar.setMsg("info", '{} {}'.format(_("Connected"), msg))
        elif status == ConnectionStatus.CLOSED:
            self.statusBar.setMsg("info", '{} {}'.format(_("Closed"), msg))
        elif status == ConnectionStatus.CONNECTING:
            self.statusBar.setMsg("info", '{} {}'.format(_("Connecting"), msg))
        elif status == ConnectionStatus.LOSE:
            self.statusBar.setMsg("warning", '{} {}'.format(_("Connection lose"), msg))
        else:
            self.statusBar.setMsg("warning", msg)

    def onWidgetMain(self, parent):
        '''
            main widget, just return a QWidget object
        '''
        raise NotImplementedError()

    def onWidgetSettings(self, parent):
        '''
            setting widget, just return a QWidget object or None
        '''
        return None

    def onWidgetFunctional(self, parent):
        '''
            functional widget, just return a QWidget object or None
        '''
        return None

    def onWidgetStatusBar(self, parent):
        self.statusBar = statusBar(rxTxCount=False)
        return self.statusBar

    def onReceived(self, data : bytes):
        '''
            call in receive thread, not UI thread
        '''
        for plugin in self.connChilds:
            plugin.onReceived(data)

    def sendData(self, data:bytes):
        '''
            send data, chidren call send will invoke this function
            if you send data in this plugin, you can directly call self.send
        '''
        self.send(data)

    def onKeyPressEvent(self, event):
        pass

    def onKeyReleaseEvent(self, event):
        pass

    def onUiInitDone(self):
        '''
            UI init done, you can update your widget here
            this method runs in UI thread, do not block too long
        '''
        pass

    def onActive(self):
        '''
            plugin active
        '''
        pass

    def bindVar(self, uiObj, varObj, varName: str, vtype=None, vErrorMsg="", checkVar=lambda v:v, invert = False, emptyDefault = None):
        objType = type(uiObj)
        if objType == QCheckBox:
            v = uiObj.isChecked()
            varObj[varName] = v if not invert else not v
            return
        elif objType == QLineEdit:
            v = uiObj.text()
            if v == "" and emptyDefault is not None:
                v = emptyDefault
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

    def parseSendData(self, data:str, encoding, usrCRLF=False, isHexStr=False, escape=False):
        if not data:
            return b''
        if usrCRLF:
            data = data.replace("\n", "\r\n")
        if isHexStr:
            if usrCRLF:
                data = data.replace("\r\n", " ")
            else:
                data = data.replace("\n", " ")
            data = utils.hex_str_to_bytes(data)
            if data == -1:
                self.hintSignal.emit("error", _("Error"), _("Format error, should be like 00 01 02 03"))
                return b''
        else:
            if not escape:
                data = data.encode(encoding,"ignore")
            else: # '11234abcd\n123你好\r\n\thello\x00\x01\x02'
                try:
                    data = utils.str_to_bytes(data, escape=True, encoding=encoding)
                except Exception as e:
                    self.hintSignal.emit("error", _("Error"), _("Escape is on, but escape error:") + str(e))
                    return b''
        return data

    def decodeReceivedData(self, data:bytes, encoding, isHexStr = False, escape=False):
        if isHexStr:
            data = utils.bytes_to_hex_str(data)
        elif escape:
            data = str(data)[2:-1] # b'1234\x01' => "b'1234\\x01'" =>"1234\\x01"
        else:
            data = data.decode(encoding=encoding, errors="ignore")
        return data
