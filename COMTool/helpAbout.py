import sys
from COMTool import parameters

versionMajor = 1
versionMinor = 1
versionDev   = 7
date = "2017.7.26"

def strAbout():
    pythonPathArray = sys.path
    for i in pythonPathArray:
        if i.find("site-packages"):
            pythonPath = i[0:i.find("lib")]
    return '''\
Python 3.6.1 + PyQt5<br><br>
<div><div>COMTool is a Open source project create by </div><a style="vertical-align: middle;" href="http://www.neucrack.com"><img src="'''+pythonPath+ parameters.strDataDirName+'''/logo2.png" width=109 height=32></img></a></div><br><br>

See more on <b><a href="https://github.com/neutree/COMTool.git">Github</a></b><br><br>
Welcome to improve it together<br><br>


Shortcut:<br>
<b style="color:red;"><kbd>Ctrl+Enter</kbd></b>: Send data<br> 

'''