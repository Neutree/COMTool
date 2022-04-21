from audioop import add
import ctypes
from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QEvent, QObject
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStyleOption, QStyle, QPushButton, QTextEdit,
                            QPlainTextEdit, QMainWindow, QComboBox, QListView, QTabWidget, QStackedWidget, QListWidget,
                            QGridLayout, QLineEdit, QDialog, QScrollArea)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QMouseEvent, QColor, QKeyEvent, QHideEvent, QKeySequence
import qtawesome as qta # https://github.com/spyder-ide/qtawesome
import os, sys

try:
    import utils_ui
    from Combobox import ComboBox
    from i18n import _
    import parameters
    from qta_icon_browser import selectIcon
except Exception:
    from COMTool import utils_ui
    from COMTool.Combobox import ComboBox
    from COMTool.i18n import _
    from COMTool import parameters
    from COMTool.qta_icon_browser import selectIcon


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
        self.top.clicked.connect(lambda : self.onSetTop())
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

    def onSetTop(self, on = None):
        flags = self.parent.windowFlags()
        needShow = self.parent.isVisible()
        def _on(flags):
            flags |= Qt.WindowStaysOnTopHint
            self.parent.setWindowFlags(flags)
            utils_ui.setButtonIcon(self.top, self.btnIcons[3][1])
            self.top.setProperty("class", "topActive")
        def _off(flags):
            flags &=  (~Qt.WindowStaysOnTopHint)
            self.parent.setWindowFlags(flags)
            utils_ui.setButtonIcon(self.top, self.btnIcons[3][0])
            self.top.setProperty("class", "top")
        oldOn = flags & Qt.WindowStaysOnTopHint
        if on is None:
            on = False if oldOn else True
        if on:
            if not oldOn:
                _on(flags)
        else:
            if oldOn:
                _off(flags)
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

    def setTitle(self, title):
        self.title.setText(title)

class EventFilter(QObject):
    Margins = 5  # 边缘边距
    windows = []
    _readyToMove = False
    _moving = False
    _resizeCursor = False

    def listenWindow(self, window):
        self.windows.append(window)

    def unlistenWindow(self, window):
        self.windows.remove(window)

    def _get_edges(self, pos, width, height, offset=0):
        edge = 0
        x, y = pos.x(), pos.y()

        if y <= self.Margins - offset and y >= 0:
            edge |= Qt.TopEdge
        if x <= self.Margins - offset and x >= 0:
            edge |= Qt.LeftEdge
        if x >= width - self.Margins + offset and x < width:
            edge |= Qt.RightEdge
        if y >= height - self.Margins + offset and y < height:
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
                cursor = self._get_cursor(self._get_edges(event.pos(), obj.width(), obj.height(), offset=1))
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
    def __init__(self, titleBar = None, init = False, title = "", icon = os.path.join(parameters.assetsDir, "logo.png")):
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
            self.titleBar = TitleBar(self, icon = icon, title=title, height=35)
        # setWindowIcon
        self.setWindowIcon(QIcon(icon))
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("comtool") # for add taskbar icon
        self.contentWidget = QWidget()
        self.rootLayout.addWidget(self.titleBar)
        self.rootLayout.addWidget(self.contentWidget)
        self.root.setLayout(self.rootLayout)
        self.rootLayout.setContentsMargins(0, 0, 0, 0) # padding
        self.root.setMouseTracking(True)
        self.titleBar.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        if sys.platform == "win32":
            try:
                from win32_utils import addShadowEffect
            except Exception:
                from COMTool.win32_utils import addShadowEffect
            addShadowEffect(self.winId())
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
    onSave = lambda : None
    def __init__(self,parent=None):
        super(QPlainTextEdit,self).__init__(parent=None)
        self.keyControlPressed = False

    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = True
            return
        elif event.key() == Qt.Key_Tab:
            tc = self.textCursor()
            tc.insertText("    ")
            event.accept()
            return
        elif event.key() == Qt.Key_S:
            self.onSave()
        return QPlainTextEdit.keyPressEvent(self,event)

    def onKeyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyControlPressed = False

