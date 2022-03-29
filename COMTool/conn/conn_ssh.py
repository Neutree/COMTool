
import os
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


class SSH_CONN:
    def __init__(self) -> None:
        self.channel = None

    def connect(self, host, port, user, password, ssh_key_file=None, pty_width=60, pty_height=20):
        print("-- ssh connect")
        if not password:
            password = None
        if not ssh_key_file:
            ssh_key_file = None
        import paramiko
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(host, port=port, username=user, password=password, key_filename=ssh_key_file)
        self.channel = self.client.get_transport().open_session()
        self.channel.get_pty(term="linux", width=pty_width, height=pty_height)
        self.channel.invoke_shell()

    def settimeout(self, timeout):
        pass

    def close(self):
        print("-- ssh disconnect")
        self.channel.close()

    def sendall(self, data:bytes):
        self.channel.send(data)

    def recv(self):
        if self.channel.recv_ready():
            data = self.channel.recv(4096)
            return data
        time.sleep(0.001)
        return None

    def isConnected(self):
        if not self.channel:
            return False
        return not self.channel.closed

    def resize(self, w, h):
        if self.channel:
            self.channel.resize_pty(width=w, height=h)


class SSH(COMM):
    '''
        call sequence:
            onInit
            onWidget
            onUiInitDone
                isConnected
                send
            getConfig
    '''
    id = "ssh"
    name = "SSH"
    showSwitchSignal = pyqtSignal(ConnectionStatus)
    connectSuccessSignal = pyqtSignal()
    def onInit(self, config):
        self.conn = None
        self.config = config
        default = {
            "host" : "127.0.0.1",
            "port" : 22,
            "user" : "root",
            "passwd": "",
            "ssh_key": "",
            "auto_reconnect": False,
            "saved": []
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.widgetConfMap = {
            "host" : None,
            "port" : None,
            "user" : None,
            "passwd": None,
            "ssh_key": None,
            "auto_reconnect": None,
            "saved": None
        }
        self.isOpened = False
        self.busy = False
        self.status = ConnectionStatus.CLOSED
        self.widget = None
        self.serverModeClientsConns = {
            # "127.0.0.1:76534": conn
        }
        self.serverModeSelectedClient = None # None means all clients, or ip:port string

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
            self.loadConfig(key, self.widgetConfMap[key], self.config[key])

    def onWidget(self):
        self.widget = QWidget()
        self.serialSettingsLayout = QGridLayout()
        hostLabel = QLabel(_("Host"))
        portLabel = QLabel(_("Port"))
        userLabel = QLabel(_("User"))
        passwdLabel = QLabel(_("Password"))
        sshKeyLabel = QLabel(_("SSH key"))
        savedLabel = QLabel(_("Saved"))
        self.hostInput = QLineEdit()
        self.portInput = QLineEdit()
        self.portInput.setInputMethodHints(Qt.ImhDigitsOnly | Qt.ImhLatinOnly | Qt.ImhPreferNumbers)
        self.userInput = QLineEdit()
        self.passwdInput = QLineEdit()
        self.passwdInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.sshKeyInput = QLineEdit()
        self.sshKeyInputBtn = QPushButton(_("File"))
        self.savedCombobox = ComboBox()
        self.serialOpenCloseButton = QPushButton(_("OPEN"))
        self.serialSettingsLayout.addWidget(hostLabel,0,0)
        self.serialSettingsLayout.addWidget(self.hostInput, 0, 1, 1, 2)
        self.serialSettingsLayout.addWidget(portLabel,1,0)
        self.serialSettingsLayout.addWidget(self.portInput, 1, 1, 1, 2)
        self.serialSettingsLayout.addWidget(userLabel,2,0)
        self.serialSettingsLayout.addWidget(self.userInput, 2, 1, 1, 2)
        self.serialSettingsLayout.addWidget(passwdLabel,3,0)
        self.serialSettingsLayout.addWidget(self.passwdInput, 3, 1, 1, 2)
        self.serialSettingsLayout.addWidget(sshKeyLabel,4,0)
        self.serialSettingsLayout.addWidget(self.sshKeyInput, 4, 1, 1, 1)
        self.serialSettingsLayout.addWidget(self.sshKeyInputBtn, 4, 2, 1, 1)
        self.serialSettingsLayout.addWidget(savedLabel,5,0)
        self.serialSettingsLayout.addWidget(self.savedCombobox, 5, 1, 1, 2)
        self.serialSettingsLayout.addWidget(self.serialOpenCloseButton, 6, 0, 1, 3)
        self.widget.setLayout(self.serialSettingsLayout)
        self.widgetConfMap["host"]          = self.hostInput
        self.widgetConfMap["port"]          = self.portInput
        self.widgetConfMap["user"]          = self.userInput
        self.widgetConfMap["passwd"]        = self.passwdInput
        self.widgetConfMap["ssh_key"]       = self.sshKeyInput
        self.widgetConfMap["auto_reconnect"]= None
        self.widgetConfMap["saved"]         = None
        self.initEvet()
        return self.widget

    def initEvet(self):
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.showSwitchSignal.connect(self.showSwitch)
        self.connectSuccessSignal.connect(self.saveConnectInfo)
        self.hostInput.textChanged.connect(lambda : self.inputChanged("host", self.hostInput))
        self.portInput.textChanged.connect(lambda : self.inputChanged("port", self.portInput, int))
        self.userInput.textChanged.connect(lambda : self.inputChanged("user", self.userInput))
        self.passwdInput.textChanged.connect(lambda : self.inputChanged("passwd", self.passwdInput))
        self.sshKeyInput.textChanged.connect(lambda : self.inputChanged("ssh_key", self.sshKeyInput))
        self.savedCombobox.activated.connect(self.loadSavedItem)
        self.sshKeyInputBtn.clicked.connect(self.selectSshKeyFile)

    def loadConfig(self, conf_type, obj, value):
        if conf_type in ["host", "port", "user", "ssh_key"]:
            obj.setText(str(value))
        elif conf_type == "saved":
            for v in value:
                item = '{}:{} - {}'.format(v["host"], v["port"], v["user"])
                self.savedCombobox.addItem(item)

    def loadSavedItem(self, idx):
        conf = self.config["saved"][idx]
        self.hostInput.setText(conf["host"])
        self.portInput.setText(str(conf["port"]))
        self.userInput.setText(conf["user"])
        self.sshKeyInput.setText(conf["ssh_key"])

    def inputChanged(self, conf_type, obj, convertType=str):
        try:
            self.config[conf_type] = convertType(obj.text().strip())
        except:
            self.hintSignal.emit("error", _("Input error"), _("Input") + f' {conf_type} ' + _("error"))

    def disconnect(self):
        if self.isConnected():
            self.openCloseSerial()

    def onDel(self):
        # remove passwd for safty
        self.config["passwd"] = ""
        if self.isConnected():
            self.openCloseSerial()

    def selectSshKeyFile(self):
        oldPath = self.sshKeyInputBtn.text()
        if oldPath=="":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self.widget,
                                    _("Select file"),
                                    oldPath,
                                    _("All Files (*)"))

        if fileName_choose == "":
            return
        self.sshKeyInput.setText(fileName_choose)

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
            except Exception as e:
                print(e)
                pass
            self.onConnectionStatus.emit(self.status, "")
            self.showSwitchSignal.emit(self.status)
        else:
            try:
                self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                self.checkAndConnect()
                self.status = ConnectionStatus.CONNECTED
                print("-- connect success")
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

    def checkAndConnect(self):
        print("-- connect")
        ok, msg = self.checkTarget(self.config)
        if not ok:
            raise Exception(_("Config error") + ": " + f'{self.config["host"]}:{self.config["port"]}' + ", " + msg)
        print("-- connect", f'{self.config["host"]}:{self.config["port"]}')
        self.conn = SSH_CONN()
        self.conn.connect(self.config["host"], self.config["port"], self.config["user"], self.config["passwd"], self.config["ssh_key"])
        self.connectSuccessSignal.emit()

    def saveConnectInfo(self):
        item = {
            "host": self.config["host"],
            "port": self.config["port"],
            "user": self.config["user"],
            "ssh_key": self.config["ssh_key"]
            }
        try:
            idx = self.config["saved"].index(item)
        except Exception:
            print(item, self.config["saved"])
            idx  = -1
        if idx >= 0:
            self.config["saved"].pop(idx)
            self.savedCombobox.removeItem(idx)
        self.config["saved"].append(item)
        item = '{}:{} - {}'.format(self.config["host"], self.config["port"], self.config["user"])
        self.savedCombobox.addItem(item)

    def checkTarget(self, config):
        if config["ssh_key"] and not os.path.exists(config["ssh_key"]):
            return False, _("SSH pub key file path error")
        return True, ""

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

    def receiveDataProcess(self, conn, remote_addr:tuple = None):
        waitingReconnect = False
        buffer = b''
        t = 0
        conn.settimeout(0.1)
        while self.status != ConnectionStatus.CLOSED:
            if waitingReconnect:
                try:
                    self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                    self.checkAndConnect()
                    conn = self.conn
                    conn.settimeout(0.1)
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
                try:
                    data = conn.recv()
                except socket.timeout:
                    data = None
                if data:
                    t = time.time()
                    # if length == 1 and not buffer: # just start receive
                    #     buffer += data
                    #     continue
                    buffer += data
                closed = not self.conn.isConnected()
                if buffer and (closed or (time.time() - t > 0.001)): # no new data in 1ms
                    try:
                        self.onReceived(buffer)
                    except Exception as e:
                        print("-- error in onReceived callback:", e)
                    buffer = b''
                if closed:
                    raise Exception(_("Closed by peer"))
            except Exception as e:
                print("-- recv error:", e, type(e), time.time())
                if not self.config["auto_reconnect"]:
                    self.status = ConnectionStatus.CLOSED
                    self.onConnectionStatus.emit(self.status, _("Connection closed!") + " " + str(e))
                    self.showSwitchSignal.emit(self.status)
                    try:
                        conn.close()
                    except Exception:
                        pass
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
        print("-- receiveDataProcess exit")

    def send(self, data : bytes):
        if self.conn:
            self.conn.sendall(data)

    def isConnected(self):
        return self.status == ConnectionStatus.CONNECTED

    def ctrl(self, k, v):
        if not self.conn:
            return
        if k == "resize":
            w, h = v
            self.conn.resize(w, h)


