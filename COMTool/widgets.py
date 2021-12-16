from PyQt5.QtCore import pyqtSignal, QPoint, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QStyleOption, QStyle, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QPainter
import os

class TitleBar(QWidget):
    windowMovedSignal = pyqtSignal(QPoint)
    def __init__(self, parent, icon=None, title="", height=35, btnContents=["-", ["□", "❒"], "×", ["○", "●"] ]) -> None:
        super().__init__()
        self.parent = parent
        self.mPos = None
        self.btnContents = btnContents
        parent.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setFixedHeight(height)
        if icon and os.path.exists(icon):
            iconWidget = QLabel()
            iconWidget.setPixmap(QPixmap(icon).scaled(self.height(), self.height()))
            layout.addWidget(iconWidget)
            iconWidget.setProperty("class", "icon")
        self.min = QPushButton(btnContents[0])
        self.max = QPushButton(btnContents[1][0])
        self.close = QPushButton(btnContents[2])
        self.top = QPushButton(btnContents[3][0])
        self.title = QLabel(title)
        layout.addWidget(self.title)
        layout.addWidget(self.top)
        layout.addStretch(1)
        layout.addWidget(self.min)
        layout.addWidget(self.max)
        layout.addWidget(self.close)
        self.min.setFixedHeight(self.height())
        self.max.setFixedHeight(self.height())
        self.close.setFixedHeight(self.height())
        self.top.setFixedHeight(self.height())

        self.min.setMinimumWidth(self.height())
        self.max.setMinimumWidth(self.height())
        self.close.setMinimumWidth(self.height())
        self.top.setMinimumWidth(self.height())

        self.min.setProperty("class", "min")
        self.max.setProperty("class", "max")
        self.close.setProperty("class", "close")
        self.title.setProperty("class", "title")
        self.top.setProperty("class", "top")
        self.close.clicked.connect(lambda : parent.close())
        self.max.clicked.connect(self.onSetMaximized)
        self.min.clicked.connect(lambda : parent.setWindowState(Qt.WindowNoState) if parent.windowState() == Qt.WindowMinimized else parent.setWindowState(Qt.WindowMinimized))
        self.top.clicked.connect(self.onSetTop)
        self.windowMovedSignal.connect(self.onParentWindowMove)
        self.setProperty("class", "TitleBar")

    def mouseDoubleClickEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.onSetMaximized()

    def onSetMaximized(self):
        if self.parent.windowState() == Qt.WindowNoState:
            self.parent.setWindowState(Qt.WindowMaximized)
            if self.btnContents[1]:
                self.max.setText(self.btnContents[1][1])
        else:
            self.parent.setWindowState(Qt.WindowNoState)
            self.max.setText(self.btnContents[1][0])

    def onSetTop(self):
        flags = self.parent.windowFlags()
        needShow = self.parent.isVisible()
        if flags & Qt.WindowStaysOnTopHint:
            flags &=  (~Qt.WindowStaysOnTopHint)
            self.parent.setWindowFlags(flags)
            self.top.setText(self.btnContents[3][0])
            self.top.setProperty("class", "top")
        else:
            flags |= Qt.WindowStaysOnTopHint
            self.parent.setWindowFlags(flags)
            self.top.setText(self.btnContents[3][1])
            self.top.setProperty("class", "topActive")
        self.style().unpolish(self.top)
        self.style().polish(self.top)
        self.update()
        if needShow:
            self.parent.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mPos = event.pos()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.mPos = None
        event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mPos:
            self.windowMovedSignal.emit(self.mapToGlobal(event.pos() - self.mPos))
        event.accept()

    def onParentWindowMove(self, pos):
        if self.parent.windowState() == Qt.WindowMaximized or self.parent.windowState() == Qt.WindowFullScreen:
            return
        self.parent.move(pos)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    style = '''
    .TitleBar {
        background-color: #0b1722;
        color: white;
    }
    .TitleBar QPushButton {
        border: none;
    }
    .TitleBar .icon{
        margin-left: 5;
    }
    .TitleBar .title{
        margin-left: 5;
        color: white;
    }
    .TitleBar .top{
        margin-left: 5;
        color: white;
        border-radius: 20;
    }
    .TitleBar .top:hover{
        background-color: #273b4e;
    }
    .TitleBar .topActive{
        margin-left: 5;
        color: white;
        border-radius: 20;
        background-color: #273b4e;
    }
    .TitleBar .min{
        background-color: #53c22a;
        color: white;
    }
    .TitleBar .max{
        background-color: #e5bf28;
        color: white;
    }
    .TitleBar .close{
        background-color: #f45952;
        color: white;
    }
    .TitleBar .min:hover {
        background-color: #2ba13e;
    }
    .TitleBar .max:hover {
        background-color: #cf9001;
    }
    .TitleBar .close:hover {
        background-color: #df2f25;
    }
    '''

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            widget = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0,0,0,0)
            widget.setLayout(layout)
            content = QVBoxLayout()
            label = QLabel("hello")
            content.addWidget(label)
            bar = TitleBar(self, icon = "assets/logo.png", title="标题", height=35)
            layout.addWidget(bar)
            layout.addLayout(content)
            self.resize(800, 600)
            self.setCentralWidget(widget)
            self.show()


    app = QApplication(sys.argv)
    app.setStyleSheet(style)
    w = MainWindow()
    app.exec_()

