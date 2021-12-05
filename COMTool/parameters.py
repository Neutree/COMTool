import sys, os
import json
try:
    from i18n import _, set_locale
except ImportError:
    from COMTool.i18n import _, set_locale

appName = "COMTool"
appIcon = "assets/logo.png"
appLogo = "assets/logo.png"
appLogo2 = "assets/logo2.png"
dataPath = os.path.abspath(os.path.dirname(__file__)).replace("\\", "/") # replace \ to / for qss usage, qss only support /
assetsDir = os.path.join(dataPath, "assets").replace("\\", "/")

defaultBaudrates = [9600, 19200, 38400, 57600, 74880, 115200, 921600, 1000000, 1500000, 2000000, 4500000]
defaultAutoLinefeedTime = 200
defaultScheduledTime = 300

author = "Neucrack"

class Strings:
    def __init__(self, locale):
        set_locale(locale)
        self.strBytes = _("bytes")
        self.strSend = _("Send")
        self.strReceive = _("Receive")
        self.strSerialPort = _("Port")
        self.strSerialBaudrate = _("Baudrate")
        self.strSerialBytes = _("DataBytes")
        self.strSerialParity = _("Parity")
        self.strSerialStopbits = _("Stopbits")
        self.strAscii = _("ASCII")
        self.strHex = _("HEX")
        self.strSendSettings = _("Send Settings")
        self.strReceiveSettings = _("Receive Settings")
        self.strOpen = _("OPEN")
        self.strClose = _("CLOSE")
        self.strAutoLinefeed = _("Auto\nLinefeed\nms")
        self.strScheduled = _("Timed Send\nms")
        self.strSerialSettings = _("Serial Settings")
        self.strSerialReceiveSettings = _("Receive Settings")
        self.strSerialSendSettings = _("Send Settings")
        self.strClearReceive = _("ClearReceive")
        self.strAdd = _("+")
        self.strFunctionalSend = _("Functional Send")
        self.strSendFile = _("Send File")
        self.strOpenFailed = _("Open Failed")
        self.strClosed = _("Closed")
        self.strWriteError = _("Send Error")
        self.strReady = _("Ready")
        self.strWriteFormatError = _("format error")
        self.strCRLF = _("<CRLF>")
        self.strTimeFormatError = _("Time format error")
        self.strHelp = _("HELP")
        self.strAbout = _("ABOUT")
        self.strSettings = _("Settings")
        self.strNeedUpdate = _("Need Update")
        self.strUpdateNow = _("update now?")
        self.strUninstallApp = _("uninstall app")


def get_config_path(configFileName):
    configFilePath = configFileName
    try:
        configFilePath = os.path.join(configFileDir, configFileName)
        if not os.path.exists(configFileDir):
            os.makedirs(configFileDir)
    except:
        pass
    return configFilePath

configFileName="config.json"
configFilePath=configFileName

if sys.platform.startswith('linux') or sys.platform.startswith('darwin') or sys.platform.startswith('freebsd'):
    configFileDir = os.path.join(os.getenv("HOME"), ".config/comtool")
    configFilePath = get_config_path(configFileName)
else:
    files = os.listdir(os.getcwd())
    if "comtool.exe" in files:
        configFilePath  = os.path.join(os.getcwd(), configFileName)
    else:
        configFilePath = get_config_path(configFileName)


class Parameters:
    baudRate = 4
    dataBytes = 3
    parity = 0
    stopBits = 0
    receiveAscii = True
    receiveAutoLinefeed = False
    receiveAutoLindefeedTime = "200"
    sendAscii = True
    sendScheduled = False
    sendScheduledTime = "300"
    useCRLF = True
    skin = 2
    rts  = 0
    dtr  = 0
    locale = "en"
    encodingIndex = 0
    sendHistoryList = []

    def save(self, path):
        path = os.path.abspath(path)
        obj = {}
        for k in Parameters.__dict__.keys():
            if k.startswith("__"):
                continue
            v = getattr(self, k)
            if callable(v):
                continue
            obj[k] = v
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=4)

    def load(self, path):
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
        for key in obj:
            self.__setattr__(key, obj[key])
        

strStyleShowHideButtonLeft = '''
QPushButton {
    border-image: url("$DataPath/assets/arrow-left.png")
}
QPushButton:hover {
    border-image: url("$DataPath/assets/arrow-left-white.png")
}'''

strStyleShowHideButtonRight = '''
QPushButton {
    border-image: url("$DataPath/assets/arrow-right.png")
}
QPushButton:hover {
    border-image: url("$DataPath/assets/arrow-right-white.png")
}'''