class _ListView(QListView):
    focusout = pyqtSignal()

    def event(self, e):
        if type(e) == QHideEvent:
            # focusOutEvent event not triggered in Linux, maybe a bug?
            # so use hide event instead
            self.focusout.emit()
        return super().event(e)

    # def focusOutEvent(self, event):
    #     self.focusout.emit()

class _Combobox(QComboBox):
    clicked = pyqtSignal()
    listviewFocusout = pyqtSignal()
    def __init__(self):
        super().__init__()
        listView = _ListView()
        listView.executeDelayedItemsLayout()
        listView.focusout.connect(lambda: self.listviewFocusout.emit())
        self.setView(listView)

    def mouseReleaseEvent(self, QMouseEvent):
        self.showItems()

    def showPopup(self):
        # self.popupAboutToBeShown.emit()
        # prevent show popup, manually call it in mouse release event
        pass

    def _showPopup(self):
        max_w = 0
        for i in range(self.count()):
            w = self.view().sizeHintForColumn(i)
            if w > max_w:
                max_w = w
        self.view().setMinimumWidth(max_w + 50)
        super().showPopup()

    def showItems(self):
        self._showPopup()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


class ButtonCombbox(QWidget):
    activated = pyqtSignal(int)
    currentIndexChanged = pyqtSignal()
    def __init__(self, text="", icon = None, btnClass="smallBtn") -> None:
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(2,2,2,2)
        self.setLayout(layout)
        self.button = QPushButton(text)
        self.button.setProperty("class", btnClass)
        if icon:
            utils_ui.setButtonIcon(self.button, icon)
        self.list = _Combobox()
        layout.addWidget(self.button)
        layout.addWidget(self.list)
        self.list.hide()
        self.button.clicked.connect(lambda:self._ctrl("show"))
        def onAvtivated(idx):
            self.activated.emit(idx)
            self._ctrl("hide")
        self.list.activated.connect(lambda idx: onAvtivated(idx))
        self.list.currentIndexChanged.connect(lambda:self.currentIndexChanged.emit())
        self.list.listviewFocusout.connect(self._listFocusout)

    def _ctrl(self, cmd):
        if cmd == "show":
            if self.list.count() == 0:
                return
            self.button.hide()
            self.list.show()
            self.list.showItems()
            self.list.setFocus()
        elif cmd == "hide":
            self.list.hide()
            self.button.show()

    def _listFocusout(self):
        self._ctrl("hide")

    def addItem(self, item):
        self.list.addItem(item)

    def insertItem(self, idx, item):
        self.list.insertItem(idx, item)

    def count(self):
        return self.list.count()

    def findText(self, text):
        return self.list.findText(text)

    def currentIndex(self):
        return self.list.currentIndex()

    def setCurrentIndex(self, idx):
        self.list.setCurrentIndex(idx)

    def currentText(self):
        return self.list.currentText()

