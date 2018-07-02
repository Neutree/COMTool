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


from PyQt5.QtCore import pyqtSignal,Qt
from PyQt5.QtWidgets import (QApplication, QWidget,QToolTip,QPushButton,QMessageBox,QDesktopWidget,QMainWindow,
                             QVBoxLayout,QHBoxLayout,QGridLayout,QTextEdit,QLabel,QRadioButton,QCheckBox,
                             QLineEdit,QGroupBox,QSplitter)
from PyQt5.QtWidgets import QComboBox,QListView
from PyQt5.QtGui import QIcon,QFont,QTextCursor,QPixmap
from PyQt5.QtCore import pyqtSignal
import  sys

class MyClass(object):
    def __init__(self, arg):
        super(MyClass, self).__init__()
        self.arg = arg

class myWindow(QWidget):
    def __init__(self, parent=None):
        super(myWindow, self).__init__(parent)

        self.comboBox = QComboBox(self)
        self.comboBox.addItems([str(x) for x in range(3)])

        self.myObject=MyClass(self )

        slotLambda = lambda: self.indexChanged_lambda(self.myObject)
        self.comboBox.currentIndexChanged.connect(slotLambda)

    # @QtCore.pyqtSlot(str)
    def indexChanged_lambda(self, obj):
        print('lambda:', type(obj), obj.arg.comboBox.currentText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName('myApp')
    dialog = myWindow()
    dialog.show()
    sys.exit(app.exec_())