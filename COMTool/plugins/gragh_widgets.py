# from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QGridLayout, QPushButton, QCheckBox, QHBoxLayout, QInputDialog)
# from PyQt5.QtCore import pyqtSignal
# from PyQt5.QtGui import QDoubleValidator
import numpy as np
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit,
                             QGridLayout, QPushButton, QCheckBox, QHBoxLayout, QInputDialog, QComboBox, QFileDialog)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator

from multiprocessing import Queue
from PIL import Image
# big package, DO NOT USE IT
# import matplotlib.pyplot as plt

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

import pyqtgraph as pg

from struct import unpack, pack
import time


class Gragh_Widget_Base(QWidget):
    def __init__(self, parent=None, hintSignal=lambda type, title, msg: None, rmCallback=lambda widget: None, send=lambda x: None, config=None, defaultConfig=None):
        QWidget.__init__(self, parent)
        self.hintSignal = hintSignal
        self.rmCallback = rmCallback
        self.send = send
        if config is None:
            config = {}
        if not defaultConfig:
            defaultConfig = {}
        self.config = config
        for k in defaultConfig:
            if not k in self.config:
                self.config[k] = defaultConfig[k]

    def onData(self, data: bytes):
        pass

    def onKeyPressEvent(self, event):
        pass

    def onKeyReleaseEvent(self, event):
        pass


class Gragh_Plot(Gragh_Widget_Base):
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