class statusBar(QWidget):
    updateUiSignal = pyqtSignal(str, str)
    def __init__(self, rxTxCount = False):
        super().__init__()
        self.rxTxCount = rxTxCount
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.msg = QLabel()
        layout.addWidget(self.msg)
        if rxTxCount:
            self.rx = QLabel('{}({}): {}'.format(_("Received"), _("bytes"), 0))
            self.tx = QLabel('{}({}): {}'.format(_("Sent"), _("bytes"), 0))
            layout.addWidget(self.tx)
            layout.addWidget(self.rx)
        self.updateUiSignal.connect(self._updateUi)
        self.setProperty("class", "statusBar")
        self.rxCount = 0
        self.txCount = 0

    def _updateUi(self, updateType, msg):
        if updateType == "rx":
            self.rx.setText(msg)
        elif updateType == "tx":
            self.tx.setText(msg)
        elif updateType == "msg":
            self.msg.setText(msg)

    def addRx(self, count):
        if not self.rxTxCount:
            return
        self.rxCount += count
        msg = '{}({}): {}'.format(_("Received"), _("bytes"), self.rxCount)
        self.updateUiSignal.emit("rx", msg)

    def addTx(self, count):
        if not self.rxTxCount:
            return
        self.rxCount += count
        msg = '{}({}): {}'.format(_("Sent"), _("bytes"), self.rxCount)
        self.updateUiSignal.emit("tx", msg)

    def clear(self):
        self.rxCount = 0
        self.txCount = 0
        self.addTx(0)
        self.addRx(0)

    def setMsg(self, level, msg):
        if level == "info":
            color = "#008200"
        elif level == "warning":
            color = "#fb8c00"
        elif level == "error":
            color = "#f44336"
        else:
            color = "#008200"
        msg = '<font color={}>{}</font>'.format(color, msg)
        self.updateUiSignal.emit("msg", msg)

class HelpWidget(QWidget, CustomTitleBarWindowMixin):
    closed = pyqtSignal()
    def __init__(self, pluginsHelp:dict, parent=None, icon=None):
        QWidget.__init__(self, parent)
        CustomTitleBarWindowMixin.__init__(self, init=True, title=_("Help"))
        self.resize(800, 700)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.contentWidget.setLayout(layout)
        # self.setLayout(layout)
        itemList = QListWidget()
        itemList.setProperty("class", "helpList")
        tabs = QStackedWidget()
        layout.addWidget(itemList)
        layout.addWidget(tabs)
        layout.setStretch(0, 1)
        layout.setStretch(1, 4)
        for name, help in pluginsHelp.items():
            tab = QWidget()
            tab.setProperty("class", "helpTab")
            tabLayout = QVBoxLayout()
            tab.setLayout(tabLayout)
            if type(help) == str:
                tabLabel = ScrollLabel(help)
            else:
                tabLabel = help
            tabLayout.addWidget(tabLabel)
            tabs.addWidget(tab)
            itemList.addItem(name)
        itemList.setCurrentRow(0)
        itemList.currentRowChanged.connect(lambda idx: tabs.setCurrentIndex(idx))
        self.show()

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()



