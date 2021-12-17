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
if not os.path.exists(assetsDir): # for pyinstaller pack
    dataPath = os.path.dirname(dataPath)
    assetsDir = os.path.join(dataPath, "assets").replace("\\", "/")

defaultBaudrates = [9600, 19200, 38400, 57600, 74880, 115200, 921600, 1000000, 1500000, 2000000, 4500000]
encodings = ["ASCII", "UTF-8", "UTF-16", "GBK", "GB2312", "GB18030"]
customSendItemHeight = 60

author = "Neucrack"

class Strings:
    def __init__(self, locale):
        set_locale(locale)
        self.strReceive = _("Receive")
        self.strSendSettings = _("Send Settings")
        self.strReceiveSettings = _("Receive Settings")
        self.strSerialSettings = _("Serial Settings")
        self.strFunctionalSend = _("Functional Send")
        self.strClosed = _("Closed")
        self.strReady = _("Ready")
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

print("-- config path:", configFilePath)


class Parameters:
    basic = {
        "skin": "light",
        "locale": "en",
        "encoding": "ASCII",
        "skipVersion": None,
        "connId": "serial",
        "plugins": [],          # enabled plugins ID
        "activePlugin": "dbg" 
    }
    conns = {
        # "serial": {
        # },
        # "tcpudp": {
        # }
    }
    plugins = {
        # "dbg": {
        # },
    }


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
        if "basic" in obj:
            self.basic.update(obj["basic"])
        if "conns" in obj:
            self.conns.update(obj["conns"])
        if "plugins" in obj:
            self.plugins.update(obj["plugins"])
        

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

