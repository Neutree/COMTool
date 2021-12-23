from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QEvent, QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStyleOption, QStyle, QPushButton, QTextEdit, QPlainTextEdit, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QMouseEvent, QColor
import qtawesome as qta # https://github.com/spyder-ide/qtawesome
import os, sys

try:
    import utils_ui
except Exception:
    from COMTool import utils_ui

class TitleBar(QWidget):
    def __init__(self, parent, icon=None, title="", height=35,
                        btnIcons = None,
                        brothers=[],
                        widgets=[[], []]
                ) -> None:
        super().__init__()
        self._height = height
        self.parent = parent
        if not btnIcons:
            btnIcons = [
                "mdi.window-minimize",
                ["mdi.window-maximize", "mdi.window-restore"],
                "mdi.window-close",
                ["ph.push-pin-bold", "ph.push-pin-fill"]
            ]
        self.btnIcons = btnIcons
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
        self.min = QPushButton("")
        self.max = QPushButton("")
        self.close = QPushButton("")
        self.top = QPushButton("")
        utils_ui.setButtonIcon(self.min, btnIcons[0])
        utils_ui.setButtonIcon(self.max, btnIcons[1][0])
        utils_ui.setButtonIcon(self.close, btnIcons[2])
        utils_ui.setButtonIcon(self.top, btnIcons[3][0])
        self.title = QLabel(title)
        widgets_l, widgets_r = widgets
        if sys.platform.startswith("darwin"):
            layout.addWidget(self.close)
            layout.addWidget(self.min)
            layout.addWidget(self.max)
            for w in widgets_r:
                layout.addWidget(w)
            layout.addStretch(0)
            if iconWidget:
                layout.addWidget(iconWidget)
            layout.addWidget(self.title)
            layout.addStretch(0)
            layout.addWidget(self.top)
            for w in widgets_l:
                layout.addWidget(w)
        else:
            if iconWidget:
                layout.addWidget(iconWidget)
            layout.addWidget(self.title)
            layout.addWidget(self.top)
            for w in widgets_l:
                layout.addWidget(w)
            layout.addStretch(0)
            for w in widgets_r:
                layout.addWidget(w)
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
        self.max.clicked.connect(lambda : self.onSetMaximized(fromMaxBtn=True))
        self.min.clicked.connect(lambda : parent.setWindowState(Qt.WindowNoState) if parent.windowState() == Qt.WindowMinimized else parent.setWindowState(Qt.WindowMinimized))
        self.top.clicked.connect(self.onSetTop)
        self.setProperty("class", "TitleBar")

    def mouseDoubleClickEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.onSetMaximized()

    def onSetMaximized(self, isMax = None, fromMaxBtn=False, fullScreen = False):
        if not isMax is None:
            if isMax:
                utils_ui.setButtonIcon(self.max, self.btnIcons[1][1])
            else:
                utils_ui.setButtonIcon(self.max, self.btnIcons[1][0])
            return
        status = Qt.WindowNoState
        if fullScreen:
            if self.parent.windowState() != Qt.WindowFullScreen:
                status = Qt.WindowFullScreen
        elif self.parent.windowState() == Qt.WindowNoState:
            if fromMaxBtn and sys.platform.startswith("darwin"): # mac max button to full screen
                status = Qt.WindowFullScreen
            else:
                status = Qt.WindowMaximized
        if status == Qt.WindowNoState:
            utils_ui.setButtonIcon(self.max, self.btnIcons[1][0])
        else:
            utils_ui.setButtonIcon(self.max, self.btnIcons[1][1])
        self.parent.setWindowState(status)
        if status == Qt.WindowFullScreen:
            self.hide()
        else:
            self.show()

    def onSetTop(self):
        flags = self.parent.windowFlags()
        needShow = self.parent.isVisible()
        if flags & Qt.WindowStaysOnTopHint:
            flags &=  (~Qt.WindowStaysOnTopHint)
            self.parent.setWindowFlags(flags)
            utils_ui.setButtonIcon(self.top, self.btnIcons[3][0])
            self.top.setProperty("class", "top")
        else:
            flags |= Qt.WindowStaysOnTopHint
            self.parent.setWindowFlags(flags)
            utils_ui.setButtonIcon(self.top, self.btnIcons[3][1])
            self.top.setProperty("class", "topActive")
        self.style().unpolish(self.top)
        self.style().polish(self.top)
        self.update()
        if needShow:
            self.parent.show()

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