class EditRemarDialog(QDialog):
    def __init__(self, remark = "", icon=None, shortcut = [], value=None) -> None:
        super().__init__()
        self.remark = remark
        self.icon = icon
        self.ok = False
        self.settingShortcut = False
        self.shortcut = shortcut
        self.value = value

        layout = QGridLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(_("Input remark")), 0, 0, 1, 1)
        self.remarkInput = QLineEdit(self.remark)
        if self.value is not None:
            self.valueInput = QLineEdit(self.value)
        self.iconBtn = QPushButton(self.remark)
        if self.icon:
            self.iconBtn.setIcon(qta.icon(self.icon, color="white"))
        if self.shortcut:
            name = "+".join([str(name) for v,name in self.shortcut])
        else:
            name = _("Record")
        self.shortcutBtn = QPushButton(name)
        self.shortcutBtn.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.remarkInput, 0, 1, 1, 1)
        if self.value is not None:
            layout.addWidget(QLabel(_("Input value")), 1, 0, 1, 1)
            layout.addWidget(self.valueInput, 1, 1, 1, 1)
        layout.addWidget(QLabel(_("Select icon")), 2, 0, 1, 1)
        layout.addWidget(self.iconBtn, 2, 1, 1, 1)
        layout.addWidget(QLabel(_("Shortcut")), 3, 0, 1, 1)
        layout.addWidget(self.shortcutBtn, 3, 1, 1, 1)
        self.shortcutHint = QLabel(_("Press key to record, or click Cancel"))
        self.shortcutHint.hide()
        layout.addWidget(self.shortcutHint, 4, 0, 1, 2)
        self.okBtn = QPushButton(_("OK"))
        self.cancelBtn = QPushButton(_("Cancel"))
        layout.addWidget(self.okBtn, 5, 0, 1, 1)
        layout.addWidget(self.cancelBtn, 5, 1, 1, 1)

        def ok():
            self.ok = True
            self.close()
        self.okBtn.clicked.connect(lambda : ok())
        self.cancelBtn.clicked.connect(lambda : self.close())
        def updateRemark(text):
            self.remark = text
            self.iconBtn.setText(self.remark)
        self.remarkInput.textChanged.connect(updateRemark)
        self.iconBtn.clicked.connect(lambda: self.selectIcon())
        self.shortcutBtn.clicked.connect(self.setShortcut)

    def selectIcon(self):
        self.icon = selectIcon(parent = self, title = _("Select icon"), btnName = _("OK"), color = utils_ui.getStyleVar("iconSelectorColor"))
        if self.icon:
            self.iconBtn.setIcon(qta.icon(self.icon, color="white"))
        else:
            self.iconBtn.setIcon(QIcon())

    def exec(self):
        super().exec()
        if self.value is not None:
            self.value = self.valueInput.text()
            return self.ok, self.remark, self.value, self.icon, self.shortcut
        return self.ok, self.remark, self.icon, self.shortcut

    def setShortcut(self):
        if not self.settingShortcut:
            self.onRecordShortcut()
        else:
            self.onRecordShortcutEnd()

    def onRecordShortcut(self):
        self.shortcut = []
        self.remarkInput.setEnabled(False)
        self.valueInput.setEnabled(False)
        self.iconBtn.setEnabled(False)
        self.okBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)
        self.shortcutBtn.setText(_("Cancel"))
        self.shortcutHint.show()
        self.settingShortcut = True
        self.shortcutBtn.setProperty("class", "deleteBtn")
        self.updateStyle(self.shortcutBtn)

    def onRecordShortcutEnd(self, setOk=False):
        self.remarkInput.setEnabled(True)
        self.valueInput.setEnabled(True)
        self.iconBtn.setEnabled(True)
        self.okBtn.setEnabled(True)
        self.cancelBtn.setEnabled(True)
        if not setOk:
            self.shortcutBtn.setText(_("Record"))
            self.shortcut = []
        self.shortcutHint.hide()
        self.settingShortcut = False
        self.shortcutBtn.setProperty("class", "")
        self.updateStyle(self.shortcutBtn)

    def keyPressEvent(self, event):
        if not self.settingShortcut:
            return
        key = event.key()
        name = QKeySequence(key).toString()
        if key == Qt.Key_Control:
            name = "Ctrl"
        elif key == Qt.Key_Shift:
            name = "Shift"
        elif key == Qt.Key_Alt:
            name = "Alt"
        elif key == Qt.Key_Super_L:
            name = "Super_L"
        elif key == Qt.Key_Super_R:
            name = "Super_R"
        self.shortcut.append((key, name))
        keys = "+".join([str(name) for v,name in self.shortcut])
        self.shortcutBtn.setText(keys)

    def keyReleaseEvent(self,event):
        if not self.settingShortcut:
            return
        self.onRecordShortcutEnd(setOk = True)

    def updateStyle(self, widget):
        self.style().unpolish(widget)
        self.style().polish(widget)
        self.update()

class ScrollLabel(QScrollArea):

    # constructor
    def __init__(self, text, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self.setWidgetResizable(True)
        # making qwidget object
        content = QWidget(self)
        self.setProperty("class", "scrollbar2")
        self.setWidget(content)
        # vertical box layout
        lay = QVBoxLayout(content)
        # creating label
        self.label = QLabel(text, parent = content)
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        # setting alignment to the text
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # making label multi-line
        self.label.setWordWrap(True)
        # adding label to the layout
        lay.addWidget(self.label)

    def setText(self, text):
        self.label.setText(text)


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
    app.removeEventFilter(eventFilter)

