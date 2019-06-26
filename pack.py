import os, sys, shutil
sys.path.insert(1,"./COMTool/")
from COMTool import helpAbout

if os.path.exists("COMTool/__pycache__"):
    shutil.rmtree("COMTool/__pycache__")

if sys.platform.startswith("win32"):
    cmd = 'pyinstaller --add-data="COMToolData;COMToolData" --add-data="README.MD;./" -i="COMToolData/assets/logo.ico" -w COMTool/Main.py -n comtool'
elif sys.platform.startswith("darwin"):
    cmd = 'pyinstaller --add-data="COMToolData:COMToolData" --add-data="README.MD:./" -i="COMToolData/assets/logo.icns" -w COMTool/Main.py  -n comtool'
else:
    cmd = 'pyinstaller --add-data="COMToolData:COMToolData" --add-data="README.MD:./" -i="COMToolData/assets/logo.png" -w COMTool/Main.py  -n comtool'

os.system(cmd)

if sys.platform.startswith("darwin"):
    if os.path.exists("./dist/comtool 0.0.0.dmg"):
        os.remove("./dist/comtool 0.0.0.dmg")
        
    os.system('create-dmg ./dist/comtool.app ./dist')
    os.rename("./dist/comtool 0.0.0.dmg", 
            "./dist/comtool_v{}.{}.{}.dmg".format(helpAbout.versionMajor, helpAbout.versionMinor, helpAbout.versionDev))


