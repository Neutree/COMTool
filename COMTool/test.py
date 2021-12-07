# import unittest,sys
# from COMTool import Main,helpAbout
#
# class COMTest(unittest.TestCase):
#
#     def setUp(self):
#         print("setup")
#
#     def tearDown(self):
#         print("teardown")
#
#     def test_1(self):
#         print("test",sys.prefix)
#         Main.main()
#
# if __name__=="__main__":
#     unittest.main()
#


# from PyQt5.QtCore import pyqtSignal,Qt
# from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
#                              QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
#                              QLineEdit,QGroupBox,QSplitter)
# from PyQt5.QtWidgets import QComboBox,QListView
# from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap
# from PyQt5.QtCore import pyqtSignal
# import  sys

# class MyClass(object):
#     def __init__(self, arg):
#         super(MyClass, self).__init__()
#         self.arg = arg

# class myWindow(QWidget):
#     def __init__(self, parent=None):
#         super(myWindow, self).__init__(parent)

#         self.comboBox = QComboBox(self)
#         self.comboBox.addItems([str(x) for x in range(3)])

#         self.myObject=MyClass(self )

#         slotLambda = lambda: self.indexChanged_lambda(self.myObject)
#         self.comboBox.currentIndexChanged.connect(slotLambda)

#     # @QtCore.pyqtSlot(str)
#     def indexChanged_lambda(self, obj):
#         print('lambda:', type(obj), obj.arg.comboBox.currentText())

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     app.setApplicationName('myApp')
#     dialog = myWindow()
#     dialog.show()
#     sys.exit(app.exec_())



import re
class A:
    def __init__(self) -> None:
        self.lastColor = None

    def _getColorByfmt(self, fmt:bytes):
        colors = {
            b"0": "#000000",
            b"31": "#ff0000",
            b"32": "#008000",
            b"33": "#ffff00"
        }
        fmt = fmt[2:-1].split(b";")
        if len(fmt) == 1:
            color = colors[b"0"]
        else:
            style, color = fmt
            color = colors[color]
        return color

    def _texSplitByColor(self, text:bytes):
        if not self.lastColor:
            self.lastColor = "#000000"
        colorFmt = re.findall(rb'\x1b\[.*?m', text)
        colorStrs = []
        if colorFmt:
            p = 0
            for fmt in colorFmt:
                idx = text[p:].index(fmt)
                if idx != 0:
                    colorStrs.append((self.lastColor, text[p:p+idx]))
                    p += idx
                self.lastColor = self._getColorByfmt(fmt)
                p += len(fmt)
            if p != len(text):
                colorStrs.append((self.lastColor, text[p:]))
        else:
            colorStrs = [(self.lastColor, text)]
        return colorStrs

text = b'\x1b[0;32mI (1092) esp_qcloud_prov: Scan this QR code from the Wechat for Provisioning.\x1b[0m'
text2 = b'\x1b[0;32mI (1092) esp_qcloud_prov: Scan this QR code from the Wechat for Provisioning.\x1b[0mProvisioning'

a = A()
text = a._texSplitByColor(text)
print(text)
print(a._texSplitByColor(text2))
