
from PyQt5.QtCore import pyqtSignal,Qt, QRect, QMargins, QObject, pyqtSlot
from PyQt5.QtWidgets import (QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor
try:
    import parameters,helpAbout,autoUpdate
    from Combobox import ComboBox
    import i18n
    from i18n import _
    import version
    import utils
except ImportError:
    from COMTool import parameters,helpAbout,autoUpdate, utils
    from COMTool.Combobox import ComboBox
    from COMTool import i18n
    from COMTool.i18n import _
    from COMTool import version
try:
    from base import COMM, ConnectionStatus
except Exception:
    from .base import COMM, ConnectionStatus
import socket, threading, time, re




class TCP_UDP(COMM):
    '''
        call sequence:
            onInit
            onWidget
            onUiInitDone
                isConnected
                send
            getConfig
    '''
    id = "tcp_udp"
    showSwitchSignal = pyqtSignal(ConnectionStatus)
    updateTargetSignal = pyqtSignal(str)
    def onInit(self, config):
        self.conn = None
        self.config = config
        default = {
            "protocol" : "tcp",
            "mode" : "client",
            "target" : "127.0.0.1:3456",
            "auto_reconnect": False
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.widgetConfMap = {
            "protocol" : None,
            "mode" : None,
            "target" : None,
            "auto_reconnect": None
        }
        self.isOpened = False
        self.busy = False
        self.status = ConnectionStatus.CLOSED
        self.widget = None

    def __del__(self):
        try:
            self.status = ConnectionStatus.CLOSED
            if not self.conn is None:
                self.conn.close()
                self.conn = None
        except Exception:
            pass
        time.sleep(0.05)  # wait for child threads, not wait also ok, cause child threads are daemon

    def getConfig(self):
        '''
            get config, dict type
        '''
        return self.config

    def onUiInitDone(self):
        for key in self.config:
            self.setSerialConfig(key, self.widgetConfMap[key], self.config[key])

    def onWidget(self):
        serialSetting = QWidget()
        serialSettingsLayout = QGridLayout()
        protocolLabel = QLabel(_("Protocol"))
        modeLabel = QLabel(_("Mode"))
        self.targetLabel = QLabel(_("Target"))
        self.targetEdit = QLineEdit()
        protocolWidget = QWidget()
        modeWidget = QWidget()
        layoutProtocol = QHBoxLayout()
        layoutMode = QHBoxLayout()
        protocolWidget.setLayout(layoutProtocol)
        modeWidget.setLayout(layoutMode)
        self.protoclTcpRadioBtn = QRadioButton("TCP")
        self.protoclUdpRadioBtn = QRadioButton("UDP")
        self.protoclTcpRadioBtn.setChecked(True)
        layoutProtocol.addWidget(self.protoclTcpRadioBtn)
        layoutProtocol.addWidget(self.protoclUdpRadioBtn)
        self.modeClientRadioBtn = QRadioButton("Client")
        self.modeServerRadioBtn = QRadioButton("Server")
        self.modeClientRadioBtn.setChecked(True)
        layoutMode.addWidget(self.modeClientRadioBtn)
        layoutMode.addWidget(self.modeServerRadioBtn)
        self.autoReconnect = QCheckBox(_("Auto reconnect"))
        self.serialOpenCloseButton = QPushButton(_("OPEN"))
        serialSettingsLayout.addWidget(protocolLabel,0,0)
        serialSettingsLayout.addWidget(modeLabel, 1, 0)
        serialSettingsLayout.addWidget(self.targetLabel, 2, 0)
        serialSettingsLayout.addWidget(self.targetEdit, 2, 1, 1, 2)
        serialSettingsLayout.addWidget(protocolWidget, 0, 1, 1, 2)
        serialSettingsLayout.addWidget(modeWidget, 1, 1, 1, 2)
        serialSettingsLayout.addWidget(self.autoReconnect, 3, 0, 1, 3)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 4, 0, 1, 3)
        serialSetting.setLayout(serialSettingsLayout)
        self.widgetConfMap["protocol"]       = self.protoclTcpRadioBtn
        self.widgetConfMap["mode"]    = self.modeClientRadioBtn
        self.widgetConfMap["target"]    = self.targetEdit
        self.widgetConfMap["auto_reconnect"] = self.autoReconnect
        self.initEvet()
        self.widget = serialSetting
        return serialSetting

    def initEvet(self):
        # self.protoclTcpRadioBtn.clicked.connect(lambda: self.onSerialConfigChanged("rts", self.checkBoxRTS, bool))
        # self.checkBoxDTR.clicked.connect(lambda: self.onSerialConfigChanged("dtr", self.checkBoxDTR, bool))
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.targetEdit.textChanged.connect(self.onTargetChanged)
        self.showSwitchSignal.connect(self.showSwitch)
        self.updateTargetSignal.connect(self.updateTarget)
        self.modeServerRadioBtn.clicked.connect(lambda: self.changeMode("server"))
        self.modeClientRadioBtn.clicked.connect(lambda: self.changeMode("client"))

    def changeMode(self, mode):
        if mode != self.config["mode"]:
            if self.isConnected():
                self.openCloseSerial()
            if mode == "server":
                self.targetEdit.hide()
                self.targetLabel.hide()
            else:
                self.targetEdit.show()
                self.targetLabel.show()
            self.config["mode"] = mode

    def onTargetChanged(self):
        text = self.targetEdit.text()
        # correct chinese ： to english :
        if text.endswith("："):
            text = text[:-1] + ":"
        self.targetEdit.setText(text)
        self.config["target"] = text

    def updateTarget(self, new):
        self.targetEdit.setText(new)

    def onSerialConfigChanged(self, conf_type, obj, value_type, caller=""):
        pass

    def setSerialConfig(self, conf_type, obj, value):
        if conf_type == "protocol":
            if value == "tcp":
                obj.setChecked(True)
            else:
                obj.setChecked(False)
        elif conf_type == "mode":
            if value == "client":
                obj.setChecked(True)
            else:
                obj.setChecked(False)
        elif conf_type == "target":
            obj.setText(value)
        elif conf_type == "auto_reconnect":
            obj.setChecked(value)

    def openCloseSerial(self):
        if self.busy:
            return
        self.busy = True
        if self.serialOpenCloseButton.text() == _("OPEN"):
            self.isOpened = False
        else:
            self.isOpened = True
        t = threading.Thread(target=self.openCloseSerialProcess)
        t.setDaemon(True)
        t.start()

    def openCloseSerialProcess(self):
        if self.isOpened:
            print("-- disconnect")
            try:
                # set status first to prevent auto reconnect
                self.status = ConnectionStatus.CLOSED
                if not self.conn is None:
                    time.sleep(0.1) # wait receive thread exit
                    self.conn.close()
                    self.conn = None
            except Exception as e:
                print(e)
                pass
            self.onConnectionStatus.emit(self.status, "")
            self.showSwitchSignal.emit(self.status)
        else:
            try:
                print("-- connect")
                target = self.checkTarget(self.config["target"])
                if not target:
                    raise Exception(_("Target error" + ": " + self.config["target"]))
                self.updateTargetSignal.emit(f'{target[0]}:{target[1]}')
                print("-- connect", target)
                self.conn = socket.socket()
                self.conn.connect(target)
                self.conn.settimeout(0.1)
                print("-- connect success")
                self.status = ConnectionStatus.CONNECTED
                self.onConnectionStatus.emit(self.status, "")
                self.showSwitchSignal.emit(self.status)
                self.receiveProcess = threading.Thread(target=self.receiveDataProcess)
                self.receiveProcess.setDaemon(True)
                self.receiveProcess.start()
            except Exception as e:
                print("----", e)
                try:
                    self.conn.close()
                    self.conn = None
                except Exception:
                    pass
                msg = _("Connect Failed") +"\n"+ str(e)
                self.hintSignal.emit("error", _("Error"), msg)
                self.status = ConnectionStatus.CLOSED
                self.onConnectionStatus.emit(self.status, msg)
                self.showSwitchSignal.emit(self.status)
        self.busy = False

    def checkTarget(self, target):
        if not target:
            return None
        host = target
        port = 80
        _host = re.match('http(.*)://(.*)', target)
        if _host:
            s, target = _host.groups()
            host = target
        _host = re.match('(.*):(\d*)', target)
        if _host:
            host, port = _host.groups()
            port = int(port)
        if host.endswith("/"):
            host = host[:-1]
        target = (host, port)
        return target

    # @pyqtSlot(ConnectionStatus)
    def showSwitch(self, status):
        if status == ConnectionStatus.CLOSED:
            self.serialOpenCloseButton.setText(_("OPEN"))
            self.serialOpenCloseButton.setProperty("class", "")
        elif status == ConnectionStatus.CONNECTED:
            self.serialOpenCloseButton.setText(_("CLOSE"))
            self.serialOpenCloseButton.setProperty("class", "")
        else:
            self.serialOpenCloseButton.setText(_("CLOSE"))
            self.serialOpenCloseButton.setProperty("class", "warning")
        self.updateStyle(self.serialOpenCloseButton)

    def updateStyle(self, widget):
        self.widget.style().unpolish(widget)
        self.widget.style().polish(widget)
        self.widget.update()


    def receiveDataProcess(self):
        waitingReconnect = False
        buffer = b''
        t = 0
        while self.status != ConnectionStatus.CLOSED:
            if waitingReconnect:
                try:
                    self.conn = socket.socket()
                    self.conn.connect()
                    self.conn.settimeout(0.1)
                    print("-- reconnect")
                    waitingReconnect = False
                    self.onConnectionStatus.emit(ConnectionStatus.CONNECTED, _("Reconnected"))
                    self.showSwitchSignal.emit(ConnectionStatus.CONNECTED)
                    continue
                except Exception as e:
                    pass
                time.sleep(0.01)
                continue
            try:
                # length = max(1, self.conn.in_waiting)
                try:
                    data = self.conn.recv(4096)
                    if data == b'': # closed by peer(peer send FIN, now we can close this connection)
                        if buffer:
                            self.onReceived(buffer)
                        raise Exception(_("Closed by peer"))
                except socket.timeout:
                    data = None
                if data:
                    t = time.time()
                    # if length == 1 and not buffer: # just start receive
                    #     buffer += data
                    #     continue
                    buffer += data
                if buffer and (time.time() - t > 0.001): # no new data in 1ms
                    try:
                        self.onReceived(buffer)
                    except Exception as e:
                        print("-- error in onReceived callback:", e)
                    buffer = b''
            except Exception as e:
                print("-- recv error:", e, type(e))
                if not self.config["auto_reconnect"]:
                    self.status = ConnectionStatus.CLOSED
                    self.onConnectionStatus.emit(self.status, _("Connection closed!") + " " + str(e))
                    self.showSwitchSignal.emit(self.status)
                    try:
                        self.conn.close()
                    except Exception:
                        pass
                elif (self.status != ConnectionStatus.CLOSED):
                    # close as fast as we can to release port
                    try:
                        self.conn.close()
                    except Exception:
                        pass
                    waitingReconnect = True
                    self.onConnectionStatus.emit(ConnectionStatus.LOSE, _("Connection lose!"))
                    self.showSwitchSignal.emit(ConnectionStatus.LOSE)
        print("-- receiveDataProcess exit")

    def send(self, data : bytes):
        if self.conn:
            self.conn.sendall(data)

    def isConnected(self):
        return self.status == ConnectionStatus.CONNECTED

