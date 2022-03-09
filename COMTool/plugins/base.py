
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
try:
    from Combobox import ComboBox
    from i18n import _
    import utils, parameters
except ImportError:
    from COMTool import utils, parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox

class Plugin_Base(QObject):
    '''
        call sequence:
            set vars like hintSignal, hintSignal
            onInit
            onWidget
            onUiInitDone
                send
                onReceived
            onDel
    '''
    # vars set by caller
    isConnected = lambda : False
    send = lambda x,y:None          # send(data_bytes=None, file_path=None, callback=lambda ok,msg:None)
    hintSignal = None               # hintSignal.emit(type(error, warning, info), title, msg)
    clearCountSignal = None         # clearCountSignal.emit()
    reloadWindowSignal = None       # reloadWindowSignal.emit(title, msg, callback(close or not)), reload window to load new configs
    configGlobal = {}
    # other vars
    connParent = "main"      # parent id
    connChilds = []          # children ids
    id = ""

    enabled = False          # user enabled this plugin
    active  = False          # using this plugin

    def __init__(self):
        super().__init__()
        if not self.id:
            raise ValueError(f"var id of Plugin {self} should be set")

    def onInit(self, config, plugins):
        '''
            init params, DO NOT take too long time in this func
            @config dict type, just change this var's content,
                               when program exit, this config will be auto save to config file
        '''
        self.config = config
        self.plugins = plugins
        self.plugins_info = {}
        for p in self.plugins:
            if p.id in self.connChilds:
                self.plugins_info[p.id] = p

    def onDel(self):
        pass

    def onWidgetMain(self, parent, rootWindow):
        raise NotImplementedError()

    def onWidgetSettings(self, parent):
        raise NotImplementedError()

    def onWidgetFunctional(self, parent):
        return None

    def onReceived(self, data : bytes):
        for id in self.connChilds:
            self.plugins_info[id].onReceived(data)

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
                            self.hintSignal.emit("error", _("Error"), _("Escape is on, but escape error:") + data[p : p+4])
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
                            self.hintSignal.emit("error", _("Error"), _("Escape is on, but escape error:") + data[p : p+4])
                            return b''
                    else:
                        r = data[p: p+2].encode(encoding, "ignore")
                        p += 2
                    final += r

                data = final
        return data

    def decodeReceivedData(self, data:bytes, encoding, isHexStr = False, escape=False):
        if isHexStr:
            data = utils.bytes_to_hex_str(data)
        elif escape:
            data = str(data)[2:-1] # b'1234\x01' => "b'1234\\x01'" =>"1234\\x01"
        else:
            data = data.decode(encoding=encoding, errors="ignore")
        return data
