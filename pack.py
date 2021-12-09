import os, sys, shutil
sys.path.insert(1,"./COMTool/")
from COMTool import version, i18n
import zipfile
import shutil


if sys.version_info < (3, 8):
    print("only support python >= 3.8, but now is {}".format(sys.version_info))
    sys.exit(1)


linux_out = "comtool_ubuntu_v{}.tar.xz".format(version.__version__)
macos_out = "comtool_macos_v{}.dmg".format(version.__version__)
windows_out = "comtool_windows_v{}.zip".format(version.__version__)

def zip(out, path):
    out = os.path.abspath(out)
    cwd = os.getcwd()
    os.chdir(os.path.dirname(path))
    with zipfile.ZipFile(out,'w', zipfile.ZIP_DEFLATED) as target:
        for i in os.walk(os.path.basename(path)):
            for n in i[2]:
                target.write(os.path.join(i[0],n))
    os.chdir(cwd)

def pack():
    # update translate
    i18n.main("finish")

    if os.path.exists("COMTool/__pycache__"):
        shutil.rmtree("COMTool/__pycache__")

    if sys.platform.startswith("win32"):
        cmd = 'pyinstaller --hidden-import babel.numbers --add-data="COMTool/assets;COMTool/assets" --add-data="COMTool/locales;COMTool/locales" --add-data="README.MD;./" -i="COMTool/assets/logo.ico" -w COMTool/Main.py -n comtool'
    elif sys.platform.startswith("darwin"):
        # macos not case insensitive, so can not contain comtool file and COMTool dir, so we copy to binary root dir
        cmd = 'pyinstaller --hidden-import babel.numbers --add-data="COMTool/assets:assets" --add-data="COMTool/locales:locales" --add-data="README.MD:./" -i="COMTool/assets/logo.icns" -w COMTool/Main.py  -n comtool'
    else:
        cmd = 'pyinstaller --hidden-import babel.numbers --add-data="COMTool/assets:assets" --add-data="COMTool/locales:locales" --add-data="README.MD:./" -i="COMTool/assets/logo.ico" -w COMTool/Main.py -n comtool'

    os.system(cmd)

    if sys.platform.startswith("darwin"):
        if os.path.exists("./dist/comtool 0.0.0.dmg"):
            os.remove("./dist/comtool 0.0.0.dmg")
            
        os.system('npm install --global create-dmg && create-dmg ./dist/comtool.app ./dist')
        shutil.copyfile("./dist/comtool 0.0.0.dmg", macos_out)
    elif sys.platform.startswith("win32"):
        zip(windows_out, "dist/comtool")
    else:
        cmd = "cd dist && tar -Jcf {} comtool/ && mv {} ../ && cd ..".format(linux_out, linux_out)
        os.system(cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        os_name = sys.argv[1]
        if os_name == "ubuntu-latest":
            print(linux_out)
        elif os_name == "windows-latest":
            print(windows_out)
        elif os_name == "macos-latest":
            print(macos_out)
        else:
            sys.exit(1)
    else:
        pack()

