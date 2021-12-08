import os, sys, shutil
sys.path.insert(1,"./COMTool/")
from COMTool import version, i18n

# update translate
i18n.main("finish")

if os.path.exists("COMTool/__pycache__"):
    shutil.rmtree("COMTool/__pycache__")

os.chdir("COMTool")
if sys.platform.startswith("win32"):
    cmd = 'pyinstaller --hidden-import babel.numbers  --add-data="assets;assets" --add-data="locales;locales" --add-data="../README.MD;./" -i="assets/logo.ico" -w Main.py -n comtool'
elif sys.platform.startswith("darwin"):
    cmd = 'pyinstaller --hidden-import babel.numbers --add-data="assets:assets" --add-data="locales:locales"--add-data="../README.MD:./" -i="assets/logo.icns" -w Main.py  -n comtool'
else:
    cmd = 'pyinstaller --hidden-import babel.numbers --add-data="assets:assets" --add-data="locales:locales"--add-data="../README.MD:./" -i="assets/logo.png" -w Main.py  -n comtool'

os.system(cmd)

os.chdir("..")

if sys.platform.startswith("darwin"):
    if os.path.exists("./COMTool/dist/comtool 0.0.0.dmg"):
        os.remove("./COMTool/dist/comtool 0.0.0.dmg")
        
    os.system('npm install --global create-dmg && create-dmg ./COMTool/dist/comtool.app ./COMTool/dist')
    os.rename("./COMTool/dist/comtool 0.0.0.dmg", 
            "./COMTool/dist/comtool_v{}.dmg".format(version.__version__))