class Gragh_Button(Gragh_Widget_Base):
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
            self.setProperty("class", "graghBtn")
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
            button = Gragh_Button.Button(
                self.onRm, self.onAdd, self.onClick, self.onChange)
            self.layout.addWidget(button)
            self.buttons = [button]
            self.config["items"] = [button.getInfo()]
        else:
            self.buttons = []
            for item in self.config["items"]:
                button = Gragh_Button.Button(
                    self.onRm, self.onAdd, self.onClick, self.onChange, value=item)
                self.layout.addWidget(button)
                self.buttons.append(button)
        self.pressedKeys = []

    def onRm(self, widget):
        '''
            @widget Gragh_Button.Button
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
            @widget Gragh_Button.Button
        '''
        button = Gragh_Button.Button(
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


# class Gragh_DragTof(Gragh_Widget_Base):
#     updateSignal = pyqtSignal(dict)
#     id = "DragTof"

#     def __init__(self, parent=None, hintSignal=lambda type, title, msg: None, rmCallback=lambda widget: None, send=lambda x: None, config=None):
#         default = {
#             "xRange": 10,
#             "xRangeEnable": True,
#             "header": "\\xCC\\xA0"
#         }
#         super().__init__(parent, hintSignal=hintSignal, rmCallback=rmCallback,
#                          send=send, config=config, defaultConfig=default)
#         self.headerBytes = utils.str_to_bytes(
#             self.config["header"], escape=True, encoding="utf-8")
#         self.layout = QGridLayout()
#         self.setLayout(self.layout)
#         self.imv = pg.ImageView()
#         self.queue = Queue()
#         # self.plotWin = pg.GraphicsLayoutWidget()
#         # self.plotWin.setMinimumHeight(200)
#         # self.plotWin
#         pg.setConfigOptions(antialias=True)
#         rmBtn = QPushButton(_("Remove"))
#         rangeLabel = QLabel(_("Range:"))
#         rangeConf = QLineEdit(str(self.config["xRange"]))
#         rangeEnable = QCheckBox(_("Enable"))
#         rangeEnable.setChecked(self.config["xRangeEnable"])
#         headerLabel = QLabel(_("Header:"))
#         headerConf = QLineEdit(self.config["header"])
#         self.headerBtn = QPushButton(_("Set"))
#         hint = _("Protocol: 2Byte header + 2Byte length + 1Byte command + 1Byte output_mode + 1Byte Sensor Temp + 1Byte Driver Temp\n"
#                  " 4Bytes exposure time + 1Byte error code + 1Byte reserved1 + 1Byte res rows + 1Byte res cols\n"
#                  " 2Byte Frame ID + 1 Byte ISP version + 1 Byte reserved3\n"
#                  " frame data\n"
#                  " 1Byte checksum + 1Byte tail\n"
#                  " length count from Byte4 to the Byte before Checksum\n"
#                  "Protocol example code see help")
#         headerConf.setToolTip(hint)
#         headerLabel.setToolTip(hint)
#         self.headerBtn.setToolTip(hint)
#         validator = QDoubleValidator()
#         rangeConf.setValidator(validator)
#         self.layout.addWidget(self.imv, 0, 0, 1, 3)
#         # self.layout.addWidget(self.plotWin, 0, 0, 1, 3)
#         self.layout.addWidget(rmBtn, 1, 0, 1, 1)
#         self.layout.addWidget(rangeLabel, 2, 0, 1, 1)
#         self.layout.addWidget(rangeConf, 2, 1, 1, 1)
#         self.layout.addWidget(rangeEnable, 2, 2, 1, 1)
#         self.layout.addWidget(headerLabel, 3, 0, 1, 1)
#         self.layout.addWidget(headerConf, 3, 1, 1, 1)
#         self.layout.addWidget(self.headerBtn, 3, 2, 1, 1)
#         self.resize(600, 400)
#         # self.p = self.plotWin.addPlot(colspan=2)
#         # self.p.addLegend()
#         # self.p.setXRange(0, self.config["xRange"])
#         self.updateSignal.connect(self.update)
#         self.rawData = b''
#         self.data = {}
#         self.builtinColors = [
#             "#BD4B4B",
#             "#3BB273",
#             "#FFFFFA",
#             "#307473",
#             "#3C6997",
#             "#746D75",
#             "#228CDB",
#             "#824C71",
#             "#7768AE",
#             "#DC6BAD",
#             "#607d8b",
#             "#F18701",
#             "#912F40",
#             "#414288",
#             "#ED4D6E",
#             "#FFD29D",
#             "#B56576",
#             "#503B31",
#             "#93E1D8",
#             "#596157",
#         ]
#         self.notUsedColors = self.builtinColors.copy()
#         self.colors = {

#         }
#         rangeConf.textChanged.connect(self.setRange)
#         rangeEnable.clicked.connect(
#             lambda: self.setEnableRange(rangeEnable.isChecked()))
#         self.headerBtn.clicked.connect(
#             lambda: self.setHeader(headerConf.text()))
#         rmBtn.clicked.connect(self.remove)
#         headerConf.textChanged.connect(self.headerChanged)

#     def remove(self):
#         self.rmCallback(self)

#     def setRange(self, text):
#         if text:
#             self.config["xRange"] = float(text)

#     def setEnableRange(self, en):
#         self.config["xRangeEnable"] = en

#     def headerChanged(self, text):
#         if self.config["header"] != text:
#             self.headerBtn.setText(_("Set") + " *")
#         else:
#             self.headerBtn.setText(_("Set"))

#     def setHeader(self, text):
#         if text:
#             try:
#                 textBytes = utils.str_to_bytes(
#                     text, escape=True, encoding="utf-8")
#                 self.config["header"] = text
#                 self.headerBytes = textBytes
#                 self.headerBtn.setText(_("Set"))
#             except Exception:
#                 self.hintSignal.emit("error", _("Error"), _("Format error"))

#     def decodeData(self, data: bytes):
#         '''
#             @data bytes, protocol:
#                          |    header(2B)    | len(2B) | command(1B) | output_mode(1B)     | sensor temp(1B) | driver temp(1B) |
#                          |     0xCC  0xA0      |  >=18   |             | 0:Depth only, 1:+IR |    uint8        | uint8           |
#                          -------------------------------------------------------------------------------------------------------
#                          |    exposure time(4B)    | errcode(1B) | reserved1(1B) | res_rows(1B) | res_cols(1B) |
#                          |[23:20][19:12][11:8][7:0]|             |       0x0     |     uint8    |     uint8    |
#                          ---------------------------------------------------------------------------------------
#                          |    Frame ID(2B)    | ISP ver(1B) | reserved3(1B) | frame data((len-16)B) | checksum(1B) | tail(1B) |
#                          |     [11:0]         |     0x23    |       0x0     | xxxxxxxxxxxxxxxxxxxxx | sum of above |   0xDD   |

#             @return haveFrame, dict {
#                 "frameID": {
#                     "res": tunple(w, h)
#                     "frameData": []
#                 }
#             }
#         '''
#         # append data
#         self.rawData += data
#         # find header
#         header = self.headerBytes
#         idx = self.rawData.find(header)
#         if idx < 0:
#             return False, self.data
#         self.rawData = self.rawData[idx:]
#         # print(self.rawData)
#         # check data length 2Byte
#         dataLen = unpack("H", self.rawData[2: 4])[0]
#         # print(dataLen)
#         frameLen = len(header) + 2 + dataLen + 2
#         frameDataLen = dataLen - 16

#         if len(self.rawData) < frameLen:
#             return False, self.data
#         # get data
#         frame = self.rawData[:frameLen]
#         # print(frame)
#         self.rawData = self.rawData[frameLen:]

#         frameTail = frame[-1]
#         # print(frameTail)
#         _sum = frame[-2]
#         # print(_sum)
#         # check sum
#         if _sum != sum(frame[:frameLen - 2]) % 256:
#             return True, self.data

#         frameID = unpack("H", frame[16:18])[0]
#         # print(frameID)

#         resR = unpack("B", frame[14:15])[0]
#         resC = unpack("B", frame[15:16])[0]
#         res = (resR, resC)
#         # print(res)
#         frameData = [unpack("H", frame[20+i:22+i])[0]
#                      for i in range(0, frameDataLen, 2)]

#         # if not frameID in self.data:
#         #     self.data[frameID] = {
#         #         "res": res,
#         #         "frameData": frameData
#         #     }
#         # else:
#         #     self.data[frameID]["res"] = res
#         #     self.data[frameID]["frameData"] = frameData

#         queueData = {
#             'frameID': frameID,
#             "res": res,
#             "frameData": frameData
#         }
#         self.queue.put(queueData)

#         return True, self.data

#     def pickColor(self, name: str):
#         if name in self.colors:
#             return self.colors[name]
#         else:
#             if not self.notUsedColors:
#                 self.notUsedColors = self.builtinColors.copy()
#             color = self.notUsedColors.pop(0)
#             self.colors[name] = color
#             return color

#     def update(self, data: dict):
#         # for k, v in data.items():
#         if not self.queue.empty():
#             v = self.queue.get()
#             k = v['frameID']
#             print("draw frame:", k)
#             res = v['res']
#             frameData = v['frameData']
#             arr = np.array(frameData, np.uint16)
#             arr[np.where(arr > 3000)] = 0
#             arr = arr.reshape(res)
#             arr = np.expand_dims(arr, 2)
#             # print(v)
#             self.imv.setImage(arr)
#             # color = self.pickColor(k)
#             # self.colors[k] = color
#             # self.curves[k] = self.p.plot(pen=pg.mkPen(color=color, width=2),
#             #                             name=k,)
#             # self.curves[k].setData(x=v["x"], y=v["y"])

#     def onData(self, data: bytes):
#         while 1:
#             haveFrame, allData = self.decodeData(data)
#             if not haveFrame:
#                 break
#             data = b''
#         self.updateSignal.emit(allData)


class Gragh_MetaSenseLite(Gragh_Widget_Base):
    updateSignal = pyqtSignal(dict)
    id = "MetaSenseLite"

    def __init__(self, parent=None, hintSignal=lambda type, title, msg: None, rmCallback=lambda widget: None, send=lambda x: None, config=None):
        default = {
            "xRange": 10,
            "xRangeEnable": True,
            "header": "\\x00\\xFF"
        }
        super().__init__(parent, hintSignal=hintSignal, rmCallback=rmCallback,
                         send=send, config=config, defaultConfig=default)
        self.headerBytes = utils.str_to_bytes(
            self.config["header"], escape=True, encoding="utf-8")
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        class ImageItemWithMouseHover(pg.ImageItem):
            def __init__(self, image=None, **kargs):
                super().__init__(image=image, kargs=kargs)

        pg.setConfigOptions(imageAxisOrder='row-major')
        self.imv = pg.ImageView(view=pg.PlotItem())
        self.imv.setMouseTracking(True)
        self.setMouseTracking(True)
        self.queue = Queue()
        self.onceShot = False
        self.frames = []
        self.distances = []
        jetcolors = [(128, 0, 0), (132, 0, 0), (136, 0, 0), (140, 0, 0), (144, 0, 0), (148, 0, 0), (152, 0, 0), (156, 0, 0), (160, 0, 0), (164, 0, 0), (168, 0, 0), (172, 0, 0), (176, 0, 0), (180, 0, 0), (184, 0, 0), (188, 0, 0), (192, 0, 0), (196, 0, 0), (200, 0, 0), (204, 0, 0), (208, 0, 0), (212, 0, 0), (216, 0, 0), (220, 0, 0), (224, 0, 0), (228, 0, 0), (232, 0, 0), (236, 0, 0), (240, 0, 0), (244, 0, 0), (248, 0, 0), (252, 0, 0), (255, 0, 0), (255, 4, 0), (255, 8, 0), (255, 12, 0), (255, 16, 0), (255, 20, 0), (255, 24, 0), (255, 28, 0), (255, 32, 0), (255, 36, 0), (255, 40, 0), (255, 44, 0), (255, 48, 0), (255, 52, 0), (255, 56, 0), (255, 60, 0), (255, 64, 0), (255, 68, 0), (255, 72, 0), (255, 76, 0), (255, 80, 0), (255, 84, 0), (255, 88, 0), (255, 92, 0), (255, 96, 0), (255, 100, 0), (255, 104, 0), (255, 108, 0), (255, 112, 0), (255, 116, 0), (255, 120, 0), (255, 124, 0), (255, 128, 0), (255, 132, 0), (255, 136, 0), (255, 140, 0), (255, 144, 0), (255, 148, 0), (255, 152, 0), (255, 156, 0), (255, 160, 0), (255, 164, 0), (255, 168, 0), (255, 172, 0), (255, 176, 0), (255, 180, 0), (255, 184, 0), (255, 188, 0), (255, 192, 0), (255, 196, 0), (255, 200, 0), (255, 204, 0), (255, 208, 0), (255, 212, 0), (255, 216, 0), (255, 220, 0), (255, 224, 0), (255, 228, 0), (255, 232, 0), (255, 236, 0), (255, 240, 0), (255, 244, 0), (255, 248, 0), (255, 252, 0), (254, 255, 1), (250, 255, 6), (246, 255, 10), (242, 255, 14), (238, 255, 18), (234, 255, 22), (230, 255, 26), (226, 255, 30), (222, 255, 34), (218, 255, 38), (214, 255, 42), (210, 255, 46), (206, 255, 50), (202, 255, 54), (198, 255, 58), (194, 255, 62), (190, 255, 66), (186, 255, 70), (182, 255, 74), (178, 255, 78), (174, 255, 82), (170, 255, 86), (166, 255, 90), (162, 255, 94), (158, 255, 98), (154, 255, 102), (150, 255, 106), (146, 255, 110), (142, 255, 114), (138, 255, 118), (134, 255, 122), (130, 255, 126),
                     (126, 255, 130), (122, 255, 134), (118, 255, 138), (114, 255, 142), (110, 255, 146), (106, 255, 150), (102, 255, 154), (98, 255, 158), (94, 255, 162), (90, 255, 166), (86, 255, 170), (82, 255, 174), (78, 255, 178), (74, 255, 182), (70, 255, 186), (66, 255, 190), (62, 255, 194), (58, 255, 198), (54, 255, 202), (50, 255, 206), (46, 255, 210), (42, 255, 214), (38, 255, 218), (34, 255, 222), (30, 255, 226), (26, 255, 230), (22, 255, 234), (18, 255, 238), (14, 255, 242), (10, 255, 246), (6, 255, 250), (2, 255, 254), (0, 252, 255), (0, 248, 255), (0, 244, 255), (0, 240, 255), (0, 236, 255), (0, 232, 255), (0, 228, 255), (0, 224, 255), (0, 220, 255), (0, 216, 255), (0, 212, 255), (0, 208, 255), (0, 204, 255), (0, 200, 255), (0, 196, 255), (0, 192, 255), (0, 188, 255), (0, 184, 255), (0, 180, 255), (0, 176, 255), (0, 172, 255), (0, 168, 255), (0, 164, 255), (0, 160, 255), (0, 156, 255), (0, 152, 255), (0, 148, 255), (0, 144, 255), (0, 140, 255), (0, 136, 255), (0, 132, 255), (0, 128, 255), (0, 124, 255), (0, 120, 255), (0, 116, 255), (0, 112, 255), (0, 108, 255), (0, 104, 255), (0, 100, 255), (0, 96, 255), (0, 92, 255), (0, 88, 255), (0, 84, 255), (0, 80, 255), (0, 76, 255), (0, 72, 255), (0, 68, 255), (0, 64, 255), (0, 60, 255), (0, 56, 255), (0, 52, 255), (0, 48, 255), (0, 44, 255), (0, 40, 255), (0, 36, 255), (0, 32, 255), (0, 28, 255), (0, 24, 255), (0, 20, 255), (0, 16, 255), (0, 12, 255), (0, 8, 255), (0, 4, 255), (0, 0, 255), (0, 0, 252), (0, 0, 248), (0, 0, 244), (0, 0, 240), (0, 0, 236), (0, 0, 232), (0, 0, 228), (0, 0, 224), (0, 0, 220), (0, 0, 216), (0, 0, 212), (0, 0, 208), (0, 0, 204), (0, 0, 200), (0, 0, 196), (0, 0, 192), (0, 0, 188), (0, 0, 184), (0, 0, 180), (0, 0, 176), (0, 0, 172), (0, 0, 168), (0, 0, 164), (0, 0, 160), (0, 0, 156), (0, 0, 152), (0, 0, 148), (0, 0, 144), (0, 0, 140), (0, 0, 136), (0, 0, 132), (0, 0, 128)]
        self.imv.setColorMap(pg.ColorMap(
            pos=np.linspace(0.0, 1.0, len(jetcolors)), color=jetcolors))
        # self.imv.setColorMap(pg.colormap.get('jet_r', source='matplotlib'))
        # self.imv.setColorMap(pg.colormap.get("CET-L17"))
        # self.plotWin = pg.GraphicsLayoutWidget()
        # self.plotWin.setMinimumHeight(200)
        # self.plotWin
        pg.setConfigOptions(antialias=True)
        rmBtn = QPushButton(_("Remove"))
        self.capTargetBtn = QPushButton(os.path.curdir)
        capBtn = QPushButton(_("Capture"))
        # rangeLabel = QLabel(_("Range:"))
        # rangeConf = QLineEdit(str(self.config["xRange"]))
        # rangeEnable = QCheckBox(_("Enable"))
        # rangeEnable.setChecked(self.config["xRangeEnable"])
        headerLabel = QLabel(_("Header:"))
        headerConf = QLineEdit(self.config["header"])
        self.headerBtn = QPushButton(_("Set"))

        rawCmdLabel = QLabel(_("RawCMD:"))
        rawCmdConf = QLineEdit(_("AT+ISP=0\\r"))
        rawCmdBtn = QPushButton(_("Send"))

        btnWin = QWidget()
        btnWin.layout = QVBoxLayout()
        btnWin.setLayout(btnWin.layout)
        ispRun = QCheckBox(_("ISP"))
        dispCbLcd = QCheckBox(_("LCD"))
        dispCbUsb = QCheckBox(_("USB"))
        dispCbUart = QCheckBox(_("UART"))
        antiMmiCb = QCheckBox(_("ANTIMMI"))

        vBoxWin = QWidget()
        vBoxWin.layout = QVBoxLayout()
        vBoxWin.setLayout(vBoxWin.layout)

        itemCb = QWidget()
        itemCb.layout = QHBoxLayout()
        itemCb.setLayout(itemCb.layout)

        binnItem = QComboBox()
        baudItem = QComboBox()

        focusCb = QCheckBox()
        focusX = QLineEdit("0")
        focusY = QLineEdit("0")
        focusD = QLineEdit("0")
        self.focus = (focusCb, (focusX, focusY), focusD)

        unitSliderBox = QWidget()
        unitSliderBox.layout = QHBoxLayout()
        unitSliderBox.setLayout(unitSliderBox.layout)
        unitLabel = QLabel(_("Unit:auto "))
        unitSlider = QSlider(Qt.Horizontal)
        self.unitSlider = unitSlider

        fpsSliderBox = QWidget()
        fpsSliderBox.layout = QHBoxLayout()
        fpsSliderBox.setLayout(fpsSliderBox.layout)
        fpsLabel = QLabel(_(" Fps:15   "))
        fpsSlider = QSlider(Qt.Horizontal)

        evSliderBox = QWidget()
        evSliderBox.layout = QHBoxLayout()
        evSliderBox.setLayout(evSliderBox.layout)
        evLabel = QLabel(_("  Ev:AE   "))
        evSlider = QSlider(Qt.Horizontal)

        hint = _("Protocol: 2Byte header + 2Byte length + 1Byte command + 1Byte output_mode + 1Byte Sensor Temp + 1Byte Driver Temp\n"
                 " 4Bytes exposure time + 1Byte error code + 1Byte reserved1 + 1Byte res rows + 1Byte res cols\n"
                 " 2Byte Frame ID + 1 Byte ISP version + 1 Byte reserved3\n"
                 " frame data\n"
                 " 1Byte checksum + 1Byte tail\n"
                 " length count from Byte4 to the Byte before Checksum\n"
                 "Protocol example code see help")
        headerConf.setToolTip(hint)
        headerLabel.setToolTip(hint)
        self.headerBtn.setToolTip(hint)
        # validator = QDoubleValidator()
        # rangeConf.setValidator(validator)
        self.layout.addWidget(self.imv, 0, 0, 3, 3)
        # self.layout.addWidget(self.plotWin, 0, 0, 1, 3)
        self.layout.addWidget(rmBtn, 3, 0, 1, 1)
        self.layout.addWidget(self.capTargetBtn, 3, 1, 1, 1)
        self.layout.addWidget(capBtn, 3, 2, 1, 1)
        # self.layout.addWidget(rangeLabel, 2, 0, 1, 1)
        # self.layout.addWidget(rangeConf, 2, 1, 1, 1)
        # self.layout.addWidget(rangeEnable, 2, 2, 1, 1)
        self.layout.addWidget(headerLabel, 4, 0, 1, 1)
        self.layout.addWidget(headerConf, 4, 1, 1, 1)
        self.layout.addWidget(self.headerBtn, 4, 2, 1, 1)

        self.layout.addWidget(rawCmdLabel, 5, 0, 1, 1)
        self.layout.addWidget(rawCmdConf, 5, 1, 1, 1)
        self.layout.addWidget(rawCmdBtn, 5, 2, 1, 1)

        self.layout.addWidget(btnWin, 6, 0, 2, 1)
        btnWin.layout.addWidget(ispRun)
        btnWin.layout.addWidget(dispCbLcd)
        btnWin.layout.addWidget(dispCbUsb)
        btnWin.layout.addWidget(dispCbUart)
        btnWin.layout.addWidget(antiMmiCb)

        self.layout.addWidget(vBoxWin, 6, 1, 2, 2)
        vBoxWin.layout.addWidget(itemCb)
        itemCb.layout.addWidget(QLabel(_("Binn:")))
        itemCb.layout.addWidget(binnItem)
        itemCb.layout.addWidget(QLabel(_("Baud:")))
        itemCb.layout.addWidget(baudItem)
        itemCb.layout.addWidget(focusCb)
        itemCb.layout.addWidget(QLabel(_("D:")))
        itemCb.layout.addWidget(focusD)
        itemCb.layout.addWidget(QLabel(_("X:")))
        itemCb.layout.addWidget(focusX)
        itemCb.layout.addWidget(QLabel(_("Y:")))
        itemCb.layout.addWidget(focusY)

        unitSliderBox.layout.addWidget(unitLabel)
        unitSliderBox.layout.addWidget(unitSlider)
        vBoxWin.layout.addWidget(unitSliderBox)

        fpsSliderBox.layout.addWidget(fpsLabel)
        fpsSliderBox.layout.addWidget(fpsSlider)
        vBoxWin.layout.addWidget(fpsSliderBox)

        evSliderBox.layout.addWidget(evLabel)
        evSliderBox.layout.addWidget(evSlider)
        vBoxWin.layout.addWidget(evSliderBox)

        self.resize(600, 400)
        # self.p = self.plotWin.addPlot(colspan=2)
        # self.p.addLegend()
        # self.p.setXRange(0, self.config["xRange"])
        self.updateSignal.connect(self.update)
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

        imgView = self.imv.getView()
        imgItem = self.imv.getImageItem()
        # p = imgItem.ItemCursorHasChanged.connect(lambda x: print(x))
        scene = imgItem.scene()

        # imgItem.mouseMoveEvent =

        # def ptint_wr(wr):
        #     if len(wr[0]) > 1:
        #         ichild = self.imv.children()[1].children()[0].children()[3]
        #         # print(ichild.pos())
        #         imgItm = wr[0][1]
        #         cursor_pos = imgItm.cursor().pos()

        #         ise = imgItm.scene()
        #         iv = ise.views()[0]
        #         print(iv.pos(), end=', ')
        #         abs_pos = iv.mapToGlobal(iv.pos())
        #         print(abs_pos)

        # self.proxy = pg.SignalProxy(scene.sigMouseHover, rateLimit=60,
        #                             slot=ptint_wr)

        # self.proxy1 = pg.SignalProxy(scene.sigMouseMoved , rateLimit=60,
        #                             slot=lambda x:print(x))

        # rangeConf.textChanged.connect(self.setRange)
        # rangeEnable.clicked.connect(lambda: self.setEnableRange(rangeEnable.isChecked()))
        self.headerBtn.clicked.connect(
            lambda: self.setHeader(headerConf.text()))
        headerConf.textChanged.connect(self.headerChanged)

        rmBtn.clicked.connect(self.remove)
        self.capTargetBtn.clicked.connect(lambda: self.capTargetBtn.setText(QFileDialog.getExistingDirectory(
            None, "Choose Directory To Save", os.path.expanduser("~")) or self.capTargetBtn.text()))
        capBtn.clicked.connect(self.capture)
        rawCmdBtn.clicked.connect(lambda: self.sendCmd(rawCmdConf.text()))

        ispRun.setChecked(True)
        ispRun.toggled.connect(
            lambda x: self.sendCmd("AT+ISP=%1d\r" % (x)))

        def dispChanged():
            self.sendCmd("AT+DISP=%1d\r" % (1 * dispCbLcd.isChecked() +
                         2 * dispCbUsb.isChecked() + 4 * dispCbUart.isChecked()))
        dispCbLcd.setChecked(True)
        dispCbLcd.toggled.connect(dispChanged)
        dispCbUsb.toggled.connect(dispChanged)
        dispCbUart.toggled.connect(dispChanged)

        antiMmiCb.setChecked(True)
        antiMmiCb.toggled.connect(
            lambda x: self.sendCmd("AT+ANTIMMI=%1d\r" % (x)))

        binnItem.addItems(["1x1", "2x2", "4x4"])
        binnItem.setCurrentIndex(0)
        binnItem.currentIndexChanged.connect(
            lambda i: self.sendCmd("AT+BINN=%1d\r" % (1 << i)))

        baudItem.addItems(["9600", " 57600", "115200", "230400",
                          "460800", "921600", "1000000", "2000000", "3000000"])
        baudItem.setCurrentIndex(2)
        baudItem.currentIndexChanged.connect(
            lambda i: self.sendCmd("AT+BAUD=%1d\r" % (i)))

        def focusCbChanged(sta):
            if sta:
                x, y = 0, 0
                try:
                    x = int(focusX.text())
                    y = int(focusY.text())
                    assert(x >= 0 and y >= 0)
                    assert(x < 100 and y < 100)
                except Exception:
                    x, y = 0, 0
                focusX.setText(str(x))
                focusY.setText(str(y))
                focusCb.setChecked(True)
                # print("set ({x},{y})".format(x=x, y=y))
        focusCb.toggled.connect(focusCbChanged)

        def focusChanged(text):
            focusCb.setChecked(False)
        focusX.textChanged.connect(focusChanged)
        focusY.textChanged.connect(focusChanged)

        focusD.setEnabled(False)

        unitSlider.setMaximum(10)
        unitSlider.setSingleStep(1)
        unitSlider.setTickInterval(1)
        unitSlider.setTickPosition(QSlider.TicksBelow)
        unitSlider.valueChanged.connect(
            lambda i: (unitLabel.setText("Unit: %-5s" % ("auto" if i == 0 else str(i))), self.sendCmd("AT+UNIT=%d\r" % (i))))
        unitSlider.setValue(0)

        fpsSlider.setMinimum(1)
        fpsSlider.setMaximum(30)
        fpsSlider.setSingleStep(1)
        fpsSlider.setTickInterval(1)
        fpsSlider.setTickPosition(QSlider.TicksBelow)
        fpsSlider.valueChanged.connect(
            lambda i: (fpsLabel.setText(" Fps: %-5d" % (i)), self.sendCmd("AT+FPS=%d\r" % (i))))
        fpsSlider.setValue(1)

        evSlider.setMinimum(0)
        evSlider.setMaximum(40000)
        evSlider.setSingleStep(2000)
        evSlider.setTickInterval(2000)
        evSlider.setTickPosition(QSlider.TicksBelow)
        evSlider.valueChanged.connect(
            lambda i: (evLabel.setText("  Ev: %-5s" % ("AE" if i == 0 else str(i))), self.sendCmd("AT+AE=%d\r" % (1 if i == 0 else 0)), self.sendCmd("AT+EV=%d\r" % (i))))
        evSlider.setValue(0)

    def remove(self):
        self.rmCallback(self)

    # def setRange(self, text):
    #     if text:
    #         self.config["xRange"] = float(text)

    # def setEnableRange(self, en):
    #     self.config["xRangeEnable"] = en

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
                         |    header(2B)    | len(2B) | command(1B) | output_mode(1B)     | sensor temp(1B) | driver temp(1B) |
                         |     0xCC  0xA0      |  >=18   |             | 0:Depth only, 1:+IR |    uint8        | uint8           |
                         -------------------------------------------------------------------------------------------------------
                         |    exposure time(4B)    | errcode(1B) | reserved1(1B) | res_rows(1B) | res_cols(1B) |
                         |[23:20][19:12][11:8][7:0]|             |       0x0     |     uint8    |     uint8    |
                         ---------------------------------------------------------------------------------------
                         |    Frame ID(2B)    | ISP ver(1B) | reserved3(1B) | frame data((len-16)B) | checksum(1B) | tail(1B) |
                         |     [11:0]         |     0x23    |       0x0     | xxxxxxxxxxxxxxxxxxxxx | sum of above |   0xDD   |

            @return haveFrame, dict {
                "frameID": {
                    "res": tunple(w, h)
                    "frameData": []
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
        # print(self.rawData)
        # check data length 2Byte
        dataLen = unpack("H", self.rawData[2: 4])[0]
        # print("len: "+str(dataLen))
        frameLen = len(header) + 2 + dataLen + 2
        frameDataLen = dataLen - 16

        if len(self.rawData) < frameLen:
            return False, self.data
        # get data
        frame = self.rawData[:frameLen]
        # print(frame.hex())
        self.rawData = self.rawData[frameLen:]

        frameTail = frame[-1]
        # print("tail: "+str(hex(frameTail)))
        _sum = frame[-2]
        # print("checksum: "+str(hex(_sum)))
        # check sum
        # spi has no checksum but i add one
        if frameTail != 0xdd and _sum != sum(frame[:frameLen - 2]) % 256:
            return False, self.data

        frameID = unpack("H", frame[16:18])[0]
        # print("frame ID: "+str(frameID))

        resR = unpack("B", frame[14:15])[0]
        resC = unpack("B", frame[15:16])[0]
        res = (resR, resC)
        # print(res)
        # frameData=[ unpack("H", frame[20+i:22+i])[0] for i in range(0, frameDataLen, 2) ]
        frameData = [unpack("B", frame[20+i:21+i])[0]
                     for i in range(0, frameDataLen, 1)]

        # if not frameID in self.data:
        #     self.data[frameID] = {
        #         "res": res,
        #         "frameData": frameData
        #     }
        # else:
        #     self.data[frameID]["res"] = res
        #     self.data[frameID]["frameData"] = frameData

        queueData = {
            'frameID': frameID,
            "res": res,
            "frameData": frameData
        }
        self.queue.put(queueData)

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
        # for k, v in data.items():
        if not self.queue.empty():
            v = self.queue.get()
            k = v['frameID']
            # print("draw frame:", k)
            res = v['res']
            frameData = v['frameData']
            arr = np.array(frameData, np.uint8)
            # arr[np.where(arr>3000)] = 0
            arr = arr.reshape(res)
            # arr = 255 - arr
            if self.onceShot:
                # print(rgba_img.shape)
                # DownloadsPATH = os.path.join(
                #     os.path.expanduser("~"), 'Downloads'
                DownloadsPATH = self.capTargetBtn.text()
                fname = "%d-unit%d" % ((time.time_ns() //
                                       1_000_000), self.unitSlider.value())
                Image.fromarray(arr).save(os.path.join(DownloadsPATH,
                                                       fname + ".bmp"))
                # plt.imsave(os.path.join(DownloadsPATH,
                #                         fname + ".bmp"), arr, cmap=plt.get_cmap('gray'))
                self.onceShot = False

            # cmap = plt.get_cmap('jet')
            # z = arr.transpose()
            # z = np.expand_dims(z, 2)

            # rgba_img = cmap(z)
            # rgba_img = np.squeeze(rgba_img)

            # print(rgba_img.shape)
            # print(v)

            if len(self.frames) != 0 and self.frames[len(self.frames)-1].shape != arr.T.shape:
                self.frames.clear()
            self.frames.append(arr)
            np_arrs = np.array(self.frames)

            if self.focus[0].isChecked():
                def compute_real_distance(val, unit):
                    ret = 0
                    if unit != 0:
                        ret = val * unit
                    else:
                        ret = int(val) / 5.1
                        ret *= ret

                    if len(self.distances) == 0:
                        for _ in range(8):
                            self.distances.append(ret)
                    else:
                        self.distances.append(ret)
                        self.distances = self.distances[-8:]
                    return int(np.mean(self.distances))

                self.focus[2].setText(str(compute_real_distance(np_arrs[len(
                    self.frames)-1][int(self.focus[1][0].text()), int(self.focus[1][1].text())], self.unitSlider.value()))+"mm")
                # print(self.focus[2].text())

                def draw_reticle_and_info(buf, x, y):
                    ll = buf.shape[0] // 25
                    u, d, l, r = min(ll*25, max(0, y-ll)), max(0, min(ll*25, y+ll+1)
                                                               ), min(ll*25, max(0, x-ll)), max(0, min(ll*25, x+ll+1))
                    buf[u:d, x] = 0x00
                    buf[y, l:r] = 0x00
                draw_reticle_and_info(np_arrs[len(self.frames)-1],
                                      int(self.focus[1][0].text()), int(self.focus[1][1].text()))

            self.imv.clear()
            self.imv.setImage(np_arrs)  # , autoRange=False)
            self.imv.setCurrentIndex(len(self.frames)-1)
            # color = self.pickColor(k)
            # self.colors[k] = color
            # self.curves[k] = self.p.plot(pen=pg.mkPen(color=color, width=2),
            #                             name=k,)
            # self.curves[k].setData(x=v["x"], y=v["y"])

            # imgItem = self.imv.getImageItem()
            # imgView = self.imv.getView()
            # print(imgItem.boundingRect())
            # print(imgView.viewGeometry())

    def capture(self):
        self.onceShot = True

    def onData(self, data: bytes):
        while True:
            haveFrame, allData = self.decodeData(data)
            if not haveFrame:
                break
            data = b''
        self.updateSignal.emit(allData)

    def sendCmd(self, cmd):
        send_bytes = utils.str_to_bytes(cmd, escape=True, encoding="ASCII")
        print(send_bytes)
        print(len(send_bytes))
        print()
        self.send(send_bytes)


graghWidgets = {
    Gragh_Plot.id: Gragh_Plot,
    Gragh_Button.id: Gragh_Button,
    # Gragh_DragTof.id: Gragh_DragTof,
    Gragh_MetaSenseLite.id: Gragh_MetaSenseLite,
}
