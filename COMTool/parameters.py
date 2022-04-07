import shutil
import sys, os
from datetime import datetime
import json

try:
    from i18n import _, set_locale
    from logger import Logger
except ImportError:
    from COMTool.i18n import _, set_locale
    from COMTool.logger import Logger

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
customSendItemHeight = 40

author = "Neucrack"

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
    configFileDir = os.path.abspath(os.getcwd())
    configFilePath  = os.path.join(configFileDir, configFileName)

logPath = os.path.join(configFileDir, "run.log")
log = Logger(file_path=logPath)
log.i("Config path:", configFilePath)
log.i("Log path:", logPath)


class Parameters:
    config = {
        "version": 3,
        "skin": "light",
        "locale": "en",
        "encoding": "UTF-8",
        "skipVersion": None,
        "connId": "serial",
        "pluginsInfo": {          # enabled plugins ID
            "external": {
                # "myplugin2": {
                #     # "package": "myplugin",  # package installed as a python package
                #     "path": "E:\main\projects\COMTool\COMTool\plugins\myplugin2\myplugin2.py"
                # }
            }
        },
        "activeItem": "dbg-1",
        "currItem": None,
        "items": [
            # {
            #     "name": "dbg-1",
            #     "pluginId": "dbg",
            #     "config": {
            #         "conns": {
            #             "currConn": "serial",
            #             "serial": {
            #              }
            #         },
            #         "plugin": {

            #         }
            #     }
            # }
        ]
    }

    def save(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def load(self, path):
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
            if "version" in config and config["version"] == self.config["version"]:
                self.config = config
            else: # for old config, just backup
                t = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                old_path = "{}.bak.{}.json".format(path, t)
                log.w("Old config file, backup to", old_path)
                shutil.copyfile(path, old_path)
        return

    def __getitem__(self, idx):
        return self.config[idx]

    def __setitem__(self, idx, v):
        self.config[idx] = v

    def __str__(self) -> str:
        return json.dumps(self.config)
        

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

styleForCode = {
    "light":{
        "iconColor": "white",
        "iconSelectorColor": "#929599"
    },
    "dark":{
        "iconColor": "#bcbcbd",
        "iconSelectorColor": "#bcbcbd"
    }
}

