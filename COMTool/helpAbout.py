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
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
import time


def HelpInfo():
        return '''\
<h1 style='color:#009688';margin=10px;>{}</h1><br>
<b style="color:#009688;margin = 5px;">v{}</b><br><br>
{} + {}<br>
{}: {}<br>
{}: {}<br>
<div>
    <div>{}</div>
    <a style="vertical-align: middle;" href="https://neucrack.com">
        <img src="{}" width=109 height=32/></a>
</div>
{}: <b><a style="color:#009688;" href="https://github.com/Neutree/COMTool#license">LGPL-3.0</a></b><br>
{}<br>
{} <b><a style="color:#009688;" href="https://github.com/neutree/COMTool">Github</a></b>, {} <b><a style="color:#009688;" href="https://github.com/Neutree/COMTool/releases"> releases {}</a></b><br>
{} <b><a style="color:#009688;" href="https://github.com/Neutree/COMTool/issues"> issues</a></b><br>
{}: 566531359 <br><br>
{}: <a style="color:#009688;" href="https://neucrack.com/donate">neucrack.com/donate<br><img src="{}"/> <img src="{}"/></a><br>
'''.format(
    parameters.appName,
    version.__version__,
    '{}{}.{}'.format(sys.implementation.name, sys.implementation.version.major, sys.implementation.version.minor),
    'PyQt{}'.format(PyQt5.QtCore.QT_VERSION_STR),
    _("Config path"),
    parameters.configFilePath,
    _("Old config backup in"),
    os.path.dirname(parameters.configFilePath,),
    _('COMTool is a Open source project create by'),
    '{}/{}'.format(parameters.dataPath, parameters.appLogo2),
    _("License"),
    _('Welcome to improve it together and add plugins'),
    _('See more details on'),
    _("and get latest version at"),
    _("page"),
    _("Have problem? see"),
    _("QQ group for plugin development discussion"),
    _("You can buy me half a cup of coffee if this software helpes you"),
    os.path.join(parameters.assetsDir, "donate_wechat.jpg"),
    os.path.join(parameters.assetsDir, "donate_alipay.jpg")
)
