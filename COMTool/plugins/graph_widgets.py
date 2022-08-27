# from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QGridLayout, QPushButton, QCheckBox, QHBoxLayout, QInputDialog)
# from PyQt5.QtCore import pyqtSignal
# from PyQt5.QtGui import QDoubleValidator
import numpy as np
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit,
                             QGridLayout, QPushButton, QCheckBox, QHBoxLayout, QInputDialog, QComboBox, QFileDialog)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator

try:
    from i18n import _
    import utils_ui
    import utils
    from widgets import EditRemarDialog
except Exception:
    from COMTool.i18n import _
    from COMTool import utils_ui
    from COMTool import utils
    from COMTool.widgets import EditRemarDialog

from .graph_widget_metasenselite import Graph_MetaSenseLite
from .graph_widgets_base import Graph_Widget_Base
import pyqtgraph as pg
from struct import unpack, pack
import time




class Graph_Plot(Graph_Widget_Base):
    updateSignal = pyqtSignal(dict)
    id = "plot"

    def __init__(self, parent=None, hintSignal=lambda type, title, msg: None, rmCallback=lambda widget: None, send=lambda x: None, config=None):
        default = {
            "xRange": 10,
            "xRangeEnable": True,
            "header": "\\xAA\\xCC\\xEE\\xBB"
        }
        super().__init__(parent, hintSignal=hintSignal, rmCallback=rmCallback,
                         send=send, config=config, defaultConfig=default)
        self.headerBytes = utils.str_to_bytes(
            self.config["header"], escape=True, encoding="utf-8")
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.plotWin = pg.GraphicsLayoutWidget()
        self.plotWin.setMinimumHeight(200)
        pg.setConfigOptions(antialias=True)
        rmBtn = QPushButton(_("Remove"))
        rangeLabel = QLabel(_("Range:"))
        rangeConf = QLineEdit(str(self.config["xRange"]))
        rangeEnable = QCheckBox(_("Enable"))
        rangeEnable.setChecked(self.config["xRangeEnable"])
        headerLabel = QLabel(_("Header:"))
        headerConf = QLineEdit(self.config["header"])
        self.headerBtn = QPushButton(_("Set"))
        hint = _("Protocol: header + 1Byte name length + name + 8Bytes x(double) + 8Bytes y(double) + 1Byte sum\n"
                 "Protocol example code see help")
        headerConf.setToolTip(hint)
        headerLabel.setToolTip(hint)
        self.headerBtn.setToolTip(hint)
        validator = QDoubleValidator()
        rangeConf.setValidator(validator)
        self.layout.addWidget(self.plotWin, 0, 0, 1, 3)
        self.layout.addWidget(rmBtn, 1, 0, 1, 1)
        self.layout.addWidget(rangeLabel, 2, 0, 1, 1)
        self.layout.addWidget(rangeConf, 2, 1, 1, 1)
        self.layout.addWidget(rangeEnable, 2, 2, 1, 1)
        self.layout.addWidget(headerLabel, 3, 0, 1, 1)
        self.layout.addWidget(headerConf, 3, 1, 1, 1)
        self.layout.addWidget(self.headerBtn, 3, 2, 1, 1)
        self.resize(600, 400)
        self.p = self.plotWin.addPlot(colspan=2)
        # self.p.setLabel('bottom', 'x', '')
        self.p.addLegend()
        self.p.setXRange(0, self.config["xRange"])
        self.updateSignal.connect(self.update)
        self.curves = {}
        self.rawData = b''
        self.data = {}
        self.builtinColors = [
            "#BD4B4B",
            "#3BB273",
            "#FFFFFA",
            "#307473",
            "#3C6997",
            "#746D75",
            "#228CDB",
            "#824C71",
            "#7768AE",
            "#DC6BAD",
            "#607d8b",
            "#F18701",
            "#912F40",
            "#414288",
            "#ED4D6E",
            "#FFD29D",
            "#B56576",
            "#503B31",
            "#93E1D8",
            "#596157",
        ]
        self.notUsedColors = self.builtinColors.copy()
        self.colors = {

        }
        rangeConf.textChanged.connect(self.setRange)
        rangeEnable.clicked.connect(
            lambda: self.setEnableRange(rangeEnable.isChecked()))
        self.headerBtn.clicked.connect(
            lambda: self.setHeader(headerConf.text()))
        rmBtn.clicked.connect(self.remove)
        headerConf.textChanged.connect(self.headerChanged)

    def remove(self):
        self.rmCallback(self)

    def setRange(self, text):
        if text:
            self.config["xRange"] = float(text)

    def setEnableRange(self, en):
        self.config["xRangeEnable"] = en

    def headerChanged(self, text):
        if self.config["header"] != text:
            self.headerBtn.setText(_("Set") + " *")
        else:
            self.headerBtn.setText(_("Set"))

    def setHeader(self, text):
        if text:
            try:
                textBytes = utils.str_to_bytes(
                    text, escape=True, encoding="utf-8")
                self.config["header"] = text
                self.headerBytes = textBytes
                self.headerBtn.setText(_("Set"))
            except Exception:
                self.hintSignal.emit("error", _("Error"), _("Format error"))

    def decodeData(self, data: bytes):
        '''
            @data bytes, protocol:
                         |    header(4B)    | line name len(1B) | line name | x(8B) | y(8B) | sum(1B) |
                         | AA CC EE BB      | 1~255             |  roll     | double | double | uint8   |
            @return haveFrame, dict {
                "name": {
                    "x": [],
                    "y": []
                }
            }
        '''
        # append data
        self.rawData += data
        # find header
        header = self.headerBytes
        idx = self.rawData.find(header)
        if idx < 0:
            return False, self.data
        self.rawData = self.rawData[idx:]
        # check data length
        nameLen = unpack("B", self.rawData[len(header): len(header) + 1])[0]
        frameLen = len(header) + nameLen + 18  # 5 + nameLen + 16 + 1
        if len(self.rawData) < frameLen:
            return False, self.data
        # get data
        frame = self.rawData[:frameLen]
        self.rawData = self.rawData[frameLen:]
        _sum = frame[-1]
        # check sum
        if _sum != sum(frame[:frameLen - 1]) % 256:
            return True, self.data
        name = frame[len(header) + 1: len(header) +
                     1 + nameLen].decode("utf-8")
        x = unpack("d", frame[-17:-9])[0]
        y = unpack("d", frame[-9:-1])[0]
        if not name in self.data:
            self.data[name] = {
                "x": [x],
                "y": [y]
            }
        else:
            self.data[name]["x"].append(x)
            self.data[name]["y"].append(y)
        return True, self.data

    def pickColor(self, name: str):
        if name in self.colors:
            return self.colors[name]
        else:
            if not self.notUsedColors:
                self.notUsedColors = self.builtinColors.copy()
            color = self.notUsedColors.pop(0)
            self.colors[name] = color
            return color

    def update(self, data: dict):
        for k, v in data.items():
            if not k in self.curves:
                print("add curve:", k)
                color = self.pickColor(k)
                self.colors[k] = color
                self.curves[k] = self.p.plot(pen=pg.mkPen(color=color, width=2),
                                             name=k,)
                # symbolBrush=color, symbolPen='w', symbol='o', symbolSize=1)
            if self.config["xRangeEnable"] and self.config["xRange"] > 0:
                self.p.setXRange(
                    v["x"][-1] - self.config["xRange"], v["x"][-1])
            self.curves[k].setData(x=v["x"], y=v["y"])

    def onData(self, data: bytes):
        while 1:
            haveFrame, allData = self.decodeData(data)
            if not haveFrame:
                break
            data = b''
        self.updateSignal.emit(allData)


