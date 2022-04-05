from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel)
from PyQt5.QtCore import pyqtSignal

import pyqtgraph as pg


class Gragh_Widget_Base(QWidget):
    def onData(self, data:bytes):
        pass


class Gragh_Plot(Gragh_Widget_Base):
    updateSignal = pyqtSignal(bytes)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.plot = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.plot)
        self.resize(600, 400)
        self.p = self.plot.addPlot(colspan=2)
        self.p.setLabel('bottom', 'Time', 's')
        self.p.setXRange(-10, 0)
        self.updateSignal.connect(self.update)
        self.data = [
            [],
            []
        ]

    def update(self, data):
        import time, math
        t = time.time()
        v = math.sin(t)
        self.data[0].append(t)
        self.data[1].append(v)
        curve = self.p.plot()
        curve.setData(x=list(self.data[0]), y=list(self.data[1]))

    def onData(self, data: bytes):
        self.updateSignal.emit(data)


graghWidgets = {
    "plot": Gragh_Plot,
}

