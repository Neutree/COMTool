
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
import serial, threading, time
import serial.tools.list_ports




class Serial(COMM):
    '''
        call sequence:
            onInit
            onWidget
            onUiInitDone
                isConnected
                send
            getConfig
    '''
    id = "serial"
    name = _("Serial")
    showSerialComboboxSignal = pyqtSignal(list)
    showSwitchSignal = pyqtSignal(ConnectionStatus)
    def onInit(self, config):
        self.com = serial.Serial()
        self.config = config
        default = {
            "port" : None,
            "baudrate" : 115200,
            "bytesize" : 8,
            "parity" : "None",
            "stopbits" : "1",
            "flowcontrol" : "None",
            "rts" : False,
            "dtr" : False,
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.widgetConfMap = {
            "port" : None,
            "baudrate" : None,
            "bytesize" : None,
            "parity" : None,
            "stopbits" : None,
            "flowcontrol" : None,
            "rts" : None,
            "dtr" : None,
        }
        self.isOpened = False
        self.busy = False
        self.status = ConnectionStatus.CLOSED
        self.isDetectSerialPort = False
        self.widget = None
        self.baudrateCustomStr = _("Custom, input baudrate")

    def disconnect(self):
        if self.isConnected():
            self.openCloseSerial()

    def onDel(self):
        if self.isConnected():
            self.openCloseSerial()

    def __del__(self):
        try:
            self.com.close()
            self.status = ConnectionStatus.CLOSED
            time.sleep(0.05)  # wait for child threads, not wait also ok, cause child threads are daemon
        except Exception:
            pass

    def getConfig(self):
        '''
            get config, dict type
        '''
        return self.config

    def onUiInitDone(self):
        for key in self.config:
            self.setSerialConfig(key, self.widgetConfMap[key], self.config[key])
        self.detectSerialPort()

    def onWidget(self):
        self.widget = QWidget()
        serialSettingsLayout = QGridLayout()
        serialPortLabek = QLabel(_("Port"))
        serailBaudrateLabel = QLabel(_("Baudrate"))
        serailBytesLabel = QLabel(_("DataBytes"))
        serailParityLabel = QLabel(_("Parity"))
        serailStopbitsLabel = QLabel(_("Stopbits"))
        serialFlowControlLabel = QLabel(_("Flow control"))
        self.serialPortCombobox = ComboBox()
        self.serailBaudrateCombobox = ComboBox()
        for baud in parameters.defaultBaudrates:
            self.serailBaudrateCombobox.addItem(str(baud))
        self.serailBaudrateCombobox.addItem(self.baudrateCustomStr)
        self.serailBaudrateCombobox.setCurrentIndex(5)
        self.serailBaudrateCombobox.setEditable(True)
        self.serailBytesCombobox = ComboBox()
        self.serailBytesCombobox.addItem("5")
        self.serailBytesCombobox.addItem("6")
        self.serailBytesCombobox.addItem("7")
        self.serailBytesCombobox.addItem("8")
        self.serailBytesCombobox.setCurrentIndex(3)
        self.serailParityCombobox = ComboBox()
        self.serailParityCombobox.addItem("None")
        self.serailParityCombobox.addItem("Odd")
        self.serailParityCombobox.addItem("Even")
        self.serailParityCombobox.addItem("Mark")
        self.serailParityCombobox.addItem("Space")
        self.serailParityCombobox.setCurrentIndex(0)
        self.serailStopbitsCombobox = ComboBox()
        self.serailStopbitsCombobox.addItem("1")
        self.serailStopbitsCombobox.addItem("1.5")
        self.serailStopbitsCombobox.addItem("2")
        self.serailStopbitsCombobox.setCurrentIndex(0)
        self.serialFlowControlCombobox = ComboBox()
        self.serialFlowControlCombobox.addItem("None")
        self.serialFlowControlCombobox.addItem("XON/XOFF")
        self.serialFlowControlCombobox.addItem("RTS/CTS")
        self.serialFlowControlCombobox.addItem("DSR/DTR")
        self.serialFlowControlCombobox.setCurrentIndex(0)
        self.checkBoxRTS = QCheckBox("rts")
        self.checkBoxDTR = QCheckBox("dtr")
        self.checkBoxRTS.setToolTip(_("Check to enable(usually output low level)"))
        self.checkBoxDTR.setToolTip(_("Check to enable(usually output low level)"))
        self.serialOpenCloseButton = QPushButton(_("OPEN"))
        serialSettingsLayout.addWidget(serialPortLabek,0,0)
        serialSettingsLayout.addWidget(serailBaudrateLabel, 1, 0)
        serialSettingsLayout.addWidget(serailBytesLabel, 2, 0)
        serialSettingsLayout.addWidget(serailParityLabel, 3, 0)
        serialSettingsLayout.addWidget(serailStopbitsLabel, 4, 0)
        serialSettingsLayout.addWidget(serialFlowControlLabel, 5, 0)
        serialSettingsLayout.addWidget(self.serialPortCombobox, 0, 1)
        serialSettingsLayout.addWidget(self.serailBaudrateCombobox, 1, 1)
        serialSettingsLayout.addWidget(self.serailBytesCombobox, 2, 1)
        serialSettingsLayout.addWidget(self.serailParityCombobox, 3, 1)
        serialSettingsLayout.addWidget(self.serailStopbitsCombobox, 4, 1)
        serialSettingsLayout.addWidget(self.serialFlowControlCombobox, 5, 1)
        serialSettingsLayout.addWidget(self.checkBoxRTS, 6, 0,1,1)
        serialSettingsLayout.addWidget(self.checkBoxDTR, 6, 1,1,1)
        serialSettingsLayout.addWidget(self.serialOpenCloseButton, 7, 0,1,2)
        self.widget.setLayout(serialSettingsLayout)
        self.widgetConfMap["port"]       = self.serialPortCombobox
        self.widgetConfMap["baudrate"]    = self.serailBaudrateCombobox
        self.widgetConfMap["bytesize"]    = self.serailBytesCombobox
        self.widgetConfMap["parity"]      = self.serailParityCombobox
        self.widgetConfMap["stopbits"]    = self.serailStopbitsCombobox
        self.widgetConfMap["flowcontrol"] = self.serialFlowControlCombobox
        self.widgetConfMap["rts"]         = self.checkBoxRTS
        self.widgetConfMap["dtr"]         = self.checkBoxDTR
        self.initEvet()
        return self.widget

    def initEvet(self):
        self.serialPortCombobox.clicked.connect(self.detectSerialPort)
        self.showSerialComboboxSignal.connect(self.showCombobox)
        self.serialPortCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("port", self.serialPortCombobox, str))
        self.serailBaudrateCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("baudrate", self.serailBaudrateCombobox, int, caller="index change"))
        self.serailBaudrateCombobox.editTextChanged.connect(lambda: self.onSerialConfigChanged("baudrate", self.serailBaudrateCombobox, int, caller="text change"))
        self.serailBytesCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("bytesize", self.serailBytesCombobox, int))
        self.serailParityCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("parity", self.serailParityCombobox, str))
        self.serailStopbitsCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("stopbits", self.serailStopbitsCombobox, str))
        self.serialFlowControlCombobox.currentIndexChanged.connect(lambda: self.onSerialConfigChanged("flowcontrol", self.serialFlowControlCombobox, str))
        self.checkBoxRTS.clicked.connect(lambda: self.onSerialConfigChanged("rts", self.checkBoxRTS, bool))
        self.checkBoxDTR.clicked.connect(lambda: self.onSerialConfigChanged("dtr", self.checkBoxDTR, bool))
        self.serialOpenCloseButton.clicked.connect(self.openCloseSerial)
        self.showSwitchSignal.connect(self.showSwitch)

    def onSerialConfigChanged(self, conf_type, obj, value_type, caller=""):
        if conf_type == "port":
            obj.setToolTip(obj.currentText())
            newPort = obj.currentText().split(" ")[0]
            if newPort and not self.isDetectSerialPort and (newPort != self.config["port"] or  not self.com.port):
                self.config["port"] = newPort
                print("-- set to new port:", self.config["port"])
                try:
                    self.com.port = self.config["port"]
                except Exception as e:
                    msg = _("Open Failed") +"\n"+ str(e)
                    self.status = ConnectionStatus.CLOSED
                    self.onConnectionStatus.emit(self.status, msg)
                    self.showSwitchSignal.emit(self.status)
        elif conf_type in ["baudrate", "bytesize", "parity", "stopbits"]:
            # custom baudrate input
            text = obj.currentText()
            if conf_type == "baudrate" and ((not text) or text == self.baudrateCustomStr):
                self.serailBaudrateCombobox.clearEditText()
                return
            self.config[conf_type] = value_type(text.split(" ")[0])
            print("-- set serial {} to {}".format(conf_type, self.config[conf_type]))
            if conf_type == "parity":
                self.com.__setattr__(conf_type, self.config[conf_type][0])
            elif conf_type == "stopbits":
                self.com.__setattr__(conf_type, float(self.config[conf_type]))
            else:
                self.com.__setattr__(conf_type, self.config[conf_type])
        elif conf_type == "flowcontrol":
            self.config[conf_type] = value_type(obj.currentText().split(" ")[0])
            if self.config[conf_type] == "XON/XOFF":
                self.com.xonxoff = True
            else:
                self.com.xonxoff = False
            if self.config[conf_type] == "RTS/CTS":
                self.com.rtscts = True
            else:
                self.com.rtscts = False
            if self.config[conf_type] == "DSR/DTR":
                self.com.dsrdtr = True
            else:
                self.com.dsrdtr = False
        elif conf_type in ["rts", "dtr"]:
            self.config[conf_type] = obj.isChecked()
            self.com.__setattr__(conf_type, self.config[conf_type])

    def setSerialConfig(self, conf_type, obj, value):
        def getCommboboxItems(obj):
            values = []
            for i in range(len(obj)):
                values.append(obj.itemText(i))
            return values
        if conf_type == "port":
            values = getCommboboxItems(obj)
            idx = 0
            try:
                idx = values.index(str(value))
            except Exception:
                # print(f"-- set {obj} index {idx} error, value {value}, items {values}")
                pass
            obj.setCurrentIndex(idx)
        elif conf_type in ["baudrate", "bytesize", "parity", "stopbits"]:
            values = getCommboboxItems(obj)
            idx = 0
            try:
                idx = values.index(str(value))
            except Exception:
                print(f"-- set {obj} index {idx} error, value {value}, items {values}")
            obj.setCurrentIndex(idx)
            if conf_type == "parity":
                value = value[0]
            elif conf_type == "stopbits":
                value = float(value)
            self.com.__setattr__(conf_type, value)
            if conf_type == "baudrate":
                self.oneByteTime = 1 / (self.com.baudrate / (self.com.bytesize + 2 + self.com.stopbits)) # 1 byte use time
        elif conf_type == "flowcontrol":
            values = getCommboboxItems(obj)
            idx = 0
            try:
                idx = values.index(str(value))
            except Exception:
                print(f"-- set {obj} index {idx} error, value {value}, items {values}")
            obj.setCurrentIndex(idx)
            if value == "XON/XOFF":
                self.com.xonxoff = True
            else:
                self.com.xonxoff = False
            if value == "RTS/CTS":
                self.com.rtscts = True
            else:
                self.com.rtscts = False
            if value == "DSR/DTR":
                self.com.dsrdtr = True
            else:
                self.com.dsrdtr = False
        elif conf_type in ["rts", "dtr"]:
            obj.setChecked(value)
            self.com.__setattr__(conf_type, value)

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
            print("-- close serial")
            try:
                # set status first to prevent auto reconnect
                self.status = ConnectionStatus.CLOSED
                self.com.close()
            except Exception:
                pass
            self.onConnectionStatus.emit(self.status, "")
            self.showSwitchSignal.emit(self.status)
        else:
            try:
                print("-- open serial")
                self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                self.com.open()
                self.status = ConnectionStatus.CONNECTED
                self.onConnectionStatus.emit(self.status, "")
                self.showSwitchSignal.emit(self.status)
                self.receiveProcess = threading.Thread(target=self.receiveDataProcess)
                self.receiveProcess.setDaemon(True)
                self.receiveProcess.start()
            except Exception as e:
                try:
                    self.com.close()
                except Exception:
                    pass
                msg = _("Open Failed") +"\n"+ str(e)
                self.hintSignal.emit("error", _("Error"), msg)
                self.status = ConnectionStatus.CLOSED
                self.onConnectionStatus.emit(self.status, msg)
                self.showSwitchSignal.emit(self.status)
        self.busy = False

    def detectSerialPort(self):
        if not self.isDetectSerialPort:
            self.isDetectSerialPort = True
            t = threading.Thread(target=self.detectSerialPortProcess)
            t.setDaemon(True)
            t.start()

    def detectSerialPortProcess(self):
        items = []
        while 1:
            portList = self.findSerialPort()
            if len(portList)>0:
                for p in portList:
                    showStr = "{} {} - {}".format(p.device, p.name, p.description)
                    if p.manufacturer:
                        showStr += ' - {}'.format(p.manufacturer)
                    if p.pid:
                        showStr += ' - pid(0x{:04X})'.format(p.pid)
                    if p.vid:
                        showStr += ' - vid(0x{:04X})'.format(p.vid)
                    if p.serial_number:
                        showStr += ' - v{}'.format(p.serial_number)
                    if p.device.startswith("/dev/cu.Bluetooth-Incoming-Port"):
                        continue
                    items.append(showStr)
                break
            time.sleep(0.5)
        self.showSerialComboboxSignal.emit(items)

    # @pyqtSlot(list)
    def showCombobox(self, items):
        set = -1
        self.serialPortCombobox.clear()
        for item in items:
            self.serialPortCombobox.addItem(item)
            if self.config["port"]:
                index = self.serialPortCombobox.findText(self.config["port"], Qt.MatchContains)
                if index>=0:
                    set = index
        self.serialPortCombobox.showPopup()
        self.isDetectSerialPort = False
        if set <= 0:
            # set to first port in list
            self.onSerialConfigChanged("port", self.serialPortCombobox, str)
        else:
            self.serialPortCombobox.setCurrentIndex(set)

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

    def findSerialPort(self):
        self.port_list = list(serial.tools.list_ports.comports())
        return self.port_list

    def portExits(self, port):
        ports = self.findSerialPort()
        devices = []
        for p in ports:
            devices.append(p.device)
        if port in devices:
            return True
        return False

    def receiveDataProcess(self):
        waitingReconnect = False
        self.com.timeout = 0.001
        buffer = b''
        t = 0
        while self.status != ConnectionStatus.CLOSED:
            if waitingReconnect:
                if self.portExits(self.com.port):
                    try:
                        self.onConnectionStatus.emit(ConnectionStatus.CONNECTING, "")
                        self.com.open()
                        print("-- reopen serial")
                        waitingReconnect = False
                        self.onConnectionStatus.emit(ConnectionStatus.CONNECTED, _("Reconnected"))
                        self.showSwitchSignal.emit(ConnectionStatus.CONNECTED)
                        continue
                    except Exception as e:
                        pass
                time.sleep(0.01)
                continue
            try:
                length = max(1, self.com.in_waiting)
                data = self.com.read(length)
                if data:
                    t = time.time()
                    if length == 1 and not buffer: # just start receive
                        buffer += data
                        continue
                    buffer += data
                if buffer and (time.time() - t > self.oneByteTime * 2): # no new data in next frame
                    try:
                        self.onReceived(buffer)
                    except Exception as e:
                        print("-- error in onReceived callback:", e)
                    buffer = b''
            except Exception as e:
                if (self.status != ConnectionStatus.CLOSED):
                    # close as fast as we can to release port
                    try:
                        self.com.close()
                    except Exception:
                        pass
                    waitingReconnect = True
                    self.onConnectionStatus.emit(ConnectionStatus.LOSE, _("Connection lose!"))
                    self.showSwitchSignal.emit(ConnectionStatus.LOSE)


    def send(self, data : bytes):
        self.com.write(data)

    def isConnected(self):
        return self.status == ConnectionStatus.CONNECTED

if __name__ == "__main__":
    import sys, os
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
    sys.path.insert(0, "")
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    conn = Serial()
    conn.onInit({})

    def onReceived(data):
        print(data)
        conn.send(data)

    conn.onReceived = onReceived
    window = conn.onWidget()
    window.show()
    ret = app.exec_()
