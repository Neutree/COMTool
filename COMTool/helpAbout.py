import sys
from COMTool import parameters
import os

versionMajor = 1
versionMinor = 2
versionDev   = 3
date = "2017.7.28"

def strAbout():
    pathDirList = sys.argv[0].replace("\\", "/").split("/")
    pathDirList.pop()
    pathDirList.pop()
    strPath = os.path.abspath("/".join(str(i) for i in pathDirList))
    return '''\
Python 3.6.1 + PyQt5<br><br>
<div><div>COMTool is a Open source project create by </div><a style="vertical-align: middle;" href="http://www.neucrack.com"><img src="'''+strPath+"/"+parameters.appLogo2+'''" width=109 height=32></img></a></div><br><br>

See more on <b><a href="https://github.com/neutree/COMTool.git">Github</a></b><br><br>
Welcome to improve it together<br><br>


Shortcut:<br>
<b style="color:red;"><kbd>Ctrl+Enter</kbd></b>: Send data<br> 

'''