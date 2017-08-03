appName = "COMTool"
strDataDirName = "COMToolData"
strDataAssetsDirName = "COMToolData/assets"
appIcon = "COMToolData/assets/logo.png"
appLogo = "COMToolData/assets/logo.png"
appLogo2 = "/COMToolData/assets/logo2.png"

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
strBaudRateDefault = "115200"
strOpenFailed = "Open Failed"
strOpenReady = "Open Ready"
strClosed = "Closed"
strWriteError = "Send Error"
strReady = "Ready"
strWriteFormatError = "format error"
strCRLF = "<CRLF>(for Windows)"
strTimeFormatError = "Time format error"
strHelp = "HELP"
strAbout = "ABOUT"
strSettings = "Settings"
strNeedUpdate = "Need Update"
strUpdateNow = "update now?"
strUninstallApp = "uninstall app"


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
    sendHistoryList = []
    def __init__(self):
        return

    def __del__(self):
        return



