import sys
try:
    import parameters
    from i18n import _
    import version
except ImportError:
    from COMTool import parameters
    from COMTool.i18n import _
    from COMTool import version
    
import os
import PyQt5.QtCore
import time


def strAbout():
    return '''\
<h1 style='color:#f75a5a';margin=10px;>{}</h1><br>
<b style="color:#08c7a1;margin = 5px;">v{}</b><br><br>
{} + {}<br>
{}:{}
<br>
<div>
    <div>{}</div>
    <a style="vertical-align: middle;" href="https://neucrack.com">
        <img src="{}" width=109 height=32/></a>
</div>
{}<br>
{} <b><a href="https://github.com/neutree/COMTool">Github</a></b><br>
{} <b><a href="https://neucrack.com/donate"> neucrack.com/donate</a></b><br>
{} <b><a href="https://github.com/Neutree/COMTool/issues"> issues</a></b><br><br>
{}<br>
 <b style="color:red;"><kbd>F11</kbd></b>: {}<br>
<b style="color:red;"><kbd>Ctrl+Enter</kbd></b>: {}<br>
 <b style="color:red;"><kbd>Ctrl+L</kbd></b>: {}<br>
 <b style="color:red;"><kbd>Ctrl+K</kbd></b>: {}<br>

'''.format(
    parameters.appName,
    version.__version__,
    '{}{}.{}'.format(sys.implementation.name, sys.implementation.version.major, sys.implementation.version.minor),
    'PyQt{}'.format(PyQt5.QtCore.QT_VERSION_STR),
    _("Config path"),
    parameters.configFilePath,
    _('COMTool is a Open source project create by'),
    '{}/{}'.format(parameters.dataPath, parameters.appLogo2),
    _('Welcome to improve it together'),
    _('See more details on'),
    _("Donate"),
    _("Have problem? see"),
    _('Shortcut:'),
    _('Full screen'),
    _('Send data'),
    _('Clear Send Area'),
    _('Clear Receive Area'),
)
