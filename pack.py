import os, sys, shutil

if os.path.exists("COMTool/__pycache__"):
    shutil.rmtree("COMTool/__pycache__")

if sys.platform.startswith("win32"):
    cmd = 'pyinstaller --add-data="COMToolData;COMToolData" --add-data="README.MD;./" -i="COMToolData/assets/logo.ico" -w COMTool/Main.py -n comtool'
elif sys.platform.startswith("darwin"):
    cmd = 'pyinstaller --add-data="COMToolData:COMToolData" --add-data="README.MD:./" -i="COMToolData/assets/logo.icns" -w COMTool/Main.py  -n comtool'
else:
    cmd = 'pyinstaller --add-data="COMToolData:COMToolData" --add-data="README.MD:./" -i="COMToolData/assets/logo.png" -w COMTool/Main.py  -n comtool'

os.system(cmd)