class EventFilter(QObject):
    Margins = 4  # 边缘边距
    windows = []
    _readyToMove = False
    _moving = False
    _resizeCursor = False

    def listenWindow(self, window):
        self.windows.append(window)

    def _get_edges(self, pos, width, height):
        edge = 0
        x, y = pos.x(), pos.y()

        if y <= self.Margins:
            edge |= Qt.TopEdge
        if x <= self.Margins:
            edge |= Qt.LeftEdge
        if x >= width - self.Margins:
            edge |= Qt.RightEdge
        if y >= height - self.Margins:
            edge |= Qt.BottomEdge
        return edge

    def _get_cursor(self, edges):
        if edges == Qt.LeftEdge | Qt.TopEdge or edges == Qt.RightEdge | Qt.BottomEdge:
            self._resizeCursor = True
            return Qt.SizeFDiagCursor
        elif edges == Qt.RightEdge | Qt.TopEdge or edges == Qt.LeftEdge | Qt.BottomEdge:
            self._resizeCursor = True
            return Qt.SizeBDiagCursor
        elif edges == Qt.LeftEdge or edges == Qt.RightEdge:
            self._resizeCursor = True
            return Qt.SizeHorCursor
        elif edges == Qt.TopEdge or edges == Qt.BottomEdge:
            self._resizeCursor = True
            return Qt.SizeVerCursor
        if self._resizeCursor:
            self._resizeCursor = False
            return Qt.ArrowCursor
        return None

    def moveOrResize(self, window, pos, width, height):
        edges = self._get_edges(pos, width, height)
        if edges:
            if window.windowState() == Qt.WindowNoState:
                window.startSystemResize(edges)
        else:
            if window.windowState() != Qt.WindowFullScreen:
                window.startSystemMove()

    def eventFilter(self, obj, event):
        # print(obj, event.type(), obj.isWindowType(), QEvent.MouseMove)
        if obj.isWindowType():
            # top window 处理光标样式
            if event.type() == QEvent.MouseMove and obj.windowState() == Qt.WindowNoState:
                cursor = self._get_cursor(self._get_edges(event.pos(), obj.width(), obj.height()))
                if not cursor is None:
                    obj.setCursor(cursor)
            if event.type() == QEvent.TouchUpdate and not self._moving:
                self._moving = True
                self.moveOrResize(obj, event.pos(), obj.width(), obj.height())
        elif isinstance(event, QMouseEvent):
            if obj in self.windows:
                if event.button() == Qt.LeftButton :
                    if event.type() == QEvent.MouseButtonPress:
                        self._readyToMove = True
                    # elif event.type() == QEvent.MouseButtonDblClick:
                    #     print(obj, event.type(), event)
                elif event.type() == QEvent.MouseMove and self._readyToMove and not self._moving:
                    self._moving = True
                    self.moveOrResize(obj.windowHandle(), event.pos(), obj.width(), obj.height())
        if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.Move:
            self._readyToMove = False
            self._moving = False
        return False


