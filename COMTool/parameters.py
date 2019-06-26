import sys, os

appName = "COMTool"
strDataDirName = "COMToolData"
strDataAssetsDirName = "COMToolData/assets"
appIcon = "assets/logo.png"
appLogo = "assets/logo.png"
appLogo2 = "assets/logo2.png"

author = "Neucrack"
strSend = "Send"
strReceive = "Receive"
strSerialPort = "Port"
strSerialBaudrate = "Baudrate"
strSerialBytes = "DataBytes"
strSerialParity = "Parity"
strSerialStopbits = "Stopbits"
strAscii = "ASCII"
strHex = "HEX"
strSendSettings = "Send Settings"
strReceiveSettings = "Receive Settings"
strOpen = "OPEN"
strClose = "CLOSE"
strAutoLinefeed = "Auto\nLinefeed\n(ms)"
strAutoLinefeedTime = "200"
strScheduled = "Scheduled\nSend(ms)"
strScheduledTime = "300"
strSerialSettings = "Serial Settings"
strSerialReceiveSettings = "Receive Settings"
strSerialSendSettings = "Send Settings"
strClearReceive = "ClearReceive"
strAdd = "+"
strFunctionalSend = "Functional Send"
strSendFile = "Send File"
strBaudRateDefault = "115200"
strOpenFailed = "Open Failed"
strOpenReady = "Open Ready"
strClosed = "Closed"
strWriteError = "Send Error"
strReady = "Ready"
strWriteFormatError = "format error"
strCRLF = "<CRLF>"
strTimeFormatError = "Time format error"
strHelp = "HELP"
strAbout = "ABOUT"
strSettings = "Settings"
strNeedUpdate = "Need Update"
strUpdateNow = "update now?"
strUninstallApp = "uninstall app"

configFileName="comtool.settings.config"
configFilePath=configFileName

if sys.platform.startswith('linux') or sys.platform.startswith('darwin') or sys.platform.startswith('freebsd'):
    configFileDir = os.path.join(os.getenv("HOME"), ".config/comtool")
    try:
        configFilePath = os.path.join(configFileDir, configFileName)
        if not os.path.exists(configFileDir):
            os.makedirs(configFileDir)
    except:
        pass
else:
    configFilePath  = os.path.join(os.getcwd(), configFileName)


class ParametersToSave:
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
    encodingIndex = 0
    sendHistoryList = []
    def __init__(self):
        return

    def __del__(self):
        return

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

