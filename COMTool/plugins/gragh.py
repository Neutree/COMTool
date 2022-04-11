
import enum
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter,QFileDialog, QScrollArea, QListWidget)
try:
    from .base import Plugin_Base
    from Combobox import ComboBox
    from i18n import _
    import utils, parameters
    from conn.base import ConnectionStatus
    from widgets import statusBar
    from plugins.gragh_widgets import graghWidgets
except ImportError:
    from COMTool import utils, parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox
    from COMTool.conn.base import  ConnectionStatus
    from COMTool.widgets import statusBar
    from COMTool.plugins.gragh_widgets import graghWidgets
    from COMTool.plugins.base import Plugin_Base


class Plugin(Plugin_Base):
    '''
        call sequence:
            set vars like hintSignal, hintSignal
            onInit
            onWidget
            onUiInitDone
            onActive
                send
                onReceived
            onDel
    '''
    # vars set by caller
    isConnected = lambda o: False
    send = lambda o,x,y:None          # send(data_bytes=None, file_path=None, callback=lambda ok,msg:None), can call in UI thread directly
    ctrlConn = lambda o,k,v:None      # call ctrl func of connection
    hintSignal = None               # hintSignal.emit(type(error, warning, info), title, msg)
    reloadWindowSignal = None       # reloadWindowSignal.emit(title, msg, callback(close or not)), reload window to load new configs
    configGlobal = {}
    # other vars
    connParent = "main"      # parent id
    connChilds = []          # children ids
    id = "gragh"
    name = _("Gragh")

    enabled = False          # user enabled this plugin
    active  = False          # using this plugin

    help = '{}<br><br>{}<br>Python:<br><pre>{}</pre><br>C/C++:<br><pre>{}</pre>'.format(_("Double click gragh item to add a gragh widget"), _("line chart plot protocol:"),
'''
from COMTool.plugin import gragh_protocol
frame = gragh_protocol.plot_pack(name, x, y, header= b'\xAA\xCC\xEE\xBB')
''',
'''
void plot_pack(uint8_t *buff, int buff_len,
               uint8_t header[4], char *name,
               double x, double y)
{
    memcpy(buff, header, 4);
    uint8_t len = (uint8_t)strlen(name);
    buff[4] = len;
    memcpy(buff + 5, name, len);
    memcpy(buff + 5 + len, &x, 8);
    memcpy(buff + 5 + len + 8, &y, 8);
    int sum = 0;
    for (int i = 0; i &lt; 4+1+len+8+8; i++)
    {
        sum += buff[i];
    }
    buff[4+1+len+8+8] = (uint8_t)(sum & 0xff);
}
''')

    def __init__(self):
        super().__init__()
        if not self.id:
            raise ValueError(f"var id of Plugin {self} should be set")

    def onInit(self, config):
        '''
            init params, DO NOT take too long time in this func
            @config dict type, just change this var's content,
                               when program exit, this config will be auto save to config file
        '''
        self.config = config
        default = {
            "version": 1,
            "graghWidgets": [
                # {
                #     "id": "plot",
                #     "config": {}
                # }
            ]
        }
        for k in default:
            if not k in self.config:
                self.config[k] = default[k]
        self.widgets = []

    def onDel(self):
        pass

    def onWidgetMain(self, parent):
        '''
            main widget, just return a QWidget object
        '''
        widget = QWidget()
        widget.setProperty("class", "scrollbar2")
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(scroll)
        widget2 = QWidget()
        scroll.setWidget(widget2)
        self.widgetsLayout = QVBoxLayout()
        widget2.setLayout(self.widgetsLayout)
        widget.resize(600, 400)
        # load gragh widgets
        for item in self.config["graghWidgets"]:
            if not item["id"] in graghWidgets:
                continue
            c = graghWidgets[item["id"]]
            w = c(hintSignal = self.hintSignal, rmCallback = self.rmWidgetFromMain, send=self.sendData, config=item["config"])
            self.widgets.append(w)
            self.widgetsLayout.addWidget(w)
        return widget

    def onWidgetSettings(self, parent):
        '''
            setting widget, just return a QWidget object or None
        '''
        itemList = QListWidget()
        for k,v in graghWidgets.items():
            itemList.addItem(k)
        itemList.setToolTip(_("Double click to add a gragh widget"))
        itemList.setCurrentRow(0)
        itemList.itemDoubleClicked.connect(self.addWidgetToMain)
        return itemList

    def addWidgetToMain(self, item):
        for k, c in graghWidgets.items():
            if k == item.text():
                config = {
                    "id": c.id,
                    "config": {}
                }
                w = c(hintSignal = self.hintSignal, rmCallback = self.rmWidgetFromMain, send=self.sendData, config=config["config"])
                self.widgets.append(w)
                self.widgetsLayout.addWidget(w)
                self.config["graghWidgets"].append(config)

    def rmWidgetFromMain(self, widget):
        self.widgetsLayout.removeWidget(widget)
        for item in self.config["graghWidgets"]:
            if id(item["config"]) == id(widget.config):
                self.config["graghWidgets"].remove(item)
                break
        widget.deleteLater()
        self.widgets.remove(widget)

    def onWidgetFunctional(self, parent):
        '''
            functional widget, just return a QWidget object or None
        '''
        button = QPushButton(_("Clear count"))
        button.clicked.connect(self.clearCount)
        return button

    def onWidgetStatusBar(self, parent):
        self.statusBar = statusBar(rxTxCount=True)
        return self.statusBar

    def clearCount(self):
        self.statusBar.clear()

    def onReceived(self, data : bytes):
        '''
            call in receive thread, not UI thread
        '''
        self.statusBar.addRx(len(data))
        for w in self.widgets:
            w.onData(data)

    def sendData(self, data:bytes):
        '''
            send data, chidren call send will invoke this function
            if you send data in this plugin, you can directly call self.send
        '''
        self.send(data, callback=self.onSent)

    def onSent(self, ok, msg, length, path):
        if ok:
            self.statusBar.addTx(length)
        else:
            self.hintSignal.emit("error", _("Error"), _("Send data failed!") + " " + msg)

    def onKeyPressEvent(self, event):
        for w in self.widgets:
            w.onKeyPressEvent(event)

    def onKeyReleaseEvent(self, event):
        for w in self.widgets:
            w.onKeyReleaseEvent(event)

    def onUiInitDone(self):
        '''
            UI init done, you can update your widget here
            this method runs in UI thread, do not block too long
        '''
        pass

    def onActive(self):
        '''
            plugin active
        '''
        pass