class CustomTitleBarWindowMixin:
    def __init__(self, titleBar = None, init = False):
        if not init:
            return
        isQMainWindow = False
        for base in self.__class__.__bases__:
            if base == QMainWindow:
                isQMainWindow = True
                break
        if isQMainWindow:
            self.root = QWidget()
            self.setCentralWidget(self.root)
        else:
            self.root = self
        self.root.setProperty("class", "customTilebarWindow")
        self.rootLayout = QVBoxLayout()
        # title bar
        if titleBar:
            self.titleBar = titleBar
        else:
            self.titleBar = TitleBar(self, icon = "assets/logo.png", title="标题", height=35)
        self.contentWidget = QWidget()
        self.rootLayout.addWidget(self.titleBar)
        self.rootLayout.addWidget(self.contentWidget)
        self.root.setLayout(self.rootLayout)
        self.rootLayout.setContentsMargins(0, 0, 0, 0) # padding
        self.root.setMouseTracking(True)
        self.titleBar.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        self.init_vars()

    def changeEvent(self, event):
        # super(CustomTitleBarWindowMixin, self).changeEvent(event)
        self.titleBar.onSetMaximized(isMax = self.isMaximized())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.titleBar.onSetMaximized(fullScreen=True)

    def keyReleaseEvent(self,event):
        pass

    # def paintEvent(self, event):
    #     # 透明背景但是需要留下一个透明度用于鼠标捕获
    #     painter = QPainter(self)
    #     painter.fillRect(self.rect(), QColor(255, 255, 255, 1))

    def init_vars(self):
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self._padding = 6
        self.mPos = None

    # def resizeEvent(self, QResizeEvent):
    #     self._right_rect = [QPoint(x, y) for x in range(self.width() - self._padding + 1, self.width())
    #             for y in range(1, self.height() - self._padding)]
    #     self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - self._padding)
    #             for y in range(self.height() - self._padding + 1, self.height())]
    #     self._corner_rect = [QPoint(x, y) for x in range(self.width() - self._padding, self.width() + 1)
    #                 for y in range(self.height() - self._padding, self.height() + 1)]
    
    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton and not self.mPos:
    #         self.mPos = event.pos()
    #         event.accept()
    #     return

    #     if (event.button() == Qt.LeftButton) and (event.pos() in self._corner_rect):
    #         self._corner_drag = True
    #         event.accept()
    #     elif (event.button() == Qt.LeftButton) and (event.pos() in self._right_rect):
    #         self._right_drag = True
    #         event.accept()
    #     elif (event.button() == Qt.LeftButton) and (event.pos() in self._bottom_rect):
    #         self._bottom_drag = True
    #         event.accept()
    #     # elif (event.button() == Qt.LeftButton) and (event.y() < self.titleBar.height()):
    #     #     self._move_drag = True
    #     #     self.move_DragPosition = event.globalPos() - self.pos()
    #     #     event.accept()
    
    # def mouseMoveEvent(self, event): # QMouseEvent
    #     if event.buttons() == Qt.LeftButton and self.mPos:
    #         pos = self.mapToGlobal(event.pos() - self.mPos)
    #         if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
    #             return
    #         self.move(pos)
    #         event.accept()
    #     return

    #     if QMouseEvent.pos() in self._corner_rect:
    #         self.setCursor(Qt.SizeFDiagCursor)
    #     elif QMouseEvent.pos() in self._bottom_rect:
    #         self.setCursor(Qt.SizeVerCursor)
    #     elif QMouseEvent.pos() in self._right_rect:
    #         self.setCursor(Qt.SizeHorCursor)
    #     else:
    #         self.setCursor(Qt.ArrowCursor)
    #     if Qt.LeftButton and self._right_drag:
    #         self.resize(QMouseEvent.pos().x(), self.height())
    #         QMouseEvent.accept()
    #     elif Qt.LeftButton and self._bottom_drag:
    #         self.resize(self.width(), QMouseEvent.pos().y())
    #         QMouseEvent.accept()
    #     elif Qt.LeftButton and self._corner_drag:
    #         self.resize(QMouseEvent.pos().x(), QMouseEvent.pos().y())
    #         QMouseEvent.accept()
    #     # elif Qt.LeftButton and self._move_drag:
    #     #     self.move(QMouseEvent.globalPos() - self.move_DragPosition)
    #     #     QMouseEvent.accept()
    
    # def mouseReleaseEvent(self, event):
    #     if self.mPos:
    #         self.mPos = None
    #         self.setCursor(Qt.ArrowCursor)
    #         event.accept()
    #     return

    #     self._move_drag = False
    #     self._corner_drag = False
    #     self._bottom_drag = False
    #     self._right_drag = False
    #     self.setCursor(Qt.ArrowCursor)


class TextEdit(QTextEdit):
    def __init__(self,parent=None):
        super(TextEdit,self).__init__(parent=None)

    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Tab:
            tc = self.textCursor()
            tc.insertText("    ")
            return
        return QTextEdit.keyPressEvent(self,event)

class PlainTextEdit(QPlainTextEdit):
    def __init__(self,parent=None):
        super(QPlainTextEdit,self).__init__(parent=None)

    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Tab:
            tc = self.textCursor()
            tc.insertText("    ")
            return
        return QPlainTextEdit.keyPressEvent(self,event)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    style = '''
    QWidget {
    }
    .customTilebarWindow {
        background-color: white;
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
        background-color: gray;
    }
    '''

    class MainWindow(QMainWindow, CustomTitleBarWindowMixin):
        _padding = 5
        def __init__(self) -> None:
            super(QMainWindow, self).__init__()
            label = QLabel("hello hhhhhhhhhhh")
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.contentWidget.setLayout(layout)
            self.resize(800, 600)
            self.show()

    app = QApplication(sys.argv)
    app.setStyleSheet(style)
    w = MainWindow()
    # w2 = MainWindow()
    eventFilter = EventFilter()
    eventFilter.listenWindow(w)
    # eventFilter.listenWindow(w2)
    app.installEventFilter(eventFilter)
    app.exec_()

