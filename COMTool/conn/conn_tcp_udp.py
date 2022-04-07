
from os import remove
from PyQt5.QtCore import pyqtSignal,Qt, QRect, QMargins, QObject, pyqtSlot, QRegExp
from PyQt5.QtWidgets import (QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea)
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap,QColor, QRegExpValidator
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
    name = "TCP UDP"
    showSwitchSignal = pyqtSignal(ConnectionStatus)
    updateTargetSignal = pyqtSignal(str)
    updateClientsSignal = pyqtSignal(bool, tuple)
    def onInit(self, config):
        self.conn = None
        self.config = config
        default = {
            "protocol" : "tcp",
            "mode" : "client",
            "target" : ["127.0.0.1:2345", ["127.0.0.1:2345"]],
            "port": 2345,
            "auto_reconnect": False,
            "auto_reconnect_interval": 1.0
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.widgetConfMap = {
            "protocol" : None,
            "mode" : None,
            "target" : None,
            "port": None,
            "auto_reconnect": None,
            "auto_reconnect_interval": None
        }
        self.isOpened = False
        self.busy = False
        self.status = ConnectionStatus.CLOSED
        self.widget = None
        self.serverModeClientsConns = {
            # "127.0.0.1:76534": conn
        }
        self.serverModeSelectedClient = None # None means all clients, or ip:port string

    def disconnect(self):
        if self.isConnected():
            self.openCloseSerial()

    def onDel(self):
        if self.isConnected():
            self.openCloseSerial()

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
        self.serialSettingsLayout = QGridLayout()
        protocolLabel = QLabel(_("Protocol"))
        self.modeLabel = QLabel(_("Mode"))
        self.targetLabel = QLabel(_("Target"))
        self.targetCombobox = ComboBox()
        self.targetCombobox.setEditable(True)
        self.portLabel = QLabel(_("Port"))
        self.portLabel.hide()
        self.porttEdit = QLineEdit()
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
        self.clientsCombobox = ComboBox()
        self.clientsCombobox.addItem("0 | " + _("All clients"))
        self.disconnetClientBtn = QPushButton(_("Disconnect"))
        self.autoReconnetLable = QLabel(_("Auto reconnect"))
        self.autoReconnect = QCheckBox()
        self.autoReconnectIntervalEdit = QLineEdit("1.0")
        self.serialOpenCloseButton = QPushButton(_("OPEN"))
        self.serialSettingsLayout.addWidget(protocolLabel,0,0)
        self.serialSettingsLayout.addWidget(protocolWidget, 0, 1, 1, 2)
        self.serialSettingsLayout.addWidget(self.modeLabel, 1, 0)
        self.serialSettingsLayout.addWidget(modeWidget, 1, 1, 1, 2)
        self.serialSettingsLayout.addWidget(self.targetLabel, 2, 0)
        self.serialSettingsLayout.addWidget(self.targetCombobox, 2, 1, 1, 2)
        self.serialSettingsLayout.addWidget(self.portLabel, 3, 0)
        self.serialSettingsLayout.addWidget(self.porttEdit, 3, 1, 1, 2)
        self.serialSettingsLayout.addWidget(self.clientsCombobox, 4, 0, 1, 2)
        self.serialSettingsLayout.addWidget(self.disconnetClientBtn, 4, 2, 1, 1)
        self.serialSettingsLayout.addWidget(self.autoReconnetLable, 5, 0, 1, 1)
        self.serialSettingsLayout.addWidget(self.autoReconnect, 5, 1, 1, 1)
        self.serialSettingsLayout.addWidget(self.autoReconnectIntervalEdit, 5, 2, 1, 1)
        self.serialSettingsLayout.addWidget(self.serialOpenCloseButton, 6, 0, 1, 3)
        serialSetting.setLayout(self.serialSettingsLayout)
        self.widgetConfMap["protocol"]       = self.protoclTcpRadioBtn
        self.widgetConfMap["mode"]    = self.modeClientRadioBtn
        self.widgetConfMap["target"]    = self.targetCombobox
        self.widgetConfMap["port"]    = self.porttEdit
        self.widgetConfMap["auto_reconnect"] = self.autoReconnect
        self.widgetConfMap["auto_reconnect_interval"] = self.autoReconnectIntervalEdit
        self.initEvet()
        self.widget = serialSetting
        return serialSetting

    def initEvet(self):
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.porttEdit.textChanged.connect(self.onPortChanged)
        self.showSwitchSignal.connect(self.showSwitch)
        self.updateTargetSignal.connect(self.updateTarget)
        self.updateClientsSignal.connect(self.updateClients)
        self.protoclTcpRadioBtn.clicked.connect(lambda: self.changeProtocol("tcp"))
        self.protoclUdpRadioBtn.clicked.connect(lambda: self.changeProtocol("udp"))
        self.modeServerRadioBtn.clicked.connect(lambda: self.changeMode("server"))
        self.modeClientRadioBtn.clicked.connect(lambda: self.changeMode("client"))
        self.clientsCombobox.currentIndexChanged.connect(self.serverModeClientChanged)
        self.disconnetClientBtn.clicked.connect(self.serverModeDisconnectClient)
        self.autoReconnect.stateChanged.connect(lambda x: self.setVar("auto_reconnect", value = x))
        self.autoReconnectIntervalEdit.textChanged.connect(lambda: self.setVar("auto_reconnect_interval"))
        self.targetCombobox.currentTextChanged.connect(self.onTargetChanged)

    def changeProtocol(self, protocol, init=False):
        if init or protocol != self.config["protocol"]:
            if self.isConnected():
                self.openCloseSerial()
            if protocol == "tcp":
                self.modeClientRadioBtn.show()
                self.modeServerRadioBtn.show()
                self.modeLabel.show()
                self.changeMode(self.config["mode"], init=True)
            else:
                self.targetCombobox.show()
                self.targetLabel.show()
                self.porttEdit.show()
                self.portLabel.show()
                self.clientsCombobox.hide()
                self.disconnetClientBtn.hide()
                self.autoReconnect.hide()
                self.autoReconnectIntervalEdit.hide()
                self.autoReconnetLable.hide()
                self.modeClientRadioBtn.hide()
                self.modeServerRadioBtn.hide()
                self.modeLabel.hide()
                self.widget.adjustSize()
            self.config["protocol"] = protocol

    def changeMode(self, mode, init=False):
        if init or mode != self.config["mode"]:
            if self.isConnected():
                self.openCloseSerial()
            if mode == "server":
                self.targetCombobox.hide()
                self.targetLabel.hide()
                self.porttEdit.show()
                self.portLabel.show()
                self.clientsCombobox.show()
                self.disconnetClientBtn.show()
                self.autoReconnect.hide()
                self.autoReconnectIntervalEdit.hide()
                self.autoReconnetLable.hide()
            else:
                self.targetCombobox.show()
                self.targetLabel.show()
                self.porttEdit.hide()
                self.portLabel.hide()
                self.clientsCombobox.hide()
                self.disconnetClientBtn.hide()
                self.autoReconnect.show()
                self.autoReconnectIntervalEdit.show()
                self.autoReconnetLable.show()
            self.widget.adjustSize()
            self.config["mode"] = mode

    def onTargetChanged(self):
        text = self.targetCombobox.currentText()
        self.config["target"][0] = text

    def updateTarget(self, new):
        idx = self.targetCombobox.findText(new)
        if idx < 0:
            self.targetCombobox.addItem(new)
            self.config["target"][1].append(new)
        self.targetCombobox.setEditText(new)
        self.config["target"][0] = new

    def updateClients(self, add:bool, addr:tuple):
        host, port = addr
        if add:
            self.clientsCombobox.addItem(f'{host}:{port}')
        else:
            idx = self.clientsCombobox.findText(f'{host}:{port}')
            if idx > 0:
                self.clientsCombobox.removeItem(idx)
        self.clientsCombobox.setItemText(0, "{} | ".format(self.clientsCombobox.count() - 1) + _("All clients"))

    def serverModeClientChanged(self):
        if self.clientsCombobox.currentIndex() == 0:
            self.serverModeSelectedClient = None
        else:
            self.serverModeSelectedClient = self.clientsCombobox.currentText()

    def serverModeDisconnectClient(self):
        if not self.serverModeSelectedClient:
            for addr, conn in self.serverModeClientsConns.items():
                try:
                    conn.close()
                except Exception:
                    pass
        else:
            conn = self.serverModeClientsConns[self.serverModeSelectedClient]
            try:
                conn.close()
            except Exception:
                pass

    def onPortChanged(self):
        text = self.porttEdit.text()
        while 1:
            try:
                port = int(text)
                break
            except Exception:
                text = text[:-1]
        self.porttEdit.setText(text)

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
                self.changeMode("client", init=True)
            else:
                obj.setChecked(False)
                self.modeServerRadioBtn.setChecked(True)
                self.changeMode("server", init=True)
        elif conf_type == "target":
            for i, target in enumerate(self.config["target"][1]):
                self.targetCombobox.addItem(target)
            self.targetCombobox.setCurrentText(self.config["target"][0])
        elif conf_type == "port":
            obj.setText(str(value))
        elif conf_type == "auto_reconnect":
            obj.setChecked(value)
        elif conf_type == "auto_reconnect_interval":
            obj.setText("%.3f" %(value))

    def setVar(self, key, value = None):
        if key == "auto_reconnect":
            self.config[key] = value
        elif key == "auto_reconnect_interval":
            text = self.autoReconnectIntervalEdit.text()
            try:
                interval = float(text)
                self.config[key] = interval
            except Exception:
                text = "".join(re.findall('[\d\.]*', text))
                self.autoReconnectIntervalEdit.setText(text)

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
                    try:
                        self.conn.close()
                    except Exception:
                        pass
                    self.conn = None
                for k, conn in self.serverModeClientsConns.items():
                    try:
                        conn.close()
                    except Exception:
                        pass
            except Exception as e:
                print(e)
                pass
            self.onConnectionStatus.emit(self.status, "")
            self.showSwitchSignal.emit(self.status)
        else:
            try:
                if self.config["protocol"] == "tcp":
                    if self.config["mode"] == "client":
                        print("-- connect")
                        target = self.checkTarget(self.config["target"][0])
                        if not target:
                            raise Exception(_("Target error") + ": " + self.config["target"][0])
                        print("-- connect", target)
                        self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                        self.conn = socket.socket()
                        self.conn.connect(target)
                        self.status = ConnectionStatus.CONNECTED
                        print("-- connect success")
                        self.receiveProcess = threading.Thread(target=self.receiveDataProcess, args=(self.conn, ))
                        self.receiveProcess.setDaemon(True)
                        self.receiveProcess.start()
                    else:
                        print("-- server mode, wait client connect")
                        self.conn = socket.socket()
                        self.conn.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                        self.conn.bind(("0.0.0.0", self.config["port"]))
                        self.conn.listen(100)
                        self.status = ConnectionStatus.CONNECTED
                        self.waitClentsProcess = threading.Thread(target=self.waitClientsProcess)
                        self.waitClentsProcess.setDaemon(True)
                        self.waitClentsProcess.start()
                else:
                    print("-- UPD protocol")
                    self.conn = socket.socket(type=socket.SOCK_DGRAM)
                    self.conn.bind(("0.0.0.0", self.config["port"]))
                    self.status = ConnectionStatus.CONNECTED
                    self.receiveProcess = threading.Thread(target=self.receiveDataProcess, args=(self.conn, ))
                    self.receiveProcess.setDaemon(True)
                    self.receiveProcess.start()
                self.onConnectionStatus.emit(self.status, "")
                self.showSwitchSignal.emit(self.status)
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
        target = target.replace("：", ":")
        if target.endswith(":"):
            target = target[:-1]
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
        target_str = f'{host}:{port}'
        self.updateTargetSignal.emit(target_str)
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

    def waitClientsProcess(self):
        while self.status != ConnectionStatus.CLOSED:
            print("-- wait for client connect")
            try:
                conn, addr = self.conn.accept()
            except Exception as e:
                if self.status != ConnectionStatus.CLOSED:
                    print("-- accept connection fail:", str(e))
                continue
            print("-- client connected, ip:", addr)
            addr_str = f'{addr[0]}:{addr[1]}'
            self.updateClientsSignal.emit(True, addr)
            self.onConnectionStatus.emit(ConnectionStatus.CONNECTED, _("Client connected:") + " " + addr_str)
            self.serverModeClientsConns[addr_str] = conn
            t = threading.Thread(target=self.receiveDataProcess, args=(conn, addr))
            t.setDaemon(True)
            t.start()
        print("-- wait connection thread exit")


    def receiveDataProcess(self, conn, remote_addr:tuple = None):
        waitingReconnect = False
        buffer = b''
        t = 0
        conn.settimeout(0.1)
        protocolIsTcp = self.config["protocol"] == "tcp"
        modeIsServer = self.config["mode"] == "server"
        remoteStr = ""
        if remote_addr:
            remoteStr = f'{remote_addr[0]}:{remote_addr[1]}'
        while self.status != ConnectionStatus.CLOSED:
            if waitingReconnect:
                try:
                    target = self.checkTarget(self.config["target"][0])
                    if not target:
                        raise Exception(_("Target error") + ": " + self.config["target"][0])
                    self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                    conn = socket.socket()
                    conn.connect(target)
                    conn.settimeout(0.1)
                    self.conn = conn
                    print("-- reconnect")
                    waitingReconnect = False
                    self.onConnectionStatus.emit(ConnectionStatus.CONNECTED, _("Reconnected"))
                    self.showSwitchSignal.emit(ConnectionStatus.CONNECTED)
                    continue
                except Exception as e:
                    pass
                time.sleep(self.config["auto_reconnect_interval"])
                continue
            try:
                # length = max(1, self.conn.in_waiting)
                flush = True
                try:
                    if protocolIsTcp:
                        data = conn.recv(4096)
                        # ignore not selected target's msg
                        if modeIsServer and self.serverModeSelectedClient and (remoteStr != self.serverModeSelectedClient):
                            data = None
                    else:
                        data, target = conn.recvfrom(4096)
                    if data == b'': # closed by peer(peer send FIN, now we can close this connection)
                        if buffer:
                            self.onReceived(buffer)
                        raise Exception(_("Closed by peer"))
                except socket.timeout:
                    data = None
                if data:
                    if len(data) > 4096:
                        flush = False
                    t = time.time()
                    # if length == 1 and not buffer: # just start receive
                    #     buffer += data
                    #     continue
                    buffer += data
                if flush or (buffer and (time.time() - t > 0.001)): # no new data in 0.1ms
                    try:
                        self.onReceived(buffer)
                    except Exception as e:
                        print("-- error in onReceived callback:", e)
                    buffer = b''
            except Exception as e:
                print("-- recv error:", e, type(e))
                if modeIsServer or not self.config["auto_reconnect"]:
                    over = False
                    if protocolIsTcp and modeIsServer:
                        self.onConnectionStatus.emit(ConnectionStatus.CLOSED, _("Connection") + f' {remote_addr[0]}:{remote_addr[1]} ' + _("closed!"))
                        over = True
                    else:
                        self.status = ConnectionStatus.CLOSED
                        self.onConnectionStatus.emit(self.status, _("Connection closed!") + " " + str(e))
                        self.showSwitchSignal.emit(self.status)
                    try:
                        conn.close()
                    except Exception:
                        pass
                    if over:
                        break
                elif (self.status != ConnectionStatus.CLOSED):
                    # close as fast as we can to release port
                    try:
                        conn.close()
                    except Exception:
                        pass
                    waitingReconnect = True
                    self.onConnectionStatus.emit(ConnectionStatus.LOSE, _("Connection lose!"))
                    self.showSwitchSignal.emit(ConnectionStatus.LOSE)
                    time.sleep(self.config["auto_reconnect_interval"])
        # server mode remove client
        if self.config["mode"] == "server":
            remote_str = f'{remote_addr[0]}:{remote_addr[1]}'
            print(f"-- client {remote_str} disconnect")
            self.updateClientsSignal.emit(False, remote_addr)
            if remote_str == self.serverModeSelectedClient:
                self.serverModeSelectedClient = None
            self.serverModeClientsConns.pop(remote_str)
        print("-- receiveDataProcess exit")

    def send(self, data : bytes):
        if self.conn:
            if self.config["protocol"] == "tcp":
                if self.config["mode"] == "client":
                    self.conn.sendall(data)
                else:
                    if not self.serverModeSelectedClient:
                        for addr, conn in self.serverModeClientsConns.items():
                            conn.sendall(data)
                    else:
                        self.serverModeClientsConns[self.serverModeSelectedClient].sendall(data)
            else:
                target = self.checkTarget(self.config["target"][0])
                if not target:
                    self.hintSignal.emit("error", _("Target error"), _("Target error") + ": " + self.config["target"])
                self.conn.sendto(data, target)

    def isConnected(self):
        return self.status == ConnectionStatus.CONNECTED

