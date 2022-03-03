try:
    from Combobox import ComboBox
    from i18n import _
    import utils, parameters
except ImportError:
    from COMTool import utils, parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon
import qtawesome as qta # https://github.com/spyder-ide/qtawesome

_buttonIcons = {}
_skin = "light"

def setSkin(skin):
    global _skin, _buttonIcons

    if skin == _skin:
        return
    delete = []
    for btn in _buttonIcons:
        if type(btn.parent()) == None:
            delete.append(btn)
            continue
        icon, colorVar = _buttonIcons[btn]
        color = parameters.styleForCode[skin][colorVar]
        btn.setIcon(qta.icon(icon, color=color))
    for btn in delete:
        _buttonIcons.pop(btn)
    _skin = skin    

def setButtonIcon(button, icon : str, colorVar = "iconColor"):
    '''
        @colorVar set in parameters.styleForCode
    '''
    global _skin, _buttonIcons

    iconColor = parameters.styleForCode[_skin][colorVar]
    _buttonIcons[button] = [icon, colorVar]
    button.setIcon(qta.icon(icon, color=iconColor))

def clearButtonIcon(button):
    global _skin, _buttonIcons
    if button in _buttonIcons:
        button.setIcon(QIcon())
        _buttonIcons.pop(button)

def getStyleVar(var):
    global _skin, _buttonIcons

    return parameters.styleForCode[_skin][var]

def updateStyle(parent, widget):
    parent.style().unpolish(widget)
    parent.style().polish(widget)
    parent.update()