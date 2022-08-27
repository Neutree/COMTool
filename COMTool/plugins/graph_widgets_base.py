
from PyQt5.QtWidgets import (QWidget)

class Graph_Widget_Base(QWidget):
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

