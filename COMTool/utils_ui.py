try:
    from Combobox import ComboBox
    from i18n import _
    import utils, parameters
except ImportError:
    from COMTool import utils, parameters
    from COMTool.i18n import _
    from COMTool.Combobox import ComboBox

import qtawesome as qta # https://github.com/spyder-ide/qtawesome

_buttonIcons = {}
_skin = "light"

def setSkin(skin):
    global _skin, _buttonIcons

    if skin == _skin:
        return
    for btn in _buttonIcons:
        icon, colorVar = _buttonIcons[btn]
        color = parameters.styleForCode[skin][colorVar]
        btn.setIcon(qta.icon(icon, color=color))
    _skin = skin    

def setButtonIcon(button, icon : str, colorVar = "iconColor"):
    '''
        @colorVar set in parameters.styleForCode
    '''
    global _skin, _buttonIcons

    iconColor = parameters.styleForCode[_skin][colorVar]
    _buttonIcons[button] = [icon, colorVar]
    button.setIcon(qta.icon(icon, color=iconColor))
