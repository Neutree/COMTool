from PyQt5.QtCore import pyqtSignal, QPoint, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStyleOption, QStyle, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QPainter
import os, sys

class TitleBar(QWidget):
    windowMovedSignal = pyqtSignal(QPoint)
    def __init__(self, parent, icon=None, title="", height=35,
                        btnContents=[
                            "-",
                            ["□", "❒"],
                            "×", ["○", "●"]
                        ],
                        brothers=[]) -> None:
        super().__init__()
        self._height = height
        self.parent = parent
        self.mPos = None
        self.btnContents = btnContents
        parent.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        layout = QHBoxLayout()
        if brothers:
            rootLayout = QVBoxLayout()
            rootLayout.setContentsMargins(0,0,0,0)
            rootLayout.setSpacing(0)
            widget = QWidget()
            widget.setProperty("class", "TitleBar")
            widget.setLayout(layout)
            widget.setFixedHeight(height)
            rootLayout.addWidget(widget)
            for w in brothers:
                rootLayout.addWidget(w)
                self._height += w.height()
            self.setLayout(rootLayout)
        else:
            self.setLayout(layout)
        self.setFixedHeight(self._height)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        iconWidget = None
        if icon and os.path.exists(icon):
            iconWidget = QLabel()
            iconWidget.setPixmap(QPixmap(icon).scaled(height, height))
            iconWidget.setProperty("class", "icon")
        self.min = QPushButton(btnContents[0])
        self.max = QPushButton(btnContents[1][0])
        self.close = QPushButton(btnContents[2])
        self.top = QPushButton(btnContents[3][0])
        self.title = QLabel(title)
        if sys.platform.startswith("darwin"):
            layout.addWidget(self.close)
            layout.addWidget(self.max)
            layout.addWidget(self.min)
            layout.addStretch(1)
            layout.addWidget(self.top)
            layout.addWidget(self.title)
            if iconWidget:
                layout.addWidget(iconWidget)
        else:
            if iconWidget:
                layout.addWidget(iconWidget)
            layout.addWidget(self.title)
            layout.addWidget(self.top)
            layout.addStretch(1)
            layout.addWidget(self.min)
            layout.addWidget(self.max)
            layout.addWidget(self.close)
        self.min.setFixedHeight(height)
        self.max.setFixedHeight(height)
        self.close.setFixedHeight(height)
        self.top.setFixedHeight(height)

        self.min.setMinimumWidth(height)
        self.max.setMinimumWidth(height)
        self.close.setMinimumWidth(height)
        self.top.setMinimumWidth(height)

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

class WindowResizableMixin:
    '''
        attrs:
            self.rootLayout: root layout, QVBoxLayout
            self.contentLayout: content layout, QVBoxLayout
            self.titleBar: titleBar widget
        if not inherits from Widget, you should add a widget, and set self.rootLayout as its layout, and call `widget.setMouseTracking(True)`
    '''
    def __init__(self, titleBar=None, contentLayoutType=QVBoxLayout) -> None:
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self._padding = 6
        # wrapper, no padding
        self.rootLayout = QVBoxLayout()
        self.rootLayout.setContentsMargins(0,0,0,0)
        self.rootLayout.setSpacing(0)
        # title bar
        if titleBar:
            self.titleBar = titleBar
        else:
            self.titleBar = TitleBar(self, icon = "assets/logo.png", title="标题", height=35)
        # content widget, have padding for resize
        content = QWidget()
        self.contentLayout = contentLayoutType()
        self.contentLayout.setContentsMargins(self._padding, 0, self._padding, self._padding)
        self.contentLayout.setSpacing(0)
        content.setLayout(self.contentLayout)
        self.rootLayout.addWidget(self.titleBar)
        self.rootLayout.addWidget(content)

        self.titleBar.setMouseTracking(True)
        self.setMouseTracking(True)
        content.setMouseTracking(True)

    def resizeEvent(self, QResizeEvent):
        self._right_rect = [QPoint(x, y) for x in range(self.width() - self._padding + 1, self.width())
                for y in range(1, self.height() - self._padding)]
        self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - self._padding)
                for y in range(self.height() - self._padding + 1, self.height())]
        self._corner_rect = [QPoint(x, y) for x in range(self.width() - self._padding, self.width() + 1)
                    for y in range(self.height() - self._padding, self.height() + 1)]
    
    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton) and (event.pos() in self._corner_rect):
            self._corner_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._right_rect):
            self._right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._bottom_rect):
            self._bottom_drag = True
            event.accept()
        # elif (event.button() == Qt.LeftButton) and (event.y() < self.titleBar.height()):
        #     self._move_drag = True
        #     self.move_DragPosition = event.globalPos() - self.pos()
        #     event.accept()
    
    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.pos() in self._corner_rect:
            self.setCursor(Qt.SizeFDiagCursor)
        elif QMouseEvent.pos() in self._bottom_rect:
            self.setCursor(Qt.SizeVerCursor)
        elif QMouseEvent.pos() in self._right_rect:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        if Qt.LeftButton and self._right_drag:
            self.resize(QMouseEvent.pos().x(), self.height())
            QMouseEvent.accept()
        elif Qt.LeftButton and self._bottom_drag:
            self.resize(self.width(), QMouseEvent.pos().y())
            QMouseEvent.accept()
        elif Qt.LeftButton and self._corner_drag:
            self.resize(QMouseEvent.pos().x(), QMouseEvent.pos().y())
            QMouseEvent.accept()
        # elif Qt.LeftButton and self._move_drag:
        #     self.move(QMouseEvent.globalPos() - self.move_DragPosition)
        #     QMouseEvent.accept()
    
    def mouseReleaseEvent(self, QMouseEvent):
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self.setCursor(Qt.ArrowCursor)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    style = '''
    QWidget {
        background-color: red;
    }
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
        background-color: #0b1722;
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
    QLabel {
        background-color: black;
    }
    '''

    class MainWindow(QMainWindow, WindowResizableMixin):
        _padding = 5
        def __init__(self) -> None:
            super().__init__()
            widget = QWidget()
            widget.setMouseTracking(True)
            widget.setLayout(self.rootLayout)
            label = QLabel("hello hhhhhhhhhhh")
            self.contentLayout.addWidget(label)
            self.resize(800, 600)
            self.setCentralWidget(widget)
            self.show()


    app = QApplication(sys.argv)
    app.setStyleSheet(style)
    w = MainWindow()
    app.exec_()

