import os, sys, shutil
sys.path.insert(1,"./COMTool/")
from COMTool import version, i18n
import zipfile
import shutil
import re


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

def upadte_spec_plist(spec_path, items={}):
    with open(spec_path) as f:
        spec = f.read()
    def BUNDLE(*args, **kw_args):
        if "info_plist" in kw_args:
            kw_args["info_plist"].update(items)
        else:
            kw_args["info_plist"] = items
        bundle_str_args = ""
        for arg in args:
            if type(arg) == str and arg != "exe":
                bundle_str_args += f'"{arg}", \n'
            else:
                bundle_str_args += f'{arg}, \n'
        for k, v in kw_args.items():
            if type(v) == str:
                bundle_str_args += f'{k}="{v}",\n'
            else:
                bundle_str_args += f'{k}={v},\n'
        return bundle_str_args

    match = re.findall(r'BUNDLE\((.*?)\)', spec, flags=re.MULTILINE|re.DOTALL)
    if len(match) <= 0:
        raise Exception("no BUNDLE found in spec, please check code")
    code =f'app = BUNDLE({match[0]})'
    vars = {
        "BUNDLE": BUNDLE,
        "exe": "exe"
    }
    exec(code, vars)
    final_str = vars["app"]

    def re_replace(c):
        print(c[0])
        return f'BUNDLE({final_str})'

    final_str = re.sub(r'BUNDLE\((.*)\)', re_replace, spec, flags=re.I|re.MULTILINE|re.DOTALL)
    print(final_str)

    with open(spec_path, "w") as f:
        f.write(spec)

def pack():
    # update translate
    i18n.main("finish")

    if os.path.exists("COMTool/__pycache__"):
        shutil.rmtree("COMTool/__pycache__")

    if sys.platform.startswith("win32"):
        cmd = ' --hidden-import babel.numbers -p "COMTool" --add-data="COMTool/assets;COMTool/assets" --add-data="COMTool/locales;COMTool/locales" --add-data="README.MD;./" --add-data="README_ZH.MD;./" -i="COMTool/assets/logo.ico" -w COMTool/Main.py -n comtool'
    elif sys.platform.startswith("darwin"):
        # macos not case insensitive, so can not contain comtool file and COMTool dir, so we copy to binary root dir
        cmd = 'pyi-makespec --hidden-import babel.numbers -p "COMTool" --add-data="COMTool/assets:assets" --add-data="COMTool/locales:locales" --add-data="README_ZH.MD:./" --add-data="README.MD:./" -i="COMTool/assets/logo.icns" -w COMTool/Main.py  -n comtool'
        os.system(cmd)
        upadte_spec_plist("comtool.spec", {"LSMultipleInstancesProhibited": False}) # enable multi instance support
        cmd = 'pyinstaller comtool.spec'
    else:
        cmd = 'pyinstaller --hidden-import babel.numbers -p "COMTool" --add-data="COMTool/assets:assets" --add-data="COMTool/locales:locales" --add-data="README.MD:./" --add-data="README_ZH.MD:./" -i="COMTool/assets/logo.ico" -w COMTool/Main.py -n comtool'

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