class Graph_Button(Graph_Widget_Base):
    class Button(QWidget):
        def __init__(self, rmCallback, addCallback, clickCallback, changeCallback,
                     value=("", "hello", "hello", "fa.circle", [])):
            super().__init__()
            if not value[0]:
                self.id = str(int(time.time() * 1000))
            else:
                self.id = value[0]
            self.rmCallback = rmCallback
            self.changeCallback = changeCallback
            self.setProperty("class", "graphBtn")
            layout = QHBoxLayout()
            layoutSetting = QVBoxLayout()
            self.setLayout(layout)
            self.button = QPushButton(value[2])
            self.button.setProperty("class", "bigBtn")
            self.value = value[2]
            self.icon = value[3]
            self.shortcut = value[4]
            layout.addLayout(layoutSetting)
            layout.addWidget(self.button)
            self.addBtn = QPushButton()
            self.rmBtn = QPushButton()
            self.editBtn = QPushButton()
            self.addBtn.setProperty("class", "smallBtn3")
            self.rmBtn.setProperty("class", "smallBtn3")
            self.editBtn.setProperty("class", "smallBtn3")
            utils_ui.setButtonIcon(self.addBtn, "fa.plus")
            utils_ui.setButtonIcon(self.rmBtn, "fa.minus")
            utils_ui.setButtonIcon(self.editBtn, "fa.edit")
            if self.icon:
                utils_ui.setButtonIcon(self.button, self.icon)
            if self.shortcut:
                tip = self.getShortcutTip()
                self.button.setToolTip(tip)
            layoutSetting.addStretch()
            layoutSetting.addWidget(self.rmBtn)
            layoutSetting.addWidget(self.addBtn)
            layoutSetting.addWidget(self.editBtn)
            self.rmBtn.clicked.connect(self.onRm)
            self.addBtn.clicked.connect(lambda: addCallback(self))
            self.editBtn.clicked.connect(self.editButton)
            self.button.clicked.connect(lambda: clickCallback(
                self, utils.str_to_bytes(self.value, escape=True, encoding="utf-8")))

        def getInfo(self):
            return [self.id, self.button.text(), self.value, self.icon, self.shortcut]

        def onRm(self):
            utils_ui.clearButtonIcon(self.addBtn)
            utils_ui.clearButtonIcon(self.rmBtn)
            utils_ui.clearButtonIcon(self.editBtn)
            utils_ui.clearButtonIcon(self.button)
            self.rmCallback(self)

        def editButton(self):
            ok, remark, value, icon, shortcut = EditRemarDialog(
                self.button.text(), self.icon, shortcut=self.shortcut, value=self.value).exec()
            if ok:
                self.value = value
                self.icon = icon
                self.shortcut = shortcut
                self.button.setText(remark)
                if self.shortcut:
                    tip = self.getShortcutTip()
                    self.button.setToolTip(tip)
                utils_ui.setButtonIcon(self.button, icon)
                self.changeCallback(self)

        def getShortcutTip(self):
            return _("Shortcut") + ": " + "+".join((name for v, name in self.shortcut))

    id = "button"

    def __init__(self, parent=None, hintSignal=lambda type, title, msg: None, rmCallback=lambda widget: None, send=lambda x: None, config=None):
        default = {
            "items": []
        }
        super().__init__(parent, hintSignal, rmCallback, send, config, default)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        if not self.config["items"]:
            button = Graph_Button.Button(
                self.onRm, self.onAdd, self.onClick, self.onChange)
            self.layout.addWidget(button)
            self.buttons = [button]
            self.config["items"] = [button.getInfo()]
        else:
            self.buttons = []
            for item in self.config["items"]:
                button = Graph_Button.Button(
                    self.onRm, self.onAdd, self.onClick, self.onChange, value=item)
                self.layout.addWidget(button)
                self.buttons.append(button)
        self.pressedKeys = []

    def onRm(self, widget):
        '''
            @widget Graph_Button.Button
        '''
        item = widget.getInfo()
        for item_ in self.config["items"]:
            if item_[0] == item[0]:  # id
                self.config["items"].remove(item_)
                break
        self.buttons.remove(widget)
        widget.setParent(None)
        if not self.buttons:
            self.rmCallback(self)

    def onAdd(self, widget):
        '''
            @widget Graph_Button.Button
        '''
        button = Graph_Button.Button(
            self.onRm, self.onAdd, self.onClick, self.onChange)
        self.layout.addWidget(button)
        self.buttons.append(button)
        self.config["items"].append(button.getInfo())

    def onClick(self, widget, data: bytes):
        self.send(data)

    def onChange(self, widget):
        self.config["items"][self.buttons.index(widget)] = widget.getInfo()

    def onKeyPressEvent(self, event):
        key = event.key()
        self.pressedKeys.append(key)
        for uid, name, value, icon, shortcut in self.config["items"]:
            if not shortcut:
                continue
            if len(shortcut) == len(self.pressedKeys):
                same = True
                for i in range(len(shortcut)):
                    if shortcut[i][0] != self.pressedKeys[i]:
                        same = False
                        break
                if same:
                    value = utils.str_to_bytes(
                        value, escape=True, encoding="utf-8")
                    self.send(value)

    def onKeyReleaseEvent(self, event):
        key = event.key()
        if key in self.pressedKeys:
            self.pressedKeys.remove(key)


graphWidgets = {
    Graph_Plot.id: Graph_Plot,
    Graph_Button.id: Graph_Button,
    # Graph_DragTof.id: Graph_DragTof,
    Graph_MetaSenseLite.id: Graph_MetaSenseLite,
}
